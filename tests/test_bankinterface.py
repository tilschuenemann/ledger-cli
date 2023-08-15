"""Tests for BankInterface.

BankInterface provides an extendable interface between ledgercli and CSV exports.

Incase you want to create a PR with your bank format, please create a dummy with
the expected values and redacted other information but still keeping the report structure.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ledgercli.bankinterface import BankInterface


def test_bankinterfaces() -> None:
    """Tests for valid formats and for raising exception if a non-supported bank is provided."""
    # valid formats
    assert BankInterface().list_bank_fmts() == ["dkb", "sp"]

    with pytest.raises(Exception) as exc_info:
        BankInterface().get_transactions(bank_fmt="not-supported", export_path=Path.cwd())
    assert exc_info.value.args[0] == "The bank_fmt you provided is not supported."

    with pytest.raises(Exception) as exc_info:
        BankInterface().get_start_balance(bank_fmt="not-supported", export_path=Path.cwd())
    assert exc_info.value.args[0] == "The bank_fmt you provided is not supported."

    with pytest.raises(Exception) as exc_info:
        BankInterface().get_end_balance(bank_fmt="not-supported", export_path=Path.cwd())
    assert exc_info.value.args[0] == "The bank_fmt you provided is not supported."

    with pytest.raises(Exception) as exc_info:
        BankInterface().get_metadata(bank_fmt="not-supported", export_path=Path.cwd())
    assert exc_info.value.args[0] == "The bank_fmt you provided is not supported."


@pytest.mark.parametrize(
    "bank_fmt, export_path, is_export_empty, is_start_balance_nan, is_end_balance_nan, start_balance, end_balance",
    [
        ("dkb", Path("tests/dkb_sample.csv"), False, True, False, None, 1000.01),
        ("dkb", Path("tests/dkb_empty.csv"), True, False, False, None, None),
        ("sp", Path("tests/sp_sample.csv"), False, True, True, None, None),
        ("sp", Path("tests/sp_empty.csv"), True, False, False, None, None),
    ],
)
def test_bankinterface(
    bank_fmt: str,
    export_path: Path,
    is_export_empty: bool,
    is_start_balance_nan: bool,
    is_end_balance_nan: bool,
    start_balance: float | None,
    end_balance: float | None,
) -> None:
    """Tests BankInterface methods with valid and empty exports.

    Args:
        bank_fmt: a bank format
        export_path: path to export
        is_export_empty: true if export is empty
        is_start_balance_nan: true if start balance is nan
        is_end_balance_nan: true if end balance is nan
        start_balance: expected start balance
        end_balance: expected end balance

    """
    if is_export_empty:
        with pytest.raises(Exception) as exc_info:
            BankInterface().get_transactions(bank_fmt, export_path)
        assert (
            exc_info.value.args[0] == "The provided export contains no transactions. Please supply a non-empty export!"
        )
        return

    tx = BankInterface().get_transactions(bank_fmt, export_path)
    assert set(tx["amount"]) == {1000.01}
    assert set(tx["recipient"]) == {"Test"}
    assert set(tx["date"]) == {pd.to_datetime("2021-01-01")}

    assert np.isnan(BankInterface().get_start_balance(bank_fmt, export_path)) == is_start_balance_nan
    assert np.isnan(BankInterface().get_end_balance(bank_fmt, export_path)) == is_end_balance_nan

    # skip coverage of next branch, no bank for this case yet
    if is_start_balance_nan is False:  # pragma: no cover
        assert BankInterface().get_start_balance(bank_fmt, export_path) == start_balance

    if is_end_balance_nan is False:
        assert BankInterface().get_end_balance(bank_fmt, export_path) == end_balance

    metadata = BankInterface().get_metadata(bank_fmt, export_path)
    assert set(metadata["bank"]) == {bank_fmt}
    assert set(metadata["starting_balance"]) == {0.0}
