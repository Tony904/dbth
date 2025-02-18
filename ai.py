from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
import os
import openai
import base64
import cv2
import numpy as np
from prompts import target_prompt, actual_prompt, delta_prompt, lost_prompt, notes_prompt
import pandas as pd
from openpyxl import load_workbook, Workbook
from datetime import datetime, timedelta
from openpyxl.utils.dataframe import dataframe_to_rows
import os
import platform
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill, Border, Side
from apikey import mykey

openai.api_key = mykey
DIM = 768 * 2

class DBTHai(qtc.QObject):
    sgl_msg = qtc.pyqtSignal(str)
    sgl_read_target = qtc.pyqtSignal(list)
    sgl_read_actual = qtc.pyqtSignal(list)
    sgl_read_delta = qtc.pyqtSignal(list)
    sgl_read_lost = qtc.pyqtSignal(list)
    sgl_read_notes = qtc.pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.include_refcol = True
        self.enabled = True
        self.abort = False
        self.model = 'gpt-4o'
        if not self.include_refcol:
            self.sysmsg = 'You will be given an image of a single column with 24 evenly spaced rows. Read each row in the column from top to bottom. Any given row may or may not contain data. In your response, format empty rows as if they had an entry of the underscore symbol (_). Respond only with a list of length 24 corresponding to the 24 rows with each row delimited by the newline character. You MUST only respond with a list of length 24. Do not respond with a list that has more or less than 24 entries.'
        else:
            self.sysmsg = 'Do not prepend your response with a sentence stating what the image shows.'
            ' DO NOT include """`""" in your response.'
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

    def send_api_messages(self, colimgs :tuple, name):
        colimgs = self.prepare_imgs(colimgs)
        entarget, enactual, endelta, enlost, ennotes = self.encode_colimgs(colimgs)
        if self.abort: return
        targetres = self.send_col_message(entarget, target_prompt)
        self.sgl_read_target.emit(targetres)
        if self.abort: return
        actualres = self.send_col_message(enactual, actual_prompt)
        self.sgl_read_actual.emit(actualres)
        if self.abort: return
        deltares = self.send_col_message(endelta, delta_prompt)
        self.sgl_read_delta.emit(deltares)
        if self.abort: return
        lostres = self.send_col_message(enlost, lost_prompt)
        self.sgl_read_lost.emit(lostres)
        if self.abort: return
        notesres = self.send_col_message(ennotes, notes_prompt)
        self.sgl_read_notes.emit(notesres)
        if self.abort: return
        if name == '': return
        self.export_to_excel(targetres, actualres, deltares, lostres, notesres, name)
    
    def export_to_excel(self, tar, act, delt, los, note, sheet_name):
        def process_string(input_string):
            return input_string.splitlines()
        tar_values = process_string(tar)
        act_values = process_string(act)
        delt_values = process_string(delt)
        los_values = process_string(los)
        note_values = process_string(note)
        hours_values = process_string('11pm\n12am\n1am\n2am\n3am\n4am\n5am\n6am\n7am\n8am\n9am\n10am\n11am\n12pm\n1pm\n2pm\n3pm\n4pm\n5pm\n6pm\n7pm\n8pm\n9pm\n10pm')
        max_length = 24  
        tar_values = tar_values[:max_length] + [''] * (max_length - len(tar_values))
        act_values = act_values[:max_length] + [''] * (max_length - len(act_values))
        delt_values = delt_values[:max_length] + [''] * (max_length - len(delt_values))
        los_values = los_values[:max_length] + [''] * (max_length - len(los_values))
        note_values = note_values[:max_length] + [''] * (max_length - len(note_values))
        results = {
            'Hours' : hours_values,
            'Target': tar_values,
            'Actual': act_values,
            'Delta': delt_values,
            'Lost': los_values,
            'Notes': note_values
            }
        #Change the below to the desired path
        excel_path = "C:\\Users\\jabil\\Desktop\\DBTH_AutoDrills_Copy.xlsx"
        df = pd.DataFrame(results)
        new_df = self.add_time(df)
        newer_df = self.blank_row(new_df)
        # with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        #     newer_df.to_excel(writer, index=False, sheet_name=sheet_name)
        print("Results exported to DBTH_AutoDrills_Copy.xlsx")
        print(f"Total rows: {len(tar_values)}")
        print(f"Example values: {tar_values[:5]}")

        if os.path.exists(excel_path):
            wb = load_workbook(excel_path)
        else:
            wb = Workbook()

        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            ws.insert_rows(1, amount=len(new_df) + 1)
            next_row = 1
        else:
            ws = wb.create_sheet(sheet_name)
            next_row = 1

        for r_idx, row in enumerate(dataframe_to_rows(newer_df, index=False, header=True), start=next_row):
            for c_idx, value in enumerate(row, start=1):
                ws.cell(row=r_idx, column=c_idx, value=value)
        # yellow_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
        # light_red_fill = PatternFill(start_color='E6B8B7', end_color='E6B8B7', fill_type='solid')
        # light_green_fill = PatternFill(start_color='B4DB8D', end_color='B4DB8D', fill_type='solid')
        # black_fill = PatternFill(start_color='000000', end_color='000000', fill_type='solid')
        # red_fill = PatternFill(start_color='FF0000', end_color='FF0000', fill_type='solid')
        # self.apply_conditional_formatting(ws, red_fill, next_row)
        wb.save(excel_path)
        self.open_excel_file(excel_path)

    def add_time(self, df):
        yesterday = (datetime.now() - timedelta(days=1)).strftime(f'%Y-%m-%d')
        df['Date'] = yesterday
        return df
    
    def blank_row(self, df):
        new_df = []
        blank_row = [''] * len(df.columns)
        for i, row in df.iterrows():
            new_df.append(row.tolist())
            if '10pm' in row.values:
                new_df.append(blank_row)
        new_df = pd.DataFrame(new_df, columns=df.columns)
        return new_df
    
    def open_excel_file(self, path):
        if platform.system() == 'Windows':
            os.startfile(path)
        else:
            os.system(f'xdg-open "{path}"')

    def apply_conditional_formatting(self, ws, red_fill, next_row):
        start_row = next_row
        max_row = ws.max_row
        formula = f'D{start_row}<>(C{start_row}-B{start_row})'
        rule_d = FormulaRule(formula=[formula], fill=red_fill)
        ws.conditional_formatting.add(f'D{start_row}:D{max_row}', rule_d)

        rule_c = FormulaRule(formula=[formula], fill=red_fill)
        ws.conditional_formatting.add(f'C{start_row}:C{max_row}', rule_c)

        rule_b = FormulaRule(formula=[formula], fill=red_fill)
        ws.conditional_formatting.add(f'B{start_row}:B{max_row}', rule_b)


    # def export_to_excel(self, tar, act, delt, los, note):
    #         results = {
    #             'Target': [tar],
    #             'Actual': [act],
    #             'Delta': [delt],
    #             'Lost': [los],
    #             'Notes': [note]
    #             }
    #         df = pd.DataFrame(results) 
    #         df.to_excel('Desktop\output3.xlsx', index=False)
    #         print("Results exported to output.xlsx")
    #         print(len(tar), len(act), len(delt), len(los), len(note), tar)

    def send_col_message(self, enimg, prompt):
        model_id = self.model
        messages = [
            {'role': 'system',
            'content': prompt},
            {'role': 'user',
            'content': [
                {'type': 'image_url',
                'image_url':  {
                    'url': f'data:image/png;base64,{enimg}',
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
        lst = response.split('\n')
        i = 0
        while i < len(lst):
            lst[i] = lst[i].strip()
            if lst[i] == 'X':
                lst[i] = 'x'
            if '```' in lst[i]:
                lst.pop(i)
            else:
                i += 1
        return lst

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
                numimg = cv2.imread('C:\\Users\\jabil\\Desktop\\dbth_images\\numcol.png')
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
