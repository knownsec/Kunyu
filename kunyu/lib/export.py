#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: export.py
@Time: 2021/6/22 15:53
'''

import os
import datetime

import csv
import xlwt

from kunyu.utils.log import logger
from kunyu.config import setting

""""
    According to different search engines,
    Select the appropriate ICO icon encryption method.
    ZoomEye, for example, supports both MMH3 and MD5,But FoFa only supports MMH3.
    Through the ICO icon search Related assets,It's very always efficient.
    Security researchers can also modify code files as needed.
"""


def createdir():
    # Create the results output directory.
    __dirnamae = datetime.datetime.now().strftime("%Y%m%d%H%M")
    path = os.path.expanduser(setting.OUTPUT_PATH)
    __path = os.path.join(path, __dirnamae)
    setting.OUTPUT_PATH = __path
    if os.path.exists(__path):
        return 0
    # Create Directory
    os.makedirs(__path)


def export_csv(columns, data):
    # The export file format is CSV
    __filename = datetime.datetime.now().strftime("%H%M%S.csv")
    path = os.path.join(setting.OUTPUT_PATH, __filename)
    try:
        with open(path, "a", newline='', encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for num, key in enumerate(data["results"]):
                writer.writerow([str(num + 1), key[0], key[1], key[2], key[3], key[4], key[5], key[6]])

    except Exception:
        logger.error("hope you don't Batch scanning")
    logger.info("File export Path:" + path)


def export_xls(content, head):
    style_head = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = "微软雅黑"  # Set title font
    font.bold = True
    font.height = 250  # Set title height
    font.colour_index = 1
    bg = xlwt.Pattern()
    bg.pattern = xlwt.Pattern.SOLID_PATTERN
    bg.pattern_fore_colour = 0x00
    al = xlwt.Alignment()
    al.horz = 0x02  # Set horizontal center
    style_head.font = font
    style_head.pattern = bg
    style_head.alignment = al
    excel = xlwt.Workbook(encoding='utf-8')
    sheet = excel.add_sheet("坤舆")
    for i in range(10):
        first_col_1 = sheet.col(i)
        first_col_1.width = 256 * 20
    for index, value in enumerate(head):
        sheet.write(0, index, value, style_head)

    # Set the cell format
    style = xlwt.XFStyle()
    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1
    borders.left_colour = 0
    borders.right_colour = 0
    borders.top_colour = 0
    borders.bottom_colour = 0
    style.alignment = al
    style.borders = borders

    # Cyclic write
    for index, value_list in enumerate(content, 1):
        for i, value in enumerate(value_list):
            sheet.write(index, i, value, style)

    # Save excel file
    __time = datetime.datetime.now().strftime("%H%M%S.xls")
    file_name = excel.save(os.path.join(setting.OUTPUT_PATH, __time))
    return file_name


def export_txt(console):
    # The export file format is TXT
    __time = datetime.datetime.now().strftime("%H%M%S.txt")
    path = os.path.join(setting.OUTPUT_PATH, __time)
    console.save_text(path)


if __name__ == "__main__":
    createdir()
