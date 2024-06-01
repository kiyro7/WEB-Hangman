import random
import json
from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import codes
from room_class import Room
from hangman_bot_model import HangmanBot
from forms.user import RegisterForm, LoginForm, BotDifficulty, Check, Partner, Word, Theme
from data import db_session
from data.users import User
from data.game_with_system import System
from data.game_with_bot import Bot
from config import secret_key, auth_email, auth_password

DB_FILENAME = "db/gallows.db"
WORDS_FILENAME = 'data/words.json'

# список id игроков, которые ищут себе рандомного напарника для игры
in_search = []
# список id игроков, которым нашли пару и они сейчас в игре
in_game = []
# словарь, где КЛЮЧ id игрока, а ЗНАЧЕНИЕ - кортеж (id игры, тип игры)
# типы игры (совпадает с названием нужной таблицы) - "games", "bot", "system"
games_id = {}

# экземпляр класса комнаты, который будет осуществлять всю работу
room = Room()

MAX_MISTAKES = 7
LETTERS = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = secret_key
api = Api(app)
db_session.global_init(DB_FILENAME)


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", gif_name="error")


# Flask-login попытается загрузить пользователя ПЕРЕД каждым запросом.
# Он используется для проверки идентификатора пользователя в текущем сеансе(вышел / не вышел)
# и загрузки объекта пользователя для этого идентификатора.
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    global in_search, in_game, games_id
    if not current_user.is_authenticated:
        return redirect(f"/login")
    user_id = current_user.id
    if user_id not in in_search:
        if user_id not in in_game:
            in_search.append(user_id)
            return render_template("wait_for_start.html", gif_name="search")
        else:
            game_id = games_id[current_user.id][0]
            return redirect(f"/input_word/{game_id}")
    else:
        if len(in_search) > 1:
            user1, user2 = in_search[0], in_search[1]
            in_search = in_search[2:]

            game_id = room.make_room(user1, user2)
            in_game.append(user1)
            in_game.append(user2)
            games_id[user1] = (game_id, "games")
            games_id[user2] = (game_id, "games")
            return redirect(f"/input_word/{game_id}")
        else:
            return render_template("wait_for_start.html", gif_name="search")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        if db_sess.query(User).filter(User.email == form.email.data).filter(not User.good).first():
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            user.name = form.name.data
            user.email = form.email.data
            user.hashed_password = form.hashed_password.data
            user.nickname = form.nickname.data
            db_sess.commit()
            return redirect(f'/check/{form.email.data}')
        if form.hashed_password.data != form.hashed_password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="На эту почту уже зарегистрирован аккаунт")
        if db_sess.query(User).filter(User.nickname == form.nickname.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            hashed_password=form.hashed_password.data,
            nickname=form.nickname.data,
            good=False,
            code=random.randint(1000, 9999),
            wins=0
        )
        db_sess.add(user)
        db_sess.commit()
        send(form.email.data)
        return redirect(f'/check/{form.email.data}')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user1 = db_sess.query(User).filter(User.email == form.nickname_email.data).first()
        user2 = db_sess.query(User).filter(User.nickname == form.nickname_email.data).first()
        if user1 and user1.hashed_password == form.password.data and user1.good:
            login_user(user1, remember=form.remember_me.data)
            return redirect("/")
        elif user2 and user2.hashed_password == form.password.data and user2.good:
            login_user(user2, remember=form.remember_me.data)
            return redirect("/")
        elif user1 and not user1.hashed_password == form.password.data or \
                user2 and not user2.hashed_password == form.password.data:
            return render_template('login.html', message="Неправильный пароль",
                                   form=form, title='Авторизация')
        return render_template('login.html', message="Нет пользователя с таким псевдонимом/почтой",
                               form=form, title='Авторизация')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/main_menu')
def main_menu():
    return render_template("main_menu.html", title='Главное меню')


@app.route('/help')
def help_rules():
    return render_template("help.html", title='Помощь')


