import time, logging

from models import Word

logging.getLogger(__name__)

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
        word = Word(word=line)
        session.add(word)
    session.commit()
    logging.info('Taken time: {:.2f} seconds'.format(time.time() - t))
