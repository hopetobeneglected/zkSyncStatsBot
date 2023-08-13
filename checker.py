import datetime
import multiprocessing

from numpy import double
from selenium import webdriver
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from loguru import logger
import json
import random
import requests
import asyncio

file = open('data.json')
data = json.load(file)

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

logger.add('/logs/checker.log', level='DEBUG', retention="1 day")


async def get_stats(wallet, max_retries=3):
    BROWSER = None

    logger.info(f"Statistic loading for {wallet}...")
    url_stats = f"https://byfishh.github.io/zk-flow/?address={wallet}"
    retries_left = max_retries

    for retry in range(max_retries):
        try:
            BROWSER = webdriver.Chrome(options=CHROME_OPTIONS)
            BROWSER.get(url_stats)
            delay = random.randint(2, 4)
            await asyncio.sleep(delay)

            amount_trx_element = BROWSER.find_element(By.XPATH,
                                                      '//*[@id="root"]/main/div/div/div[1]/div[1]/div/div/div/h3')
            volume_element = BROWSER.find_element(By.XPATH, '//*[@id="root"]/main/div/div/div[1]/div[2]/div/div/div/h3')
            fee_spent_element = BROWSER.find_element(By.XPATH,
                                                     '//*[@id="root"]/main/div/div/div[1]/div[3]/div/div/div/h3')

            amount_trx = amount_trx_element.text
            volume = volume_element.text
            fee_spent = fee_spent_element.text

            logger.success(f"{wallet} has {amount_trx} transactions | {volume} volume | {fee_spent} fee spent")
            return f"\n\nWallet {wallet}\n" \
                   f"Account stats: {amount_trx} transactions | {volume} volume | {fee_spent} fee spent\n"

        except (selenium.common.exceptions.WebDriverException, selenium.common.NoSuchElementException) as e:
            logger.warning(f"Something went wrong, retrying wallet {wallet}... (Retries left: {retries_left}), {e}")
            retries_left -= 1

    else:
        logger.error(f"Failed to retrieve stats for wallet {wallet}. Max retries exceeded.")
        BROWSER.quit()
        return "Failed to load the statistic. Please try again later"


# def get_wallets():
#     with open("wallets.txt", "r") as f:
#         return [row.strip() for row in f]


async def get_balance(wallet, max_retries=3):
    logger.info(f"Balances loading for {wallet}...")

    retries_left = max_retries
    for retry in range(max_retries):
        try:
            params = {
                'module': 'account',
                'action': 'tokenlist',
                'address': wallet,
            }

            response = requests.get('https://zksync2-mainnet.zkscan.io/api', params=params, headers=HEADERS,
                                    proxies=PROXIES)

            response.raise_for_status()

            tokens_array = json.loads(response.text)["result"][:3]
            token_info_strings = [f"{round(calculate_amount(token['balance'], token['decimals']), 4)} {token['symbol']}" for token
                                  in tokens_array]

            usd_price = str(round(1850 * double(token_info_strings[0].rsplit(' ')[0]), 2))
            logger.success(f"Balance of {wallet} : " + " | ".join(token_info_strings))
            return f"Account balances: (${usd_price}) " + " | ".join(token_info_strings)

        except (requests.exceptions.RequestException, TypeError) as e:
            await asyncio.sleep(1)
            logger.warning(f"Something went wrong, retrying wallet {wallet}... (Retries left: {retries_left}), {e}")
            retries_left -= 1

    else:
        logger.error(f"Failed to retrieve balances for wallet {wallet}. Max retries exceeded.")
        return "Failed to load balances. Please try again later"


def calculate_amount(balance, decimals):
    return int(balance) / (10 ** int(decimals)) if decimals else int(balance)


def run_pair(wallet):
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(asyncio.gather(get_stats(wallet), get_balance(wallet)))
    return result


def get_info(wallets):
    output = ""

    start_time = datetime.datetime.now()

    with multiprocessing.Pool() as pool:
        results = pool.map(run_pair, wallets)

    for result in results:
        for info in result:
            output += info

    end_time = datetime.datetime.now()
    elapsed_time = end_time - start_time
    ret = [output, elapsed_time.seconds]
    return ret
