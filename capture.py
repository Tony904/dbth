import logging
import sys
import time
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import cv2
import numpy as np


class Capture(qtc.QObject):
    sgl_cap_prop_updated = qtc.pyqtSignal(tuple)

    def __init__(self, cap_name: str, capture_index: int = 0, resolution: tuple = (1920, 1080), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = cap_name
        self.cap_index = capture_index
        if 'win32' in sys.platform:
            self.cap_protocol = cv2.CAP_DSHOW
        elif 'linux' in sys.platform:
            self.cap_protocol = cv2.CAP_V4L2
        else:
            self.cap_protocol = cv2.CAP_ANY
        self.cap = None
        self.frame = np.zeros((100, 100, 3), np.uint8)
        self.props = {
            'resolution': resolution,
            'focus': 300.,
            'autofocus': qtc.Qt.CheckState.Checked,
            'brightness': 50,
            'contrast': 32,
            'hue': 0,
            'saturation': 64,
            'sharpness': 3,
            'gamma': 100,
            'white': 4600,
            'autowhite': qtc.Qt.CheckState.Checked,
            'backlight': 2,
            'gain': 0,
            'exposure': -6,
            'autoexposure': qtc.Qt.CheckState.Checked  # if disabled, must be re-enabled in AMcap software
        }
        self.open = False
        self.attempts = 3
        # cropping
        self.top = 0
        self.bottom = 0
        self.left = 0
        self.right = 0
        self.do_crop = False
        self._enabled = False

    def do_capture(self):
        if not self.open:
            self.xlog(f'[{self.name}] Capture is not open. (index = {self.cap_index})', logging.ERROR)
            return None
        ok, frame = None, None
        for i in range(self.attempts):
            ok, frame = self.cap.read()
            if ok:
                break
            self.xlog(f'[{self.name}] Capture read failed on try {i+1}.')
        if not ok:
            self.xlog(f'[{self.name}] Capture is open but failed to read. (index = {self.cap_index})', logging.ERROR)
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.do_crop:
            return self.crop(frame)
        return frame

    def start_capture(self):
        self.cap = cv2.VideoCapture(self.cap_index, self.cap_protocol)
        if self.cap.isOpened():
            self.open = True
        else:
            self.open = False
            return False
        self._set_props()
        self.do_crop = (self.top or self.bottom or self.left or self.right)
        self.xlog(f'[{self.name}] Capture started.', logging.INFO)
        return True
    
    def change_index(self, i :int):
        if i == self.cap_index:
            return
        if self.open:
            try:
                cap = cv2.VideoCapture(self.cap_index, self.cap_protocol)
                qtc.QThread.msleep(1000)
            except Exception as e:
                self.xlog(f'{e}\n[{self.name}] Unable to change index to {i}.', logging.WARNING)
                self.sgl_cap_prop_updated.emit((self.name, 'index', self.cap_index))
                return
            self.cap.release()
            self.cap = cap
            self._set_props()
        self.xlog(f'[{self.name}] Index changed from {self.cap_index} to {i}.', logging.INFO)
        self.cap_index = i
        self.sgl_cap_prop_updated.emit((self.name, 'index', self.cap_index))

    def update_prop(self, kv: tuple):
        k, v = kv
        v = self._update_prop(k, v)
        self.xlog(f'[{self.name}] Capture property updated: {k, v}', logging.INFO)
        self.sgl_cap_prop_updated.emit((self.name, k, v))

    def _update_prop(self, prop, v):
        self.xlog(f'[{self.name}] Updating camera property: {prop}, {v}')
        if prop == 'autofocus':
            enable = 1
            disable = 2
            if v == qtc.Qt.CheckState.Checked:
                v = enable
            else:
                v = disable
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, v)
            v = self.cap.get(cv2.CAP_PROP_AUTOFOCUS)
            if v == enable:
                self.props[prop] = True
            else:
                self.props[prop] = False
        elif prop == 'autoexposure':
            enable = 1
            disable = 2
            if v == qtc.Qt.CheckState.Checked:
                v = enable
            else:
                v = disable
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, v)
            # v = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            if v == enable:
                self.props[prop] = True
            else:
                self.props[prop] = False
        elif prop == 'autowhite':
            enable = 1
            disable = 2
            if v == qtc.Qt.CheckState.Checked:
                v = enable
            else:
                v = disable
            self.cap.set(cv2.CAP_PROP_AUTO_WB, v)
            if v == enable:
                self.props[prop] = True
            else:
                self.props[prop] = False
        elif prop == 'focus':
            self.cap.set(cv2.CAP_PROP_FOCUS, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_FOCUS)
        elif prop == 'exposure':
            if not self.props['autoexposure']:
                self.cap.set(cv2.CAP_PROP_EXPOSURE, v)
                self.props[prop] = self.cap.get(cv2.CAP_PROP_EXPOSURE)
            else:
                self.xlog(f'[{self.name}] Exposure not changed due to Autoexposure being enabled.', logging.INFO)
        elif prop == 'backlight':
            self.cap.set(cv2.CAP_PROP_BACKLIGHT, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_BACKLIGHT)
        elif prop == 'sharpness':
            self.cap.set(cv2.CAP_PROP_SHARPNESS, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_SHARPNESS)
        elif prop == 'brightness':
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
        elif prop == 'contrast':
            self.cap.set(cv2.CAP_PROP_CONTRAST, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_CONTRAST)
        elif prop == 'gain':
            self.cap.set(cv2.CAP_PROP_GAIN, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_GAIN)
        elif prop == 'gamma':
            self.cap.set(cv2.CAP_PROP_GAMMA, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_GAMMA)
        elif prop == 'hue':
            self.cap.set(cv2.CAP_PROP_HUE, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_HUE)
        elif prop == 'saturation':
            self.cap.set(cv2.CAP_PROP_SATURATION, v)
            self.props[prop] = self.cap.get(cv2.CAP_PROP_SATURATION)
        elif prop == 'white':
            if not self.props['autowhite']:
                self.cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, v)
                self.cap.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, v)
                self.props[prop] = self.cap.get(cv2.CAP_PROP_WHITE_BALANCE_RED_V)
        elif prop == 'resolution':
            if 'x' in v:
                res = v.split('x')
                w = res[0]
                h = res[1]
            else:
                w, h = v
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(w))
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(h))
            w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.props[prop] = (w, h)
        else:
            self.xlog(f'[{self.name}] No capture property called: {prop}')
            return
        return self.props[prop]

    def _set_props(self):
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        for k, v in self.props.items():
            self.update_prop((k, v))

    def crop(self, image):
        rows, cols, _ = image.shape
        cropped = image[self.top:rows - self.bottom, self.left:cols - self.right].copy()
        return cropped

    def release(self):
        self.open = False
        self.cap.release() 

    def xlog(self, msg: str, level=None):
        pass

    @property
    def enabled(self):
        return self._enabled
    
    @enabled.setter
    def enabled(self, b :bool):
        if b:
            if not self._enabled and not self.open:
                self.start_capture()
        self._enabled = b


if __name__ == '__main__':
    cap_ = Capture('test_cap', 0)
    cap_.start_capture()
    w_ = int(cap_.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_ = int(cap_.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f'w = {w_}, h = {h_}')
    while True:
        img_ = cap_.do_capture()
        cv2.imshow('test_cap', img_)
        k_ = cv2.waitKey(1)
        if k_ == 27:
            break
    cap_.release()
    cv2.destroyAllWindows()
    print('Exited capture.py')