import telegram

import time, logging
import datetime

from models import Word, User, ActiveGame


logging.getLogger(__name__)

#letters that suitable for words to start from
GOOD_LETTERS = ["а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф",
                "х", "ц", "ч", "ш", "щ", "э", "ю", "я"]


def parse_words_from_file(session_cls, filename='word_rus.txt'):
    """
    Import data from dictionary to DB. There is no data validation.
    """
    logging.info('Starting import of words to DB')
    t = time.time()
    session = session_cls()
    for line in open(filename, mode='r'):
        word = Word(word=line.rstrip())
        session.add(word)
    session.commit()
    logging.info('Taken time: {:.2f} seconds'.format(time.time() - t))

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

# Check if there is only one player left, and if so return True and close game
def is_game_over(bot, update, session):
    game = session.query(ActiveGame).get(update.message.chat_id)
    if len(game.players) == 1 and game.has_started:
        winner = game.players[0]
        winner.games_played += 1
        winner.games_won += 1
        session.delete(game)
        session.commit()
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Игра закончена. Победил игрок {}'.format(winner.first_name))
        return True
    return False

def check_timeout(bot, update, timeout, turn_start):
    now = datetime.datetime.now()
    delta = (now - turn_start).seconds
    if delta > timeout and timeout != 0:
        return True
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Нужно подождать {} секунд'.format(timeout - delta))
        return False

def quit_game(bot, update, session, game, player):
    if game and game.has_started:
        curr = game.current_player
        players = game.players
        player_pos = players.index(player)
        if player not in players:
            bot.sendMessage(chat_id=update.message.chat_id, text='Вы не участвуете в этой игре.')
        else:
            game.players.remove(player)
            player.games_played += 1
            if player_pos < curr:
                game.current_player -= 1
            elif game.current_player > len(game.players) - 1:
                game.current_player = 0
            session.commit()
            if not is_game_over(bot, update, session):
                bot.sendMessage(chat_id=update.message.chat_id,
                                text='Игрок *{}* покинул игру, следующим ходит *{}*'.format(player.first_name,
                                                                                            game.players[
                                                                                                game.current_player].first_name),
                                parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text='В этом чате нет активной игры.')
