import random
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

    def __init__(self, database, wait=120):
        self.database = database
        self.wait = wait
        self.driver = webdriver.Chrome()

    def play(self, game_url):
        categories, language, player_count, round_count = self.get_game_info(game_url)
        self._join_game(game_url, categories, round_count)

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

    def _join_game(self, game_url, categories, round_count):
        self.driver.get(game_url)
        join_game_button = self.driver.find_element_by_id('gameForm:joinMe')
        join_game_button.click()
        for round_ in range(round_count):
            self._get_letter(categories)

    def _get_letter(self, categories):
        WebDriverWait(self.driver, self.wait).until(ec.title_contains('WRITING_CATEGORIES'))
        letter = WebDriverWait(self.driver, self.wait).until(
            ec.presence_of_element_located((By.ID, 'currentLetter'))).text
        self._get_answers(categories, letter)

    def _get_answers(self, categories, letter):
        answers = []
        for category in categories:
            try:
                answers.append(self.database.get_random_answer(category, letter))
            except KeyError:
                answers.append('')
        self._get_input_fields(answers)

    def _get_input_fields(self, answers):
        input_fields = self.driver.find_element_by_id('gameForm:gameRow').find_elements_by_tag_name('input')
        self._send_answers(input_fields, answers)

    def _send_answers(self, input_fields, answers):
        for input_field, answer in zip(input_fields, answers):
            input_field.clear()
            input_field.send_keys(answer)
        self.driver.find_element_by_id('gameForm:checkSendBtn').send_keys(Keys.RETURN)
        self._confirm_results()

    def _confirm_results(self):
        WebDriverWait(self.driver, self.wait).until(ec.title_contains('CONFIRMATION_RESULTS'))
        wait = WebDriverWait(self.driver, self.wait)
        confirm_button = wait.until(ec.presence_of_element_located((By.ID, 'gameForm:j_idt226')))
        confirm_button.send_keys(Keys.RETURN)


class SLFDatabase:

    def __init__(self, database_path):
        self.database_path = database_path
        if os.path.exists(self.database_path):
            with open(self.database_path, 'rb') as file_object:
                self.database = pickle.load(file_object)
        else:
            self.database = {}
            self.save()

    def save(self):
        with open(self.database_path, 'wb') as file_object:
            pickle.dump(self.database, file_object)

    def reset(self):
        os.remove(self.database_path)
        self.database = {}
        self.save()

    @staticmethod
    def _prepare_input(raw_inputs):
        # Return first element in list if list only has one element, otherwise return a list
        if len(raw_inputs) == 1:
            return raw_inputs[0].strip().lower()
        else:
            return [raw_input.strip().lower() for raw_input in raw_inputs]

    def check_database_for_category(self, raw_category):
        category = self._prepare_input([raw_category])
        if category in self.database:
            return True
        else:
            return False

    def check_database_for_letter(self, raw_category, raw_letter):
        # Returns True if the category exists and the letter exists within the category
        category, letter = self._prepare_input([raw_category, raw_letter])
        if self.check_database_for_category(category):
            if letter in self.database[category]:
                return True
        return False

    def check_database_for_answer(self, raw_category, raw_letter, raw_answer):
        # Returns True if the category exists, the letter exists within the category
        # and the answer exists within the letter
        category, letter, answer = self._prepare_input([raw_category, raw_letter, raw_answer])
        if self.check_database_for_letter(category, letter):
            if answer in self.database[category][letter]:
                return True
        return False

    def get_answers(self, raw_category, raw_letter):
        category, letter = self._prepare_input([raw_category, raw_letter])
        if self.check_database_for_letter(category, letter):
            return self.database[category][letter]
        else:
            raise KeyError('Can not get answers (none in database)')

    def get_random_answer(self, raw_category, raw_letter):
        answers = self.get_answers(raw_category, raw_letter)
        return random.choice(answers)

    def add_answer(self, raw_category, raw_letter, raw_answer):
        category, letter, answer = self._prepare_input([raw_category, raw_letter, raw_answer])
        if self.check_database_for_answer(category, letter, answer):
            raise KeyError('Can not add answer (already in database)')
        if category not in self.database:
            self.database[category] = {}
        if letter not in self.database[category]:
            self.database[category][letter] = []
        self.database[category][letter].append(answer)

    def remove_answer(self, raw_category, raw_letter, raw_answer):
        category, letter, answer = self._prepare_input([raw_category, raw_letter, raw_answer])
        if not self.check_database_for_answer(category, letter, answer):
            raise KeyError('Can not remove answer (not in database)')
        self.database[category][letter].remove(answer)
        if not self.database[category][letter]:
            del self.database[category][letter]
        if not self.database[category]:
            del self.database[category]

    def print_categories(self):
        for category in self.database.keys():
            print(category)

    def scrape_answers(self):
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
                self.add_answer(couplers[category], letter, answer)


def main():
    slf_database = SLFDatabase('slf_database')
    slf_bot = SLFBot(slf_database)
    slf_bot.play('https://stadtlandflussonline.net/g/AO2IFBWI')


if __name__ == '__main__':
    main()
