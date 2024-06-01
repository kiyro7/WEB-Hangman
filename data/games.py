import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Game (SqlAlchemyBase, SerializerMixin):
    # таблица, которая будет создана
    __tablename__ = 'games'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    player_1 = sqlalchemy.Column(sqlalchemy.Integer)
    player_2 = sqlalchemy.Column(sqlalchemy.Integer)
    ready_1 = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    ready_2 = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    word_1 = sqlalchemy.Column(sqlalchemy.String, default="")
    word_2 = sqlalchemy.Column(sqlalchemy.String, default="")
    wordfind_1 = sqlalchemy.Column(sqlalchemy.String, default="")
    wordfind_2 = sqlalchemy.Column(sqlalchemy.String, default="")
    lvl_1 = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    lvl_2 = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    letters_1 = sqlalchemy.Column(sqlalchemy.String, default="")
    letters_2 = sqlalchemy.Column(sqlalchemy.String, default="")
    win_1 = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    win_2 = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    win = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
