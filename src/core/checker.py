import requests, tabulate, datetime, csv, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from tqdm import tqdm
from fake_useragent import UserAgent
from dotenv import load_dotenv

from config import GAS_SPENT_COEF, VOLUME_COEF, LEVEL_DICT
from .wallet import Wallet
from .utils import get_eth_price

load_dotenv()


class Checker:
    def __init__(self, wallets: list[Wallet]):
        self.wallets = wallets
        self.eth_price = get_eth_price()
        self.total_eth = 0
        self.total_weth = 0
        self.total_today_txns = 0
        self.total_all_txns = 0
        self.total_today_gas = 0
        self.total_all_gas = 0

    @staticmethod
    def get_txns(wallet: Wallet):
        r = requests.get(
            f"https://api.taikoscan.io/api",
            params={
                "module": "account",
                "action": "txlist",
                "address": wallet.address,
                "startblock": 0,
                "endblock": 9999999999,
                "page": 1,
                "sort": "asc",
                "apikey": os.getenv("EXPLORER_API_KEY"),
            },
            headers={"User-Agent": UserAgent().random},
        )
        data = r.json()
        if r.status_code != 200 or data["status"] != "1":
            logger.error(f"{wallet.info} Request for stats failed!")
            return logger.debug(r.text)

        txns = data["result"]
        return [
            {**txn, "burnedFees": int(txn["gasUsed"]) * int(txn["gasPrice"])}
            for txn in txns
            if txn["from"] == wallet.address.lower()
            and txn["to"] != wallet.address.lower()
            and not txn["functionName"].startswith("transfer")
            and not txn["functionName"].startswith("approve")
            and txn["isError"] == "0"
        ]

    @staticmethod
    def filter_today_txns(txns: list[dict]) -> list[dict]:
        timestamp = datetime.datetime.combine(
            datetime.datetime.now(datetime.timezone.utc).date(),
            datetime.time.min,
            tzinfo=datetime.timezone.utc,
        ).timestamp()
        return [txn for txn in txns if int(txn["timeStamp"]) > timestamp]

    @staticmethod
    def get_gas_spent_pts(txns: list[dict]) -> float:
        return sum(
            [
                Checker.get_txn_gas_spent_pts(int(txn["burnedFees"]) / 10**18)
                for txn in txns
            ]
        )

    @staticmethod
    def get_txn_gas_spent_pts(txn_gas_eth: float) -> float:
        return min(txn_gas_eth / GAS_SPENT_COEF, 1000)

    @staticmethod
    def get_volume_pts(txns: list[dict]) -> float:
        return sum(
            [Checker.get_txn_volume_pts(int(txn["value"]) / 10**18) for txn in txns]
        )

    @staticmethod
    def get_txn_volume_pts(txn_value_eth: float) -> float:
        return min(txn_value_eth / VOLUME_COEF, 1000)

    def get_stats(self, wallet: Wallet):
        r = requests.get(
            url="https://trailblazer.mainnet.taiko.xyz/s2/user/rank",
            params={"address": wallet.address},
            headers={"User-Agent": UserAgent().random},
        )
        if r.status_code != 200:
            logger.error(f"{wallet.info} Request for stats failed!")
            return logger.debug(r.text)

        return r.json()

    def get_level(self, rank: int):
        if rank == 0:
            return 0
        for level, min_rank in LEVEL_DICT.items():
            if min_rank >= rank:
                return level

        return 0

    def get_gas_spent(self, txns: list[dict]) -> float:
        gas_spent_eth = sum([int(txn["burnedFees"]) / 10**18 for txn in txns])
        return gas_spent_eth * self.eth_price

    def check_wallet(self, wallet: Wallet):
        stats = self.get_stats(wallet)
        all_txns = Checker.get_txns(wallet)
        today_txns = Checker.filter_today_txns(all_txns)
        all_gas = self.get_gas_spent(all_txns)
        today_gas = self.get_gas_spent(today_txns)
        volume_pts = Checker.get_volume_pts(today_txns)
        gas_spent_pts = Checker.get_gas_spent_pts(today_txns)

        self.total_eth += wallet.eth_balance / 10**18 or 0
        self.total_weth += wallet.weth_balance or 0
        self.total_all_txns += len(all_txns or [])
        self.total_today_txns += len(today_txns or [])
        self.total_all_gas += all_gas or 0
        self.total_today_gas += today_gas or 0

        return {
            "№": wallet.index,
            "Address": f"{wallet.address[:5]}...{wallet.address[-5:]}",
            "ETH": f"{wallet.eth_balance/10**18:.5f}",
            "WETH": f"{wallet.weth_balance:.5f}",
            "Txns\n24h|all": f"{len(today_txns):,.0f}|{len(all_txns):,.0f}",
            "Score": f"{stats['score']:,.0f}",
            "Rank": f"#{stats['rank']:,.0f}",
            "LVL": self.get_level(stats["rank"]),
            "Ban": "✅" if stats["blacklisted"] else "❌",
            "Vol\n(%)": f"{volume_pts/73000*100:.1f}%",
            "Gas\n(%)": f"{gas_spent_pts/73000*100:.1f}%",
            "Gas ($)\n24h|all": f"{today_gas:,.2f}|{all_gas:,.2f}",
        }

    def get_total(self, results: list[dict]):
        return {
            "№": "Total",
            "ETH": f"{self.total_eth:.5f}",
            "WETH": f"{self.total_weth:.5f}",
            "Txns\n24h|all": f"{self.total_today_txns:,.0f}|{self.total_all_txns:,.0f}",
            "Ban": f"{sum(wallet["Ban"] == "✅" for wallet in results)}/{len(results)}",
            "Gas ($)\n24h|all": f"{self.total_today_gas:.2f}|{self.total_all_gas:.2f}",
        }

    def run(self):
        results = []
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.check_wallet, wallet): wallet
                for wallet in self.wallets
            }
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Checking wallets",
                leave=False,
            ):
                results.append(future.result())
        results.append(self.get_total(results))
        results = sorted(
            results,
            key=lambda x: (
                x["№"] == "total",
                x["№"] if isinstance(x["№"], int) else float("inf"),
            ),
        )

        print(
            tabulate.tabulate(
                results,
                headers="keys",
                tablefmt="rounded_grid",
            )
        )

        time_now = datetime.datetime.now().strftime("%Y-%m-%d")
        results = [
            {key.replace("\n", " "): value for key, value in result.items()}
            for result in results
        ]
        with open(f"data/checker/{time_now}.csv", mode="w", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=results[0].keys(),
            )
            writer.writeheader()
            writer.writerows(results)
