import json, os


paths = ["data/checker", "data/logs"]
for path in paths:
    if not os.path.exists(path):
        os.makedirs(path)


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
