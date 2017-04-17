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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
logger = logging.getLogger(__name__)


def getConfig():
    with open(os.path.join(pwd, "./config.yml"), 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg

def start(bot, update):
    custom_keyboard = [['Kommen 🏠 ','Gehen 🚙'],['Nur Öffnen ⏫']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text("Hallo " + update.message.from_user.first_name + u" ✌🏻", reply_markup=reply_markup)

def switchGarage(bot, update):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(26, GPIO.OUT)
 
    GPIO.output(26, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(26, GPIO.LOW)
    time.sleep(2)
    GPIO.cleanup()

def main():
    global pwd
    global cfg

    pwd = os.path.dirname(__file__)
    cfg = getConfig()
    
    updater = Updater(cfg['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, switchGarage))
    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
