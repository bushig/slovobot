# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from sqlalchemy.orm import sessionmaker

import random, logging
from datetime import datetime

import config
from utils import parse_words_from_file, get_or_add_user, is_game_over, quit_game, check_timeout,GOOD_LETTERS
from models import Base, engine
from models import ActiveGame, User, ActiveGameUserLink, Word, ActiveGameWordLink

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Configure sessionmaker for sqlalchemy
Session = sessionmaker(bind=engine)


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
                            text='Сейчас должен ходить *{}*.'.format(right_player.first_name),
                            parse_mode=telegram.ParseMode.MARKDOWN)
            return

        word = session.query(Word).filter_by(word=message_text).first()
        logging.info('Found word: {} in database by "{}" query'.format(word, message_text)) # TODO: make unique word constrait
        if word and word.word[0] == game.last_letter:
            if session.query(ActiveGameWordLink).filter_by(word_id=word.id, game_id=game.id).one_or_none():
                bot.sendMessage(chat_id=update.message.chat_id, text='Это слово уже было угадано.')
                return
            for let in word.word[::-1]:
                if let in GOOD_LETTERS:
                    next_letter = let
                    break
            # TODO: If no good next letter in word, select random letter
            game.current_player = (game.current_player + 1) % len(players)
            next_player = players[game.current_player]
            game.guessed_words.append(word)
            game.last_letter = next_letter
            game.turn_start = datetime.now()
            session.commit()
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Слово _\"{}\"_ найдено, ходит {}.\nВам слово на букву \"*{}*\".".format(message_text,
                                                                                                         next_player.first_name,
                                                                                                         next_letter),
                            parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text="Это слово не подходит, попробуй еще.")


def stats(bot, update):
    session = Session()
    user = get_or_add_user(bot, update, session)
    played = user.games_played
    won = user.games_won
    lost = played - won
    bot.sendMessage(chat_id=update.message.chat_id,
                    text='Статистика игрока {}:\nВсего игр: {}\nВыиграно: {}\nПроиграно: {}'.format(user.first_name,
                                                                                                    played, won, lost))


# Function to give up, if player don't want to play further or dont know next word
def giveup(bot, update):
    session = Session()
    user = get_or_add_user(bot, update, session)
    game = session.query(ActiveGame).get(update.message.chat_id)
    quit_game(bot, update, session, game, user)


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
                        text='Пользователь *{}* присоединился к игре.'.format(user.first_name), parse_mode=telegram.ParseMode.MARKDOWN)
    elif active_game.has_started:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Игра уже началась.")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Пользователь *{}* уже участвует в этой игре.'.format(user.first_name), parse_mode=telegram.ParseMode.MARKDOWN)


# Function to start game
def start_game(bot, update, args):
    # parse time paramert
    timeout = 0
    if len(args) <= 1:
        if len(args) == 1 and args[0].isdigit():
            timeout = int(args[0])
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text="Невалидное время.")
        return
    # Вывести пользователей которые играют и сделать игру активной. Назначить первого пользователя и проверить чтобы было минимум 2 игрока
    session = Session()
    user = get_or_add_user(bot, update, session)
    game = session.query(ActiveGame).get(update.message.chat_id)
    player_count = 0
    if game and game.has_started:
        bot.sendMessage(chat_id=update.message.chat_id, text="Игра уже началась.")
        return
    if game:
        players = game.players
        player_count = len(players)
        player_names = ', '.join([player.first_name for player in players])
    if game and player_count > 1:
        game.has_started = True
        game.timeout = timeout
        letter = random.choice(GOOD_LETTERS)
        game.last_letter = letter
        game.turn_start = datetime.now()
        session.commit()
        bot.sendMessage(chat_id=update.message.chat_id, text="Начинаем игру с игроками: {}.".format(player_names))
        if timeout == 0:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Первым ходит {}. Без ограничений по времени. Первая буква: *{}*.".format(
                                players[0].first_name, letter),
                            parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                        text="Первым ходит {}.\n Допустимое время между ходами: *{}* сек.\n Первая буква: *{}*.".format(players[0].first_name, timeout, letter),
                        parse_mode=telegram.ParseMode.MARKDOWN)

    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Нельзя начать игру, так как минимальное количество игроков: 2.\n Сейчас игроков: {}.\n Введите команду /join чтобы присоединиться.".format(
                            player_count))

# Skip turn
def skip(bot, update):
    session = Session()
    game = session.query(ActiveGame).get(update.message.chat_id)
    is_timedout = check_timeout(bot, update, game.timeout, game.turn_start)
    if is_timedout:
        quit_game(bot, update, session, game, game.players[game.current_player])


def main():
    updater = Updater(config.TOKEN)
    dispatcher = updater.dispatcher

    # Initialize DB
    Base.metadata.create_all(engine)

    # Import words to db
    parse_words_from_file(Session)

    # Add handlers to dispatcher
    dispatcher.add_handler(CommandHandler('start', start_game, pass_args=True))
    dispatcher.add_handler(CommandHandler('join', join))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('giveup', giveup))
    dispatcher.add_handler(CommandHandler('skip', skip))
    # dispatcher.add_handler(CommandHandler('info', info))  Display info of current game(user steps count, First letter)
    dispatcher.add_handler(MessageHandler([Filters.text], listen_players))

    # Start bot
    updater.start_webhook(listen="0.0.0.0",
                          port=config.PORT,
                          url_path=config.TOKEN)
    updater.idle()


# Start server
if __name__ == '__main__':
    main()
