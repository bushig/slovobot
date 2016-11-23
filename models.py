from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

engine = create_engine('sqlite:///database.db', echo=False)
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)


class Word(Base):
    __tablename__ = 'word'

    id = Column(Integer, primary_key=True)
    word = Column(String(120))


class ActiveGame(Base):
    __tablename__ = 'active_game'

    id = Column(Integer, primary_key=True) #chat_id
    has_started = Column(Boolean, default=False)
    current_player = Column(Integer, default=0)
    timeout = Column(Integer, default=0)
    turn_start = Column(DateTime)
    last_letter = Column(String(1),)
    #add time between answers in seconds

    players = relationship(User, secondary='active_game_user_link', backref='active_games')
    guessed_words = relationship(Word, secondary='active_game_word_link')


class ActiveGameWordLink(Base):
    """Guessed words of active game"""
    __tablename__ = 'active_game_word_link'

    game_id = Column(Integer, ForeignKey('active_game.id'), primary_key=True)
    word_id = Column(Integer, ForeignKey('word.id'), primary_key=True)
    #user_id = Column(Integer, ForeignKey('User.id'))


class ActiveGameUserLink(Base):
    """Players of active game"""
    __tablename__ = 'active_game_user_link'

    game_id = Column(Integer, ForeignKey('active_game.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)