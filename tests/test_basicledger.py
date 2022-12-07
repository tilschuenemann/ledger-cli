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


@pytest.fixture
def mapping_stub() -> pd.DataFrame:
    """Creates a mapping stub."""
    return pd.DataFrame(
        {
            "recipient": ["Test"],
            "label1": ["test1"],
            "label2": ["test2"],
            "label3": ["test3"],
            "occurence": [1000],
            "recipient_clean": ["Test_clean"],
        }
    )


@pytest.fixture
def coalesce_stub() -> pd.DataFrame:
    """Creates a stub for coalescing."""
    tmp = pd.to_datetime("1999-01-01")
    return pd.DataFrame(
        {
            "date_custom": [tmp],
            "amount_custom": [9999],
            "recipient_clean_custom": ["test_custom"],
            "occurence_custom": [8888],
            "label1_custom": ["test_custom"],
            "label2_custom": ["test_custom"],
            "label3_custom": ["test_custom"],
            "recipient_clean": ["test_custom"],
        }
    )


@pytest.fixture
def distribute_stub() -> pd.DataFrame:
    """Creates a stub for distribution."""
    tmp = pd.to_datetime("2021-06-01")
    return pd.DataFrame(
        {
            "date": [tmp, tmp, tmp],
            "amount": [60, -60, 60],
            "occurence": [2, -2, 0],
        }
    )


def test_initialisation(output_dir: Path) -> None:
    """Tests if the ledger gets initialised correctly."""
    # valid input
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")
    assert ledger.output_dir == output_dir
    assert ledger.bank_type == "dkb"

    # non existing output_dir defaults to cwd
    ledger = Ledger(output_dir=(output_dir / "not-existing"), bank_type="dkb")
    assert ledger.output_dir == Path.cwd()

    # bank_type not supported
    with pytest.raises(Exception) as exc_info:
        ledger = Ledger(output_dir=output_dir, bank_type="not-supported")
    assert str(exc_info.value) == "The bank_format you provided is not supported."


def test_init_tx(output_dir: Path, export_path: Path) -> None:
    """Tests if transactions get read."""
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")
    assert ledger.tx.empty

    ledger.init_tx(export_path=export_path)
    assert ledger.tx.empty is False


def test_init_metadata(output_dir: Path, export_path: Path) -> None:
    """Tests for metadata generation."""
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")
    assert ledger.metadata.empty

    ledger.init_tx(export_path=export_path)
    ledger.init_metadata(export_path=export_path)
    assert set(ledger.metadata["starting_balance"]) == {0}
    assert set(ledger.metadata["bank_format"]) == {"dkb"}


def test_init_mapping(output_dir: Path, export_path: Path) -> None:
    """Tests for mapping generation."""
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")
    assert ledger.mapping.empty

    ledger.init_tx(export_path=export_path)
    ledger.init_metadata(export_path=export_path)
    ledger.update_mapping()

    assert set(ledger.mapping["recipient"]) == {"Test"}
    assert ledger.mapping["label1"].isnull().sum() == 1
    assert ledger.mapping["label2"].isnull().sum() == 1
    assert ledger.mapping["label3"].isnull().sum() == 1
    assert ledger.mapping["recipient_clean"].isnull().sum() == 1
    assert ledger.mapping["occurence"].isnull().sum() == 1


def test_update_tx_mapping(
    output_dir: Path, export_path: Path, mapping_stub: pd.DataFrame
) -> None:
    """Tests if updating transactions with mapping is done correctly."""
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")

    ledger.init_tx(export_path=export_path)
    ledger.init_metadata(export_path=export_path)
    ledger.update_mapping()

    ledger.mapping = mapping_stub

    ledger.update_tx_mapping()
    assert set(ledger.tx["recipient"]) == {"Test"}
    assert set(ledger.tx["recipient_clean"]) == {"Test_clean"}
    assert set(ledger.tx["label1"]) == {"test1"}
    assert set(ledger.tx["label2"]) == {"test2"}
    assert set(ledger.tx["label3"]) == {"test3"}
    assert set(ledger.tx["occurence"]) == {1000}


def test_init_history(
    output_dir: Path, export_path: Path, coalesce_stub: pd.DataFrame
) -> None:
    """Tests if the history is initialised correctly."""
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")
    ledger.init_tx(export_path)
    ledger.init_metadata(export_path)
    ledger.update_mapping()
    ledger.update_tx_mapping()
    ledger.init_history()

    assert set(ledger.history["date"]) == {datetime(2021, 1, 1)}
    assert set(ledger.history["balance"]) == {1000.01}


def test_init_c(
    output_dir: Path, export_path: Path, coalesce_stub: pd.DataFrame
) -> None:
    """Tests if coalesced transactions are generated correctly."""
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")
    ledger.init_tx(export_path)
    ledger.init_metadata(export_path)
    ledger.update_mapping()
    ledger.update_tx_mapping()

    ledger.tx = ledger.tx.drop(columns=coalesce_stub.columns)
    ledger.tx = pd.concat([ledger.tx, coalesce_stub], axis=1, verify_integrity=True)

    ledger.init_tx_c()

    assert set(ledger.tx_c["date"]) == {datetime(1999, 1, 1)}
    assert set(ledger.tx_c["label1"]) == {"test_custom"}
    assert set(ledger.tx_c["label2"]) == {"test_custom"}
    assert set(ledger.tx_c["label3"]) == {"test_custom"}
    assert set(ledger.tx_c["recipient"]) == {"test_custom"}
    assert set(ledger.tx_c["occurence"]) == {8888}
    assert set(ledger.tx_c["amount"]) == {9999}


def test_init_tx_d(
    output_dir: Path, export_path: Path, distribute_stub: pd.DataFrame
) -> None:
    """Tests if distributed transactions are generated correctly."""
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")
    ledger.init_tx(export_path)
    ledger.init_metadata(export_path)
    ledger.update_mapping()
    ledger.update_tx_mapping()

    ledger.tx = ledger.tx.drop(columns=distribute_stub.columns)
    ledger.tx = pd.concat([ledger.tx, distribute_stub], axis=1, verify_integrity=True)

    ledger.init_tx_c()
    ledger.init_tx_d()

    assert ledger.tx_d.shape[0] == 5
    assert set(ledger.tx_d["date"]) == {
        datetime(2021, 6, 1),
        datetime(2021, 5, 1),
        datetime(2021, 7, 1),
    }
    assert set(ledger.tx_d["amount"]) == {30, -30, 60}


def test_write(output_dir: Path, export_path: Path) -> None:
    """Tests if all tables are written."""
    ledger = Ledger(output_dir=output_dir, bank_type="dkb")
    ledger.update(export_path)
    ledger.write()

    for item in [
        "transactions.csv",
        "metadata.csv",
        "mapping.csv",
        "tx_c.csv",
        "tx_d.csv",
    ]:
        tmp = output_dir / item
        assert tmp.exists()
