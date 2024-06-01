import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    # таблица, которая будет создана
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    nickname = sqlalchemy.Column(sqlalchemy.String, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    code = sqlalchemy.Column(sqlalchemy.Integer)
    good = sqlalchemy.Column(sqlalchemy.Boolean)
    wins = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    fails = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    nones = sqlalchemy.Column(sqlalchemy.Integer, default=0)

