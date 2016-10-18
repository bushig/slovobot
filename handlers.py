from telegram.ext import MessageHandler, Filters

from bot import dispatcher
import random


def start_single(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Да начанется синглплеер!")
    message_handler = MessageHandler(Filters.text, listen_single)
    dispatcher.add_handler(message_handler)


def listen_single(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=random.randint(1,100))