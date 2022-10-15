from ledgercli.bankformat import BankFormat
from pathlib import Path
import datetime


def test_dkb():
    # regular export
    df = BankFormat().get_transactions("dkb", Path("tests/bank_exports/dkb_export_regular.csv"))
    assert df.shape == (3, 3)
    assert set(df.columns) == set(["date", "amount", "recipient"])
    assert set(df["recipient"]) == set(["rec1", "rec2", "rec3"])
    assert set(df["date"]) == set([datetime.datetime(2022, 9, 15), datetime.datetime(2022, 9, 16)])
    assert df["amount"].sum() == 1

    start_balance = BankFormat().get_start_balance("dkb", Path("tests/bank_exports/dkb_export_regular.csv"))
    assert start_balance == 0

    end_balance = BankFormat().get_end_balance("dkb", Path("tests/bank_exports/dkb_export_regular.csv"))
    assert end_balance == 1000.01

    # empty export
    df = BankFormat().get_transactions("dkb", Path("tests/bank_exports/dkb_export_empty.csv"))
    assert df.shape == (0, 3)
    assert set(df.columns) == set(["date", "amount", "recipient"])

    start_balance = BankFormat().get_start_balance("dkb", Path("tests/bank_exports/dkb_export_empty.csv"))
    assert start_balance == 0

    end_balance = BankFormat().get_end_balance("dkb", Path("tests/bank_exports/dkb_export_empty.csv"))
    assert end_balance == 1010.01
