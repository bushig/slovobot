# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from sqlalchemy.orm import sessionmaker

import random
import logging

import config
from models import Base, engine
from models import ActiveGame, User, ActiveGameUserLink


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
updater = Updater(config.TOKEN)
dispatcher = updater.dispatcher

# Configure sessionmaker for sqlalchemy
Session = sessionmaker(bind=engine)


# Function to listen players messages in singleplayer
def listen_players(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=str(random.randint(1, 100)))


# Function to add user to ActiveGame and register user if not registered
def signup(bot, update):
    session = Session()
    user = session.query(User).get(update.message.from_user.id)
    if not user:
        user = User(id=update.message.from_user.id,
                    first_name=update.message.from_user.first_name,
                    last_name=update.message.from_user.last_name,
                    username=update.message.from_user.username)
        session.add(user)
        session.commit()
        logging.info('New user {} registered'.format(user.first_name))
        bot.sendMessage(chat_id=update.message.chat_id, text='Новый пользователь {}'.format(user.first_name))

    active_game = session.query(ActiveGame).filter_by(chat_id=update.message.chat_id).first()
    if not active_game:
        active_game = ActiveGame(chat_id=update.message.chat_id)
        session.add(active_game)
        session.commit()
        logging.info('New active game created')

    player = session.query(ActiveGameUserLink).filter_by(game_id=active_game.id, user_id=user.id)
    if not player:
        player = ActiveGameUserLink(game_id=active_game.game_id, user_id=user.id)
        session.add(player)
        session.commit()
        logging.info('New player {} added to game {}'.format(user.first_name, active_game.id))
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Пользователь {} присоединился к игре.'.format(user.first_name))
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Пользователь {} уже участвует в этой игре.'.format(user.first_name))


# Function to start game
def start_game(bot, update):
    # Добавить всех пользователей в чате в бд, если их нет и создать Active game

    bot.sendMessage(chat_id=update.message.chat_id, text="Начинаем игру в с игроками...")


# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler('start', start_game))
dispatcher.add_handler(CommandHandler('signup', signup))
dispatcher.add_handler(MessageHandler(Filters.text, listen_players))

# Start server
if __name__ == '__main__':
    Base.metadata.create_all(engine)
    updater.start_webhook(listen="0.0.0.0",
                          port=config.PORT,
                          url_path=config.TOKEN)
    updater.bot.setWebhook("https://slovobot.herokuapp.com/" + config.TOKEN)
    updater.idle()
