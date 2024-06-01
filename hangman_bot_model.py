import json
from random import choice

import codes

WORDS_FILENAME = 'data/words.json'


class HangmanBot:
    def __init__(self, game_data):
        with open(WORDS_FILENAME, mode='r', encoding='utf-8') as file:
            data = json.load(file)

        self.word_list = data[game_data.theme]

        self.difficulty = game_data.difficulty

        self.letter_indexes = []
        self.used_letters = game_data.bot_letters

        self.wrong_letters = ''

        self.letter_list, self.max_frequency =\
            self.get_sorted_letters_with_max_frequency(self.word_list)

    def process_word(self, hidden_word):
        for let in self.used_letters:
            if let not in hidden_word:
                self.wrong_letters += let

        for i in range(len(hidden_word)):
            if hidden_word[i].isalpha():
                self.letter_indexes.append(i)

        matched_words = []
        for word in self.word_list:
            if len(word) == len(hidden_word):
                word = word.upper()

                matched = True
                for i in self.letter_indexes:
                    if hidden_word[i] != word[i]:
                        matched = False
                if matched:
                    matched_words.append(word)
        self.word_list = matched_words

        letter = ''

        if self.difficulty == codes.LOW_BOT_DIFFICULTY:
            word = choice(self.word_list)
            letter = choice(word)
            while word.index(letter) in self.letter_indexes:
                letter = choice(word)

        elif self.difficulty == codes.MEDIUM_BOT_DIFFICULTY:
            word = choice(self.word_list)
            letter = self.get_the_most_frequent_letter(word)

        elif self.difficulty == codes.HIGH_BOT_DIFFICULTY:
            self.delete_wrong_words(self.word_list, hidden_word)
            self.letter_list, self.max_frequency = \
                self.get_sorted_letters_with_max_frequency(self.word_list)

            word = choice(self.word_list)
            letter = self.get_the_most_frequent_letter(word)

        return letter

    def get_the_most_frequent_letter(self, word):
        the_most_frequent = ['', 0]

        for letter in word:
            frequency = self.letter_list[letter]
            if frequency > the_most_frequent[1]:
                if word.index(letter) not in self.letter_indexes and letter not in\
                        self.used_letters:
                    the_most_frequent = [letter, frequency]

        return the_most_frequent[0]

    @staticmethod
    def get_sorted_letters_with_max_frequency(word_list):
        letter_list = {}
        max_frequency = 0

        for word in word_list:
            for letter in word:
                letter = letter.upper()

                if letter in letter_list:
                    letter_list[letter] += 1
                else:
                    letter_list[letter] = 1

                letter_frequency = letter_list[letter]
                if letter_frequency > max_frequency:
                    max_frequency = letter_frequency

        return letter_list, max_frequency

    def delete_wrong_words(self, word_list, hidden_word):
        for word in word_list.copy():

            word_in_list = True
            for letter in word:
                if letter in hidden_word and word.count(letter) != hidden_word.count(letter):
                    word_list.remove(word)
                    word_in_list = False
                    break

            if word_in_list:
                for letter in self.wrong_letters:
                    if letter in word:
                        word_list.remove(word)
                        break
