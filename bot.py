# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import config

updater = Updater(config.TOKEN)
dispatcher = updater.dispatcher

import random


#Function to listen players messages in singleplayer
def listen_single(bot, update):
    print('listened')
    bot.sendMessage(chat_id=update.message.chat_id, text=str(random.randint(1,100)))


#Function to start singleplayer
def start_single(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Да начанется синглплеер!")
    message_handler = MessageHandler(Filters.text, listen_single)
    dispatcher.add_handler(message_handler)





# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler('singleplayer', start_single))

#Start server
updater.start_webhook(listen="0.0.0.0",
                      port=config.PORT,
                      url_path=config.TOKEN)
updater.bot.setWebhook("https://slovobot.herokuapp.com/" + config.TOKEN)
updater.idle()




