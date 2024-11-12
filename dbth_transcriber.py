import sys
import time
import functools
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import darknet
import cv2
import numpy as np
import math
import openai

import logging
from logging.handlers import RotatingFileHandler
LOG_FILENAME = 'dbth_transcriber.log'
LOGGER_ = logging.getLogger('dbthlogger')
LOGGER_.setLevel(logging.WARNING)
ROTATING_HANDLER = RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=1)
ROTATING_HANDLER.setLevel(logging.WARNING)
LOG_FORMATTER = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ROTATING_HANDLER.setFormatter(LOG_FORMATTER)
LOGGER_.addHandler(ROTATING_HANDLER)

from dbth_transcriber_designer import Ui_root_form
from scanner import Scanner


class MainApp(qtw.QApplication):

    def __init__(self, argv):
        super().__init__(argv)
        self.mw = MainWindow()
        screen_center = qtw.QDesktopWidget().availableGeometry().center()
        frame = self.mw.frameGeometry()
        frame.moveCenter(screen_center)
        self.mw.move(frame.topLeft())
        self.mw.show()


class MainWindow(qtw.QWidget):
    sgl_main_loop_activated = qtc.pyqtSignal()
    sgl_do_main_loop_cycle = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #  Logging
        self.xlog_enabled = True
        self.xlog_level = logging.getLogger().getEffectiveLevel()
        self.xlog_quiet = False
        #  UI creation
        self.ui = Ui_root_form()
        self.ui.setupUi(self)
        self.scanner = Scanner()
        self.scanner_qthread = qtc.QThread()
        self.scanner.moveToThread(self.scanner_qthread)
        self.scanner_qthread.start()
        # Other
        self.connect_signals()

    def connect_signals(self):
        #  Scanner
        self.scanner.sgl_msg.connect(self.on_sgl_msg, type=qtc.Qt.QueuedConnection)
        #  Loop
        self.ui.btn_enable.clicked.connect(self.begin_loop, type=qtc.Qt.QueuedConnection)
        self.scanner.sgl_main_loop_finished.connect(self.on_main_loop_finished, type=qtc.Qt.QueuedConnection)
        self.sgl_do_main_loop_cycle.connect(self.scanner.main_loop, type=qtc.Qt.QueuedConnection)
        #  Displays
        self.scanner.sgl_update_main_display.connect(self.on_update_main_display, type=qtc.Qt.QueuedConnection)
        #  AI
        self.scanner.ai.sgl_read_target.connect(self.on_read_target, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_actual.connect(self.on_read_actual, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_delta.connect(self.on_read_delta, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_lost.connect(self.on_read_lost, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_notes.connect(self.on_read_notes, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_allimg.connect(self.on_read_allimg, type=qtc.Qt.QueuedConnection)

    @qtc.pyqtSlot()
    def begin_loop(self):
        if self.scanner.loop_active:
            return
        self.scanner.loop_active = True
        self.scanner.detector.enabled = True
        self.scanner.main_cap.enabled = True
        self.sgl_do_main_loop_cycle.emit()

    @qtc.pyqtSlot()
    def on_main_loop_finished(self):
        # self.sgl_do_main_loop_cycle.emit()
        pass

    def update_main_display_pixmap(self, img :np.ndarray):
        img_w = img.shape[1]
        img_h = img.shape[0]
        w = self.ui.lbl_main_display.geometry().width()
        h = self.ui.lbl_main_display.geometry().height()
        fx = w / img_w
        fy = h / img_h
        if fx < fy:
            fy = fx
        else:
            fx = fy
        img = cv2.resize(img, (0, 0), fx=fx, fy=fy, interpolation=cv2.INTER_LINEAR)
        qimg = qtg.QImage(img.data, img.shape[1], img.shape[0], img.strides[0], qtg.QImage.Format_RGB888)
        qpix = qtg.QPixmap.fromImage(qimg)
        self.ui.lbl_main_display.setPixmap(qpix)

    # --------------------------------------------------------------
    # Event callbacks
    # --------------------------------------------------------------

    @qtc.pyqtSlot(tuple)
    def on_update_main_display(self, tpl :tuple):
        img, detections = tpl
        if img is not None:
            self.update_main_display_pixmap(img)
        if detections is None:
            self.ui.lstw_detections.clear()
            return
        if len(detections):
            self.ui.lstw_detections.clear()
            for lbl, conf, bbox in detections:
                self.ui.lstw_detections.addItem(f'{lbl}, {conf} ({bbox[2]:.2f}, {bbox[3]:.2f})')

    @qtc.pyqtSlot(list)
    def on_read_allimg(self, lst :list):
        if len(lst) != 24 * 5:
            self.xlog(f'[All] entries read does not equal 24 * 5. (is {len(lst)})', logging.ERROR)
            # return
        self.ui.lstw_target.clear()
        self.ui.lstw_actual.clear()
        self.ui.lstw_delta.clear()
        self.ui.lstw_lost.clear()
        self.ui.lstw_notes.clear()
        self.ui.lstw_target.addItems(lst[0:24])
        self.ui.lstw_actual.addItems(lst[24:48])
        self.ui.lstw_delta.addItems(lst[48:72])
        self.ui.lstw_lost.addItems(lst[72:96])
        self.ui.lstw_notes.addItems(lst[96:120])

    @qtc.pyqtSlot(list)
    def on_read_target(self, lst :list):
        if len(lst) != 24:
            self.xlog(f'[Target] entries read does not equal 24. (is {len(lst)})', logging.ERROR)
            # return
        self.ui.lstw_target.clear()
        self.ui.lstw_target.addItems(lst[0:24])

    @qtc.pyqtSlot(list)
    def on_read_actual(self, lst :list):
        if len(lst) != 24:
            self.xlog(f'[Actual] entries read does not equal 24. (is {len(lst)})', logging.ERROR)
            # return
        self.ui.lstw_actual.clear()
        self.ui.lstw_actual.addItems(lst[0:24])

    @qtc.pyqtSlot(list)
    def on_read_delta(self, lst :list):
        if len(lst) != 24:
            self.xlog(f'[Delta] entries read does not equal 24. (is {len(lst)})', logging.ERROR)
            # return
        self.ui.lstw_delta.clear()
        self.ui.lstw_delta.addItems(lst[0:24])

    @qtc.pyqtSlot(list)
    def on_read_lost(self, lst :list):
        if len(lst) != 24:
            self.xlog(f'[Lost] entries read does not equal 24. (is {len(lst)})', logging.ERROR)
            # return
        self.ui.lstw_lost.clear()
        self.ui.lstw_lost.addItems(lst[0:24])

    @qtc.pyqtSlot(list)
    def on_read_notes(self, lst :list):
        if len(lst) != 24:
            self.xlog(f'[Notes] entries read does not equal 24. (is {len(lst)})', logging.ERROR)
            # return
        self.ui.lstw_notes.clear()
        self.ui.lstw_notes.addItems(lst[0:24])

    # --------------------------------------------------------------
    # Logging & Console
    # --------------------------------------------------------------
    def console(self, s):
        self.ui.ptxt_console.appendPlainText(f'{s}')

    @qtc.pyqtSlot(str)
    def on_sgl_msg(self, msg):
        self.console(msg)

    def xlog(self, msg: str, level: int = logging.DEBUG):
        if level > logging.DEBUG:
            self.console(msg)
        if level < self.xlog_level:
            return
        if not self.xlog_quiet:
            print(msg)
        if not self.xlog_enabled:
            return
        logging.log(level, msg)

    # --------------------------------------------------------------
    # Other
    # --------------------------------------------------------------

    def _block_signals(func):
        @functools.wraps(func)
        def wrapper(*args):
            args[0].blockSignals(True)
            func(*args)
            args[0].blockSignals(False)
        return wrapper

    @staticmethod
    @_block_signals
    def _setValue_no_signal(widget, value):
        widget.setValue(value)

    @staticmethod
    @_block_signals
    def _setChecked_no_signal(widget, state: bool):
        if state is True:
            widget.setChecked(qtc.Qt.CheckState.Checked)
        else:
            widget.setChecked(qtc.Qt.CheckState.Unchecked)

    @staticmethod
    @_block_signals
    def _setText_no_signal(widget, text):
        widget.setText(str(text))


if __name__ == "__main__":
    app = MainApp(sys.argv)
    sys.exit(app.exec_())
