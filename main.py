import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


driver = webdriver.Chrome()
driver.get('https://stadtlandflussonline.net/g/AJDICIXW')
driver.find_element_by_id('gameForm:joinMe').click()
while True:
    if 'FINISHED' in driver.title:
        break
    WebDriverWait(driver, 120).until(EC.title_contains('WRITING_CATEGORIES'))
    current_letter = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, 'currentLetter'))).text
    round_inputs = driver.find_elements_by_class_name('form-group')[:-1]
    for round_input in round_inputs:
        category = round_input.text
        input_field = round_input.find_element_by_tag_name('input')
        input_field.clear()
        input_field.send_keys(current_letter + category)
    driver.find_element_by_id('gameForm:checkSendBtn').click()
    confirm_results = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, 'gameForm:j_idt226')))
    confirm_results.click()
driver.close()
