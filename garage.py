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


def get_config():
    with open(os.path.join(pwd, "./config.yml"), 'r') as ymlfile:
        config = yaml.load(ymlfile)
    return config


def start(bot, update):
    if authorized(update, bot):
        custom_keyboard = [['Kommen 🏠', 'Gehen 🚙'], ['Garage öffnen ⏫', '2 Minuten öffnen ⏱']]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text("Hallo " + update.message.from_user.first_name + u" ✌🏻",
                                  reply_markup=reply_markup)


def ping(ip):
    ret = subprocess.call(['ping', '-c', '2', '-W', '1', ip],
                          stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
    return ret == 0


def switch_garage():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(26, GPIO.OUT)

    GPIO.output(26, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(26, GPIO.LOW)
    time.sleep(2)
    GPIO.cleanup()


def count_down(bot, job):
    global counter
    global abort
    counter = counter - 1
    reply_markup = False
    down_job = Job(count_down, 1, repeat=False, context=job.context)
    if abort:
        text = "Wird abgebrochen..."
        abort = False
    elif counter == -1:
        text = "Garage wird geschlossen..."
    else:
        text = "Garage wird in *" + str(counter) + " Sekunden* geschlossen."
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('❌ Abbrechen', callback_data='abort')]])
        job.context[1].put(down_job)
    bot.editMessageText(text=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN,
                        chat_id=job.context[0].chat_id, message_id=job.context[0].message_id)
    if counter == -1:
        switch_garage()


def auto_close(bot, update, job_queue, state):
    msg = update.message.reply_text("Garage wird geöffnet...\nWieder schließen?",
                                    reply_markup=InlineKeyboardMarkup(
                                        [[InlineKeyboardButton('⏬ Schließen', callback_data='close')]]))
    switch_garage()
    job = Job(check_state, 5, repeat=False, context=[update, state, job_queue, msg])
    job_queue.put(job)


def check_state(bot, job):
    global abort
    ip = cfg['owner']['ip']
    if bool(ping(ip)) != bool(job.context[1]):
        if abort:
            abort = False
            return
        else:
            ping_job = Job(check_state, 5, repeat=False, context=job.context)
            job.context[2].put(ping_job)
    else:
        bot.editMessageText(text="Garage wird geöffnet...", chat_id=job.context[3].chat_id,
                            message_id=job.context[3].message_id)
        msg = job.context[0].message.reply_text("Garage wird in *20 Sekunden* geschlossen.",
                                                parse_mode=ParseMode.MARKDOWN,
                                                reply_markup=InlineKeyboardMarkup(
                                                    [[InlineKeyboardButton('❌ Abbrechen', callback_data='abort')]]))
        down_job = Job(count_down, 1, repeat=False, context=[msg, job.context[2]])
        job.context[2].put(down_job)

        global counter
        counter = 20


def button(bot, update):
    global abort
    query = update.callback_query
    if query.data == "abort":
        abort = True
    elif query.data == "close":
        abort = True
        bot.editMessageText(text='Garage wird geschlossen...',
                            chat_id=query.message.chat_id, message_id=query.message.message_id)
        switch_garage()
    update.callback_query.answer()


def authorized(update, bot):
    userlist = [cfg['owner']['id']] + list(cfg['user'].values())
    if update.message.chat_id in userlist:
        return True
    else:
        update.message.reply_text(
            "Zugriff verweigert.\nZum Freischalten bitte an @" + cfg['owner']['username'] + " wenden.")
        bot.sendMessage(
            text="Zugriff für *" + update.message.from_user.first_name + " " + update.message.from_user.last_name
                 + " " + str(update.message.from_user.id) + "* wurde verweigert.", chat_id=cfg['owner']['id'],
            parse_mode=ParseMode.MARKDOWN)
        return False


def open_short(bot, update, job_queue, close):
    update.message.reply_text("Garage wird geöffnet...")
    switch_garage()
    msg = update.message.reply_text("Garage schließen?",
                                    reply_markup=InlineKeyboardMarkup(
                                        [[InlineKeyboardButton('⏬ Schließen', callback_data='close')]]))
    if close:
        down_job = Job(msg_before_close, 90, repeat=False, context=[msg, job_queue])
        job_queue.put(down_job)


def msg_before_close(bot, job):
    global counter
    counter = 29
    bot.editMessageText(text="Automatisches schließen...", chat_id=job.context[0].chat_id,
                        message_id=job.context[0].message_id)
    job.context[0] = bot.sendMessage(text="Garage wird in 30 Sekunden geschlossen.", chat_id=job.context[0].chat_id)
    down_job = Job(count_down, 1, repeat=False, context=job.context)
    job.context[1].put(down_job)


def analyze_text(bot, update, job_queue):
    if authorized(update, bot):
        if update.message.text == 'Kommen 🏠':
            auto_close(bot, update, job_queue, True)
        elif update.message.text == 'Gehen 🚙':
            auto_close(bot, update, job_queue, False)
        elif update.message.text == 'Garage öffnen ⏫':
            open_short(bot, update, job_queue, False)
        elif update.message.text == '2 Minuten öffnen ⏱':
            open_short(bot, update, job_queue, True)
        else:
            start(bot, update)
        if not update.message.chat_id == cfg['owner']['id']:
            bot.sendMessage(text="*" + update.message.from_user.first_name + "* hat *'" + update.message.text
                                 + "'* gesendet.", chat_id=cfg['owner']['id'], parse_mode=ParseMode.MARKDOWN)


def main():
    global pwd
    global cfg
    global abort

    abort = False
    pwd = os.path.dirname(__file__)
    cfg = get_config()

    updater = Updater(cfg['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text, analyze_text, pass_job_queue=True))
    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
