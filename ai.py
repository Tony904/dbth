from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import os
import openai
import apikey
import base64
import cv2
import numpy as np

openai.api_key = apikey.api_key
DIM = 512

class DBTHai(qtc.QObject):
    sgl_msg = qtc.pyqtSignal(str)
    sgl_read_target = qtc.pyqtSignal(list)
    sgl_read_actual = qtc.pyqtSignal(list)
    sgl_read_delta = qtc.pyqtSignal(list)
    sgl_read_lost = qtc.pyqtSignal(list)
    sgl_read_notes = qtc.pyqtSignal(list)
    sgl_read_allimg = qtc.pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.include_refcol = True
        self.allimg = np.zeros((DIM, DIM, 3), dtype=np.uint8)
        self.enabled = True
        if not self.include_refcol:
            self.sysmsg = 'You will be given an image of a single column with 24 evenly spaced rows. Read each row in the column from top to bottom. Any given row may or may not contain data. In your response, format empty rows as if they had an entry of the underscore symbol (_). Respond only with a list of length 24 corresponding to the 24 rows with each row delimited by the newline character. You MUST only respond with a list of length 24. Do not respond with a list that has more or less than 24 entries.'
        else:
            self.sysmsg = 'Do not prepend your response with a sentence stating what the image shows.'
            'You will be given an image of a two columns with 24 evenly spaced rows. '
            'Read each row in the first column from top to bottom. '
            'The second column to the right is simply the index of each row from 1 to 24, top to bottom. '
            'Do not output data in the second column to the right, it is only a reference. '
            'Any given row may or may not contain data. '
            'In your response, format empty rows as if they had an entry of the underscore symbol (_). '
            'Respond only with a list of length 24 corresponding to the 24 rows of the first column on the left '
            'with each row delimited by the newline character. '
            'You MUST only respond with a list of length 24. '
            'Do not prepend your message with what your message will be about. '
            'Do not respond with a list that has more or less than 24 entries.'


    def send_api_messages(self, colimgs :tuple):
        colimgs = self.prepare_imgs(colimgs)
        # cv2.imshow('allimg', self.allimg)
        # cv2.waitKey(0)
        # enallimg = self.encode_allimg()
        # allimgres = self.send_allimg_message(enallimg)
        # self.sgl_read_allimg.emit(allimgres.split(':'))
        entarget, enactual, endelta, enlost, ennotes = self.encode_colimgs(colimgs)
        targetres = self.send_targetcol_message(entarget)
        self.sgl_read_target.emit(targetres.split('\n'))
        actualres = self.send_actualcol_message(enactual)
        self.sgl_read_actual.emit(actualres.split('\n'))
        deltares = self.send_deltacol_message(endelta)
        self.sgl_read_delta.emit(deltares.split('\n'))
        lostres = self.send_lostcol_message(enlost)
        self.sgl_read_lost.emit(lostres.split('\n'))
        notesres = self.send_notescol_message(ennotes)
        self.sgl_read_notes.emit(notesres.split('\n'))

    def send_allimg_message(self, enallimg):
        model_id = 'gpt-4o'
        messages = [
            {'role': 'system',
            'content': self.sysmsg},
            {'role': 'user',
            'content': [
                {'type': 'image_url',
                'image_url':  {
                    'url': f'data:image/png;base64,{enallimg}',
                    'detail': 'high'
                                }
                }
                        ]
            }
        ]
        response = openai.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0)
        response = response.choices[0].message.content
        print(response)
        return response

    def send_targetcol_message(self, entarget):
        model_id = 'gpt-4o'
        messages = [
            {'role': 'system',
            'content': self.sysmsg},
            {'role': 'user',
            'content': [
                {'type': 'image_url',
                'image_url':  {
                    'url': f'data:image/png;base64,{entarget}',
                    'detail': 'high'
                                }
                }
                        ]
            }
        ]
        response = openai.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0)
        response = response.choices[0].message.content
        print(response)
        return response

    def send_actualcol_message(self, enactual):
        model_id = 'gpt-4o'
        messages = [
            {'role': 'system',
            'content': self.sysmsg},
            {'role': 'user',
            'content': [
                {'type': 'image_url',
                'image_url':  {
                    'url': f'data:image/png;base64,{enactual}',
                    'detail': 'high'
                                }
                }
                        ]
            }
        ]
        response = openai.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0)
        response = response.choices[0].message.content
        print(response)
        return response

    def send_deltacol_message(self, endelta):
        model_id = 'gpt-4o'
        messages = [
            {'role': 'system',
            'content': self.sysmsg},
            {'role': 'user',
            'content': [
                {'type': 'image_url',
                'image_url':  {
                    'url': f'data:image/png;base64,{endelta}',
                    'detail': 'high'
                                }
                }
                        ]
            }
        ]
        response = openai.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0)
        response = response.choices[0].message.content
        print(response)
        return response

    def send_lostcol_message(self, enlost):
        model_id = 'gpt-4o'
        messages = [
            {'role': 'system',
            'content': self.sysmsg},
            {'role': 'user',
            'content': [
                {'type': 'image_url',
                'image_url':  {
                    'url': f'data:image/png;base64,{enlost}',
                    'detail': 'high'
                                }
                }
                        ]
            }
        ]
        response = openai.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0)
        response = response.choices[0].message.content
        print(response)
        return response

    def send_notescol_message(self, ennotes):
        model_id = 'gpt-4o'
        messages = [
            {'role': 'system',
            'content': self.sysmsg},
            {'role': 'user',
            'content': [
                {'type': 'image_url',
                'image_url':  {
                    'url': f'data:image/png;base64,{ennotes}',
                    'detail': 'high'
                                }
                }
                        ]
            }
        ]
        response = openai.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.)
        response = response.choices[0].message.content
        print(response)
        return response

    def encode_colimgs(self, colimgs :tuple):
        targetimg, actualimg, deltaimg, lostimg, notesimg = colimgs
        wdir = os.path.dirname(os.path.abspath(__file__)) + '\\'
        print(wdir)
        targetpath = wdir + 'target.png'
        actualpath = wdir + 'actual.png'
        deltapath = wdir + 'delta.png'
        lostpath = wdir + 'lost.png'
        notespath = wdir + 'notes.png'
        cv2.imwrite(targetpath, targetimg)
        cv2.imwrite(actualpath, actualimg)
        cv2.imwrite(deltapath, deltaimg)
        cv2.imwrite(lostpath, lostimg)
        cv2.imwrite(notespath, notesimg)
        target64 = self.encode_image(targetpath)
        actual64 = self.encode_image(actualpath)
        delta64 = self.encode_image(deltapath)
        lost64 = self.encode_image(lostpath)
        notes64 = self.encode_image(notespath)
        return target64, actual64, delta64, lost64, notes64

    @staticmethod
    def encode_image(img_path):
        with open(img_path, 'rb') as img_file:
            imgdata = img_file.read()
            return base64.b64encode(imgdata).decode('utf-8')
        
    def encode_allimg(self):
        wdir = os.curdir
        cv2.imwrite(wdir + 'allimg.png', self.allimg)
        return self.encode_image(wdir + 'allimg.png')
    
    # def prepare_imgs(self, imgs :tuple) -> list:
    #     prepimgs = []
    #     # assume height > width and imgs is in correct order according to dbth table
    #     w = 50
    #     s = 10  # spacing between cols
    #     i = 0
    #     for img in imgs:
    #         im = cv2.resize(img, (w, DIM), interpolation=cv2.INTER_CUBIC)
    #         self.allimg[0:DIM,(w + s) * i :(w + s) * i + w] = im.copy()
    #         prepimgs.append(im)
    #         i += 1
    #     return prepimgs

    def prepare_imgs(self, imgs :tuple) -> list:
        # assume height > width and imgs is in correct order according to dbth table
        prepimgs = []
        for img in imgs:
            height, width, _ = img.shape
            scale = DIM / height
            img = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            h, w, _ = img.shape
            img, _, _ = self.pad_image_to_square(img)
            if self.include_refcol:
                numimg = cv2.imread('D:\\TonyDev\\dbth\\numcol.png')
                scale = DIM / numimg.shape[0]
                numimg = cv2.resize(numimg, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                print(img.shape, numimg.shape)
                img[0:DIM,w:w+numimg.shape[1]] = numimg.copy()
            # cv2.imshow('img', img)
            # cv2.waitKey(0)

            prepimgs.append(img)
        return prepimgs
    
    @staticmethod
    def pad_image_to_square(src):
        image = src.copy()
        w = image.shape[1]
        h = image.shape[0]
        top_pad = 0
        bottom_pad = 0
        left_pad = 0
        right_pad = 0
        padded = None
        if w < h:
            right_pad = h - w
            print("Padding right: " + str(right_pad))
            padded = np.pad(image, ((top_pad, bottom_pad), (left_pad, right_pad), (0, 0)), mode='constant')
        elif h < w:
            bottom_pad = w - h
            print("Padding bottom: " + str(bottom_pad))
            padded = np.pad(image, ((top_pad, bottom_pad), (left_pad, right_pad), (0, 0)), mode='constant')
        else:
            print("No padding. Image is already square.")
            padded = image
        return padded, bottom_pad, right_pad
    
    def xlog(self, msg: str, level=None):
        pass


# def split_image(img):
#     h, w, _ = img.shape
#     num = 2
#     #  img[top:bottom, left:right]
#     img1 = img[0:h//num,0:w].copy()
#     img2 = img[h//num:h,0:w].copy()
#     cv2.imshow('img1', img1)
#     cv2.imshow('img2', img2)
#     cv2.waitKey(0)