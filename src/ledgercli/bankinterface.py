"""BankInterface."""
from pathlib import Path

import pandas as pd


class BankInterface:
    """BankInterface."""

    @staticmethod
    def list_banks() -> list[str]:
        """Lists all currently supported bank formats."""
        return ["dkb", "sp"]

    @staticmethod
    def is_supported(bank: str) -> str:
        """Returns provided bank if supported and throws exception otherwise.

        Args:
          bank: str

        Returns:
          bank

        Raises:
          Exception, if bank is not supported.
        """
        if bank not in BankInterface().list_banks():
            raise Exception("The bank you provided is not supported.")

        return bank

    @staticmethod
    def get_transactions(bank: str, export_path: Path) -> pd.DataFrame:
        """Reads transactions from export_path with bank.

        Args:
          bank:
          export_path:

        Returns:
          transactions dataframe
        """
        BankInterface().is_supported(bank=bank)
        if bank == "dkb":
            tmp = pd.read_csv(
                export_path,
                sep=";",
                decimal=",",
                thousands=".",
                parse_dates=["Buchungstag", "Wertstellung"],
                dayfirst=True,
                encoding="latin1",
                skiprows=6,
            )
            df = tmp.iloc[:, [0, 3, 7]].copy()
            df.columns = ["date", "recipient", "amount"]
        elif bank == "sp":
            tmp = pd.read_csv(
                export_path,
                sep=";",
                decimal=",",
                thousands=".",
                parse_dates=["Buchungstag", "Valutadatum"],
                dayfirst=True,
                encoding="latin1",
            )
            df = tmp.iloc[:, [2, 11, 14]].copy()
            df.columns = ["date", "recipient", "amount"]

        if df.empty:
            raise Exception(
                "The provided export contains no transactions. Please supply a non-empty export!"
            )
        return df

    @staticmethod
    def get_metadata(bank: str, export_path: Path) -> pd.DataFrame:
        """Creates metadata dataframe from export.

        Metadata stores bank and the starting balance which is needed for historical balances.

        Args:
          bank:
          export_path:

        Returns:
          dataframe
        """
        tx = BankInterface().get_transactions(bank, export_path)
        start_balance = BankInterface().get_start_balance(
            bank=bank, export_path=export_path
        )
        end_balance = BankInterface().get_end_balance(
            bank=bank, export_path=export_path
        )

        tmp_start_balance: float = 0.0

        if start_balance == 0.0 and end_balance == 0.0:
            pass
        elif start_balance == 0.0 and end_balance != 0.0:
            revenue = tx["amount"].sum()
            tmp_start_balance = end_balance - float(revenue)
        else:
            tmp_start_balance = start_balance

        return pd.DataFrame(
            {
                "starting_balance": [tmp_start_balance],
                "bank": [bank],
            }
        )

    @staticmethod
    def get_start_balance(bank: str, export_path: Path) -> float:
        """Reads start balance of given export.

        If a bank doesn't provide a starting balance, 0 is returned.

        Args:
          bank
          export_path

        Returns:
          end balance of given export
        """
        BankInterface().is_supported(bank=bank)
        start_balance = 0.0
        if bank in ["dkb", "sp"]:
            start_balance = 0.0

        return start_balance

    @staticmethod
    def get_end_balance(bank: str, export_path: Path) -> float:
        """Reads end balance of given export.

        If a bank doesn't provide a ending balance, 0 is returned.

        Args:
          bank
          export_path

        Returns:
          end balance of given export
        """
        BankInterface().is_supported(bank=bank)
        if bank == "dkb":
            header = pd.read_csv(
                export_path,
                sep=";",
                decimal=",",
                thousands=".",
                encoding="latin1",
                skiprows=2,
                nrows=3,
                header=None,
            )

            # locale.atof not used here as de_DE locale needs to be installed
            end_balance = float(
                header.iloc[2, 1].replace(".", "").replace(",", ".").replace(" EUR", "")
            )
        else:
            end_balance = 0.0
        return end_balance
