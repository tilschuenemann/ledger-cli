import pytest
from ledgercli.ledger import Ledger
import pathlib
import datetime
import pandas as pd


@pytest.fixture
def tmp_folder(tmp_path) -> pathlib.Path:
    """Creates and returns a temporary folder"""
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def ledger_empty_export(tmp_folder) -> Ledger:
    """Creates Ledger object with empty export."""
    export_path = pathlib.Path("tests/export_empty.csv")
    l = Ledger(tmp_folder, export_path=export_path, bank_format="dkb")
    return l


@pytest.fixture
def ledger_regular_export(tmp_folder) -> Ledger:
    """Creates Ledger object with regular export."""
    export_path = pathlib.Path("tests/export_regular.csv")
    l = Ledger(tmp_folder, export_path=export_path, bank_format="dkb")
    return l


@pytest.fixture
def empty_ledger(tmp_folder) -> Ledger:
    """Creates empty Ledger object."""
    l = Ledger(tmp_folder, export_path=None, bank_format=None)

    assert l.transactions.shape == (0, 19)
    assert l.transactions_coalesced.shape == (0, 7 + 4 + 1)
    assert l.transactions_distributed.shape == (0, 7 + 4 + 1)

    assert l.mappings.shape == (0, 6)
    assert l.history.shape == (0, 3 + 4 + 1)
    assert l.metadata.shape == (0, 2)

    return l


def test_write(ledger_regular_export, ledger_empty_export, empty_ledger, tmp_folder) -> None:
    """Empty and regular ledger should write to disk in any case."""

    write_map = dict({"output1": ledger_regular_export, "output2": ledger_empty_export, "output3": empty_ledger})

    for k, v in write_map.items():
        tmp = tmp_folder / k
        tmp.mkdir()
        v.current_output_dir = tmp
        v.write()

        maptab = tmp / "mappingtable.csv"
        ledger = tmp / "ledger.csv"
        metadata = tmp / "metadata.csv"
        transactions_coalesced = tmp / "transactions_coalesced.csv"
        transactions_distributed = tmp / "transactions_distributed.csv"

        assert maptab.exists()
        assert ledger.exists()
        assert metadata.exists()
        assert transactions_coalesced.exists()
        assert transactions_distributed.exists()


def test_init_ledger_valid(ledger_regular_export, tmp_folder) -> None:
    """Test for correct reading of export."""
    l = ledger_regular_export

    assert l.mappings.shape == (3, 6)
    assert l.transactions.shape == (3, 19)
    assert l.metadata.shape == (1, 2)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.metadata["bank_format"].iloc[0] == "dkb"

    assert l.transactions["amount"].sum() == 1
    assert set(l.transactions["recipient"]) == set(["rec1", "rec2", "rec3"])
    assert set(l.transactions["date"]) == set([datetime.datetime(2022, 9, 16), datetime.datetime(2022, 9, 15)])
    assert l.transactions.isna().sum().sum() == 3 * 12


def test_mappingtable_keeporphans(ledger_regular_export, tmp_folder) -> None:
    """Mappings exist after recipients are removed from ledger."""

    l = ledger_regular_export
    l.transactions = l.transactions.reindex().drop(index=0)
    l.write()

    appendage_path = pathlib.Path("tests/appendage_regular.csv")
    al = Ledger(tmp_folder, appendage_path, bank_format="dkb")

    assert al.mappings.shape == (6, 6)
    assert set(al.mappings["recipient"]) == set(["rec1", "rec2", "rec3", "rec4", "rec5", "rec6"])
    assert "rec1" not in al.transactions["recipient"].values


def test_append1(ledger_regular_export, tmp_folder) -> None:
    ledger_regular_export.write()
    appendage_path = pathlib.Path("tests/appendage_regular.csv")
    l = Ledger(tmp_folder, export_path=appendage_path, bank_format="dkb")
    l.write()

    assert l.mappings.shape == (6, 6)
    assert l.transactions.shape == (6, 19)
    assert l.metadata.shape == (1, 2)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.transactions["amount"].sum() == 2
    assert set(l.transactions["recipient"]) == set(["rec1", "rec2", "rec3", "rec4", "rec5", "rec6"])


def test_append2(ledger_regular_export, tmp_folder) -> None:
    """check for appending new, empty export"""
    ledger_regular_export.write()

    appendage_path = pathlib.Path("tests/export_empty.csv")
    l = Ledger(tmp_folder, export_path=appendage_path, bank_format="dkb")
    l.write()

    assert l.mappings.shape == (3, 6)
    assert l.transactions.shape == (3, 19)
    assert l.metadata.shape == (1, 2)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.transactions["amount"].sum() == 1
    assert set(l.transactions["recipient"]) == set(["rec1", "rec2", "rec3"])


def test_init_history_valid(ledger_regular_export) -> None:
    """
    Checks for correct balances, additional columns.
    TODO check dates for coalesce.
    """
    l = ledger_regular_export
    assert l.history.shape == (2, 8)
    assert set(l.history.columns) == set(["date", "amount", "balance", "year", "month", "quarter", "week", "type"])
    assert l.history["balance"].sum() == 1995.02


def test_init_datecols_valid(ledger_regular_export) -> None:
    l = ledger_regular_export
    l._create_date_columns()
    assert l.transactions.shape == (3, 19)
    assert l.transactions["week"].iloc[0] == datetime.datetime(2022, 9, 12)
    assert l.transactions["month"].iloc[0] == datetime.datetime(2022, 9, 1)
    assert l.transactions["quarter"].iloc[0] == datetime.datetime(2022, 7, 1)
    assert l.transactions["year"].iloc[0] == datetime.datetime(2022, 1, 1)


def test_coalesce(ledger_empty_export) -> None:
    l = ledger_empty_export
    l.transactions = pd.read_csv("tests/ledger.csv", parse_dates=["date", "date_custom"])
    l.init_coalesced_ledger()
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


def test_coalesce_special(ledger_regular_export) -> None:
    """Correct special coalescing.
    date, amount and occurence dont get coalesced with nan
    """
    l = ledger_regular_export
    l.transactions = pd.read_csv("tests/ledger.csv", parse_dates=["date", "date_custom"])
    l.init_coalesced_ledger()
    assert l.transactions_coalesced["date"].iloc[4] == datetime.datetime(2022, 1, 2)
    assert l.transactions_coalesced["amount"].iloc[4] == 0.0
    assert l.transactions_coalesced["occurence"].iloc[4] == 1


def test_distribute(ledger_empty_export) -> None:
    """ """
    l = ledger_empty_export

    l.transactions = pd.read_csv("tests/ledger.csv", parse_dates=["date", "date_custom"])
    l.init_coalesced_ledger()
    l.init_distributed_ledger()

    df = l.transactions_distributed

    # TODO check in a better way for this
    # TODO separate test ledgers
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