@app.route('/main_table')
def main_table():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.good).all()
    user.sort(key=lambda x: x.nones)
    user.sort(key=lambda x: x.fails)
    user.sort(key=lambda x: x.wins, reverse=True)
    return render_template("main_table.html", title='Таблица', users=user)


def send_mail(email, password, from_who, to_who, msg):
    # инициализировать SMTP-сервер
    server = smtplib.SMTP("smtp.gmail.com", 587)
    # подключиться к SMTP-серверу в режиме TLS (безопасный) и отправить EHLO
    server.starttls()
    # войти в учетную запись, используя учетные данные
    server.login(email, password)
    # отправить электронное письмо
    server.sendmail(from_who, to_who, msg.as_string())
    # завершить сеанс SMTP
    server.quit()


def send(email):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()
    check = user.code
    msg = MIMEMultipart()
    message = 'Ваш код: ' + str(check)
    msg.attach(MIMEText(message, 'plain'))
    send_mail(auth_email, auth_password, auth_email, email, msg)


@app.route('/check/<email>', methods=['GET', 'POST'])
def check_email(email):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()
    if user is None:
        return not_found(404)
    check = user.code
    form = Check()
    if form.validate_on_submit():
        if str(form.check.data) != str(check):
            return render_template('check.html', form=form,
                                   message="Проверьте код и введите его еще раз",
                                   title='Подтверждение почты')
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == email).first()
        user.good = True
        db_sess.commit()
        return redirect("/")
    return render_template('check.html', form=form, title='Подтверждение почты')


@app.route('/choosing_partner', methods=['GET', 'POST'])
def choosing_partner():
    global games_id
    if not current_user.is_authenticated:
        return redirect(f"/login")
    form = Partner()
    if form.validate_on_submit():
        friend_email = room.is_user_exist(form.check.data)
        if friend_email:  # такой юзер есть, теперь в рес его мыло
            friend_id = room.get_user_id(friend_email)
            if friend_id == current_user.id:
                return render_template('choosing_partner.html', form=form, title='Поиск партнера',
                                       message="Это вы, найдите друга)")
            game_id = room.make_room(current_user.id, friend_id)
            in_game.append(current_user.id)
            in_game.append(friend_id)
            games_id[current_user.id] = (game_id, "games")
            games_id[friend_id] = (game_id, "games")

            msg = MIMEMultipart()
            message = f'Дарова, вас тут в игру пригласил некий чел "{current_user.nickname}"\n' \
                      f'Если ты неожиданно хочешь с ним сыграть, то на ссылку: ' \
                      f'{request.host_url + f"wait_for_start/{game_id}"}'
            msg.attach(MIMEText(message, 'plain'))
            send_mail(auth_email, auth_password, auth_email, friend_email, msg)

            return redirect(f"/wait_for_start/{game_id}")
        else:
            return render_template('choosing_partner.html', form=form, title='Поиск партнера',
                                   message="Нет пользователя с таким ником, проверьте")
    else:
        return render_template('choosing_partner.html', form=form, title='Поиск партнера')


@app.route('/wait_for_start/<int:id_game>', methods=['GET', 'POST'])
def wait_for_start(id_game):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    room.set_user_in(id_game, current_user.id)
    if not room.all_2_in(id_game):
        return render_template("wait_for_start.html", title='Ждем-с', gif_name="wait_friend")
    # room.set_user_in(id_game, current_user.id)   LMAO WHY DOESNT IN WORK? XDXDXDXD
    return redirect(f"/input_word/{id_game}")


@app.route('/wait_for_start2/<int:id_game>', methods=['GET', 'POST'])
def wait_for_start2(id_game):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    room.set_user_in(id_game, current_user.id)
    if not room.all_2_in(id_game):
        return render_template("wait_for_start.html", title='Ждем-с', gif_name="wait_input")
    # room.set_user_in(id_game, current_user.id)   LMAO WHY DOESNT IN WORK? XDXDXDXD
    return redirect(f"/guess/{id_game}")


