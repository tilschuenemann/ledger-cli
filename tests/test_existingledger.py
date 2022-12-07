"""Tests for using Ledger when a structure already exists."""
from ledgercli.main import Ledger
from pathlib import Path
import pytest


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    o = tmp_path / "output_dir"
    o.mkdir()
    return o


@pytest.fixture
def export_path() -> Path:
    return Path("tests/dkb_sample.csv")


def test_update(output_dir: Path, export_path: Path) -> None:
    # setup existing files
    l = Ledger(output_dir, bank_type="dkb")
    l.update(export_path)
    l.write()

    l = Ledger(output_dir, bank_type="dkb")

    assert l.tx.shape == (1, 20)
    assert l.mapping.empty is False
    assert l.metadata.empty is False

    # adding more transactions
    l.update(export_path)
    l.update(export_path)
    assert l.tx.shape == (3, 20)

    # update without new export
    l.update()
    assert l.tx.shape == (3, 20)


def test_metadata(output_dir: Path, export_path: Path) -> None:
    # init without bank_type
    with pytest.raises(Exception) as exc_info:
        l = Ledger(output_dir, bank_type=None)
    assert str(exc_info.value) == "Please supply a valid BANK_TYPE! Couldn't read BANK_TYPE from metadata."

    # setup existing files
    l = Ledger(output_dir, bank_type="dkb")
    l.update(export_path)
    l.write()

    assert l.metadata.empty is False
    assert l.metadata["bank_format"].iloc[0] == "dkb"
    assert (output_dir / "metadata.csv").exists()

    # init with bank_type
    l = Ledger(output_dir, bank_type=None)
    assert l.metadata["bank_format"].iloc[0] == "dkb"
