import os
import shutil
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import cv2
import numpy as np
import logging
from detector import Detector
from ai import DBTHai

class Scanner(qtc.QObject):
    sgl_msg = qtc.pyqtSignal(str, int)
    sgl_update_display = qtc.pyqtSignal(tuple)
    sgl_loop_cycle_complete = qtc.pyqtSignal()
    sgl_aborted = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop_active = False
        #  Detector
        self.detector = Detector('detector')
        self.detector.xlog = self.xlog
        # ai
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

    def main_loop(self, tpl):
        machine, img, filename = tpl
        colimgs = None
        detections = []
        if self.detector.enabled:
            img, colimgs, detections = self.detect_columns(img)
            if detections is not None:
                self.detector.draw_detections(img, detections)
            if self.ai.enabled:
                if colimgs is not None:
                    self.sgl_update_display.emit((img, detections))
                    ret = self.ai.send_api_messages(colimgs, machine)
                    if ret > 0: self.sgl_aborted.emit()
                    else: shutil.move(filename, os.getcwd() + '/sheets/out/')
        self.sgl_loop_cycle_complete.emit()

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
            elif lbl == self.lbls['notes_header']:
                notesbbox = bbox
        _, y0, _, h = timesbbox
        t, _, _, _ = self.xywh2tblr(timesbbox)
        dets = []
        for lbl, conf, bbox in detections:
            _, b, _, _ = self.xywh2tblr(bbox)
            y = y0 + (b - t) // 2
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
        return img, ((targetimg, 'target'), (actualimg, 'actual'), (deltaimg, 'delta'), (lostimg, 'lost'), (notesimg, 'notes')), dets
    
    @staticmethod
    def rotate_image(image, angle, point=None):
        h, w = image.shape[:2]
        if point is None:
            point = (w // 2, h // 2)
        mat = cv2.getRotationMatrix2D(point, angle, 1.0)
        return cv2.warpAffine(image, mat, (w, h))
    
    @staticmethod
    def angle_between_points(p1, p2):
        """
        Calculates the angle between two points and the horizontal axis.

        :param p1: Tuple (x1, y1) - First point.
        :param p2: Tuple (x2, y2) - Second point.
        :return: Angle in degrees.
        """
        delta_y = p2[1] - p1[1]
        delta_x = p2[0] - p1[0]
        angle_rad = np.arctan2(delta_y, delta_x)  # arctan2 handles quadrants correctly
        angle_deg = np.degrees(angle_rad)  # Convert to degrees
        return angle_deg
    
    def verify_detections(self, detections):
        dets = [None] * 7  # target, actual, delta, lost, notes
        for lbl, conf, bbox in detections:
            if lbl == self.lbls['hour_times']:
                dets[0] = (lbl, conf, bbox)
            elif lbl == self.lbls['hour_header']:
                dets[1] = (lbl, conf, bbox)
            elif lbl == self.lbls['target_header']:
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
    
    @qtc.pyqtSlot()
    def load_network(self):
        self.detector.enabled = True

    def xlog(self, msg :str, level :int = logging.DEBUG):
        self.sgl_msg.emit(msg, level)
