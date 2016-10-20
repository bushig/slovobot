import time, logging

from models import Word

logging.getLogger(__name__)

def parse_words_from_file(filename='word_rus.txt', session_cls):
    """
    Import data from dictionary to DB. There is no data validation.
    """
    logging.info('Starting import of words to DB')
    t = time.time()
    session = Session()
    for line in open(filename, mode='r'):
        word = Word(word=line)
        session.add(word)
    session.commit()
    logging.info('Taken time: {:.2f} seconds'.format(time.time()-t))