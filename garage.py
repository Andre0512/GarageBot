#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import logging
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time
import RPi.GPIO as GPIO
import yaml
import os
import subprocess

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
logger = logging.getLogger(__name__)


def getConfig():
    with open(os.path.join(pwd, "./config.yml"), 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg

def start(bot, update):
    custom_keyboard = [['Kommen 🏠','Gehen 🚙'],['Nur Öffnen ⏫']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text("Hallo " + update.message.from_user.first_name + u" ✌🏻", reply_markup=reply_markup)

def ping(ip):
    ret = subprocess.call(['ping', '-c', '2', '-W', '1', ip],
            stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
    return ret == 0

def switchGarage():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(26, GPIO.OUT)
 
    GPIO.output(26, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(26, GPIO.LOW)
    time.sleep(2)
    GPIO.cleanup()

def msgGehen(bot, update):
    switchGarage()
    update.message.reply_text("Garage wird geöffnet...") 
    ip = cfg['owner']['ip']
    while ping(ip):
        time.sleep(20)
    update.message.reply_text("Garage wird geschlossen...") 
    switchGarage()

def analyzeText(bot,update):
    if update.message.text == 'Kommen 🏠':
        None
    elif update.message.text == 'Gehen 🚙':
        msgGehen(bot,update)
    elif update.message.text == 'Nur Öffnen ⏫':
        None

def main():
    global pwd
    global cfg

    pwd = os.path.dirname(__file__)
    cfg = getConfig()
    
    updater = Updater(cfg['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, analyzeText))
    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
