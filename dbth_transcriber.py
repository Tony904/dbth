import sys
import os
import functools
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import cv2
import numpy as np
import glob
import shutil

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
from parsr import Parsr

class MainApp(qtw.QApplication):

    def __init__(self, argv):
        super().__init__(argv)
        self.mw = MainWindow()
        screen_center = qtw.QDesktopWidget().availableGeometry().center()
        y = screen_center.y()
        screen_center.setY(y - 20)
        frame = self.mw.frameGeometry()
        frame.moveCenter(screen_center)
        self.mw.move(frame.topLeft())
        self.mw.show()

class MainWindow(qtw.QWidget):
    sgl_main_loop_activated = qtc.pyqtSignal()
    sgl_do_loop_cycle = qtc.pyqtSignal(tuple)

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
        self.machines = []
        self.selected_machine = None
        self._stop_loop = False
        self.run_once = False
        self.connect_signals()
        self.load_machines_list()
        self.get_next_file_and_update_lists()

    def connect_signals(self):
        #  Loop
        self.ui.btn_run_cont.clicked.connect(self.start_loop, type=qtc.Qt.QueuedConnection)
        self.ui.btn_run_once.clicked.connect(self.do_loop_cycle_once, type=qtc.Qt.QueuedConnection)
        self.ui.btn_stop.clicked.connect(self.stop_loop, type=qtc.Qt.QueuedConnection)
        self.scanner.sgl_loop_cycle_complete.connect(self.on_loop_cycle_complete, type=qtc.Qt.QueuedConnection)
        self.sgl_do_loop_cycle.connect(self.scanner.main_loop, type=qtc.Qt.QueuedConnection)
        #  Displays
        self.scanner.sgl_update_display.connect(self.update_display, type=qtc.Qt.QueuedConnection)
        #  AI
        self.scanner.ai.sgl_read_target.connect(self.on_read_target, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_actual.connect(self.on_read_actual, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_delta.connect(self.on_read_delta, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_lost.connect(self.on_read_lost, type=qtc.Qt.QueuedConnection)
        self.scanner.ai.sgl_read_notes.connect(self.on_read_notes, type=qtc.Qt.QueuedConnection)
        #  Other
        self.scanner.sgl_msg.connect(self.xlog, type=qtc.Qt.QueuedConnection)
        self.ui.btn_refresh.clicked.connect(self.get_next_file_and_update_lists, type=qtc.Qt.QueuedConnection)
        self.ui.btn_move_out_to_in.clicked.connect(self.move_all_out_files_to_in, type=qtc.Qt.QueuedConnection)

    def load_machines_list(self):
        path = os.getcwd() + '/machines.txt'
        if not os.path.exists(path):
            self.xlog(f'Warning: No machines.txt file found in {os.getcwd()}', logging.INFO)
            return
        with open(path, 'r') as file:
            lines = file.readlines()
        lines = Parsr.clean_lines(lines)
        self.ui.cbox_machine.clear()
        self.ui.cbox_machine.addItem('')
        for line in lines:
            self.ui.cbox_machine.addItem(line)
        self.machines = lines
    
    @qtc.pyqtSlot()
    def start_loop(self):
        if self.scanner.loop_active:
            self.xlog(f'Already running.', logging.INFO)
            return
        self._stop_loop = False
        self.scanner.loop_active = True
        self.scanner.ai.abort = False
        self.scanner.detector.enabled = True
        self.do_loop_cycle()

    @qtc.pyqtSlot()
    def do_loop_cycle_once(self):
        if self.scanner.loop_active:
            self.xlog(f'Already running.', logging.INFO)
            return
        self.run_once = True
        self._stop_loop = False
        self.scanner.loop_active = True
        self.scanner.ai.abort = False
        self.scanner.detector.enabled = True
        self.xlog('Running once...', logging.INFO)
        self.do_loop_cycle()

    def get_next_file_and_update_lists(self):
        # output files
        ext = '.png'
        dir = os.getcwd() + '/sheets/out/'
        path = dir + '*' + ext
        files = glob.glob(path)
        self.ui.lstw_out.clear()
        self.ui.lstw_out.addItems(files)
        # input files
        dir = os.getcwd() + '/sheets/in/'
        path = dir + '*' + ext
        files = glob.glob(path)
        self.ui.lstw_in.clear()
        self.ui.lstw_in.addItems(files)
        if len(files) == 0:
            self.xlog(f'No {ext} files found in {dir}', logging.INFO)
            return None
        return files[0]
    
    @qtc.pyqtSlot()
    def move_all_out_files_to_in(self):
        ext = '.png'
        out_dir = os.getcwd() + '/sheets/out/'
        in_dir = os.getcwd() + '/sheets/in/'
        path = out_dir + '*' + ext
        files = glob.glob(path)
        for f in files:
            shutil.move(f, in_dir)
        self.get_next_file_and_update_lists()

    def do_loop_cycle(self):
        filename = self.get_next_file_and_update_lists()
        if filename is None:
            self.scanner.loop_active = False
            return
        try:
            img = cv2.imread(filename)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as ex:
            self.xlog(f'Error occured while loading {filename}\n{ex}', logging.INFO)
            return
        self.ui.lstw_target.clear()
        self.ui.lstw_actual.clear()
        self.ui.lstw_delta.clear()
        self.ui.lstw_lost.clear()
        self.ui.lstw_notes.clear()
        machine = self.ui.cbox_machine.currentText()
        if machine == '':
            self.xlog('Warning: No machine selected. No data will be written to excel.', logging.INFO)
        self.xlog(f'Processing {filename}', logging.INFO)
        self.sgl_do_loop_cycle.emit((machine, img, filename))

    @qtc.pyqtSlot()
    def stop_loop(self):
        if not self.scanner.loop_active:
            self.xlog('Not running.', logging.INFO)
            return
        self._stop_loop = True
        self.xlog('Stopping...', logging.INFO)

    @qtc.pyqtSlot()
    def abort_loop(self):
        if self.scanner.ai.abort:
            self.xlog('Already attempting to abort.', logging.INFO)
            return
        self.scanner.ai.abort = True
        self._stop_loop = True
        self.xlog('Aborting...', logging.INFO)

    @qtc.pyqtSlot(tuple)
    def update_display(self, tpl :tuple):
        img, detections = tpl
        if img is not None:
            self.update_display_pixmap(img)
        # if detections is None:
        #     self.ui.lstw_detections.clear()
        #     return
        # if len(detections):
        #     self.ui.lstw_detections.clear()
        #     for lbl, conf, bbox in detections:
        #         self.ui.lstw_detections.addItem(f'{lbl}, {conf} ({bbox[2]:.2f}, {bbox[3]:.2f})')

    def update_display_pixmap(self, img :np.ndarray):
        img_w = img.shape[1]
        img_h = img.shape[0]
        w = self.ui.lbl_main_display.geometry().width()
        h = self.ui.lbl_main_display.geometry().height()
        fx = w / img_w
        fy = h / img_h
        f = fx if fx < fy else fy
        img = cv2.resize(img, (0, 0), fx=f, fy=f, interpolation=cv2.INTER_LINEAR)
        qimg = qtg.QImage(img.data, img.shape[1], img.shape[0], img.strides[0], qtg.QImage.Format_RGB888)
        qpix = qtg.QPixmap.fromImage(qimg)
        self.ui.lbl_main_display.setPixmap(qpix)

    # --------------------------------------------------------------
    # Event callbacks
    # --------------------------------------------------------------
    @qtc.pyqtSlot()
    def on_loop_cycle_complete(self):
        if self.run_once:
            self.scanner.loop_active = False
            self.run_once = False
            self.get_next_file_and_update_lists()
            return
        if not self._stop_loop:
            self.do_loop_cycle()
        else:
            self.scanner.loop_active = False
            self.xlog('Stopped.', logging.INFO)

    @qtc.pyqtSlot(list)
    def on_read_target(self, lst :list):
        self.ui.lstw_target.clear()
        self.ui.lstw_target.addItems(lst)
        self.xlog('Target column updated.', logging.INFO)

    @qtc.pyqtSlot(list)
    def on_read_actual(self, lst :list):
        self.ui.lstw_actual.clear()
        self.ui.lstw_actual.addItems(lst)
        self.xlog('Actual column updated.', logging.INFO)

    @qtc.pyqtSlot(list)
    def on_read_delta(self, lst :list):
        self.ui.lstw_delta.clear()
        self.ui.lstw_delta.addItems(lst)
        self.xlog('Delta column updated.', logging.INFO)

    @qtc.pyqtSlot(list)
    def on_read_lost(self, lst :list):
        self.ui.lstw_lost.clear()
        self.ui.lstw_lost.addItems(lst)
        self.xlog('Lost Time column updated.', logging.INFO)

    @qtc.pyqtSlot(list)
    def on_read_notes(self, lst :list):
        self.ui.lstw_notes.clear()
        self.ui.lstw_notes.addItems(lst)
        self.xlog('Notes column updated.', logging.INFO)

    # --------------------------------------------------------------
    # Logging & Console
    # --------------------------------------------------------------
    def console(self, s):
        self.ui.ptxt_console.appendPlainText(f'{s}')

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

    
