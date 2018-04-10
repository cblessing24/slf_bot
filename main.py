import random
import re
import os
import pickle

import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup


class SLFBot:

    game_base_url = 'https://stadtlandflussonline.net'
    answers_base_url = 'https://www.stadt-land-fluss-online.de'
    game_answers_couplers = {
        'Stadt': 'Stadt|Städte',
        'Land': 'Land|Länder',
        'Fluss': 'Fluss|Flüsse',
        'Vorname': 'Name|Namen',
        'Tier': 'Tier|Tiere',
        'Beruf': 'Beruf|Berufe',
        'Pflanze': 'Pflanze|Pflanzen',
        'Band/Musiker': 'Musiker',
        'Filme/Serien': 'Filmtitel'
    }

    def __init__(self, wait=120):
        self.wait = wait
        self.driver = webdriver.Chrome()

    def play(self, game_url):
        categories, language, player_count, round_count = self.get_game_info(game_url)
        self.join_game(game_url)
        for current_round in range(round_count):
            current_letter = self.get_current_letter()
            answers = self.get_answers(categories, current_letter)
            self.send_answers(answers)
            self.confirm_results()

    @staticmethod
    def get_game_info(game_url):
        game_page_response = requests.get(game_url)
        game_page_response.raise_for_status()
        game_page_soup = BeautifulSoup(game_page_response.text, 'html.parser')
        game_information = game_page_soup.find('div', class_='alert alert-info').find_all('b')
        categories = str(game_information[0].next_sibling).strip().split(', ')
        language = game_page_soup.find('span', class_='flag-xs').attrs['class'][-1]
        player_count = int(game_information[2].next_sibling)
        round_count = int(game_information[3].next_sibling)
        return categories, language, player_count, round_count

    def join_game(self, game_url):
        self.driver.get(game_url)
        join_game_button = self.driver.find_element_by_id('gameForm:joinMe')
        join_game_button.click()

    def get_current_letter(self):
        WebDriverWait(self.driver, self.wait).until(ec.title_contains('WRITING_CATEGORIES'))
        return WebDriverWait(self.driver, self.wait).until(
            ec.presence_of_element_located((By.ID, 'currentLetter'))).text

    def send_answers(self, answers):
        input_fields = self.driver.find_element_by_id('gameForm:gameRow').find_elements_by_tag_name('input')
        for answer, input_field in zip(answers, input_fields):
            input_field.clear()
            input_field.send_keys(answer)
        self.driver.find_element_by_id('gameForm:checkSendBtn').send_keys(Keys.RETURN)

    def confirm_results(self):
        WebDriverWait(self.driver, self.wait).until(ec.title_contains('CONFIRMATION_RESULTS'))
        wait = WebDriverWait(self.driver, self.wait)
        confirm_button = wait.until(ec.presence_of_element_located((By.ID, 'gameForm:j_idt226')))
        confirm_button.send_keys(Keys.RETURN)

    @classmethod
    def get_answers(cls, categories, current_letter):
        answers = []
        for category in categories:
            answers.append(cls.get_answer(category, current_letter))
        return answers

    @classmethod
    def get_answer(cls, category, current_letter):
        url = SLFBot.answers_base_url + '/buchstabe-' + current_letter.lower()
        res = requests.get(url, verify=False)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        reg_exp = re.compile(cls.game_answers_couplers[category])
        category_tag = soup.find('h3', text=reg_exp)
        answer_tags = None
        for next_element in category_tag.next_elements:
            if next_element.name == 'ul':
                answer_tags = next_element.find_all('li')
                break
        if not answer_tags:
            return f'{current_letter} ({category}) does not exist'
        else:
            return random.choice(answer_tags).text.split()[0]


class SLFDatabase:

    def __init__(self, database_path):
        self.database_path = database_path
        if os.path.exists(self.database_path):
            with open(self.database_path, 'rb') as file_object:
                self.database = pickle.load(file_object)
        else:
            self.database = {}
            self.save_database()

    def save_database(self):
        with open(self.database_path, 'wb') as file_object:
            pickle.dump(self.database, file_object)

    @staticmethod
    def prepare_input(raw_inputs):
        return [raw_input.strip().lower() for raw_input in raw_inputs]

    def check_database(self, raw_category, raw_letter, raw_answer):
        category, letter, answer = self.prepare_input([raw_category, raw_letter, raw_answer])
        if category not in self.database:
            return False
        if letter not in self.database[category]:
            return False
        if answer not in self.database[category][letter]:
            return False
        else:
            return True

    def add_answer(self, raw_category, raw_letter, raw_answer):
        category, letter, answer = self.prepare_input([raw_category, raw_letter, raw_answer])
        if self.check_database(category, letter, answer):
            raise KeyError('Can not add answer (already in database)')
        if category not in self.database:
            self.database[category] = {}
        if letter not in self.database[category]:
            self.database[category][letter] = []
        self.database[category][letter].append(answer)

    def remove_answer(self, raw_category, raw_letter, raw_answer):
        category, letter, answer = self.prepare_input([raw_category, raw_letter, raw_answer])
        if not self.check_database(category, letter, answer):
            raise KeyError('Can not remove answer (not in database)')
        self.database[category][letter].remove(answer)
        if not self.database[category][letter]:
            del self.database[category][letter]
        if not self.database[category]:
            del self.database[category]

    def print_categories(self):
        for category in self.database.keys():
            print(category)


def main():
    slf_database = SLFDatabase('slf_database')
    slf_database.add_answer('Stadt', 'B', 'Berlin')
    print(slf_database.check_database('Stadt', 'B', 'Berlin'))
    slf_database.remove_answer('Stadt', 'B', 'Berlin')
    print(slf_database.check_database('Stadt', 'B', 'Berlin'))


def download_answers(database):
    couplers = {
        'Städte': 'Stadt',
        'Länder': 'Land',
        'Flüsse': 'Fluss'
    }
    url = 'https://www.stadt-land-fluss-online.de/kategorien/'
    res = requests.get(url, verify=False)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    category_tags = [tag.find('a') for tag in soup.find_all('h3', limit=3)]
    categories = [tag.text.split()[0] for tag in category_tags]
    category_links = [tag['href'] for tag in category_tags]
    for category, category_link in zip(categories, category_links):
        res_category = requests.get(category_link, verify=False)
        res_category.raise_for_status()
        soup_category = BeautifulSoup(res_category.text, 'html.parser')
        list_tags = soup_category.find('div', class_='post-content').find('ul').find_all('li')
        letters = [tag.text.split(':')[0][-1] for tag in list_tags]
        answers = [tag.text.split(':')[1].strip() for tag in list_tags]
        for index, answer in reversed(list(enumerate(answers))):
            if answer.startswith('Es gibt'):
                del letters[index]
                del answers[index]
        for letter, answer in zip(letters, answers):
            database.add_answer(couplers[category], letter, answer)


if __name__ == '__main__':
    main()
