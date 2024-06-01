import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase
import codes


class Bot (SqlAlchemyBase, SerializerMixin):
    # таблица, которая будет создана
    __tablename__ = 'bot'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    player = sqlalchemy.Column(sqlalchemy.Integer)
    word = sqlalchemy.Column(sqlalchemy.String, default="")
    wordfind_1 = sqlalchemy.Column(sqlalchemy.String, default="")
    wordfind_2 = sqlalchemy.Column(sqlalchemy.String, default="")
    lvl_1 = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    lvl_2 = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    letters = sqlalchemy.Column(sqlalchemy.String, default="")
    bot_letters = sqlalchemy.Column(sqlalchemy.String, default="")
    win_1 = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    win_2 = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    tie = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    theme = sqlalchemy.Column(sqlalchemy.String, default="")
    difficulty = sqlalchemy.Column(sqlalchemy.Integer, default=codes.LOW_BOT_DIFFICULTY)
