import json
import sqlite3
import requests
import os

from bs4 import BeautifulSoup

MIN_WORD_LEN = 5
MAX_WORD_LEN = 20
MAX_MISTAKES = 7
DB_FILENAME = "db/gallows.db"
WORDS_FILENAME = 'data/words.json'

current_dir = os.path.abspath(os.getcwd())
if not os.path.exists(f"{current_dir}/db"):
    os.makedirs(f"{current_dir}/db")

# connecting to db
con = sqlite3.connect(DB_FILENAME, check_same_thread=False)
cur = con.cursor()

with open(WORDS_FILENAME, mode='r', encoding='utf-8') as file:
    DATA = json.load(file)


class Room:
    @staticmethod
    def make_room(player1_id, player2_id=None):
        game_id = list(cur.execute("""SELECT id FROM games""").fetchall())
        if game_id:
            game_id = max([x[0] for x in game_id]) + 1
        else:
            game_id = 1

        if player2_id is not None:
            cur.execute(f"""
            INSERT INTO games(id, player_1, player_2, ready_1, ready_2, word_1, word_2, wordfind_1,
                              wordfind_2, lvl_1, lvl_2, letters_1, letters_2, win_1, win_2, win)
                    VALUES({game_id}, {player1_id}, {player2_id}, 0, 0, '', '', '', '',
                                0, 0, '', '', 0, 0, 0)""")
        else:
            cur.execute(f"""
                        INSERT INTO games(id, player_1, player_2, ready_1, ready_2, word_1, word_2, 
                    wordfind_1, wordfind_2, lvl_1, lvl_2, letters_1, letters_2, win_1, win_2, win)
                                VALUES({game_id}, {player1_id}, NULL, 0, 0, '', '', '', '',
                                            0, 0, '', '', 0, 0, 0)""")
        con.commit()
        return game_id

    @staticmethod
    def get_word(game_id, user_id):
        res = cur.execute(f"SELECT * FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            if user_id == res[1]:
                return res[5]
            elif user_id == res[2]:
                return res[6]
        return None

    @staticmethod
    def get_word_for_another_player(game_id, user_id):
        res = cur.execute(f"SELECT * FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            if user_id == res[1]:
                return res[6]
            elif user_id == res[2]:
                return res[5]
        return None

    @staticmethod
    def get_hidden_word(game_id, user_id):
        res = cur.execute(f"SELECT * FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            if user_id == res[1]:
                return res[7]
            elif user_id == res[2]:
                return res[8]
        return None

    @staticmethod
    def get_hidden_word_fail(game_id, game_type):
        res = cur.execute(f"SELECT word FROM '{game_type}' WHERE id = {game_id}").fetchone()
        if res is not None:
            return res[0]
        return None

    @staticmethod
    def get_mistakes(game_id, user_id):
        res = cur.execute(f"SELECT * FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            if user_id == res[1]:
                return res[9]
            elif user_id == res[2]:
                return res[10]
        return None

    @staticmethod
    def all_2_in(game_id):
        res = cur.execute(f"SELECT ready_1, ready_2 FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            return bool(res[0]) and bool(res[1])
        return None

    @staticmethod
    def is_the_end(game_id):
        res = cur.execute(f"SELECT win FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            return bool(res[0])
        return None

    def check_word(self, word):
        if not self.correct_word_len(word):
            return False

        req = requests.get(f"http://gramota.ru/slovari/dic/?word={word}")
        html_code = req.text

        soup = BeautifulSoup(html_code, "html.parser")
        soup = soup.find("body")
        soup = soup.prettify()

        if "искомое слово отсутствует" in soup or "Орфографический словарь" not in soup:
            return False

        return True

    @staticmethod
    def correct_word_len(word):
        return MIN_WORD_LEN <= len(word) <= MAX_WORD_LEN

    @staticmethod
    def process_letter(game_id, player_id, letter):
        letter = letter.lower()
        res = cur.execute(f"SELECT * FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            if player_id == res[1]:
                if letter not in res[11]:
                    word, word_h = list(res[5].lower()), list(res[7].lower())
                    letters = res[11] + letter
                    if letter in word:
                        for i in range(len(word)):
                            if word[i] == letter:
                                word_h[i] = letter
                        word_h = "".join(word_h)
                        cur.execute(f"UPDATE games SET wordfind_1 = '{word_h}' WHERE id = {game_id}")
                    else:
                        lvl = res[9] + 1
                        cur.execute(f"UPDATE games SET lvl_1 = {lvl} WHERE id = {game_id}")
                    cur.execute(f"UPDATE games SET letters_1 = '{letters}' WHERE id = {game_id}")
            elif player_id == res[2]:
                if letter not in res[12]:
                    word, word_h = list(res[6].lower()), list(res[8].lower())
                    letters = res[12] + letter
                    if letter in word:
                        for i in range(len(word)):
                            if word[i] == letter:
                                word_h[i] = letter
                        word_h = "".join(word_h)
                        cur.execute(f"UPDATE games SET wordfind_2 = '{word_h}' WHERE id = {game_id}")
                    else:
                        lvl = res[10] + 1
                        cur.execute(f"UPDATE games SET lvl_2 = {lvl} WHERE id = {game_id}")
                    cur.execute(f"UPDATE games SET letters_2 = '{letters}' WHERE id = {game_id}")
            con.commit()

    @staticmethod
    def set_second_player(game_id, player_id):
        cur.execute(f"""UPDATE games SET player_2 = {player_id} WHERE id = {game_id}""")
        con.commit()

    @staticmethod
    def set_word(game_id, player_id, word):
        res = cur.execute(f"SELECT * FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            if player_id == res[1]:
                cur.execute(f"""UPDATE games SET word_1 = '{word}' WHERE id = {game_id}""")
                cur.execute(
                    f"""UPDATE games SET wordfind_1 = '{'_' * len(word)}' WHERE id = {game_id}""")
            elif player_id == res[2]:
                cur.execute(f"""UPDATE games SET word_2 = '{word}' WHERE id = {game_id}""")
                cur.execute(
                    f"""UPDATE games SET wordfind_2 = '{'_' * len(word)}' WHERE id = {game_id}""")
            con.commit()

    @staticmethod
    def set_word_for_another_player(game_id, player_id, word):
        res = cur.execute(f"SELECT * FROM games WHERE id = {game_id}").fetchone()
        if res is not None:
            if player_id == res[1]:
                cur.execute(f"""UPDATE games SET word_2 = '{word}' WHERE id = {game_id}""")
                cur.execute(
                    f"""UPDATE games SET wordfind_2 = '{'_' * len(word)}' WHERE id = {game_id}""")
            elif player_id == res[2]:
                cur.execute(f"""UPDATE games SET word_1 = '{word}' WHERE id = {game_id}""")
                cur.execute(
                    f"""UPDATE games SET wordfind_1 = '{'_' * len(word)}' WHERE id = {game_id}""")
            con.commit()

    @staticmethod
    def is_user_exist(user):
        res = cur.execute(f"""SELECT * FROM users WHERE nickname = '{user}'""").fetchone()
        if res is not None:
            return res[3]
        res = cur.execute(f"""SELECT * FROM users WHERE email = '{user}'""").fetchone()
        if res is not None:
            return res[3]
        return False

    @staticmethod
    def get_user_id(user):
        res = cur.execute(f"""SELECT id FROM users WHERE nickname = '{user}'""").fetchone()
        if res is not None:
            return res[0]
        res = cur.execute(f"""SELECT id FROM users WHERE email = '{user}'""").fetchone()
        if res is not None:
            return res[0]

    @staticmethod
    def set_user_in(game_id, user_id):
        res = cur.execute(
            f"""SELECT player_1, player_2 FROM games WHERE id = {game_id}""").fetchone()
        if res is not None:
            if user_id == res[0]:
                cur.execute(f"UPDATE games SET ready_1 = 1 WHERE id = {game_id}")
            elif user_id == res[1]:
                cur.execute(f"UPDATE games SET ready_2 = 1 WHERE id = {game_id}")
            con.commit()

    @staticmethod
    def set_users_not_in(game_id):
        cur.execute(f"UPDATE games SET ready_1 = 0 WHERE id = {game_id}")
        cur.execute(f"UPDATE games SET ready_2 = 0 WHERE id = {game_id}")
        con.commit()

    def set_user_win(self, game_id, user_id):
        res = cur.execute(f"""SELECT player_1, player_2, word_1, word_2, wordfind_1, wordfind_2, 
        win FROM games WHERE id = {game_id}""").fetchone()
        if res is not None:
            if not bool(res[-1]):
                if user_id == res[0]:
                    if res[2].lower() == res[4].lower() or self.all_2_debils(game_id):
                        cur.execute(f"UPDATE games SET win_1 = 1 WHERE id = {game_id}")
                        cur.execute(f"UPDATE games SET win = 1 WHERE id = {game_id}")
                elif user_id == res[1]:
                    if res[3].lower() == res[5].lower() or self.all_2_debils(game_id):
                        cur.execute(f"UPDATE games SET win_2 = 1 WHERE id = {game_id}")
                        cur.execute(f"UPDATE games SET win = 1 WHERE id = {game_id}")
                con.commit()

    @staticmethod
    def is_user_win(game_id, user_id):
        res = cur.execute(f"""SELECT player_1, player_2, win_1, win_2 FROM games 
        WHERE id = {game_id}""").fetchone()
        if res is not None:
            if user_id == res[0]:
                return bool(res[2])
            elif user_id == res[1]:
                return bool(res[3])
        return None

    @staticmethod
    def all_2_debils(game_id):
        res = cur.execute(f"""SELECT lvl_1, lvl_2 FROM games WHERE id = {game_id}""").fetchone()
        if res is not None:
            return bool(res[0] >= MAX_MISTAKES and res[1] >= MAX_MISTAKES)
        return None

"""
Таблица games в базе данных

CREATE TABLE games (
    0 id         INTEGER NOT NULL,
    1 player_1   INTEGER,
    2 player_2   INTEGER,
    3 ready_1    BOOLEAN,
    4 ready_2    BOOLEAN,
    5 word_1     VARCHAR,
    6 word_2     VARCHAR,
    7 wordfind_1 VARCHAR,
    8 wordfind_2 VARCHAR,
    9 lvl_1      INTEGER,
    10 lvl_2      INTEGER,
    11 letters_1  VARCHAR,
    12 letters_2  VARCHAR,
    13 win_1      BOOLEAN,
    14 win_2      BOOLEAN,
    15 win        INTEGER,
    PRIMARY KEY (
        id
    )
);
"""
