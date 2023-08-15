"""Tests for using the Ledger without an already existing Ledger."""
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from ledgercli.main import Ledger


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Creates an output dir for storing output."""
    o = tmp_path / "output_dir"
    o.mkdir()
    return o


@pytest.fixture
def export_path() -> Path:
    """Returns an export path."""
    return Path("tests/dkb_sample.csv")


def test_initialisation(output_dir: Path, export_path: Path) -> None:
    """Tests if the ledger gets initialised correctly."""
    # valid input
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    assert ledger.output_dir == output_dir
    assert ledger.bank_fmt == "dkb"
    assert ledger.tx.empty
    assert ledger.tx_c.empty
    assert ledger.tx_d.empty
    assert ledger.history.empty
    assert ledger.metadata.empty
    assert ledger.mapping.empty

    # non existing output_dir defaults to cwd
    ledger = Ledger(output_dir=(output_dir / "not-existing"), bank_fmt="dkb")
    assert ledger.output_dir == Path.cwd()

    # bank not supported
    with pytest.raises(Exception) as exc_info:
        ledger = Ledger(output_dir=output_dir, bank_fmt="not-supported")
    assert str(exc_info.value) == "'Please supply a valid BANK_FMT!'"

    # init without bank, no metadata fallback
    with pytest.raises(Exception) as exc_info:
        ledger = Ledger(output_dir, bank_fmt=None)
    assert str(exc_info.value) == "Please supply a valid BANK_FMT! Couldn't read BANK_FMT from metadata."

    # init without bank, fallback to metadata
    ledger = Ledger(output_dir, bank_fmt="dkb")
    ledger.update(export_path)
    ledger.write()

    assert ledger.metadata.empty is False
    assert ledger.metadata["bank"].iloc[0] == "dkb"
    assert (output_dir / "metadata.csv").exists()

    ledger = Ledger(output_dir, bank_fmt=None)
    assert ledger.metadata["bank"].iloc[0] == "dkb"


def test_init_tx(output_dir: Path, export_path: Path) -> None:
    """Tests if transactions get read."""
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    ledger._init_tx(export_path=export_path)
    assert ledger.tx.empty is False


def test_init_metadata(output_dir: Path, export_path: Path) -> None:
    """Tests for metadata generation."""
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    ledger._init_tx(export_path=export_path)
    ledger._init_metadata(export_path=export_path)
    assert set(ledger.metadata["starting_balance"]) == {0}
    assert set(ledger.metadata["bank"]) == {"dkb"}


def test_init_mapping(output_dir: Path, export_path: Path) -> None:
    """Tests for mapping generation."""
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    ledger._init_tx(export_path=export_path)
    ledger._init_metadata(export_path=export_path)
    ledger._update_mapping()

    assert set(ledger.mapping["recipient"]) == {"Test"}
    assert set(ledger.mapping["occurence"]) == {0}
    assert ledger.mapping["label1"].isna().sum() == 1
    assert ledger.mapping["label2"].isna().sum() == 1
    assert ledger.mapping["label3"].isna().sum() == 1
    assert ledger.mapping["recipient_clean"].isna().sum() == 1


def test_update_tx_mapping(output_dir: Path, export_path: Path) -> None:
    """Tests if updating transactions with mapping is done correctly."""
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    ledger._init_tx(export_path=export_path)
    ledger._init_metadata(export_path=export_path)
    ledger._update_mapping()

    ledger.mapping = pd.DataFrame(
        {
            "recipient": ["Test"],
            "label1": ["test1"],
            "label2": ["test2"],
            "label3": ["test3"],
            "occurence": [1000],
            "recipient_clean": ["Test_clean"],
        }
    )

    ledger._update_tx_mapping()
    assert set(ledger.tx["recipient"]) == {"Test"}
    assert set(ledger.tx["recipient_clean"]) == {"Test_clean"}
    assert set(ledger.tx["label1"]) == {"test1"}
    assert set(ledger.tx["label2"]) == {"test2"}
    assert set(ledger.tx["label3"]) == {"test3"}
    assert set(ledger.tx["occurence"]) == {1000}


def test_init_history(output_dir: Path, export_path: Path) -> None:
    """Tests if the history is initialised correctly."""
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    ledger._init_tx(export_path)
    ledger._init_metadata(export_path)
    ledger._update_mapping()
    ledger._update_tx_mapping()
    ledger._init_history()

    assert set(ledger.history["date"]) == {datetime(2021, 1, 1)}
    assert set(ledger.history["balance"]) == {1000.01}


def test_init_c(output_dir: Path, export_path: Path) -> None:
    """Tests if coalesced transactions are generated correctly."""
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    ledger._init_tx(export_path)
    ledger._init_metadata(export_path)
    ledger._update_mapping()
    ledger._update_tx_mapping()

    coalesce_stub = pd.DataFrame(
        {
            "date_custom": [pd.to_datetime("1999-01-01")],
            "label1_custom": ["test_custom"],
            "label2_custom": ["test_custom"],
            "label3_custom": ["test_custom"],
            "recipient_clean_custom": ["test_custom"],
            "recipient_clean": ["test_custom"],
            "occurence_custom": [8888],
            "amount_custom": [9999],
        }
    )

    ledger.tx = ledger.tx.drop(columns=coalesce_stub.columns)
    ledger.tx = pd.concat([ledger.tx, coalesce_stub], axis=1, verify_integrity=True)

    ledger._init_tx_c()

    assert set(ledger.tx_c["date"]) == {datetime(1999, 1, 1)}
    assert set(ledger.tx_c["label1"]) == {"test_custom"}
    assert set(ledger.tx_c["label2"]) == {"test_custom"}
    assert set(ledger.tx_c["label3"]) == {"test_custom"}
    assert set(ledger.tx_c["recipient"]) == {"test_custom"}
    assert set(ledger.tx_c["occurence"]) == {8888}
    assert set(ledger.tx_c["amount"]) == {9999}


def test_init_tx_d(output_dir: Path, export_path: Path) -> None:
    """Tests if distributed transactions are generated correctly."""
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    ledger._init_tx(export_path)
    ledger._init_metadata(export_path)
    ledger._update_mapping()
    ledger._update_tx_mapping()

    tmp = pd.to_datetime("2021-06-01")
    distribute_stub = pd.DataFrame(
        {
            "date": [tmp, tmp, tmp],
            "amount": [60, -60, 60],
            "occurence": [2, -2, 0],
        }
    )
    ledger.tx = ledger.tx.drop(columns=distribute_stub.columns)
    ledger.tx = pd.concat([ledger.tx, distribute_stub], axis=1, verify_integrity=True)

    ledger._init_tx_c()
    ledger._init_tx_d()

    assert ledger.tx_d.shape[0] == 5
    assert set(ledger.tx_d["date"]) == {
        datetime(2021, 6, 1),
        datetime(2021, 5, 1),
        datetime(2021, 7, 1),
    }
    assert set(ledger.tx_d["amount"]) == {30, -30, 60}


def test_write(output_dir: Path, export_path: Path) -> None:
    """Tests if all tables are written."""
    ledger = Ledger(output_dir=output_dir, bank_fmt="dkb")
    ledger.update(export_path)
    ledger.write()

    for item in [
        "transactions.csv",
        "metadata.csv",
        "mapping.csv",
        "tx_coalesced.csv",
        "tx_distributed.csv",
    ]:
        tmp = output_dir / item
        assert tmp.exists()


def test_update(output_dir: Path, export_path: Path) -> None:
    """Tests for updating existing files."""
    # setup existing files
    ledger = Ledger(output_dir, bank_fmt="dkb")
    ledger.update(export_path)
    ledger.write()

    ledger = Ledger(output_dir, bank_fmt="dkb")

    assert ledger.tx.shape == (1, 15)
    assert ledger.mapping.empty is False
    assert ledger.metadata.empty is False

    # adding more transactions
    ledger.update(export_path)
    ledger.update(export_path)
    assert ledger.tx.shape == (3, 15)

    # update without new export
    ledger.update()
    assert ledger.tx.shape == (3, 15)
