import random
import re

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
        for round in range(round_count):
            self.play_round(categories)
            self.confirm_results()

    def get_game_info(self, game_url):
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

    def play_round(self, categories):
        WebDriverWait(self.driver, self.wait).until(ec.title_contains('WRITING_CATEGORIES'))
        wait_letter = WebDriverWait(self.driver, self.wait)
        current_letter = wait_letter.until(ec.presence_of_element_located((By.ID, 'currentLetter'))).text
        answers = SLFBot.get_answers(categories, current_letter)
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
            answers.append(SLFBot.get_answer(category, current_letter))
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


def main():
    slf_bot = SLFBot()
    slf_bot.play('https://stadtlandflussonline.net/g/AH6IEFQA')


if __name__ == '__main__':
    main()
