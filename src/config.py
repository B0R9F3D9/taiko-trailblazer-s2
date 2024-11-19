import json, os, sys, datetime
from loguru import logger


logger.remove()
logs_format = "<white>{time:HH:mm:ss}</white> | <bold><level>{level: <7}</level></bold> | <level>{message}</level>"
logger.add(sink=sys.stdout, format=logs_format)
logger.add(
    sink=f'data/logs/{datetime.datetime.today().strftime("%Y-%m-%d")}.log',
    format=logs_format,
)


if not os.path.exists("data/checker"):
    os.makedirs("data/checker")
if not os.path.exists("data/logs"):
    os.makedirs("data/logs")
if not os.path.exists("data/keys.txt"):
    open("data/keys.txt", "w").close()
    logger.critical(
        f"Fill in the wallet list! 👉 {os.path.join(os.getcwd(), 'data/keys.txt')}"
    )
    sys.exit(0)


with open("data/keys.txt", "r") as file:
    KEYS = [x.strip() for x in file.readlines()]

with open("data/abi/weth.json", "r") as file:
    WETH_CONTRACT_ABI = json.load(file)

with open("data/abi/rubyscore.json", "r") as file:
    RUBYSCORE_CONTRACT_ABI = json.load(file)


WETH_CONTRACT_ADDRESS = "0xA51894664A773981C6C112C43ce576f315d5b1B6"
RUBYSCORE_CONTRACT_ADDRESS = "0x4D1E2145082d0AB0fDa4a973dC4887C7295e21aB"


GAS_SPENT_COEF = 0.000000004856534
VOLUME_COEF = 0.0002200895244
LEVEL_DICT = {
    14: 77,
    13: 777,
    12: 3888,
    11: 7776,
    10: 15300,
    9: 30720,
    8: 46085,
    7: 61447,
    6: 76809,
    5: 138256,
    4: 199703,
    3: 261151,
    2: 322598,
    1: 384045,
}
