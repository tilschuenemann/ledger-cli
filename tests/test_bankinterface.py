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
    assert BankInterface().list_banks() == ["dkb", "sp"]

    with pytest.raises(Exception) as exc_info:
        BankInterface().get_start_balance(bank="not-supported", export_path=Path.cwd())
    assert exc_info.value.args[0] == "The bank you provided is not supported."
    with pytest.raises(Exception) as exc_info:
        BankInterface().get_end_balance(bank="not-supported", export_path=Path.cwd())
    assert exc_info.value.args[0] == "The bank you provided is not supported."
    with pytest.raises(Exception) as exc_info:
        BankInterface().get_metadata(bank="not-supported", export_path=Path.cwd())
    assert exc_info.value.args[0] == "The bank you provided is not supported."


@pytest.mark.parametrize(
    "bank, export_path, is_start_balance_nan, is_end_balance_nan, start_balance, end_balance",
    [
        ("dkb", Path("tests/dkb_sample.csv"), True, False, None, 1000.01),
        ("sp", Path("tests/sp_sample.csv"), True, True, None, None),
    ],
)
def test_bankinterface(
    bank: str,
    export_path: Path,
    is_start_balance_nan: bool,
    is_end_balance_nan: bool,
    start_balance: float | None,
    end_balance: float | None,
) -> None:
    """Tests BankInterface methods with valid exports."""
    df = BankInterface().get_transactions(bank, export_path)
    assert set(df["amount"]) == {1000.01}
    assert set(df["recipient"]) == {"Test"}
    assert set(df["date"]) == {pd.to_datetime("2021-01-01")}

    assert (
        np.isnan(BankInterface().get_start_balance(bank, export_path))
        == is_start_balance_nan
    )
    # skip coverage of next branch, no bank for this case yet
    if is_start_balance_nan is False:  # pragma: no cover
        assert BankInterface().get_start_balance(bank, export_path) == start_balance

    assert (
        np.isnan(BankInterface().get_end_balance(bank, export_path))
        == is_end_balance_nan
    )
    if is_end_balance_nan is False:
        assert BankInterface().get_end_balance(bank, export_path) == end_balance

    metadata = BankInterface().get_metadata(bank, export_path)
    assert set(metadata["bank"]) == {bank}
    assert set(metadata["starting_balance"]) == {0.0}


@pytest.mark.parametrize(
    "bank, empty_export_path",
    [("dkb", Path("tests/dkb_empty.csv")), ("sp", Path("tests/sp_empty.csv"))],
)
def test_empty_export(bank: str, empty_export_path: Path) -> None:
    """Tests BankInterface methods with invalid exports."""
    with pytest.raises(Exception) as exc_info:
        BankInterface().get_transactions(bank, empty_export_path)
    assert (
        exc_info.value.args[0]
        == "The provided export contains no transactions. Please supply a non-empty export!"
    )
