from selenium import webdriver
from time import sleep
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from loguru import logger
from multiprocessing import Pool
import json
import random
import requests

chrome_options = webdriver.ChromeOptions()

chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-infobars')
chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
chrome_options.add_argument("lang=en-US")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument('log-level=3')
chrome_options.add_argument("--headless")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])


def start(wallet, max_retries=3):
    logger.info(f"Statistic loading for {wallet}...")
    url_stats = f"https://byfishh.github.io/zk-flow/?address={wallet}"
    browser = webdriver.Chrome(options=chrome_options)

    retries_left = max_retries
    for retry in range(max_retries):
        try:
            browser.get(url_stats)
            delay = random.randint(2, 5)
            sleep(delay)

            amount_trx_element = browser.find_element(By.XPATH,
                                                      '//*[@id="root"]/main/div/div/div[1]/div[1]/div/div/div/h3')
            volume_element = browser.find_element(By.XPATH, '//*[@id="root"]/main/div/div/div[1]/div[2]/div/div/div/h3')
            fee_spent_element = browser.find_element(By.XPATH,
                                                     '//*[@id="root"]/main/div/div/div[1]/div[3]/div/div/div/h3')

            amount_trx = amount_trx_element.text
            volume = volume_element.text
            fee_spent = fee_spent_element.text

            logger.success(f"{wallet} has {amount_trx} transactions | {volume} volume | {fee_spent} fee spent")
            browser.quit()
            break

        except (selenium.common.exceptions.WebDriverException, selenium.common.NoSuchElementException) as e:
            logger.warning(f"Something went wrong, retrying wallet {wallet}... (Retries left: {retries_left})")
            retries_left -= 1

    else:
        logger.error(f"Failed to retrieve stats for wallet {wallet}. Max retries exceeded.")
        browser.quit()


def get_wallets():
    with open("wallets.txt", "r") as f:
        return [row.strip() for row in f]


def get_balance(wallet, max_retries=3):
    logger.info(f"Balances loading for {wallet}...")

    retries_left = max_retries
    for retry in range(max_retries):
        try:
            url_balances = f"https://zksync2-mainnet.zkscan.io/api?module=account&action=tokenlist&address={wallet}"
            delay = random.randint(2, 5)
            sleep(delay)

            response = requests.get(url_balances)
            response.raise_for_status()

            tokens_array = json.loads(response.text)["result"][:3]
            token_info_strings = [f"{calculate_amount(token['balance'], token['decimals'])} {token['symbol']}" for token
                                  in tokens_array]

            logger.success(f"Balance of {wallet} : " + " | ".join(token_info_strings))
            break

        except requests.exceptions.RequestException as e:
            logger.warning(f"Something went wrong, retrying wallet {wallet}... (Retries left: {retries_left}), {e}")
            retries_left -= 1

    else:
        logger.error(f"Failed to retrieve stats for wallet {wallet}. Max retries exceeded.")


def calculate_amount(balance, decimals):
    return int(balance) / (10 ** int(decimals)) if decimals else int(balance)


if __name__ == '__main__':
    # pool = Pool(2)
    # pool.map(get_balance, list(get_wallets()))

    get_balance("0xF79998AD9B7b61294a1726f11f4897cFD9Ed20E7")