@app.route('/wait_for_end/<int:id_game>', methods=['GET', 'POST'])
def wait_for_end(id_game):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    room.set_user_win(id_game, current_user.id)
    if not room.is_the_end(id_game):
        return render_template("wait_for_start.html", title='Ждем-с', gif_name="wait_random")
    # room.set_user_in(id_game, current_user.id)   LMAO WHY DOESNT IN WORK? XDXDXDXD
    if room.is_user_win(id_game, current_user.id):
        return redirect(f"/win")
    return redirect(f"/fail")


@app.route('/input_word/<int:game_id>', methods=['GET', 'POST'])
def input_word(game_id):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    word = room.get_word_for_another_player(game_id, current_user.id)
    if word is None:
        return not_found(404)
    form = Word()
    form.word = word
    if request.method == "POST":
        if not room.check_word(word):
            room.set_word_for_another_player(game_id, current_user.id, '')
            return render_template('input_word.html', form=form, title='Ввод слова', word=word,
                                   game_id=game_id,
                                   message="Пожалуйста введите существующее слово от 5 до 20 букв",
                                   abc1=["Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ"],
                                   abc2=["Ф", "Ы", "В", "А", "П", "Р", "О", "Л", "Д", "Ж", "Э"],
                                   abc3=["Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю"])
        else:
            room.set_users_not_in(game_id)
            return redirect(f"/wait_for_start2/{game_id}")
    return render_template('input_word.html', form=form, title='Ввод слова', word=word,
                           game_id=game_id,
                           abc1=["Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ"],
                           abc2=["Ф", "Ы", "В", "А", "П", "Р", "О", "Л", "Д", "Ж", "Э"],
                           abc3=["Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю"])


@app.route('/input_letter/<symb>/<int:game_id>', methods=['GET', 'POST'])
def input_letter(symb, game_id):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    if symb.isalpha() and len(symb) == 1 and symb in LETTERS:
        word = room.get_word_for_another_player(game_id, current_user.id)
        if word is None:
            return not_found(404)
        if symb == 'Backspace':
            word = word[:-1]
        else:
            word += symb
        room.set_word_for_another_player(game_id, current_user.id, word)
    return redirect(f"/input_word/{game_id}")


@app.route('/word/<symb>/<int:game_id>', methods=['GET', 'POST'])
def word(symb, game_id):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    if symb.isalpha() and len(symb) == 1 and symb in LETTERS:
        room.process_letter(game_id, current_user.id, symb)
    return redirect(f"/guess/{game_id}")


@app.route('/word_2/<symb>/<int:game_id>', methods=['GET', 'POST'])
def word_2(symb, game_id):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    if symb.isalpha() and len(symb) == 1 and symb in LETTERS:
        db_sess = db_session.create_session()
        game = db_sess.query(System).filter(System.player == current_user.id).all()
        if game is None:
            return not_found(404)
        user = game[-1]
        word = user.word
        wordfind = [i for i in user.wordfind]
        let = user.letters
        lvl = user.lvl
        if symb in let:
            pass
        elif symb in word:
            let += symb
            for i in range(len(word)):
                if word[i] == symb:
                    wordfind[i] = symb
        else:
            let += symb
            lvl += 1
        user.wordfind = ''.join(wordfind)
        user.letters = let
        user.lvl = lvl
        db_sess.commit()
    return redirect(f"/game_with_system/{game_id}")


@app.route('/word_3/<symb>/<int:game_id>', methods=['GET', 'POST'])
def word_3(symb, game_id):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    if symb.isalpha() and len(symb) == 1 and symb in LETTERS:
        db_sess = db_session.create_session()
        game = db_sess.query(Bot).filter(Bot.player == current_user.id).all()
        if game is None:
            return not_found(404)
        user = game[-1]
        word = user.word
        wordfind = [i for i in user.wordfind_1]
        let = user.letters
        lvl = user.lvl_1
        if symb not in let:
            if symb in word:
                let += symb
                for i in range(len(word)):
                    if word[i] == symb:
                        wordfind[i] = symb
            else:
                let += symb
                lvl += 1
            user.wordfind_1 = ''.join(wordfind)
            user.letters = let
            user.lvl_1 = lvl

            bot = HangmanBot(user)
            bot_let_name = bot.process_word(user.wordfind_2)
            wordfind = [i for i in user.wordfind_2]
            bot_lvl = user.lvl_2
            if bot_let_name in word:
                for i in range(len(word)):
                    if word[i] == bot_let_name:
                        wordfind[i] = bot_let_name
            else:
                bot_lvl += 1
            user.wordfind_2 = ''.join(wordfind)
            user.bot_letters += bot_let_name
            user.lvl_2 = bot_lvl
            db_sess.commit()

    return redirect(f"/game_with_bot/{game_id}")


