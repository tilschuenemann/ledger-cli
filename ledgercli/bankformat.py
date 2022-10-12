import pandas as pd

import locale
import pathlib


class BankFormat:
    @staticmethod
    def list_bank_format() -> None:
        print("supported bank_formats:")
        for bank_format in ["dkb"]:
            print(bank_format)

    @staticmethod
    def get_transactions(bank_format: str, export_path: pathlib.Path) -> pd.DataFrame:
        if bank_format == "dkb":
            df = pd.read_csv(
                export_path,
                sep=";",
                decimal=",",
                thousands=".",
                parse_dates=["Buchungstag", "Wertstellung"],
                dayfirst=True,
                encoding="latin1",
                skiprows=6,
            )
            df = df.iloc[:, [0, 3, 7]].copy()
        return df

    @staticmethod
    def get_end_balance(bank_format: str, export_path: pathlib.Path) -> pd.DataFrame:
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
        return end_balance
