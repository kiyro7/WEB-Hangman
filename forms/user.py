from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    nickname_email = StringField("Почта\псевдоним", validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    hashed_password = PasswordField('Пароль', validators=[DataRequired()])
    hashed_password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    nickname = StringField('Псевдоним', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class Check(FlaskForm):
    check = StringField('Код из сообщения:', validators=[DataRequired()])
    submit = SubmitField('Отправить')


class Partner(FlaskForm):
    check = StringField('Псевдоним', validators=[DataRequired()])
    submit = SubmitField('Поиск')


class Word(FlaskForm):
    word = StringField('Слово', validators=[DataRequired()])
    submit = SubmitField('Ввод')


class BotDifficulty(FlaskForm):
    bot_difficulty = SelectField('Выберите сложность бота:', choices=[('Низкая', 'Низкая'),
                                                                      ('Средняя', 'Средняя'),
                                                                      ('Высокая', 'Высокая')])
    submit = SubmitField('Ввод')


class Theme(FlaskForm):
    theme = SelectField('Выберите тему:', choices=[('Блюда', 'Блюда'), ('ВУЗ', 'ВУЗ'),
                                                   ('Город', 'Город'), ('Животные', 'Животные'),
                                                   ('Жилище', 'Жилище'),
                                                   ('Заболевания', 'Заболевания'),
                                                   ('Здоровье', 'Здоровье'), ('Кино', 'Кино'),
                                                   ('Музыка', 'Музыка'), ('Погода', 'Погода'),
                                                   ('Программирование', 'Программирование'),
                                                   ('Профессии', 'Профессии'), ('Спорт', 'Спорт'),
                                                   ('Театр', 'Театр')])
    submit = SubmitField('Ввод')
