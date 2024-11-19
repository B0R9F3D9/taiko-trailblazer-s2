import random, time, requests
from loguru import logger
from tqdm import tqdm


def sleep(min: int, max: int):
    sleep_time = random.randint(min, max)
    logger.info(f"Sleeping for {sleep_time:.0f} seconds...")
    for _ in tqdm(range(sleep_time), leave=False):
        time.sleep(1)


def get_eth_price():
    r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT")
    return float(r.json()["price"])
