from loguru import logger

from web3.contract import Contract

from .wallet import Wallet
from .checker import Checker
from .utils import sleep
from config import RUBYSCORE_CONTRACT_ADDRESS, RUBYSCORE_CONTRACT_ABI
from settings import RETRY_COUNT, SLEEP_BETWEEN_TXNS


class Rubyscore:
    def __init__(self, wallet: Wallet):
        self.wallet = wallet
        self.contract: Contract = self.wallet.w3.eth.contract(
            address=RUBYSCORE_CONTRACT_ADDRESS, abi=RUBYSCORE_CONTRACT_ABI
        )

    def vote(self):
        logger.info(f"{self.wallet.info} Voting on Rubyscore...")
        txn = self.contract.functions.vote().build_transaction(
            self.wallet.get_txn_data()
        )
        return self.wallet.send_txn(txn)

    def try_vote(self):
        for attempt in range(1, RETRY_COUNT + 1):
            try:
                result = self.vote()
                if result not in (None, False):
                    return result
                else:
                    raise Exception
            except Exception as e:
                logger.error(f"{self.wallet.info} Vote attempt {attempt} failed!")
                logger.debug(e)
        logger.critical(f"{self.wallet.info} All vote attempts failed!")

    def run(self):
        txns = Checker.filter_today_txns(Checker.get_txns(self.wallet))
        gas_spent_pts = Checker.get_gas_spent_pts(txns)
        if gas_spent_pts >= 73000:
            return logger.warning(
                f"{self.wallet.info} Wallet already have 73k gas spent points!"
            )
        i = 0

        while True:
            vote_success = self.try_vote()
            if vote_success:
                gas_spent_pts += Checker.get_txn_gas_spent_pts(
                    self.wallet.get_txn_cost(vote_success)
                )
            else:
                break

            i += 1
            logger.success(f"{self.wallet.info} Successfully voted on Rubyscore!")
            logger.debug(
                f"{self.wallet.info} Times voted: {i} | Gas progress: {gas_spent_pts/73000*100:.1f}%"
            )

            if gas_spent_pts >= 73000:
                break
            sleep(*SLEEP_BETWEEN_TXNS)
