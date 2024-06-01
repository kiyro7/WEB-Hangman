import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class System (SqlAlchemyBase, SerializerMixin):
    # таблица, которая будет создана
    __tablename__ = 'system'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    player = sqlalchemy.Column(sqlalchemy.Integer)
    word = sqlalchemy.Column(sqlalchemy.String, default="")
    wordfind = sqlalchemy.Column(sqlalchemy.String, default="")
    lvl = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    letters = sqlalchemy.Column(sqlalchemy.String, default="")
    win = sqlalchemy.Column(sqlalchemy.Boolean, default=False)