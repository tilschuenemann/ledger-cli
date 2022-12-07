"""Tests for BankInterface.

BankInterface provides an extendable interface between ledgercli and CSV exports.

Incase you want to create a PR with your bank format, please create a dummy with
the expected values and redacted other information but still keeping the report structure.
"""

from pathlib import Path
from typing import Dict
from typing import Tuple

import pandas as pd
import pytest

from ledgercli.bankinterface import BankInterface


@pytest.fixture
def exp_values() -> Dict[str, float | Path | str]:
    """Expected values for parametric testing."""
    date = pd.to_datetime("2021-01-01")
    return {"amount": 1000.01, "recipient": "Test", "date": date}


@pytest.fixture
def dkb_setup() -> Tuple[str, Path]:
    # Dict[str, str | Path]:
    """Fixture for DKB test setup."""
    # return {"bank_format": "dkb", "export_path": Path("tests/dkb_sample.csv")}
    return ("dkb", Path("tests/dkb_sample.csv"))


@pytest.fixture
def sp_setup() -> Tuple[str, Path]:
    """Fixture for Sparkasse test setup."""
    # return {"bank_format": "sp", "export_path": "tests/sp_sample.csv"}
    return ("sp", Path("tests/sp_sample.csv"))


def test_bankinterfaces() -> None:
    """Tests for valid formats and for raising exception if a non-supported bank_format is provided."""
    # valid formats
    assert BankInterface().list_bank_formats() == ["dkb", "sp"]

    # invalid formats
    with pytest.raises(Exception) as exc_info:
        BankInterface().is_supported("this_format_is_not_supported")
    assert str(exc_info.value) == "The bank_format you provided is not supported."


def test_dkb(
    dkb_setup: Tuple[str, Path], exp_values: Dict[str, float | Path | str]
) -> None:
    """Tests for DKB."""
    bank_format, export_path = dkb_setup

    # valid input
    assert 0 == BankInterface().get_start_balance(bank_format, export_path)
    assert 1000.01 == BankInterface().get_end_balance(bank_format, export_path)

    df = BankInterface().get_transactions(bank_format, export_path)

    for item in ["amount", "date", "recipient"]:
        assert set(df[item]) == {exp_values[item]}

    # empty input
    with pytest.raises(Exception) as exc_info:
        BankInterface().get_transactions(bank_format, Path("tests/dkb_empty.csv"))
    assert (
        str(exc_info.value)
        == "The provided export contains no transactions. Please supply a non-empty export!"
    )


def test_sp(
    sp_setup: Tuple[str, Path], exp_values: Dict[str, float | Path | str]
) -> None:
    """Tests for Sparkasse."""
    # valid input
    bank_format, export_path = sp_setup

    assert 0 == BankInterface().get_start_balance(bank_format, export_path)
    assert 0 == BankInterface().get_end_balance(bank_format, export_path)

    df = BankInterface().get_transactions(bank_format, export_path)

    for item in ["amount", "date", "recipient"]:
        assert set(df[item]) == {exp_values[item]}

    # empty input
    with pytest.raises(Exception) as exc_info:
        BankInterface().get_transactions(bank_format, Path("tests/sp_empty.csv"))
    assert (
        str(exc_info.value)
        == "The provided export contains no transactions. Please supply a non-empty export!"
    )
