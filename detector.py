import logging
import darknet
import cv2
import numpy as np
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import os
from parsr import Parsr


class Detector(qtc.QObject):
    sgl_setting_changed = qtc.pyqtSignal(tuple)

    def __init__(self, name :str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.network = None
        self.net_w = None
        self.net_h = None
        self.cfg_path = ''
        self.data_path = ''
        self.weights_path = ''
        self._enabled = False
        # Settings
        self.st = {
            'thresh': 0.5
        }
        self.load_settings()

    def load_settings(self, path=None):
        if path is None:
            path = os.getcwd() + f'/settings_{self.name}.txt'
        p = Parsr(path)
        if p is None:
            return
        self.st['thresh'] = p.get('thresh', 'float', default=0.5)
        self.cfg_path = p.get('cfg_path', 'str', required=True)
        self.data_path = p.get('data_path', 'str', required=True)
        self.weights_path = p.get('weights_path', 'str', required=True)

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
            raise FileNotFoundError(err)
        self.network, self.class_names, _ = darknet.load_network(self.cfg_path, self.data_path, self.weights_path, 1)
        self.net_w = darknet.network_width(self.network)
        self.net_h = darknet.network_height(self.network)
        self.xlog('Network loaded.', logging.INFO)

    def detect(self, img: np.ndarray):
        _img = cv2.resize(img, (self.net_w, self.net_h), interpolation=cv2.INTER_LINEAR)
        darknet_image = darknet.make_image(self.net_w, self.net_h, 3)
        darknet.copy_image_from_bytes(darknet_image, _img.tobytes())
        detections = darknet.detect_image(self.network, self.class_names, darknet_image, self.st['thresh'])
        darknet.free_image(darknet_image)
        return img, self._adjust_detections(detections, img.shape[1], img.shape[0])

    def _adjust_detections(self, detections :list, img_width, img_height):
        detections_adjusted = []
        for label, confidence, bbox in detections:
            bbox_adjusted = self._adjust_bbox(bbox, img_width, img_height)
            conf = float(min(float(confidence), 99.))
            detections_adjusted.append((str(label), conf, bbox_adjusted))
        return detections_adjusted

    def _adjust_bbox(self, bbox, img_width, img_height):
        x, y, w, h = bbox
        x = x / self.net_w
        y = y / self.net_h
        w = w / self.net_w
        h = h / self.net_h
        return int(x * img_width), int(y * img_height), int(w * img_width), int(h * img_height)
    
    @staticmethod
    def draw_detections(img, detections, omit=[]):
        color = (0, 0, 255)  # red
        for label, confidence, bbox in detections:
            if label in omit:
                continue
            x, y, w, h = bbox
            w2 = int(w / 2)
            h2 = int(h / 2)
            left :int = x - w2
            right :int = x + w2
            top :int = y - h2
            bottom :int = y + h2
            cv2.rectangle(img, (left, top), (right, bottom), color, 3)
            cv2.putText(img, "{} [{:.0f}]".format(label, float(confidence)), (left, top - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    @qtc.pyqtSlot(tuple)
    def change_setting(self, kv :tuple):
        k, v = kv
        if k in self.st.keys():
            self.st[k] = v
        else:
            raise KeyError(f'[{self.name}] Invalid key: {k}')
        self.sgl_setting_changed.emit((k, v))

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
