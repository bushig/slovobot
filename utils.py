import time, logging

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
        game.delete()
        session.commit()
        bot.sendMessage(chat_id=update.message.chat_id,
                        text='Игра закончена. Победил игрок {}'.format(winner.first_name))
        return True
    return False
