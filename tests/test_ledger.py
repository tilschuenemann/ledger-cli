import pytest
from ledger.ledger import Ledger
import pathlib
import datetime
import pandas as pd


@pytest.fixture
def tmp_folder(tmp_path) -> pathlib.Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def empty_ledger(tmp_folder) -> Ledger:
    export_path = pathlib.Path("tests/export_empty.csv")
    return Ledger(tmp_folder, export_path=export_path, bank_format="dkb")


@pytest.fixture
def regular_ledger(tmp_folder) -> Ledger:
    export_path = pathlib.Path("tests/export_regular.csv")
    return Ledger(tmp_folder, export_path=export_path, bank_format="dkb")


def test_init_ledger_nosetup(tmp_folder) -> None:
    """No setup provided"""
    Ledger(tmp_folder, export_path=None, bank_format="dkb")


def test_init_ledger_emptyexport(empty_ledger, tmp_folder) -> None:
    """Empty export is provided"""
    maptab = tmp_folder / "mappingtable.csv"
    ledger = tmp_folder / "ledger.csv"
    metadata = tmp_folder / "metadata.csv"

    assert maptab.exists()
    assert ledger.exists()
    assert metadata.exists()


def test_init_ledger_valid(regular_ledger, tmp_folder) -> None:
    """Valid export is provided"""
    l = regular_ledger

    maptab = tmp_folder / "mappingtable.csv"
    ledger = tmp_folder / "ledger.csv"
    metadata = tmp_folder / "metadata.csv"
    assert maptab.exists()
    assert ledger.exists()
    assert metadata.exists()

    assert l.mappings.shape == (3, 6)
    assert l.transactions.shape == (3, 15)
    assert l.metadata.shape == (1, 2)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.transactions["amount"].sum() == 1
    assert set(l.transactions["recipient"]) == set(["rec1", "rec2", "rec3"])
    # assert l.transactions["date"].unique() == []
    assert l.transactions.isna().sum().sum() == 3 * 12


def test_mappingtable_keeporphans(regular_ledger, tmp_folder) -> None:
    """Mappings exist after recipients are removed from ledger."""

    # TODO rename l & ll
    l = regular_ledger
    l.transactions = l.transactions.reindex().drop(index=0)
    l._write("ledger.csv", tmp_folder)

    appendage_path = pathlib.Path("tests/appendage_regular.csv")
    ll = Ledger(tmp_folder, appendage_path, bank_format="dkb")
    assert ll.mappings.shape == (6, 6)
    assert set(ll.mappings["recipient"]) == set(
        ["rec1", "rec2", "rec3", "rec4", "rec5", "rec6"]
    )
    assert "rec1" not in ll.transactions["recipient"].values


def test_append1(regular_ledger, tmp_folder) -> None:
    appendage_path = pathlib.Path("tests/appendage_regular.csv")
    l = Ledger(tmp_folder, export_path=appendage_path, bank_format="dkb")

    maptab = tmp_folder / "mappingtable.csv"
    ledger = tmp_folder / "ledger.csv"
    metadata = tmp_folder / "metadata.csv"

    assert maptab.exists()
    assert ledger.exists()
    assert metadata.exists()

    assert l.mappings.shape == (6, 6)
    assert l.transactions.shape == (6, 15)
    assert l.metadata.shape == (1, 2)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.transactions["amount"].sum() == 2
    assert set(l.transactions["recipient"]) == set(
        ["rec1", "rec2", "rec3", "rec4", "rec5", "rec6"]
    )


def test_append2(regular_ledger, tmp_folder) -> None:
    """check for appending new, empty export"""
    appendage_path = pathlib.Path("tests/export_empty.csv")
    l = Ledger(tmp_folder, export_path=appendage_path, bank_format="dkb")

    maptab = tmp_folder / "mappingtable.csv"
    ledger = tmp_folder / "ledger.csv"
    metadata = tmp_folder / "metadata.csv"

    assert maptab.exists()
    assert ledger.exists()
    assert metadata.exists()

    assert l.mappings.shape == (3, 6)
    assert l.transactions.shape == (3, 15)
    assert l.metadata.shape == (1, 2)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.transactions["amount"].sum() == 1
    assert set(l.transactions["recipient"]) == set(["rec1", "rec2", "rec3"])


