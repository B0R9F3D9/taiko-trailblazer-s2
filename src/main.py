import sys, questionary, os
from loguru import logger

from core import *
from config import *
from settings import *


def wallet_selector():
    Checker(WALLETS).run()
    if len(WALLETS) == 1:
        return WALLETS
    print(
        "Select accounts to work with. Format: \n"
        "1 — to select only the first wallet\n"
        "1,2,3 — to select the first, second, and third wallets\n"
        "1-3 — to select wallets from the first to the third inclusive\n"
        "all — to select all wallets (or press Enter)\n"
    )
    result = input("Enter your choice: ")
    if result in ["all", ""]:
        return WALLETS
    try:
        if "," in result:
            return [WALLETS[int(i) - 1] for i in result.split(",")]
        elif "-" in result:
            first_digit, second_digit = result.split("-")
            return WALLETS[int(first_digit) - 1 : int(second_digit)]
        else:
            return [WALLETS[int(result) - 1]]
    except ValueError:
        raise ValueError("Invalid wallet selection!")


def main():
    module = questionary.select(
        message="Select module: ",
        instruction="(use the arrows to navigate)",
        choices=[
            questionary.Choice("💼 Wrap-Unwrap", Wrap),
            questionary.Choice("💻 Rubyscore", Rubyscore),
            questionary.Choice("📊 Checker", "checker"),
            questionary.Choice("🔙 Go back to wallet selection", "back"),
            questionary.Choice("❌ Exit", "exit"),
        ],
        qmark="\n❓ ",
        pointer="👉 ",
    ).ask()

    if module == "checker":
        return Checker(wallets).run()
    elif module == "back":
        return True
    elif module in ["exit", None]:
        sys.exit(0)

    for wallet in wallets:
        module(wallet).run()
        logger.success(f"{wallet.info} Wallet completed 🏁")
        if wallet != wallets[-1]:
            sleep(*SLEEP_BETWEEN_WALLETS)


if __name__ == "__main__":
    logger.info("-" * 50)
    sys.stdout.write("\033[2J\033[H")  # clear console
    sys.stdout.flush()

    WALLETS = [Wallet(i, key) for i, key in enumerate(KEYS, 1)]
    if len(WALLETS) == 0:
        logger.critical(
            f"Fill in the wallet list! 👉 {os.path.join(os.getcwd(), 'data/keys.txt')}"
        )
        sys.exit(0)
    wallets = wallet_selector()

    while True:
        try:
            run_wallet_selector = main()
            if run_wallet_selector:
                wallets = wallet_selector()
        except Exception as e:
            logger.critical(e)
        except (KeyboardInterrupt, SystemExit):
            print("\n👋👋👋")
            exit()
