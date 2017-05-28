#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import logging
from telegram import ReplyKeyboardMarkup, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, Job
import time
#import RPi.GPIO as GPIO
import yaml
import os
import subprocess

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def custom_str_constructor(loader, node):
    return loader.construct_scalar(node).encode('utf-8')


def get_yml(file):
    result = {}
    with open(os.path.join(pwd, file), 'rb') as ymlfile:
        values = yaml.load(ymlfile)
        for k, v in values.items():
            result[k.decode('utf-8')] = dict_byte_to_str(v)
    return result


def dict_byte_to_str(v):
    result = {}
    if hasattr(v, 'items'):
        for key, value in v.items():
            if isinstance(value, bytes):
                value = value.decode('utf-8')
                value = str.replace(value, "\\n", "\n")
            result[key.decode('utf-8')] = value
    else:
        result = v.decode('utf-8')
        result = str.replace(result, "\\n", "\n")
    return result


def start(bot, update):
    if authorized(update, bot):
        custom_keyboard = [[string['arrive'] + ' 🏠', string['leave'] + ' 🚙'],
                           [string['open'] + ' ⏫', string['open_time'] + ' ⏱']]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text("Hallo " + update.message.from_user.first_name + u" ✌🏻",
                                  reply_markup=reply_markup)


def ping(ip):
    ret = subprocess.call(['ping', '-c', '2', '-W', '1', ip],
                          stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
    return ret == 0


def switch_garage():
    return
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
    if abort:
        text = string['stopping']
        abort = False
    elif counter == -1:
        text = string['closing']
    else:
        text = string['timer']
        text = str.replace(text, 'xxx', '*' + str(counter) + '*')
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(string['stop'], callback_data='abort')]])
        job.context[1].run_once(count_down, 1, context=job.context)
    bot.editMessageText(text=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN,
                        chat_id=job.context[0].chat_id, message_id=job.context[0].message_id)
    if counter == -1:
        switch_garage()


def auto_close(bot, update, job_queue, state):
    msg = update.message.reply_text(string['close_now'],
                                    reply_markup=InlineKeyboardMarkup(
                                        [[InlineKeyboardButton('⏬ ' + string['close'], callback_data='close')]]))
    switch_garage()
    job_queue.run_once(check_state, 5, context=[update, state, job_queue, msg])


def check_state(bot, job):
    global abort
    ip = cfg['owner']['ip']
    if bool(ping(ip)) != bool(job.context[1]):
        if abort:
            abort = False
            return
        else:
            job.context[2].run_once(check_state, 5, context=job.context)
    else:
        bot.editMessageText(text=string['opening'], chat_id=job.context[3].chat_id,
                            message_id=job.context[3].message_id)
        text = string['timer']
        text = str.replace(text, 'xxx', '*20*')
        msg = job.context[0].message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('❌ ' + string['stop'], callback_data='abort')]]))
        job.context[2].run_once(count_down, 1, context=[msg, job.context[2]])

        global counter
        counter = 20


def button(bot, update):
    global abort
    query = update.callback_query
    if query.data == "abort":
        abort = True
    elif query.data == "close":
        abort = True
        bot.editMessageText(text=string['closing'], chat_id=query.message.chat_id, message_id=query.message.message_id)
        switch_garage()
    update.callback_query.answer()


def authorized(update, bot):
    userlist = [cfg['owner']['id']] + list(cfg['user'].values())
    if update.message.chat_id in userlist:
        return True
    else:
        their_text = string['denied']
        their_text = str.replace(their_text, 'xxx', '@' + cfg['owner']['username'])
        my_text = string['denied_info']
        my_text = str.replace(my_text, 'xxx',
                              '*' + update.message.from_user.first_name + " " + update.message.from_user.last_name
                              + " (" + str(update.message.from_user.id) + ')*')
        update.message.reply_text(their_text)
        bot.sendMessage(text=my_text, chat_id=cfg['owner']['id'], parse_mode=ParseMode.MARKDOWN)
        return False


def open_short(bot, update, job_queue, close):
    update.message.reply_text(string['opening'])
    switch_garage()
    msg = update.message.reply_text(string['close_question'], reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton('⏬ ' + string['close'], callback_data='close')]]))
    if close:
        job_queue.run_once(msg_before_close, 90, context=[msg, job_queue])


def msg_before_close(bot, job):
    global counter
    counter = 29
    bot.editMessageText(text=string['automatic'], chat_id=job.context[0].chat_id,
                        message_id=job.context[0].message_id)
    text = string['timer']
    text = str.replace(text, 'xxx', '*30*')
    job.context[0] = bot.sendMessage(text=text, chat_id=job.context[0].chat_id, parse_mode=ParseMode.MARKDOWN)
    job.context[1].run_once(count_down, 1, context=job.context)


def analyze_text(bot, update, job_queue):
    if authorized(update, bot):
        if update.message.text == string['arrive'] + ' 🏠':
            auto_close(bot, update, job_queue, True)
        elif update.message.text == string['leave'] + ' 🚙':
            auto_close(bot, update, job_queue, False)
        elif update.message.text == string['open'] + ' ⏫':
            open_short(bot, update, job_queue, False)
        elif update.message.text == string['open_time'] + ' ⏱':
            open_short(bot, update, job_queue, True)
        else:
            start(bot, update)
        if not update.message.chat_id == cfg['owner']['id']:
            text = string['use_info']
            text = str.replace(text, 'xxx', "*" + update.message.from_user.first_name + "*")
            text = str.replace(text, 'yyy', "*" + update.message.text + "*")
            bot.sendMessage(text=text, chat_id=cfg['owner']['id'], parse_mode=ParseMode.MARKDOWN)


def main():
    global pwd
    global cfg
    global string
    global abort

    yaml.add_constructor(u'tag:yaml.org,2002:str', custom_str_constructor)
    abort = False
    pwd = os.path.dirname(__file__)
    cfg = get_yml("./config.yml")
    string = get_yml("./strings.yml")

    updater = Updater(cfg['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text, analyze_text, pass_job_queue=True))
    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