def test_init_history_valid(regular_ledger) -> None:
    """"""
    l = regular_ledger
    l._init_history()
    assert l.history.shape == (2, 3)
    assert set(l.history.columns) == set(["date", "amount", "balance"])
    assert l.history["balance"].sum() == 1995.02


def test_init_history_empty(empty_ledger) -> None:
    """ """
    l = empty_ledger
    l._init_history()
    assert l.history.shape == (0, 3)


def test_init_datecols_empty(empty_ledger) -> None:
    l = empty_ledger
    l._init_datecols()
    assert l.transactions.shape == (0, 19)


def test_init_datecols_valid(regular_ledger) -> None:
    l = regular_ledger
    l._init_datecols()
    assert l.transactions.shape == (3, 19)
    assert l.transactions["week"].iloc[0] == datetime.datetime(2022, 9, 12)
    assert l.transactions["month"].iloc[0] == datetime.datetime(2022, 9, 1)
    assert l.transactions["quarter"].iloc[0] == datetime.datetime(2022, 7, 1)
    assert l.transactions["year"].iloc[0] == datetime.datetime(2022, 1, 1)


def test_coalesce(empty_ledger) -> None:
    l = empty_ledger
    l.transactions = pd.read_csv(
        "tests/ledger.csv", parse_dates=["date", "date_custom"]
    )
    l._coalesce()
    assert l.transactions_coalesced.shape == (5, 7)
    assert set(l.transactions_coalesced.columns) == set(
        [
            "date",
            "amount",
            "recipient",
            "label1",
            "label2",
            "label3",
            "occurence",
        ]
    )
    assert l.transactions_coalesced["date"].iloc[0] == datetime.datetime(2022, 12, 1)
    assert l.transactions_coalesced["amount"].iloc[0] == 4.0
    assert l.transactions_coalesced["recipient"].iloc[0] == "rec_clean"
    assert l.transactions_coalesced["label1"].iloc[0] == "lab1"
    assert l.transactions_coalesced["label2"].iloc[0] == "lab2"
    assert l.transactions_coalesced["label3"].iloc[0] == "lab3"
    assert l.transactions_coalesced["occurence"].iloc[0] == 1


def test_coalesce_special(regular_ledger) -> None:
    """Correct special coalescing."""
    l = regular_ledger
    l.transactions = pd.read_csv(
        "tests/ledger.csv", parse_dates=["date", "date_custom"]
    )
    l._coalesce()
    assert l.transactions_coalesced["date"].iloc[4] == datetime.datetime(2022, 1, 2)
    assert l.transactions_coalesced["amount"].iloc[4] == 0.0
    assert l.transactions_coalesced["occurence"].iloc[4] == 1


def test_distribute(empty_ledger) -> None:

    l = empty_ledger
    l.transactions = pd.read_csv(
        "tests/ledger.csv", parse_dates=["date", "date_custom"]
    )
    l._coalesce()
    l._init_distributed_ledger()

    df = l.transactions_distributed

    non_repeating = df[df["recipient"] == "rec_clean"]
    assert non_repeating.shape == (1, 7)
    assert non_repeating["amount"].iloc[0] == 4.0

    repeat_future = df[df["recipient"] == "rec2"]
    assert repeat_future.shape == (2, 7)
    assert repeat_future["date"].iloc[0] == datetime.datetime(2021, 1, 1)
    assert repeat_future["date"].iloc[1] == datetime.datetime(2021, 2, 1)
    assert repeat_future["amount"].iloc[0] == 2.5
    assert repeat_future["amount"].iloc[1] == 2.5

    repeat_past = df[df["recipient"] == "rec3"]
    assert repeat_past.shape == (2, 7)
    assert repeat_past["date"].iloc[0] == datetime.datetime(2022, 11, 1)
    assert repeat_past["date"].iloc[1] == datetime.datetime(2022, 12, 1)
    assert repeat_past["amount"].iloc[0] == 2.5
    assert repeat_past["amount"].iloc[1] == 2.5

    repeat_keep = df[df["recipient"] == "rec1"]
    assert repeat_keep.shape == (1, 7)
    assert repeat_keep["date"].iloc[0] == datetime.datetime(2022, 2, 1)
    assert repeat_keep["amount"].iloc[0] == 5

    # TODO test special: empty
