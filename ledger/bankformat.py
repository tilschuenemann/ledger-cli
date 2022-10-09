import locale
import pandas as pd
import pathlib


class BankFormat:
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
            return df.iloc[:, [0, 3, 7]].copy()

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
            return locale.atof(header.iloc[2, 1].replace(" EUR", ""))