@app.route('/guess/<int:game_id>', methods=['GET', 'POST'])
def guess(game_id):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    word = room.get_word(game_id, current_user.id)
    if word is None:
        return not_found(404)
    word_h = room.get_hidden_word(game_id, current_user.id).upper()
    lvl = room.get_mistakes(game_id, current_user.id)
    if not word.lower() == word_h.lower() and lvl < MAX_MISTAKES:
        return render_template('guess.html', title='Виселица)', lvl=lvl, word=word_h,
                               game_id=game_id,
                               abc1=["Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ"],
                               abc2=["Ф", "Ы", "В", "А", "П", "Р", "О", "Л", "Д", "Ж", "Э"],
                               abc3=["Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю"])
    return redirect(f"/wait_for_end/{game_id}")


@app.route('/themes', methods=['GET', 'POST'])
def themes():
    global games_id
    if not current_user.is_authenticated:
        return redirect(f"/login")
    db_sess = db_session.create_session()
    form = Theme()
    if form.validate_on_submit():
        word_theme = form.theme.data
        with open(WORDS_FILENAME, mode='r', encoding='utf-8') as file:
            data = json.load(file)
        q = random.choice(data[word_theme])
        sys = System(
            player=current_user.id,
            word=q.upper(),
            wordfind="_" * len(q)
        )
        db_sess.add(sys)
        db_sess.commit()
        game = db_sess.query(System).filter(System.player == current_user.id).all()
        if game is None:
            return not_found(404)
        game_id = game[-1].id
        games_id[current_user.id] = [game_id, "system"]
        return redirect(f"/game_with_system/{game_id}")
    return render_template('themes.html', form=form, title='Выбор темы')


@app.route('/theme/<difficulty>', methods=['GET', 'POST'])
def theme(difficulty):
    global games_id
    if not current_user.is_authenticated:
        return redirect(f"/login")
    db_sess = db_session.create_session()
    form = Theme()
    if form.validate_on_submit():
        word_theme = form.theme.data
        with open(WORDS_FILENAME, mode='r', encoding='utf-8') as file:
            data = json.load(file)
        q = random.choice(data[word_theme])
        bot = Bot(
            player=current_user.id,
            word=q.upper(),
            wordfind_1="_" * len(q),
            wordfind_2="_" * len(q),
            theme=word_theme,
            difficulty=difficulty
        )
        db_sess.add(bot)
        db_sess.commit()
        game = db_sess.query(Bot).filter(Bot.player == current_user.id).all()
        if game is None:
            return not_found(404)
        game_id = game[-1].id
        games_id[current_user.id] = [game_id, "bot"]
        return redirect(f"/game_with_bot/{game_id}")
    return render_template('themes.html', form=form, title='Выбор темы')


@app.route('/bot_difficulty', methods=['GET', 'POST'])
def bot_difficulty():
    if not current_user.is_authenticated:
        return redirect(f"/login")

    form = BotDifficulty()

    if form.validate_on_submit():
        difficulty = form.bot_difficulty.data
        if difficulty == 'Низкая':
            difficulty = codes.LOW_BOT_DIFFICULTY
        elif difficulty == 'Средняя':
            difficulty = codes.MEDIUM_BOT_DIFFICULTY
        elif difficulty == 'Высокая':
            difficulty = codes.HIGH_BOT_DIFFICULTY

        return redirect(f'/theme/{difficulty}')
    return render_template('bot_difficulty.html', form=form, title='Выбор сложности')


