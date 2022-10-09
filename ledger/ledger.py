from pathlib import Path
import pandas as pd
import datetime
from typing import Optional
import locale
import numpy
from ledger.bankformat import BankFormat
import math
import numpy as np


class Ledger:
    def __init__(
        self, output_path: Path, export_path: Optional[Path], bank_format: str
    ):
        mapping_schema = {
            "recipient_clean": pd.Series(dtype=str),
            "label1": pd.Series(dtype=str),
            "label2": pd.Series(dtype=str),
            "label3": pd.Series(dtype=str),
            "occurence": pd.Series(dtype=int),
        }
        transaction_schema = {
            "amount_custom": pd.Series(dtype=float),
            "date_custom": pd.Series(dtype=object),
            "recipient_clean_custom": pd.Series(dtype=str),
            "label1_custom": pd.Series(dtype=str),
            "label2_custom": pd.Series(dtype=str),
            "label3_custom": pd.Series(dtype=str),
            "occurence_custom": pd.Series(dtype=int),
        }
        self.transactions = pd.DataFrame(
            {
                "amount": pd.Series(dtype=float),
                "date": pd.Series(dtype=object),
                "recipient": pd.Series(dtype=str),
                **mapping_schema,
                **transaction_schema,
            }
        )
        # self.transactions_coalesced,
        self.transactions_coalesced = pd.DataFrame(
            {
                "amount": pd.Series(dtype=float),
                "date": pd.Series(dtype=object),
                **mapping_schema,
            }
        )
        self.mappings = pd.DataFrame(
            {"recipient": pd.Series(dtype=str), **mapping_schema}
        )
        self.metadata = pd.DataFrame(
            {
                "starting_balance": pd.Series(dtype=float),
                "bank_format": pd.Series(dtype=str),
            }
        )
        self.history = pd.DataFrame(
            {
                "date": pd.Series(dtype=object),
                "amount": pd.Series(dtype=float),
                "balance": pd.Series(dtype=float),
            }
        )

        self.init_ledger(output_path, export_path, bank_format)
        self.init_metadata(output_path, export_path, bank_format)
        self.init_mappingtable(output_path)
        self.update_mappings()
        self._write("ledger.csv", output_path)
        self._write("mappingtable.csv", output_path)
        self._write("metadata.csv", output_path)
        self._write("history.csv", output_path)

    def _write(self, fname: str, output_path: Path) -> None:
        """Writes csv to output_path."""
        tmp_path = output_path / fname
        if fname == "ledger.csv":
            self.transactions.to_csv(tmp_path, index=False)
        elif fname == "metadata.csv":
            self.metadata.to_csv(tmp_path, index=False)
        elif fname == "mappingtable.csv":
            self.mappings.to_csv(tmp_path, index=False)
        elif fname == "history.csv":
            self.mappings.to_csv(tmp_path, index=False)
        else:
            print(f"fname: {fname} not configured")

    def update_mappings(self) -> None:
        """Re-maps transactions."""
        self.transactions = self.transactions[
            self.transactions.columns.difference(
                ["label1", "label2", "label3", "recipient_clean", "occurence"]
            )
        ].merge(self.mappings, how="left", on="recipient")

    def init_ledger(
        self, output_path: Path, export_path: Optional[Path], bank_format: str
    ) -> None:
        """Reads existing ledger and appends export."""
        tmp_ledger = output_path / "ledger.csv"
        if tmp_ledger.exists() is True:
            tmp = pd.read_csv(tmp_ledger)
            self.transactions = pd.concat([self.transactions, tmp])

        if export_path is not None and export_path.exists():
            tmp = BankFormat.get_transactions(
                bank_format=bank_format, export_path=export_path
            )
            tmp.columns = ["date", "recipient", "amount"]
            self.transactions = pd.concat([self.transactions, tmp])

    def init_metadata(
        self, output_path: Path, export_path: Optional[Path], bank_format: str
    ) -> None:
        """Calculates starting balance from export."""
        tmp_metadata = output_path / "metadata.csv"
        if tmp_metadata.exists() is True:
            tmp = pd.read_csv(tmp_metadata)
            self.metadata = pd.concat([self.metadata, tmp])
        elif export_path is not None and export_path.exists():

            end_balance = BankFormat.get_end_balance(
                bank_format=bank_format, export_path=export_path
            )

            revenue = self.transactions["amount"].sum()

            self.metadata = pd.DataFrame(
                {
                    "starting_balance": [float(end_balance - revenue)],
                    "bank_format": [bank_format],
                }
            )

    def init_mappingtable(self, output_path: Path) -> None:
        """Reads mapping table and appends new recipients."""
        tmp_maptab = output_path / "mappingtable.csv"

        if tmp_maptab.exists() is True:
            tmp = pd.read_csv(tmp_maptab)
            self.mappings = pd.concat([self.mappings, tmp])

        new_recipients = self.transactions[
            ~self.transactions["recipient"].isin(self.mappings["recipient"].unique())
        ].loc[:, ["recipient"]]
        self.mappings = pd.concat([self.mappings, new_recipients], ignore_index=True)

    def _coalesce(self) -> None:
        """Coalesces all custom values."""
        tmp = self.transactions.copy()

        for col in [
            "date",
            "amount",
            "occurence",
            "recipient_clean",
            "label1",
            "label2",
            "label3",
        ]:
            tmp[col] = np.where(
                pd.isnull(tmp[f"{col}_custom"]), tmp[col], tmp[f"{col}_custom"]
            )
            tmp = tmp.drop(f"{col}_custom", axis=1)
        tmp = tmp.drop("recipient", axis=1).rename(
            columns={"recipient_clean": "recipient"}
        )
        self.transactions_coalesced = tmp

    def _init_history(self) -> None:
        """Calculate daily balance."""
        if self.transactions.empty is False:
            tmp_history = self.transactions.groupby(["date"], as_index=False)[
                "amount"
            ].sum()

            tmp_history["balance"] = (
                tmp_history["amount"].cumsum()
                + self.metadata["starting_balance"].iloc[0]
            )

            self.history = pd.concat([self.history, tmp_history], ignore_index=True)

    def _init_datecols(self) -> None:
        for df in [
            self.transactions,
            # self.transactions_coalesced
        ]:
            for col in ["week", "month", "quarter", "year"]:
                df[col] = (
                    pd.to_datetime(df["date"])
                    .dt.to_period(col.upper()[0])
                    .dt.to_timestamp()
                )

    def _init_distributed_ledger(self) -> None:
        """Distributes coalesced transactions basd on occurence."""

        # TODO check if transactions_coalesced empty
        mask = self.transactions_coalesced["occurence"] == 0
        repeat = self.transactions_coalesced[~mask].copy()
        rest = self.transactions_coalesced[mask].copy()

        if repeat.empty is False:
            repeat["date"] = repeat.apply(
                lambda x: pd.date_range(
                    start=x.date if x.occurence > 0 else None,
                    end=x.date if x.occurence < 0 else None,
                    periods=abs(x.occurence),
                    freq="MS",
                ),
                axis=1,
            )

            repeat = repeat.explode("date")
            repeat["amount"] = repeat["amount"] / abs(repeat["occurence"])
        self.transactions_distributed = pd.concat([rest, repeat], ignore_index=True)
