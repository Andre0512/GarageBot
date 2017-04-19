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
    if authorized(update, bot):
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
    downJob = Job(countDown, 1, repeat=False, context=job.context)
    reply_markup=False
    if counter == -1:
        text="Garage wird geschlossen..."
    elif abort:
        text="Wird abgebrochen..."
        abort = False
    else:
        job.context[1].put(downJob)
        text="Garage wird in *" + str(counter) + " Sekunden* geschlossen."
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Abbrechen', callback_data='abort')]])
    bot.editMessageText(text=text,reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, 
            chat_id=job.context[0].chat_id, message_id=job.context[0].message_id)
    if counter == -1:
        switchGarage()

def autoClose(bot, update, job_queue, state):
    msg = update.message.reply_text("Garage wird geöffnet...\nWieder schließen?", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏬ Schließen', callback_data='close')]]))
    switchGarage()
    job = Job(checkState, 5, repeat=False, context=[update,state,job_queue,msg])
    job_queue.put(job)

def checkState(bot, job):
    global abort
    ip = cfg['owner']['ip']
    if bool(ping(ip)) != bool(job.context[1]):
        if abort:
            abort=False
            return
        else:
            pingJob = Job(checkState, 5, repeat=False, context=job.context)
            job.context[2].put(pingJob)
    else:
        bot.editMessageText(text="Garage wird geöffnet...", chat_id=job.context[3].chat_id, message_id=job.context[3].message_id)
        msg = job.context[0].message.reply_text("Garage wird in *20 Sekunden* geschlossen.", parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Abbrechen', callback_data='abort')]]))
        downJob = Job(countDown, 1, repeat=False, context=[msg,job.context[2]])
        job.context[2].put(downJob)
    
        global counter
        counter = 20

def button(bot, update):
    global abort
    query = update.callback_query
    if query.data == "abort":
        abort = True
    elif query.data == "close":
        abort=True
        bot.editMessageText(text='Garage wird geschlossen...', 
                        chat_id=query.message.chat_id, message_id=query.message.message_id)
        switchGarage()    
    update.callback_query.answer()

def authorized(update, bot):
    userlist = [cfg['owner']['id']] + list(cfg['user'].values())
    if update.message.chat_id in userlist:
        return True
    else:
        update.message.reply_text("Zugriff verweigert.\nZum Freischalten bitte an @" + cfg['owner']['username'] + " wenden.")
        bot.sendMessage(text="Zugriff für *" + update.message.from_user.first_name + " " + update.message.from_user.last_name 
                 + " " + str(update.message.from_user.id) + "* wurde verweigert.", chat_id=cfg['owner']['id'], parse_mode=ParseMode.MARKDOWN)
        return False

def analyzeText(bot,update, job_queue):
    if authorized(update,bot):
        if update.message.text == 'Kommen 🏠':
            autoClose(bot,update,job_queue,True)
        elif update.message.text == 'Gehen 🚙':
            autoClose(bot,update,job_queue,False)
        elif update.message.text == 'Nur Öffnen ⏫':
            update.message.reply_text("Garage wird geöffnet...") 
            switchGarage()    
            update.message.reply_text("Garage schließen?",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏬ Schließen', callback_data='close')]]))
        else:
            start(bot,update)
        if not update.message.chat_id == cfg['owner']['id']:
            bot.sendMessage(text="*" + update.message.from_user.first_name + "* hat *'" + update.message.text 
                    + "'* gesendet.", chat_id=cfg['owner']['id'], parse_mode=ParseMode.MARKDOWN)

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
