#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ssd1306.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 12/16/2021, 11:22:36 AM

import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from datetime import datetime


class SSD1306(object):
    def __init__(self):
        self.oled = Adafruit_SSD1306.SSD1306_128_64(rst=0)
        self.oled.begin()
        self.oled.clear()
        self.width = self.oled.width
        self.height = self.oled.height
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.truetype('../ARIALUNI.TTF', 9)
        self.cur_y = 0

    def show(self):
        self.oled.image(self.image)
        self.oled.display()

    def line(self, text, font_size=9):
        font = ImageFont.truetype("../ARIALUNI.TTF", font_size)
        self.draw.text((0, self.cur_y), text,  font=font, fill=255)
        self.cur_y += font_size

    def display(self, device_id="", temp=0, humi=0, pm25=0, co2=0, tvoc=0, flag="", version="", nbiot_csq=""):
        self.cur_y = 0
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        time_pairs = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S").split(' ')

        self.line(f'ID: {device_id}', 14)
        self.line(f'Date: {time_pairs[0]} {time_pairs[1]}')
        self.line(f'Temp: {temp} / RH: {humi}')
        self.line(f'PM2.5: {pm25} μg/m3')
        self.line(f'TVOC: {tvoc} ppb')
        self.line(f'CO2: {co2} ppm')
        self.draw.text((80, 40), f'csq: {nbiot_csq}', font=self.font, fill=255)
        self.draw.text((80, 51), f'V{version}',  font=self.font, fill=255)
        self.draw.text((117, 51), flag,  font=self.font, fill=255)
        self.show()
