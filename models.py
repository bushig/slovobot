from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

engine = create_engine('sqlite:///database.db', echo=False)
Base = declarative_base()


class User(Base):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)


class Word(Base):
    __tablename__ = 'Word'

    id = Column(Integer, primary_key=True)
    word = Column(String(120))


class ActiveGame(Base):
    __tablename__ = 'ActiveGame'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    has_started = Column(Boolean, default=False)
    #add time between answers in seconds

    players = relationship(User, secondary='ActiveGameUserLink', backref='active_games')
    guessed_words = relationship(Word, secondary='ActiveGameWordLink')


class ActiveGameWordLink(Base):
    """Guessed words of active game"""
    __tablename__ = 'ActiveGameWordLink'

    game_id = Column(Integer, ForeignKey('ActiveGame.id'), primary_key=True)
    word_id = Column(Integer, ForeignKey('Word.id'), primary_key=True)
    #user_id = Column(Integer, ForeignKey('User.id'))


class ActiveGameUserLink(Base):
    """Players of active game"""
    __tablename__ = 'ActiveGameUserLink'

    game_id = Column(Integer, ForeignKey('ActiveGame.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id'), primary_key=True)