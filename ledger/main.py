from pathlib import Path
import pandas as pd
import datetime
import csv
import locale


class Ledger:
    def __init__(self, output_path: Path, export_path: Path = None):
        self.transactions = pd.DataFrame(
            {
                "amount": pd.Series(dtype=float),
                "date": pd.Series(dtype=object),
                "recipient": pd.Series(dtype=str),
                "recipient_clean": pd.Series(dtype=str),
                "label1": pd.Series(dtype=str),
                "label2": pd.Series(dtype=str),
                "label3": pd.Series(dtype=str),
                "occurence": pd.Series(dtype=int),
                "amount_custom": pd.Series(dtype=float),
                "date_custom": pd.Series(dtype=object),
                "recipient_clean_custom": pd.Series(dtype=str),
                "label1_custom": pd.Series(dtype=str),
                "label2_custom": pd.Series(dtype=str),
                "label3_custom": pd.Series(dtype=str),
                "occurence_custom": pd.Series(dtype=int),
            }
        )
        self.mappings = pd.DataFrame(
            {
                "recipient": pd.Series(dtype=str),
                "recipient_clean": pd.Series(dtype=str),
                "label1": pd.Series(dtype=str),
                "label2": pd.Series(dtype=str),
                "label3": pd.Series(dtype=str),
                "occurence": pd.Series(dtype=int),
            }
        )
        self.metadata = pd.DataFrame({"starting_balance": pd.Series(dtype=float)})

        self.init_ledger(output_path, export_path)
        self.init_metadata(output_path, export_path)
        self.init_mappingtable(output_path)
        self.update_mappings()
        self._write("ledger.csv", output_path)
        self._write("mappingtable.csv", output_path)
        self._write("metadata.csv", output_path)

    def _write(self, fname: str, output_path: Path):
        """Writes csv to output_path."""
        tmp_path = output_path / fname
        if fname == "ledger.csv":
            self.transactions.to_csv(tmp_path, index=False)
        elif fname == "metadata.csv":
            self.metadata.to_csv(tmp_path, index=False)
        elif fname == "mappingtable.csv":
            self.mappings.to_csv(tmp_path, index=False)
        else:
            print(f"fname: {fname} not configured")

    def update_mappings(self):
        """Re-maps transactions."""
        self.transactions = self.transactions[
            self.transactions.columns.difference(
                ["label1", "label2", "label3", "recipient_clean", "occurence"]
            )
        ].merge(self.mappings, how="left", on="recipient")

    def init_ledger(self, output_path: Path, export_path: Path = None):
        """Reads existing ledger and appends export."""
        tmp_ledger = output_path / "ledger.csv"
        if tmp_ledger.exists() is True:
            tmp = pd.read_csv(tmp_ledger)
            self.transactions = pd.concat([self.transactions, tmp])

        if export_path != None and export_path.exists():
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
            df = df[["Buchungstag", "Auftraggeber / Begünstigter", "Betrag (EUR)"]]
            df.columns = ["date", "recipient", "amount"]
            self.transactions = pd.concat([self.transactions, df])

    def init_metadata(self, output_path: Path, export_path: Path = None):
        """Calculates starting balance from export."""
        tmp_metadata = output_path / "metadata.csv"
        if tmp_metadata.exists() is True:
            tmp = pd.read_csv(tmp_metadata)
            self.metadata = pd.concat([self.metadata, tmp])
        elif export_path != None and export_path.exists():
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
            revenue = df["amount"].sum()

            self.metadata = (
                pd.DataFrame({"starting_balance": [float(end_balance - revenue)]}),
            )

    def init_mappingtable(self, output_path: Path):
        """Reads mapping table and appends new recipients."""
        tmp_maptab = output_path / "mappingtable.csv"

        if tmp_maptab.exists() is True:
            tmp = pd.read_csv(tmp_maptab)
            self.mappings = pd.concat([self.mappings, tmp])

        new_recipients = self.transactions[
            ~self.transactions["recipient"].isin(self.mappings["recipient"].unique())
        ].loc[:, ["recipient"]]
        self.mappings = pd.concat([self.mappings, new_recipients], ignore_index=True)
