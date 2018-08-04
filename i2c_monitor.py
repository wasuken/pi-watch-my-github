#!/usr/bin/python
# -*- coding: utf-8 -*-

import smbus
import time
import wiringpi
import requests
import json
import dateutil.parser
import pytz
import datetime

def json_in_datetime(json):
    return dateutil.parser.parse(json["created_at"])
def json_in_print_text(json):
    try:
        title=json[u"repo"][u"name"]
        cm_msg=json[u"payload"][u"commits"][0][u"message"]
    except KeyError as e:
        title=""
        cm_msg=""
        print(e)
    return title,cm_msg


wiringpi.wiringPiSetupGpio()
led_pin = 23
wiringpi.pinMode( led_pin, 1 )
# Define some device parameters
I2C_ADDR  = 0x27 # I2C device address, if any error, change this address to 0x27
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

def lcd_init():
    # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = the data
    # mode = 1 for data
    #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
    # Toggle enable
  time.sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  time.sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)

def lcd_string(message,line):
    # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
      lcd_byte(ord(message[i]),LCD_CHR)

def katakana(text):
	list1a = u"「。、」ヲ・ィァェゥォャュョッーアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン゛゜"
	list1b = u"アァイィウゥエェオォカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミ"
	list2a = u"ガギグゲゴザジズゼゾダヂヅデドバビブベボ"
	list2b = u"ザシジスズセゼソゾタダチヂッツナニヌネノ"
	list3a = u"パピプペポ"
	list3b = u"ナニヌネノ"

	text_changed = ""
	for l in text:
		#カタカナを変換
		if list1a.find(l) >= 0:
			text_changed += list1b[list1a.find(l)]
		#濁音を清音＋濁点に
		elif list2a.find(l) >= 0:
			text_changed += list2b[list2a.find(l)]
			text_changed += u"マ"
		#半濁音を清音＋半濁点に
		elif list3a.find(l) >= 0:
			text_changed += list3b[list3a.find(l)]
			text_changed += u"ミ"
		#その他の文字はそのままにする
		else:
			text_changed += l

	return text_changed

def get_my_github_events():
    dt_now = datetime.datetime.now()
    today_start=pytz.utc.localize(datetime.datetime(dt_now.year, dt_now.month, dt_now.day - 1, 0, 0, 0))
    url=u"https://api.github.com/users/wasuken/events"
    js_text=requests.get(url).text
    data=json.loads(js_text)
    return  [x for x in data if json_in_datetime(x) > today_start]
def main():
    # Main program block

  # Initialise display
  lcd_init()
  cnt=1
  result=get_my_github_events()
  while True:
    if cnt % 60 == 0:
        result = get_my_github_events()
        cnt=1
    for x in result[0:3]:
        repo=json_in_print_text(x)[0].split('/')
        print(repo)
        if len(repo) > 1:
            repo=repo[1]
        else:
            continue
        lcd_string(repo,LCD_LINE_1)
        lcd_string(json_in_print_text(x)[1],LCD_LINE_2)
        time.sleep(1)

    wiringpi.digitalWrite( led_pin, cnt % 2 )
    time.sleep(2)
    cnt+=1

if __name__ == '__main__':
  try:
      main()
  except KeyboardInterrupt:
    pass
  finally:
      lcd_byte(0x01, LCD_CMD)
