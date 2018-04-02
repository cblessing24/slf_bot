import random

import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def main():
    driver = webdriver.Chrome()
    driver.get('https://stadtlandflussonline.net/g/AP7ICPNE')
    rounds = int(driver.find_element_by_css_selector('.alert.alert-info').text[-1])
    join_button = driver.find_element_by_id('gameForm:joinMe').find_element_by_tag_name('a')
    join_button.send_keys(Keys.RETURN)
    for round in range(rounds):
        WebDriverWait(driver, 60).until(EC.title_contains('WRITING_CATEGORIES'))
        current_letter = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'currentLetter'))).text
        round_inputs = driver.find_elements_by_class_name('form-group')[:-1]
        for round_input in round_inputs:
            category = round_input.text
            input_field = round_input.find_element_by_tag_name('input')
            input_field.clear()
            input_field.send_keys(get_answer(category, current_letter))
        submit_button = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'gameForm:checkSendBtn')))
        submit_button.send_keys(Keys.RETURN)
        results_button = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'gameForm:j_idt226')))
        results_button.send_keys(Keys.RETURN)


def get_answer(category, current_letter):
    base_url = 'https://www.stadt-land-fluss-online.de'
    links = {
        'Stadt': 'Städte',
        'Land': 'Länder',
        'Fluss': 'Flüsse',
        'Vorname': 'Namen',
        'Tier': 'Tiere',
        'Beruf': 'Berufe',
        'Pflanze': 'Pflanzen',
        'Band/Musiker': 'Musiker',
        'Filme/Serien': 'Filmtitel'
    }
    url = f'{base_url}/buchstabe-{current_letter.lower()}'
    res = requests.get(url, verify=False)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    answer_tags = soup.find('h3', text=f'{links[category]} mit {current_letter.upper()}').next_sibling.find_all('li')
    return random.choice(answer_tags).text


if __name__ == '__main__':
    main()
