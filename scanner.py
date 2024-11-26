import os
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import cv2
import numpy as np
import darknet
import logging
from capture import Capture
from detector import Detector
from ai import DBTHai

class Scanner(qtc.QObject):
    sgl_msg = qtc.pyqtSignal(str)
    sgl_update_main_display = qtc.pyqtSignal(tuple)
    sgl_update_chute_display = qtc.pyqtSignal(tuple)
    sgl_main_loop_finished = qtc.pyqtSignal()

    def __init__(self, main_cap_index :int = 0, main_cap_res :tuple = (1920, 1080), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop_active = False
        #  Logging
        self.logging_enabled = True
        self.xlog_level = logging.getLogger().getEffectiveLevel()
        self.xlog_quiet = True
        #  Main Capture
        self.main_cap = Capture('main', main_cap_index, main_cap_res)
        self.main_cap.xlog = self.xlog
        #  Detector
        cfg = 'D:/yolo_v4/darknet/build/darknet/x64/cfg/yolov7-tiny-dbth.cfg'
        data = 'D:/yolo_v4/darknet/build/darknet/x64/data/dbth.data'
        # weights = 'D:/yolo_v4/darknet/build/darknet/x64/data/yolov7-tiny-dbth_10000.weights'
        weights = 'D:/yolo_v4/darknet/build/darknet/x64/data/yolov7-tiny-dbth-11-13-24_10000.weights'
        self.detector = Detector(cfg, data, weights)
        self.detector.xlog = self.xlog
        # AI
        self.ai = DBTHai()
        self.lbls = {
            'hour_times': 'times',
            'hour_header': 'hour',
            'target_header': 'target',
            'actual_header': 'actual',
            'delta_header': 'delta',
            'lost_header': 'lost',
            'notes_header': 'notes'
        }

    def test_cap(self):
        # img = cv2.imread('D:\\TonyDev\\dbth\\img.png')
        img = cv2.imread('D:\\TonyDev\\dbth\\ana_233_13.png')
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def main_loop(self):
        if not self.loop_active:
            return
        if self.main_cap.enabled:
            img = self.test_cap()
            # img = self.main_cap.do_capture()
            colimgs = None
            detections = []
            if self.detector.enabled:
                img, colimgs, detections = self.detect_columns(img)
                if detections is not None:
                    self.detector.draw_detections(img, detections)
                if self.ai.enabled:
                    if colimgs is not None:
                        self.ai.send_api_messages(colimgs)
            self.sgl_update_main_display.emit((img, detections))
        self.sgl_main_loop_finished.emit()

    def detect_columns(self, img :np.ndarray):
        img, detections = self.detector.detect(img)
        detections = self.verify_detections(detections)
        if detections is None:
            return img, None, None
        targetimg = None
        actualimg = None
        deltaimg = None
        lostimg = None
        notesimg = None
        hoursbbox = None
        timesbbox = None
        for lbl, conf, bbox in detections:
            if lbl == self.lbls['hour_header']:
                hoursbbox = bbox
            elif lbl == self.lbls['hour_times']:
                timesbbox = bbox
        _, b, _, _ = self.xywh2tblr(hoursbbox)
        t, _, _, _ = self.xywh2tblr(timesbbox)
        _, y, _, h = timesbbox
        y += b - t
        dets = []
        for lbl, conf, bbox in detections:
            databox = (bbox[0], y, bbox[2], h)
            if lbl == self.lbls['target_header']:
                dets.append((lbl, conf, databox))
                targetimg = self.crop_bbox(img, databox)
            elif lbl == self.lbls['actual_header']:
                dets.append((lbl, conf, databox))
                actualimg = self.crop_bbox(img, databox)
            elif lbl == self.lbls['delta_header']:
                dets.append((lbl, conf, databox))
                deltaimg = self.crop_bbox(img, databox)
            elif lbl == self.lbls['lost_header']:
                dets.append((lbl, conf, databox))
                lostimg = self.crop_bbox(img, databox)
            elif lbl == self.lbls['notes_header']:
                dets.append((lbl, conf, databox))
                notesimg = self.crop_bbox(img, databox)
        return img, (targetimg, actualimg, deltaimg, lostimg, notesimg), dets
    
    def verify_detections(self, detections):
        # if len(detections) != 7:
        #     self.xlog(f'# of detections is not 7. ({len(detections)})', logging.INFO)
        #     return None
        dets = [None] * 7  # target, actual, delta, lost, notes
        for lbl, conf, bbox in detections:
            if lbl == self.lbls['hour_times']:
                dets[0] = (lbl, conf, bbox)
            if lbl == self.lbls['hour_header']:
                dets[1] = (lbl, conf, bbox)
            if lbl == self.lbls['target_header']:
                dets[2] = (lbl, conf, bbox)
            elif lbl == self.lbls['actual_header']:
                dets[3] = (lbl, conf, bbox)
            elif lbl == self.lbls['delta_header']:
                dets[4] = (lbl, conf, bbox)
            elif lbl == self.lbls['lost_header']:
                dets[5] = (lbl, conf, bbox)
            elif lbl == self.lbls['notes_header']:
                dets[6] = (lbl, conf, bbox)
        for i in range(1, 6):
            if dets[i][2][0] > dets[i+1][2][0]:
                self.xlog('Incorrect column detection', logging.INFO)
                return None
        return dets

    @staticmethod
    def crop_bbox(img :np.ndarray, bbox :tuple):
        x, y, w, h = bbox
        top = max(0, y - h // 2)
        bottom = min(img.shape[0], y + h // 2)
        left = max(0, x - w // 2)
        right = min(img.shape[1], x + w // 2)
        return img[top:bottom, left:right].copy()
    
    @staticmethod
    def xywh2tblr(xywhbox :tuple):
        x, y, w, h = xywhbox
        top = round(y - h / 2.)
        bot = round(y + h / 2.)
        left = round(x - w / 2.)
        right = round(x + w / 2.)
        return top, bot, left, right

    def xlog(self, msg :str, level :int = logging.DEBUG):
        if level > logging.DEBUG:
            self.sgl_msg.emit(msg)
        if level < self.xlog_level:
            return
        if not self.xlog_quiet or level >= logging.ERROR:
            print(msg)
        if not self.logging_enabled:
            return
        logging.log(level, msg)
