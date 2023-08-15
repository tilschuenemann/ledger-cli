"""BankInterface.

This module provides an easily extendable interface for reading transactions from a file.
"""
from pathlib import Path

import numpy as np
import pandas as pd


class BankInterface:
    """BankInterface."""

    @staticmethod
    def list_bank_fmts() -> list[str]:
        """Lists all currently supported bank formats.

        Returns:
            list of supported bank formats
        """
        return ["dkb", "sp"]

    @staticmethod
    def get_transactions(bank_fmt: str, export_path: Path) -> pd.DataFrame:
        """Reads transactions from export_path using bank_fmt.

        Args:
            bank_fmt: a bank format
            export_path: path to export

        Returns:
            transactions dataframe

        Raises:
            KeyError: bad bank_fmt
            Exception: if parsed export has no transactions
        """
        if bank_fmt not in BankInterface().list_bank_fmts():
            raise KeyError("The bank_fmt you provided is not supported.")

        if bank_fmt == "dkb":
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
            tx = tmp.iloc[:, [0, 3, 7]].copy()
            tx.columns = ["date", "recipient", "amount"]
        else:
            tmp = pd.read_csv(
                export_path,
                sep=";",
                decimal=",",
                thousands=".",
                parse_dates=["Buchungstag", "Valutadatum"],
                dayfirst=True,
                encoding="latin1",
            )
            tx = tmp.iloc[:, [2, 11, 14]].copy()
            tx.columns = ["date", "recipient", "amount"]

        if tx.empty:
            raise Exception("The provided export contains no transactions. Please supply a non-empty export!")
        return tx

    @staticmethod
    def get_start_balance(bank_fmt: str, export_path: Path) -> float:
        """Reads start balance of given export.

        If a bank doesn't provide a starting balance, np.nan is returned.

        Args:
            bank_fmt: a bank format
            export_path: path to export

        Returns:
            start balance of given export

        Raises:
            KeyError: bad bank_fmt
        """
        if bank_fmt not in BankInterface().list_bank_fmts():
            raise KeyError("The bank_fmt you provided is not supported.")

        start_balance = np.nan
        if bank_fmt in ["dkb", "sp"]:
            start_balance = np.nan

        return start_balance  # pragma: no cover

    @staticmethod
    def get_end_balance(bank_fmt: str, export_path: Path) -> float:
        """Reads end balance of given export.

        If a bank doesn't provide a ending balance, np.nan is returned.

        Args:
            bank_fmt: a bank format
            export_path: path to export

        Returns:
            end balance of given export

        Raises:
            KeyError: bad bank_fmt
        """
        if bank_fmt not in BankInterface().list_bank_fmts():
            raise KeyError("The bank_fmt you provided is not supported.")

        end_balance = np.nan

        if bank_fmt == "dkb":
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
            end_balance = float(header.iloc[2, 1].replace(".", "").replace(",", ".").replace(" EUR", ""))

        return end_balance

    @staticmethod
    def get_metadata(bank_fmt: str, export_path: Path) -> pd.DataFrame:
        """Creates metadata dataframe from export.

        Metadata stores bank and the starting balance which is needed for historical balances.
        If the bank exports provides no start or end balance to calculate the start balance, it is set to 0.

        Args:
            bank_fmt: a bank format
            export_path: path to export

        Returns:
            dataframe
        """
        tmp_start_balance = BankInterface().get_start_balance(bank_fmt=bank_fmt, export_path=export_path)
        end_balance = BankInterface().get_end_balance(bank_fmt=bank_fmt, export_path=export_path)

        start_balance: float = 0.0

        if ~np.isnan(tmp_start_balance) and np.isnan(end_balance):  # pragma: no cover
            start_balance = tmp_start_balance
        elif np.isnan(tmp_start_balance) and ~np.isnan(end_balance):
            tx = BankInterface().get_transactions(bank_fmt, export_path)
            revenue = tx["amount"].sum()
            start_balance = end_balance - float(revenue)

        return pd.DataFrame(
            {
                "starting_balance": [start_balance],
                "bank": [bank_fmt],
            }
        )
