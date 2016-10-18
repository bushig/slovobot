# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler

import config
from handlers import start_single

updater = Updater(config.TOKEN)
dispatcher = updater.dispatcher



start_handler = CommandHandler('singleplayer', start_single)

dispatcher.add_handler(start_handler)

updater.start_webhook(listen="0.0.0.0",
                      port=config.PORT,
                      url_path=config.TOKEN)
updater.bot.setWebhook("https://slovobot.herokuapp.com/" + config.TOKEN)
updater.idle()




