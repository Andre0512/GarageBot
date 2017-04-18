#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import logging
from telegram import ReplyKeyboardMarkup, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, Job
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
    update.message.reply_text("Hallo " + update.message.from_user.first_name + u" ✌🏻",
           reply_markup=reply_markup)

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

def countDown(bot, job):
    global counter
    global abort
    counter = counter -1
    job = Job(countDown, 1, repeat=False, context=job.context)
    reply_markup=False
    if counter == -1:
        text="Garage wird geschlossen..."
    elif abort:
        text="Wird abgebrochen..."
        abort = False
    else:
        job.context[1].put(job)
        text="Garage wird in *" + str(counter) + " Sekunden* geschlossen."
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Abbrechen', callback_data='abort')]])
    bot.editMessageText(text=text,reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, 
            chat_id=job.context[0].chat_id, message_id=job.context[0].message_id)
    if counter == -1:
        switchGarage()

def autoClose(bot, update, job_queue, state):
    update.message.reply_text("Garage wird geöffnet...") 
    switchGarage()
    ip = cfg['owner']['ip']
    while bool(ping(ip)) != bool(state):
        time.sleep(5)
    msg = update.message.reply_text("Garage wird in *20 Sekunden* geschlossen.", parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Abbrechen', callback_data='abort')]]))
 
    job = Job(countDown, 1, repeat=False, context=[msg,job_queue])
    job_queue.put(job)
    
    global counter
    counter = 20

def button(bot, update):
    global abort
    query = update.callback_query
    if query.data == "abort":
        abort = True
    elif query.data == "close":
        bot.editMessageText(text='Garage wird geschlossen...', 
                        chat_id=query.message.chat_id, message_id=query.message.message_id)
        switchGarage()    
    update.callback_query.answer()

def analyzeText(bot,update, job_queue):
    userlist = [cfg['owner']['id']] + list(cfg['user'].values())
    if update.message.chat_id in userlist:
        if update.message.text == 'Kommen 🏠':
            autoClose(bot,update,job_queue,True)
        elif update.message.text == 'Gehen 🚙':
            autoClose(bot,update,job_queue,False)
        elif update.message.text == 'Nur Öffnen ⏫':
            update.message.reply_text("Garage wird geöffnet...") 
            switchGarage()    
            msg = update.message.reply_text("Garage schließen?",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏬ Schließen', callback_data='close')]]))
    else:
         update.message.reply_text("Zugriff verweigert.\nZum Freischalten bitte an @Andre0512 wenden.")


def main():
    global pwd
    global cfg
    global abort

    abort = False
    pwd = os.path.dirname(__file__)
    cfg = getConfig()
    
    updater = Updater(cfg['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text, analyzeText, pass_job_queue=True))
    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