@app.route('/game_with_system/<int:game_id>', methods=['GET', 'POST'])
def game_with_system(game_id):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    db_sess = db_session.create_session()
    game = db_sess.query(System).filter(System.player == current_user.id).all()
    if game is None:
        return not_found(404)
    user = game[-1]
    lvl = user.lvl
    word = user.wordfind
    if lvl == MAX_MISTAKES:
        user.win = False
        db_sess.commit()
        return redirect(f"/fail")
    elif word == user.word:
        user.win = True
        db_sess.commit()
        return redirect(f"/win")
    return render_template('game_with_system.html', title='Виселица)', lvl=lvl, word=word,
                           game_id=game_id,
                           abc1=["Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ"],
                           abc2=["Ф", "Ы", "В", "А", "П", "Р", "О", "Л", "Д", "Ж", "Э"],
                           abc3=["Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю"])


@app.route('/game_with_bot/<int:game_id>', methods=['GET', 'POST'])
def game_with_bot(game_id):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    db_sess = db_session.create_session()
    game = db_sess.query(Bot).filter(Bot.player == current_user.id).all()
    if game is None:
        return not_found(404)
    user = game[-1]
    lvl = user.lvl_1
    word = user.wordfind_1

    bot_lvl = user.lvl_2
    bot_word = user.wordfind_2

    curr_user = db_sess.query(User).filter(User.id == current_user.id).all()
    curr_user = curr_user[-1]

    if word == user.word and bot_word == user.word:
        user.win_1 = True
        user.win_2 = True
        curr_user.nones += 1
        db_sess.commit()
        return redirect("/tie/both")
    elif lvl >= 7 and bot_lvl >= 7:
        user.win_1 = False
        user.win_2 = False
        curr_user.nones += 1
        db_sess.commit()
        return redirect("/tie/none")
    elif word == user.word:
        user.win_1 = True
        user.win_2 = False
        curr_user.wins += 1
        db_sess.commit()
        return redirect("/win")
    elif bot_word == user.word:
        user.win_1 = False
        user.win_2 = True
        curr_user.fails += 1
        db_sess.commit()
        return redirect("/fail")

    lvlbot = user.lvl_2
    return render_template('game_with_bot.html', title='Виселица)', word=word, game_id=game_id,
                           lvl1=lvl, lvl2=lvlbot,
                           abc1=["Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ"],
                           abc2=["Ф", "Ы", "В", "А", "П", "Р", "О", "Л", "Д", "Ж", "Э"],
                           abc3=["Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю"])


@app.route('/win', methods=['GET', 'POST'])
def win():
    global in_game, games_id
    if not current_user.is_authenticated:
        return redirect(f"/login")

    cur_id = current_user.id
    if cur_id in in_game:
        in_game.remove(cur_id)
    if cur_id in games_id:
        del games_id[cur_id]
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == cur_id).first()
    if user is None:
        return not_found(404)
    user.wins += 1
    db_sess.commit()
    return render_template('win.html', title='Победа)')


@app.route('/fail', methods=['GET', 'POST'])
def fail():
    global in_game, games_id
    if not current_user.is_authenticated:
        return redirect(f"/login")

    cur_id = current_user.id
    if cur_id in in_game:
        in_game.remove(cur_id)
    hidden_word = ""
    if cur_id in games_id:
        game_id, game_type = games_id[cur_id]
        del games_id[cur_id]
        if game_type != "games":
            hidden_word = room.get_hidden_word_fail(game_id, game_type)
        else:
            hidden_word = room.get_word(game_id, cur_id)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == cur_id).first()
    if user is None:
        return not_found(404)
    user.fails += 1
    db_sess.commit()
    return render_template('fail.html', title='Увы! Проигрыш(', word=hidden_word)


@app.route('/tie/<winners>', methods=['GET', 'POST'])
def tie(winners):
    if not current_user.is_authenticated:
        return redirect(f"/login")
    return render_template('tie.html', result=winners, title='Ничья')


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
