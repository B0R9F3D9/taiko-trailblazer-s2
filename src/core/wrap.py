import random
from loguru import logger

from web3.contract import Contract

from .checker import Checker
from .utils import sleep
from .wallet import Wallet
from config import WETH_CONTRACT_ADDRESS, WETH_CONTRACT_ABI
from settings import RETRY_COUNT, SLEEP_BETWEEN_TXNS


class Wrap:
    def __init__(self, wallet: Wallet) -> None:
        self.wallet = wallet
        self.contract: Contract = self.wallet.w3.eth.contract(
            address=WETH_CONTRACT_ADDRESS, abi=WETH_CONTRACT_ABI
        )
        self.traded_volume = 0

    def wrap_eth(self, amount: int):
        logger.info(f"{self.wallet.info} Making deposit of {amount/10**18:.3f} ETH...")
        txn = self.contract.functions.deposit().build_transaction(
            self.wallet.get_txn_data(amount)
        )
        return self.wallet.send_txn(txn)

    def unwrap_eth(self):
        amount = self.wallet.weth_contract.functions.balanceOf(
            self.wallet.address
        ).call()
        logger.info(
            f"{self.wallet.info} Making withdrawal of {amount/10**18:.3f} ETH..."
        )
        txn = self.contract.functions.withdraw(amount).build_transaction(
            self.wallet.get_txn_data()
        )
        return self.wallet.send_txn(txn)

    def try_deposit(self, amount: int):
        for attempt in range(1, RETRY_COUNT + 1):
            try:
                result = self.wrap_eth(amount)
                if result not in (None, False):
                    return result
                else:
                    raise Exception
            except Exception as e:
                logger.error(f"{self.wallet.info} Deposit attempt {attempt} failed!")
                logger.debug(e)
        logger.critical(f"{self.wallet.info} All deposit attempts failed!")

    def try_withdraw(self):
        for attempt in range(1, RETRY_COUNT + 1):
            try:
                result = self.unwrap_eth()
                if result not in (None, False):
                    return result
                else:
                    raise Exception
            except Exception as e:
                logger.error(f"{self.wallet.info} Withdraw attempt {attempt} failed!")
                logger.debug(e)
        logger.critical(f"{self.wallet.info} All withdraw attempts failed!")

    def run(self):
        txns = Checker.filter_today_txns(Checker.get_txns(self.wallet))

        gas_spent_pts = Checker.get_gas_spent_pts(txns)
        if gas_spent_pts >= 73000:
            return logger.warning(
                f"{self.wallet.info} Wallet already have 73k gas spent points!"
            )
        volume_pts = Checker.get_volume_pts(txns)
        if volume_pts >= 73000:
            return logger.warning(
                f"{self.wallet.info} Wallet already have 73k volume points!"
            )

        while True:
            keep_amount = int(random.uniform(0.0001, 0.0003) * 10**18)
            deposit_amount = self.wallet.eth_balance - keep_amount
            if deposit_amount < (0.01 * 10**18):
                if self.wallet.weth_balance > 0:
                    withdraw_success = self.try_withdraw()
                    if withdraw_success:
                        gas_spent_pts += Checker.get_txn_gas_spent_pts(
                            self.wallet.get_txn_cost(withdraw_success)
                        )
                        sleep(*SLEEP_BETWEEN_TXNS)
                        continue
                logger.error(f"{self.wallet.info} Deposit amount < 0.01ETH!")
                break

            deposit_success = self.try_deposit(deposit_amount)
            if deposit_success:
                gas_spent_pts += Checker.get_txn_gas_spent_pts(
                    self.wallet.get_txn_cost(deposit_success)
                )
            else:
                break

            sleep(*SLEEP_BETWEEN_TXNS)

            withdraw_success = self.try_withdraw()
            if withdraw_success:
                gas_spent_pts += Checker.get_txn_gas_spent_pts(
                    self.wallet.get_txn_cost(withdraw_success)
                )
            else:
                break

            self.traded_volume += deposit_amount / 10**18
            volume_pts += Checker.get_txn_volume_pts(deposit_amount / 10**18)
            logger.success(
                f"{self.wallet.info} Successfully wrapped and unwrapped {deposit_amount/10**18:.3f}ETH!"
            )
            logger.debug(
                f"{self.wallet.info} Traded volume: {self.traded_volume:.2f}ETH | "
                + f"Gas progress: {gas_spent_pts/73000*100:.1f}% | "
                + f"Volume progress: {volume_pts/73000*100:.1f}%"
            )

            if gas_spent_pts >= 73000 or volume_pts >= 73000:
                break
            sleep(*SLEEP_BETWEEN_TXNS)
