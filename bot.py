# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler

import config

updater = Updater(config.TOKEN)
dispatcher = updater.dispatcher

# Handlers
def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Биби я бот!")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_webhook(listen="0.0.0.0",
                      port=config.PORT,
                      url_path=config.TOKEN)
updater.bot.setWebhook("https://slovobot.herokuapp.com/" + config.TOKEN)
updater.idle()




