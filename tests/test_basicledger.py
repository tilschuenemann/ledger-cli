import pytest
from ledgercli.main import Ledger
from pathlib import Path
import pandas as pd
from datetime import datetime
import numpy as np


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    o = tmp_path / "output_dir"
    o.mkdir()
    return o


@pytest.fixture
def export_path() -> Path:
    return Path("tests/dkb_sample.csv")


@pytest.fixture
def mapping_stub() -> pd.DataFrame:
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
    tmp = pd.to_datetime("2021-06-01")
    return pd.DataFrame(
        {
            "date": [tmp, tmp, tmp],
            "amount": [60, -60, 60],
            "occurence": [2, -2, 0],

        }
    )


def test_initialisation(output_dir: Path) -> None:
    # valid input
    l = Ledger(output_dir=output_dir, bank_type="dkb")
    assert l.output_dir == output_dir
    assert l.bank_type == "dkb"

    # non existing output_dir defaults to cwd
    l = Ledger(output_dir=(output_dir / "not-existing"), bank_type="dkb")
    assert l.output_dir == Path.cwd()

    # bank_type not supported
    with pytest.raises(Exception) as exc_info:
        l = Ledger(output_dir=output_dir, bank_type="not-supported")
    assert str(exc_info.value) == "The bank_format you provided is not supported."


def test_init_tx(output_dir: Path, export_path: Path) -> None:
    l = Ledger(output_dir=output_dir, bank_type="dkb")
    assert l.tx.empty

    l.init_tx(export_path=export_path)
    assert l.tx.empty is False


def test_init_metadata(output_dir: Path, export_path: Path) -> None:
    l = Ledger(output_dir=output_dir, bank_type="dkb")
    assert l.metadata.empty

    l.init_tx(export_path=export_path)
    l.init_metadata(export_path=export_path)
    assert set(l.metadata["starting_balance"]) == set([0])
    assert set(l.metadata["bank_format"]) == set(["dkb"])


def test_init_mapping(output_dir: Path, export_path: Path) -> None:
    l = Ledger(output_dir=output_dir, bank_type="dkb")
    assert l.mapping.empty

    l.init_tx(export_path=export_path)
    l.init_metadata(export_path=export_path)
    l.update_mapping()

    assert set(l.mapping["recipient"]) == set(["Test"])
    assert l.mapping["label1"].isnull().sum() == 1
    assert l.mapping["label2"].isnull().sum() == 1
    assert l.mapping["label3"].isnull().sum() == 1
    assert l.mapping["recipient_clean"].isnull().sum() == 1
    assert l.mapping["occurence"].isnull().sum() == 1


def test_update_tx_mapping(
    output_dir: Path, export_path: Path, mapping_stub: pd.DataFrame
) -> None:
    l = Ledger(output_dir=output_dir, bank_type="dkb")

    l.init_tx(export_path=export_path)
    l.init_metadata(export_path=export_path)
    l.update_mapping()

    l.mapping = mapping_stub

    l.update_tx_mapping()
    assert set(l.tx["recipient"]) == set(["Test"])
    assert set(l.tx["recipient_clean"]) == set(["Test_clean"])
    assert set(l.tx["label1"]) == set(["test1"])
    assert set(l.tx["label2"]) == set(["test2"])
    assert set(l.tx["label3"]) == set(["test3"])
    assert set(l.tx["occurence"]) == set([1000])


def test_init_history(output_dir: Path, export_path: Path, coalesce_stub: pd.DataFrame) -> None:
    l = Ledger(output_dir=output_dir, bank_type="dkb")
    l.init_tx(export_path)
    l.init_metadata(export_path)
    l.update_mapping()
    l.update_tx_mapping()
    l.init_history()

    assert set(l.history["date"]) == set([datetime(2021, 1, 1)])
    assert set(l.history["balance"]) == set([1000.01])


def test_init_c(output_dir: Path, export_path: Path, coalesce_stub: pd.DataFrame) -> None:
    l = Ledger(output_dir=output_dir, bank_type="dkb")
    l.init_tx(export_path)
    l.init_metadata(export_path)
    l.update_mapping()
    l.update_tx_mapping()

    l.tx = l.tx.drop(columns=coalesce_stub.columns)
    l.tx = pd.concat([l.tx, coalesce_stub], axis=1, verify_integrity=True)

    l.init_tx_c()

    assert set(l.tx_c["date"]) == set([datetime(1999, 1, 1)])
    assert set(l.tx_c["label1"]) == set(["test_custom"])
    assert set(l.tx_c["label2"]) == set(["test_custom"])
    assert set(l.tx_c["label3"]) == set(["test_custom"])
    assert set(l.tx_c["recipient"]) == set(["test_custom"])
    assert set(l.tx_c["occurence"]) == set([8888])
    assert set(l.tx_c["amount"]) == set([9999])


def test_init_tx_d(output_dir: Path, export_path: Path, distribute_stub: pd.DataFrame) -> None:
    l = Ledger(output_dir=output_dir, bank_type="dkb")
    l.init_tx(export_path)
    l.init_metadata(export_path)
    l.update_mapping()
    l.update_tx_mapping()

    l.tx = l.tx.drop(columns=distribute_stub.columns)
    l.tx = pd.concat([l.tx, distribute_stub], axis=1, verify_integrity=True)

    l.init_tx_c()
    l.init_tx_d()

    assert l.tx_d.shape[0] == 5
    assert set(l.tx_d["date"]) == set(
        [datetime(2021, 6, 1), datetime(2021, 5, 1), datetime(2021, 7, 1)])
    assert set(l.tx_d["amount"]) == set([30, -30, 60])


def test_write(output_dir: Path, export_path: Path) -> None:
    l = Ledger(output_dir=output_dir, bank_type="dkb")
    l.update(export_path)
    l.write()

    for item in ["transactions.csv", "metadata.csv", "mapping.csv", "tx_c.csv", "tx_d.csv"]:
        tmp = output_dir / item
        assert tmp.exists()
