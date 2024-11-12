import logging
import darknet
import cv2
import numpy as np
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import os


class Detector(qtc.QObject):
    sgl_prop_updated = qtc.pyqtSignal(tuple)

    def __init__(self, cfg_path: str = '', data_path: str = '', weights_path: str = '', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logging_enabled = True
        self.xlog_level = logging.getLogger().getEffectiveLevel()
        self.xlog_quiet = True

        self.network = None
        self.net_w = None
        self.net_h = None
        self._thresh: float = 0.5
        self.cfg_path = cfg_path
        self.data_path = data_path
        self.weights_path = weights_path
        self.crop_to_square = False
        self._enabled = False

    def load_network(self):
        self.xlog('Loading network...', logging.INFO)
        err = ''
        if not os.path.isfile(self.cfg_path):
            err += f'No cfg file exists with path: {self.cfg_path}\n'
        if not os.path.isfile(self.data_path):
            err += f'No data file exists with path: {self.data_path}\n'
        if not os.path.isfile(self.weights_path):
            err += f'No weights file exists with path: {self.weights_path}'
        if err is not '':
            self.xlog(err, logging.ERROR)
            raise FileNotFoundError
        self.network, self.class_names, _ = darknet.load_network(self.cfg_path, self.data_path, self.weights_path, 1)
        self.net_w = darknet.network_width(self.network)
        self.net_h = darknet.network_height(self.network)
        self.xlog('Network loaded.', logging.INFO)

    def detect(self, img: np.ndarray):
        img = self._preprocess_image(img)
        darknet_image = darknet.make_image(self.net_w, self.net_h, 3)
        darknet.copy_image_from_bytes(darknet_image, img.tobytes())
        detections = darknet.detect_image(self.network, self.class_names, darknet_image, self._thresh)
        darknet.free_image(darknet_image)
        return img, self._adjust_detections(detections,img.shape[1], img.shape[0])

    def _preprocess_image(self, img: np.ndarray):
        h, w, _ = img.shape
        if self.crop_to_square and h != w:
            x1 = int(w / 2.0 - h / 2.0)
            x2 = x1 + h
            img = img[0:h, x1:x2].copy()
        return cv2.resize(img, (self.net_w, self.net_h), interpolation=cv2.INTER_LINEAR)

    def _adjust_detections(self, detections :list, img_width, img_height):
        detections_adjusted = []
        for label, confidence, bbox in detections:
            bbox_adjusted = self._adjust_bbox(bbox, img_width, img_height)
            conf = float(min(float(confidence), 99.))
            detections_adjusted.append((str(label), conf, bbox_adjusted))
        return detections_adjusted

    def _adjust_bbox(self, bbox, img_width, img_height):
        x, y, w, h = bbox
        return int(x * img_width), int(y * img_height), int(w * img_width), int(h * img_height)
    
    @staticmethod
    def draw_detections(img, detections):
        color = (0, 0, 255)  # red
        for label, confidence, bbox in detections:
            print(str(label) + ": " + str(confidence) + ": " + str(bbox))
            x, y, w, h = bbox
            w2 = int(w / 2)
            h2 = int(h / 2)
            left :int = x - w2
            right :int = x + w2
            top :int = y - h2
            bottom :int = y + h2
            cv2.rectangle(img, (left, top), (right, bottom), color, 3)
            cv2.putText(img, "{}".format(label), (left, top - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
    def update_prop(self, kv :tuple):
        k, v = kv
        if k == 'thresh':
            self.thresh = v
            v = self.thresh
        elif k == 'crop_to_square':
            self.crop_to_square = v
            v = self.crop_to_square
        self.sgl_prop_updated.emit((k, v))

    @property
    def thresh(self):
        return self._thresh
    
    @thresh.setter
    def thresh(self, i :int):
        if i < 0: i = 0
        elif i > 100: i = 100
        self._thresh = i

    @property
    def enabled(self):
        return self._enabled
    
    @enabled.setter
    def enabled(self, b :bool):
        if b:
            if not self._enabled and self.network is None:
                self.load_network()
        self._enabled = b

    def xlog(self, msg: str, level: int = logging.DEBUG):
        pass
