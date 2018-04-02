import random
import re

import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup


def main():
    base_url = 'https://stadtlandflussonline.net'
    game_string = input('>> ')
    url = base_url + '/g/' + game_string
    driver = webdriver.Chrome()
    driver.get(url)
    rounds = int(driver.find_element_by_css_selector('.alert.alert-info').text[-1])
    join_button = driver.find_element_by_id('gameForm:joinMe').find_element_by_tag_name('a')
    join_button.send_keys(Keys.RETURN)
    for round_number in range(rounds):
        WebDriverWait(driver, 60).until(ec.title_contains('WRITING_CATEGORIES'))
        current_letter = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.ID, 'currentLetter'))).text
        round_inputs = driver.find_elements_by_class_name('form-group')[:-1]
        for round_input in round_inputs:
            category = round_input.text
            input_field = round_input.find_element_by_tag_name('input')
            input_field.clear()
            input_field.send_keys(get_answer(category, current_letter))
        sub_button = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.ID, 'gameForm:checkSendBtn')))
        sub_button.send_keys(Keys.RETURN)
        results_button = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.ID, 'gameForm:j_idt226')))
        results_button.send_keys(Keys.RETURN)


def get_answer(category, current_letter):
    base_url = 'https://www.stadt-land-fluss-online.de'
    links = {
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
    url = f'{base_url}/buchstabe-{current_letter.lower()}'
    res = requests.get(url, verify=False)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    reg_exp = re.compile(links[category])
    answer_tags = soup.find('h3', text=reg_exp).next_sibling.find_all('li')
    if not answer_tags:
        return ''
    else:
        return random.choice(answer_tags).text.split()[0]


if __name__ == '__main__':
    main()
