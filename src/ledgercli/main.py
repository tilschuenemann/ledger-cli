"""Ledger."""
from pathlib import Path

import numpy as np
import pandas as pd

from ledgercli.bankinterface import BankInterface


class Ledger:
    """Ledger."""

    def __init__(self, output_dir: Path, bank_fmt: str | None) -> None:
        """Initializes the Ledger.

        If no output_dir is provided, the current working dir will be used.

        Args:
            output_dir: dir where files get written to
            bank_fmt: which bank format to parse

        Raises:
            KeyError: if no bank is provided and bank can't be read from metadata file
        """
        if output_dir is None or output_dir.exists() is False:
            self.output_dir = Path.cwd()
        else:
            self.output_dir = output_dir

        self._create_template()
        self._read_existing()

        if bank_fmt is None:
            try:
                self.bank_fmt = self.metadata["bank"].iloc[0]
            except Exception as exc:
                raise KeyError("Please supply a valid BANK_FMT! Couldn't read BANK_FMT from metadata.") from exc
        else:
            if bank_fmt in BankInterface().list_bank_fmts():
                self.bank_fmt = bank_fmt
            else:
                raise KeyError("Please supply a valid BANK_FMT!")

    def _read_existing(self) -> None:
        """Reads existing transactions, mapping and metadata files.

        If a file is missing none of the existing ones will be used.
        """
        files = ["transactions.csv", "mapping.csv", "metadata.csv"]

        dfs = []
        for file in files:
            tmp_path = self.output_dir / file
            if tmp_path.exists():
                tmp = pd.read_csv(tmp_path)
                dfs.append(tmp)

        if len(dfs) == 3:
            self.tx, self.mapping, self.metadata = dfs

    def _init_tx(self, export_path: Path) -> None:
        """Adds export to transactions.

        Args:
            export_path: path to export
        """
        tmp = BankInterface().get_transactions(bank_fmt=self.bank_fmt, export_path=export_path)
        self.tx = pd.concat([self.tx, tmp])

    def _init_metadata(self, export_path: Path) -> None:
        """Initialize metadata from export.

        Args:
            export_path: path to export
        """
        self.metadata = BankInterface().get_metadata(bank_fmt=self.bank_fmt, export_path=export_path)

    def _update_mapping(self) -> None:
        """Adds new transaction recipients to mapping table.

        Takes all recipients from transactions, removes recipients already featured in mapping table and appends
        them to current mapping table. Sorts mapping table after.
        """
        tx_recipients = set(self.tx["recipient"].unique())
        mp_recipients = set(self.mapping["recipient"].unique())
        new_recipients = tx_recipients - mp_recipients
        new_mapping = pd.DataFrame(new_recipients, columns=["recipient"])

        self.mapping = pd.concat([self.mapping, new_mapping], ignore_index=True).sort_values("recipient")
        self.mapping["occurence"] = self.mapping["occurence"].fillna(0)

    def _update_tx_mapping(self) -> None:
        """Updates mappings in transactions with current mapping table."""
        tmp_tx = self.tx[
            [
                "amount",
                "date",
                "recipient",
                "amount_custom",
                "date_custom",
                "recipient_clean_custom",
                "label1_custom",
                "label2_custom",
                "label3_custom",
                "occurence_custom",
            ]
        ].copy()

        self.tx = tmp_tx.merge(self.mapping, how="left", on="recipient")

    def _init_tx_c(self) -> None:
        """Coalesces all custom values."""
        self.tx["date"] = pd.to_datetime(self.tx["date"])
        self.tx["date_custom"] = pd.to_datetime(self.tx["date_custom"])
        tmp = self.tx.copy()

        coalesce_map = {
            "date": "date_custom",
            "amount": "amount_custom",
            "recipient_clean": "recipient_clean_custom",
            "occurence": "occurence_custom",
            "label1": "label1_custom",
            "label2": "label2_custom",
            "label3": "label3_custom",
            "recipient": "recipient_clean",
        }

        for k, v in coalesce_map.items():
            tmp[k] = np.where(tmp[v].notna(), tmp[v], tmp[k])
            tmp = tmp.drop(v, axis=1)

        # np.where above converts datetimes into ns
        tmp["date"] = pd.to_datetime(tmp["date"], unit="ns")
        self.tx_c = tmp

    def _init_tx_d(self) -> None:
        """Distributes coalesced transactions based on occurence."""
        tmp = self.tx_c
        mask = pd.notna(tmp["occurence"]) & ~tmp["occurence"].between(-1, 1, inclusive="both")
        distribute = tmp.loc[mask].copy()
        keep = tmp.loc[~mask].copy()

        if distribute.empty is False:
            distribute["date"] = distribute.apply(
                lambda x: pd.date_range(
                    start=x.date if x.occurence > 0 else None,
                    end=x.date if x.occurence < 0 else None,
                    periods=abs(x.occurence),
                    freq="MS",
                ),
                axis=1,
            )

            distribute = distribute.explode("date")
            distribute["amount"] = distribute["amount"] / abs(distribute["occurence"])
            distribute["occurence"] = np.where(distribute["occurence"] > 0, 1, -1)

        self.tx_d = pd.concat([keep, distribute], axis=0, ignore_index=True)

    def _init_history(self) -> None:
        """Creates history dataframe.

        All transactions (TX) are grouped by date and a cumulative sum is calculated while taking starting_balance into account.
        history gets rewritten everytime it's generated and based on TX as there is no way to generate a valid cumulative sum
        after coalescing or distributing.
        """
        tmp = self.tx.groupby(["date"], as_index=False)["amount"].sum()
        tmp["balance"] = tmp["amount"].cumsum() + self.metadata["starting_balance"].iloc[0]
        self.history = tmp

    def update(self, export_path: Path | None = None) -> None:
        """Wrapper for updating the Ledger.

        Args:
            export_path: path to export
        """
        if export_path is not None:
            self._init_tx(export_path=export_path)

            if self.metadata.empty:
                self._init_metadata(export_path=export_path)

        self._update_mapping()
        self._update_tx_mapping()
        self._init_tx_c()
        self._init_tx_d()
        self._init_history()
        self._assign_types()

    def write(self) -> None:
        """Writes all tables to output_dir."""
        write_map = {
            "transactions": self.tx,
            "metadata": self.metadata,
            "mapping": self.mapping,
            "history": self.history,
            "tx_coalesced": self.tx_c,
            "tx_distributed": self.tx_d,
        }

        for k, v in write_map.items():
            v.to_csv(
                self.output_dir / f"{k}.csv",
                index=False,
                date_format="%Y-%m-%d",
                float_format="%.2f",
                na_rep="",
            )

    def _assign_types(self) -> None:
        types = {
            # base format
            "amount": "float",
            "recipient": "str",
            "date": "datetime64[ns]",
            # custom
            "amount_custom": "float",
            "recipient_clean_custom": "str",
            "date_custom": "datetime64[ns]",
            "label1_custom": "str",
            "label2_custom": "str",
            "label3_custom": "str",
            "occurence_custom": "float",
            # mapping
            "recipient_clean": "str",
            "label1": "str",
            "label2": "str",
            "label3": "str",
            "occurence": "float",
            # history
            "balance": "float",
            # metadata
            "bank": "str",
            # helpers
            "type": "category",
            "week": "datetime64[ns]",
            "month": "datetime64[ns]",
            "quarter": "datetime64[ns]",
            "year": "datetime64[ns]",
        }

        for df in [self.tx, self.tx_c, self.tx_d, self.history, self.mapping]:
            for k, v in types.items():
                if k in df.columns:
                    df[k] = df[k].astype(v)
                    if k != "recipient" and v == "str":
                        df[k] = df[k].replace("nan", "")

    def _create_template(self) -> None:
        """Creates internal dataframes with correct dtypes."""
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
        self.tx = pd.DataFrame(
            {
                "amount": pd.Series(dtype=float),
                "date": pd.Series(dtype=object),
                "recipient": pd.Series(dtype=str),
                **mapping_schema,
                **transaction_schema,
            }
        )
        self.tx_c = pd.DataFrame(
            {
                "amount": pd.Series(dtype=float),
                "date": pd.Series(dtype=object),
                **mapping_schema,
            }
        )
        self.tx_d = self.tx_c.copy()

        self.mapping = pd.DataFrame({"recipient": pd.Series(dtype=str), **mapping_schema})
        self.metadata = pd.DataFrame(
            {
                "starting_balance": pd.Series(dtype=float),
                "bank": pd.Series(dtype=str),
            }
        )
        self.history = pd.DataFrame(
            {
                "date": pd.Series(dtype=object),
                "amount": pd.Series(dtype=float),
                "balance": pd.Series(dtype=float),
            }
        )
