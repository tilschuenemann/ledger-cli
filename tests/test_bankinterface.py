"""Tests for BankInterface.

BankInterface provides an extendable interface between ledgercli and CSV exports.

Incase you want to create a PR with your bank format, please create a dummy with
the expected values and redacted other information but still keeping the report structure.
"""
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from ledgercli.bankinterface import BankInterface


def test_bankinterfaces() -> None:
    """Tests for valid formats and for raising exception if a non-supported bank_format is provided."""
    # valid formats
    assert BankInterface().list_bank_formats() == ["dkb", "sp"]

    # invalid formats
    with pytest.raises(Exception) as exc_info:
        BankInterface().is_supported("this_format_is_not_supported")
    assert str(exc_info.value) == "The bank_format you provided is not supported."


@pytest.mark.parametrize(
    "bank_format, export_path,empty_export_path,amount,recipient, date, start_balance, end_balance",
    [
        (
            "dkb",
            Path("tests/dkb_sample.csv"),
            Path("tests/dkb_empty.csv"),
            1000.01,
            "Test",
            pd.to_datetime("2021-01-01"),
            0.0,
            1000.01,
        ),
        (
            "sp",
            Path("tests/sp_sample.csv"),
            Path("tests/sp_empty.csv"),
            1000.01,
            "Test",
            pd.to_datetime("2021-01-01"),
            0.0,
            0.0,
        ),
    ],
)
def test_banks(
    bank_format: str,
    export_path: Path,
    empty_export_path: Path,
    amount: float,
    recipient: str,
    date: datetime,
    start_balance: float,
    end_balance: float,
) -> None:
    """Tests each bank for correct transactions, start and end balance for both valid and empty exports."""
    # valid input
    assert start_balance == BankInterface().get_start_balance(bank_format, export_path)
    assert end_balance == BankInterface().get_end_balance(bank_format, export_path)

    df = BankInterface().get_transactions(bank_format, export_path)

    assert set(df["amount"]) == {amount}
    assert set(df["recipient"]) == {recipient}
    assert set(df["date"]) == {date}

    # empty input
    with pytest.raises(Exception) as exc_info:
        BankInterface().get_transactions(bank_format, empty_export_path)
    assert (
        str(exc_info.value)
        == "The provided export contains no transactions. Please supply a non-empty export!"
    )
