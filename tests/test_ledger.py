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
    export_path = pathlib.Path("tests/bank_exports/dkb_export_empty.csv")
    l = Ledger(tmp_folder, export_path=export_path, bank_format="dkb")
    return l


@pytest.fixture
def ledger_regular_export(tmp_folder) -> Ledger:
    """Creates Ledger object with regular export."""
    export_path = pathlib.Path("tests/bank_exports/dkb_export_regular.csv")
    l = Ledger(tmp_folder, export_path=export_path, bank_format="dkb")
    return l


@pytest.fixture
def empty_ledger(tmp_folder) -> Ledger:
    """Creates empty Ledger object."""
    l = Ledger(tmp_folder)

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


def test_update_multiple(ledger_regular_export, tmp_folder) -> None:
    l = ledger_regular_export
    assert l.transactions.shape == (3, 19)

    # just updating should keep the same amount of rows
    for i in range(1, 4):
        l.update()
        assert l.transactions.shape == (3, 19)
        assert l.mappings.shape == (3, 6)
        assert l.metadata.shape == (1, 2)
        assert l.transactions.isna().sum().sum() == 3 * 12

    # append and update with export
    for i in range(1, 3):
        export_path = pathlib.Path("tests/bank_exports/dkb_export_regular.csv")
        l.update(export_path=export_path, bank_format="dkb")
        assert l.transactions.shape == (3 + 3 * i, 19)
        assert l.mappings.shape == (3, 6)
        assert l.metadata.shape == (1, 2)
        assert l.transactions.isna().sum().sum() == (3 + 3 * i) * 12


def test_update_regular_appendage(ledger_regular_export):
    l = ledger_regular_export
    appendage_path = pathlib.Path("tests/appendage_regular.csv")
    l.update(appendage_path, "dkb")
    assert l.mappings.shape == (6, 6)
    assert l.transactions.shape == (6, 19)
    assert l.metadata.shape == (1, 2)

    assert l.metadata["starting_balance"].iloc[0] == 999.01
    assert l.transactions["amount"].sum() == 2
    assert set(l.transactions["recipient"]) == set(["rec1", "rec2", "rec3", "rec4", "rec5", "rec6"])


def test_update_empty_appendage(ledger_regular_export):
    l = ledger_regular_export
    appendage_path = pathlib.Path("tests/export_empty.csv")
    l.update(export_path=appendage_path, bank_format="dkb")

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
    l.transactions = pd.read_csv("tests/ledger_coalesce.csv", parse_dates=["date", "date_custom"])
    l.init_coalesced_ledger()

    assert l.transactions_coalesced.shape == (3, 7)
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

    # check that original values dont get overwritten incase of no coalesce
    assert l.transactions_coalesced["amount"].iloc[0] == 5.0
    assert l.transactions_coalesced["date"].iloc[0] == datetime.datetime(2022, 9, 16)
    assert l.transactions_coalesced["recipient"].iloc[0] == "rec0"

    # assert l.transactions_coalesced["recipient"].iloc[0] == "rec0"
    assert l.transactions_coalesced["label1"].iloc[0] == "lab1"
    assert l.transactions_coalesced["label2"].iloc[0] == "lab2"
    assert l.transactions_coalesced["label3"].iloc[0] == "lab3"
    assert l.transactions_coalesced["occurence"].iloc[0] == 0

    # check that if coalesce happens the correct values are used
    assert l.transactions_coalesced["amount"].iloc[1] == 4.0
    assert l.transactions_coalesced["date"].iloc[1] == datetime.datetime(2022, 12, 1)
    assert l.transactions_coalesced["recipient"].iloc[1] == "rec_cleancustom"
    assert l.transactions_coalesced["label1"].iloc[1] == "lab1custom"
    assert l.transactions_coalesced["label2"].iloc[1] == "lab2custom"
    assert l.transactions_coalesced["label3"].iloc[1] == "lab3custom"
    assert l.transactions_coalesced["occurence"].iloc[1] == 1

    # check that amount can be coalesced with 0
    assert l.transactions_coalesced["amount"].iloc[2] == 0


def test_distribute(ledger_empty_export) -> None:
    """ """
    l = ledger_empty_export

    l.transactions = pd.read_csv("tests/ledger_distribute.csv", parse_dates=["date", "date_custom"])
    l.init_coalesced_ledger()
    l.init_distributed_ledger()
    df = l.transactions_distributed.copy()

    no_repeat = df[df["recipient"].isin(["rec0", "rec1", "rec2"])].copy()
    repeat_forward = df[df["recipient"] == "rec3"].copy()
    repeat_backward = df[df["recipient"] == "rec4"].copy()

    # check for correct frequency of rows
    assert no_repeat.shape == (3, 7)
    assert repeat_forward.shape == (2, 7)
    assert repeat_backward.shape == (2, 7)

    # check for correct dates
    assert set(repeat_forward["date"]) == set([datetime.datetime(2022, 6, 1), datetime.datetime(2022, 5, 1)])
    assert set(repeat_backward["date"]) == set([datetime.datetime(2022, 6, 1), datetime.datetime(2022, 7, 1)])
    assert set(no_repeat["date"]) == set([datetime.datetime(2022, 6, 1), datetime.datetime(2022, 6, 15)])

    # check for correct amount
    assert set(repeat_backward["amount"]) == set([2.5])
    assert set(repeat_forward["amount"]) == set([2.5])
    assert set(no_repeat["amount"]) == set([5])
