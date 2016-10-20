# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from sqlalchemy.orm import sessionmaker

import random, logging

import config
from utils import parse_words_from_file, GOOD_LETTERS
from models import Base, engine
from models import ActiveGame, User, ActiveGameUserLink, Word, ActiveGameWordLink

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Configure sessionmaker for sqlalchemy
Session = sessionmaker(bind=engine)


# Function to add user in DB
def get_or_add_user(bot, update, session):
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
    return user


# Function to listen players messages in multiplayer
def listen_players(bot, update):
    message_text = update.message.text.lower()
    if len(message_text.split()) != 1: return
    session = Session()
    user = get_or_add_user(bot, update, session)
    game = session.query(ActiveGame).get(update.message.chat_id)
    if game and game.has_started:
        players = game.players
        right_player = players[game.current_player]
        if user != right_player:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text='Сейчас должен ходить {}'.format(right_player.first_name))
            return

        word = session.query(Word).filter_by(word=message_text).first()
        logging.info('Found word: {} in database by "{}" query'.format(word, message_text))
        if word and word.word[0] == game.last_letter:
            for let in word.word[::-1]:
                if let in GOOD_LETTERS:
                    next_letter = let
                    break
            game.current_player = (game.current_player + 1) % len(players)
            next_player = players[game.current_player]
            game.guessed_words.append(word)
            game.last_letter = next_letter
            session.commit()
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Слово \"{}\" найдено, ходит {}. Вам слово на букву \"{}\"".format(message_text,
                                                                                                    next_player,
                                                                                                    next_letter))
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text="Это слово не подходит, попробуй еще.")


# Function to add user to ActiveGame and register user if not registered
def join(bot, update):
    session = Session()
    user = get_or_add_user(bot, update, session)
    active_game = session.query(ActiveGame).get(update.message.chat_id)
    if not active_game:
        active_game = ActiveGame(id=update.message.chat_id)
        session.add(active_game)
        session.commit()
        logging.info('New active game created in chat {}'.format(update.message.chat_id))

    player = session.query(ActiveGameUserLink).filter_by(game_id=active_game.id, user_id=user.id).one_or_none()
    # print('ИГРОК:', player, 'Активная игра:',active_game.id,'Пользователь', user.id)
    if not player and not active_game.has_started:
        player = ActiveGameUserLink(game_id=active_game.id, user_id=user.id)
        session.add(player)
        session.commit()
        logging.info('New player {} added to game {}'.format(user.first_name, active_game.id))
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Пользователь {} присоединился к игре.'.format(user.first_name))
    elif active_game.has_started:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Игра уже началась")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Пользователь {} уже участвует в этой игре.'.format(user.first_name))


# Function to start game
def start_game(bot, update):
    # Вывести пользователей которые играют и сделать игру активной. Назначить первого пользователя и проверить чтобы было минимум 2 игрока
    session = Session()
    user = get_or_add_user(bot, update, session)
    game = session.query(ActiveGame).get(update.message.chat_id)
    player_count = 0
    if game and game.has_started:
        bot.sendMessage(chat_id=update.message.chat_id, text="Игра уже началась")
        return
    if game:
        players = game.players
        player_count = len(players)
        player_names = ', '.join([player.first_name for player in players])
    if game and player_count > 1:
        game.has_started = True
        letter = random.choice(GOOD_LETTERS)
        game.last_letter = letter
        session.commit()
        bot.sendMessage(chat_id=update.message.chat_id, text="Начинаем игру с игроками: {}".format(player_names))

        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Первым ходит {}. Первая буква: {}".format(players[0].first_name, letter))

    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Нельзя начать игру, так как минимальное количество игроков: 2. Сейчас игроков: {}. Введите команду /join чтобы присоединиться".format(
                            player_count))


def main():
    updater = Updater(config.TOKEN)
    dispatcher = updater.dispatcher

    # Initialize DB
    Base.metadata.create_all(engine)

    # Import words to db
    parse_words_from_file(Session)

    # Add handlers to dispatcher
    dispatcher.add_handler(CommandHandler('start', start_game))
    dispatcher.add_handler(CommandHandler('join', join))
    # dispatcher.add_handler(CommandHandler('giveup', giveup))
    dispatcher.add_handler(MessageHandler([Filters.text], listen_players))

    # Start bot
    updater.start_webhook(listen="0.0.0.0",
                          port=config.PORT,
                          url_path=config.TOKEN)
    updater.idle()


# Start server
if __name__ == '__main__':
    main()
