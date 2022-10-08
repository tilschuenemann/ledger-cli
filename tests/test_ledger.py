import pytest
from ledger.ledger import Ledger
import pathlib


def test_init_ledger_nosetup(tmp_path):
    """No setup provided"""
    d = tmp_path / "output"
    d.mkdir()
    Ledger(d, export_path=None)


def test_init_ledger_emptyexport(tmp_path):
    """Empty export is provided"""
    d = tmp_path / "output"
    d.mkdir()
    export_path = pathlib.Path("tests/export_empty.csv")
    Ledger(d, export_path=export_path)

    maptab = d / "mappingtable.csv"
    ledger = d / "ledger.csv"
    metadata = d / "metadata.csv"

    # TODO set to false, write no empty files?
    assert maptab.exists()
    assert ledger.exists()
    assert metadata.exists()


def test_init_ledger_valid(tmp_path):
    """Valid export is provided"""
    d = tmp_path / "output"
    d.mkdir()
    export_path = pathlib.Path("tests/export_regular.csv")
    l = Ledger(d, export_path=export_path)

    maptab = d / "mappingtable.csv"
    ledger = d / "ledger.csv"
    metadata = d / "metadata.csv"
    assert maptab.exists()
    assert ledger.exists()
    assert metadata.exists()

    assert l.mappings.shape == (3, 6)
    assert l.transactions.shape == (3, 15)
    assert l.metadata.shape == (1, 1)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.transactions["amount"].sum() == 1
    assert set(l.transactions["recipient"]) == set(["rec1", "rec2", "rec3"])
    # assert l.transactions["date"].unique() == []
    assert l.transactions.isna().sum().sum() == 3 * 12


def test_func(tmp_path):
    """TODO check for correctly updating mp"""
    pass


def test_append1(tmp_path):
    d = tmp_path / "output"
    d.mkdir()
    export_path = pathlib.Path("tests/export_regular.csv")
    appendage_path = pathlib.Path("tests/appendage_regular.csv")
    Ledger(d, export_path=export_path)

    maptab = d / "mappingtable.csv"
    ledger = d / "ledger.csv"
    metadata = d / "metadata.csv"

    l = Ledger(d, export_path=appendage_path)
    assert maptab.exists()
    assert ledger.exists()
    assert metadata.exists()

    assert l.mappings.shape == (6, 6)
    assert l.transactions.shape == (6, 15)
    assert l.metadata.shape == (1, 1)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.transactions["amount"].sum() == 2
    assert set(l.transactions["recipient"]) == set(
        ["rec1", "rec2", "rec3", "rec4", "rec5", "rec6"]
    )


def test_append2(tmp_path):
    """TODO check for appending new, empty export"""
