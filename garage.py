#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time
import RPi.GPIO as GPIO

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
logger = logging.getLogger(__name__)

def start(bot, update):
        update.message.reply_text('Hi!')

def switchGarage(bot, update):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(26, GPIO.OUT)
 
    GPIO.output(26, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(26, GPIO.LOW)
    time.sleep(2)
    GPIO.cleanup()

def main():
    updater = Updater("366736703:AAH4Cvc7-j4aQWro0sdlWvnh6MEgPA78nqY")

    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text, switchGarage))

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
