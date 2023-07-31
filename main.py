from selenium import webdriver
from time import sleep
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from loguru import logger
from multiprocessing import Pool
import random

co = webdriver.ChromeOptions()

co.add_argument('--disable-gpu')
co.add_argument('--disable-infobars')
co.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
co.add_argument("lang=en-US")
co.add_argument("--mute-audio")
co.add_argument('log-level=3')
co.add_argument("--headless")
co.add_experimental_option('excludeSwitches', ['enable-logging'])


def start(wallet):

    url = f"https://byfishh.github.io/zk-flow/?address={wallet}"
    browser = webdriver.Chrome(options=co)
    browser.get(url)

    delay = random.randint(2, 5)

    try:
        logger.info(f"Statistic for wallet {wallet} is being loaded...")
        sleep(delay)

        amount_trx = browser.find_element(By.XPATH, '//*[@id="root"]/main/div/div/div[1]/div[1]/div/div/div/h3').text
        volume = browser.find_element(By.XPATH, '//*[@id="root"]/main/div/div/div[1]/div[2]/div/div/div/h3').text
        fee_spent = browser.find_element(By.XPATH, '//*[@id="root"]/main/div/div/div[1]/div[3]/div/div/div/h3').text

        logger.success(f"{wallet} has {amount_trx} transactions | {volume} volume | {fee_spent} fee spent")
        browser.quit()

    except selenium.common.exceptions.WebDriverException as e:
        logger.error("Error occurred while creating or using the browser:", e)


def get_wallets():
    with open("wallets.txt", "r") as f:
        return [row.strip() for row in f]


if __name__ == '__main__':
    pool = Pool(5)
    pool.map(start, list(get_wallets()))


