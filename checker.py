from selenium import webdriver
from time import sleep
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from loguru import logger
from multiprocessing import Pool
import json
import random
import requests

file = open('data.json')
data = json.load(file)

BROWSER = None

CHROME_OPTIONS = webdriver.ChromeOptions()
CHROME_OPTIONS.add_argument('--disable-gpu')
CHROME_OPTIONS.add_argument('--disable-infobars')
CHROME_OPTIONS.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
CHROME_OPTIONS.add_argument("lang=en-US")
CHROME_OPTIONS.add_argument("--mute-audio")
CHROME_OPTIONS.add_argument('log-level=3')
CHROME_OPTIONS.add_argument("--headless")
CHROME_OPTIONS.add_experimental_option('excludeSwitches', ['enable-logging'])

HEADERS = data.get('headers')
PROXIES = data.get('proxies')


def get_stats(wallet, max_retries=3):

    global BROWSER

    logger.info(f"Statistic loading for {wallet}...")
    url_stats = f"https://byfishh.github.io/zk-flow/?address={wallet}"

    retries_left = max_retries
    for retry in range(max_retries):
        try:
            BROWSER = webdriver.Chrome(options=CHROME_OPTIONS)
            BROWSER.get(url_stats)
            delay = random.randint(2, 5)
            sleep(delay)

            amount_trx_element = BROWSER.find_element(By.XPATH,
                                                      '//*[@id="root"]/main/div/div/div[1]/div[1]/div/div/div/h3')
            volume_element = BROWSER.find_element(By.XPATH, '//*[@id="root"]/main/div/div/div[1]/div[2]/div/div/div/h3')
            fee_spent_element = BROWSER.find_element(By.XPATH,
                                                     '//*[@id="root"]/main/div/div/div[1]/div[3]/div/div/div/h3')

            amount_trx = amount_trx_element.text
            volume = volume_element.text
            fee_spent = fee_spent_element.text

            logger.success(f"{wallet} has {amount_trx} transactions | {volume} volume | {fee_spent} fee spent")
            BROWSER.quit()
            return f"{amount_trx} transactions | {volume} volume | {fee_spent} fee spent"

        except (selenium.common.exceptions.WebDriverException, selenium.common.NoSuchElementException) as e:
            logger.warning(f"Something went wrong, retrying wallet {wallet}... (Retries left: {retries_left}), {e}")
            retries_left -= 1

    else:
        logger.error(f"Failed to retrieve stats for wallet {wallet}. Max retries exceeded.")
        BROWSER.quit()
        return "Failed to load the statistic. Please try again later"


def get_wallets():
    with open("wallets.txt", "r") as f:
        return [row.strip() for row in f]


def get_balance(wallet, max_retries=3):
    logger.info(f"Balances loading for {wallet}...")

    retries_left = max_retries
    for retry in range(max_retries):
        try:
            delay = random.randint(2, 6)
            sleep(delay)

            params = {
                'module': 'account',
                'action': 'tokenlist',
                'address': wallet,
            }

            response = requests.get('https://zksync2-mainnet.zkscan.io/api', params=params, headers=HEADERS,
                                    proxies=PROXIES)

            response.raise_for_status()

            tokens_array = json.loads(response.text)["result"][:3]
            token_info_strings = [f"{calculate_amount(token['balance'], token['decimals'])} {token['symbol']}" for token
                                  in tokens_array]

            logger.success(f"Balance of {wallet} : " + " | ".join(token_info_strings))
            return f" | ".join(token_info_strings)

        except (requests.exceptions.RequestException, TypeError) as e:
            logger.warning(f"Something went wrong, retrying wallet {wallet}... (Retries left: {retries_left}), {e}")
            retries_left -= 1

    else:
        logger.error(f"Failed to retrieve balances for wallet {wallet}. Max retries exceeded.")
        return "Failed to load the balances. Please try again later"


def calculate_amount(balance, decimals):
    return int(balance) / (10 ** int(decimals)) if decimals else int(balance)


def get_info(wallet):
    if len(wallet) != 42 or wallet[:2] != "0x":
        print(f"{wallet} seems to be invalid! Please enter the correct wallet!")
        return

    statistic = get_stats(wallet)
    balances = get_balance(wallet)
    print(f"\nWallet {wallet}\n\n"
          f"Account stats: {statistic}\n"
          f"Account balances: {balances}\n")


def check_all():
    pool = Pool(5)
    pool.map(get_info, list(get_wallets()))


if __name__ == '__main__':
    # get_info("0xF79998AD9B7b61294a1726f11f4897cFD9Ed20E7")
    check_all()




