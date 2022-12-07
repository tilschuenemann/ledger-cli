import pandas as pd

import locale
from pathlib import Path
from typing import List


class BankInterface:
    @staticmethod
    def list_bank_formats() -> List[str]:
        return ["dkb", "sp"]

    @staticmethod
    def is_supported(bank_format: str) -> str:
        """Returns provided bank_format if supported and throws exception otherwise.

        Args:
          bank_format: str

        Returns:
          bank_format

        Raises:
          Exception, if bank_format is not supported.
        """
        if bank_format not in BankInterface().list_bank_formats():
            raise Exception("The bank_format you provided is not supported.")

        return bank_format

    @staticmethod
    def get_transactions(bank_format: str, export_path: Path) -> pd.DataFrame:
        """Reads transactions from export_path with bank_format.

        Args:
          bank_format:
          export_path:

        Returns:
          transactions dataframe
        """
        BankInterface().is_supported(bank_format=bank_format)
        if bank_format == "dkb":
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
        elif bank_format == "sp":
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
            raise Exception("The provided export contains no transactions. Please supply a non-empty export!")
        return df

    @staticmethod
    def get_metadata(bank_format: str, export_path: Path) -> pd.DataFrame:
        """Creates metadata dataframe from export.

        Metadata stores bank_format and the starting balance which is needed for historical balances.

        Args:
          bank_format:
          export_path:

        Returns:
          dataframe
        """
        tx = BankInterface().get_transactions(bank_format, export_path)
        start_balance = BankInterface().get_start_balance(
            bank_format=bank_format, export_path=export_path
        )
        end_balance = BankInterface().get_end_balance(
            bank_format=bank_format, export_path=export_path
        )

        revenue = tx["amount"].sum()
        tmp_start_balance: float = 0

        if start_balance == end_balance == 0:
            pass
        elif start_balance == 0 and end_balance != 0:
            tmp_start_balance = end_balance - float(revenue)
        else:
            tmp_start_balance = start_balance

        return pd.DataFrame(
            {
                "starting_balance": [tmp_start_balance],
                "bank_format": [bank_format],
            }
        )

    @staticmethod
    def get_start_balance(bank_format: str, export_path: Path) -> float:
        """Reads start balance of given export.

        If a bank_format doesn't provide a starting balance, 0 is returned.

        Args:
          bank_format
          export_path

        Returns:
          end balance of given export
        """
        BankInterface().is_supported(bank_format=bank_format)
        start_balance = 0
        if bank_format in ["dkb", "sp"]:
            start_balance = 0

        return start_balance

    @staticmethod
    def get_end_balance(bank_format: str, export_path: Path) -> float:
        """Reads end balance of given export.

        If a bank_format doesn't provide a ending balance, 0 is returned.

        Args:
          bank_format
          export_path

        Returns:
          end balance of given export
        """
        BankInterface().is_supported(bank_format=bank_format)
        if bank_format == "dkb":
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

            locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
            end_balance = locale.atof(header.iloc[2, 1].replace(" EUR", ""))
        else:
            end_balance = 0
        return end_balance
