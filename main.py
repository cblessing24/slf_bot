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

    def play(self):
        game_string = input('>> ')
        url = SLFBot.game_base_url + '/g/' + game_string
        driver = webdriver.Chrome()
        driver.get(url)
        number_of_rounds = int(driver.find_element_by_css_selector('.alert.alert-info').text[-1])
        join_game_button = driver.find_element_by_id('gameForm:joinMe').find_element_by_tag_name('a')
        join_game_button.send_keys(Keys.RETURN)
        for current_round in range(number_of_rounds):
            WebDriverWait(driver, self.wait).until(ec.title_contains('WRITING_CATEGORIES'))
            current_letter = WebDriverWait(driver, self.wait).until(ec.presence_of_element_located(
                (By.ID, 'currentLetter')))
            current_letter = current_letter.text
            categories_and_input_fields = driver.find_elements_by_class_name('form-group')[:-1]
            submit_flag = True
            for category_and_input_field in categories_and_input_fields:
                category = category_and_input_field.text
                # Skip unknown categories
                if category not in SLFBot.game_answers_couplers:
                    submit_flag = False
                    continue
                input_field = category_and_input_field.find_element_by_tag_name('input')
                input_field.clear()
                input_field.send_keys(self.get_answer(category, current_letter))
            # Do not submit answers if unknown categories were encountered
            if submit_flag:
                sub_button = WebDriverWait(driver, self.wait).until(ec.presence_of_element_located(
                    (By.ID, 'gameForm:checkSendBtn')))
                sub_button.send_keys(Keys.RETURN)
            results_button = WebDriverWait(driver, 60).until(
                ec.presence_of_element_located((By.ID, 'gameForm:j_idt226')))
            results_button.send_keys(Keys.RETURN)
        driver.close()

    @staticmethod
    def get_answer(category, current_letter):
        url = SLFBot.answers_base_url + '/buchstabe-' + current_letter.lower()
        res = requests.get(url, verify=False)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        reg_exp = re.compile(SLFBot.game_answers_couplers[category])
        answer_tags = soup.find('h3', text=reg_exp).next_sibling.find_all('li')
        if not answer_tags:
            return f'{current_letter} ({category}) does not exist'
        else:
            return random.choice(answer_tags).text.split()[0]


def main():
    slf_bot = SLFBot()
    slf_bot.play()


if __name__ == '__main__':
    main()
