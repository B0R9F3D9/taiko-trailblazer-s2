import time, random
from loguru import logger

from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account as EthereumAccount

from config import WETH_CONTRACT_ABI, WETH_CONTRACT_ADDRESS
from settings import EXPLORER, RPC, GAS_MULTIPLIER


class Wallet:
    def __init__(self, index: int, private_key: str):
        self.index = index
        self.private_key = private_key
        self.account = EthereumAccount.from_key(private_key)
        self.w3 = Web3(Web3.HTTPProvider(RPC))
        self.weth_contract = self.w3.eth.contract(
            address=WETH_CONTRACT_ADDRESS, abi=WETH_CONTRACT_ABI
        )
        self.address = self.w3.to_checksum_address(self.account.address)
        self.info = f"[№{self.index} - {self.address[:5]}...{self.address[-5:]}]"

    @property
    def eth_balance(self) -> int:
        return self.w3.eth.get_balance(self.address)

    @property
    def weth_balance(self) -> float:
        balance = self.weth_contract.functions.balanceOf(self.address).call()
        return balance / 10**18

    @property
    def txn_count(self) -> int:
        return self.w3.eth.get_transaction_count(self.address)

    def get_txn_cost(self, txn_hash: str) -> float:
        txn = self.w3.eth.get_transaction(txn_hash)
        return (txn["gas"] * txn["gasPrice"]) / 10**18

    def get_txn_data(self, value: int = 0) -> dict:
        return {
            "from": self.address,
            "value": value,
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "gasPrice": int(self.w3.eth.gas_price * random.uniform(*GAS_MULTIPLIER)),
            "chainId": self.w3.eth.chain_id,
        }

    def send_txn(self, txn: dict):
        txn["gas"] = self.w3.eth.estimate_gas(txn)
        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return self.wait_txn(txn_hash.hex())

    def wait_txn(self, hash: str) -> str | None:
        start_time = time.time()
        while True:
            try:
                receipts: dict = self.w3.eth.get_transaction_receipt(hash)
                status = receipts.get("status")
                if status == 1:
                    logger.success(
                        f"{self.info} Transaction successful! {EXPLORER+'0x'+hash}"
                    )
                    return hash
                elif status is None:
                    time.sleep(0.5)
                else:
                    return logger.error(
                        f"{self.info} Transaction failed! {EXPLORER+'0x'+hash}"
                    )
            except TransactionNotFound:
                if time.time() - start_time > 300:
                    return
                time.sleep(1)
