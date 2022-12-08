"""Tests for using Ledger when a structure already exists."""
from pathlib import Path

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


def test_update(output_dir: Path, export_path: Path) -> None:
    """Tests for updating existing files."""
    # setup existing files
    ledger = Ledger(output_dir, bank_type="dkb")
    ledger.update(export_path)
    ledger.write()

    ledger = Ledger(output_dir, bank_type="dkb")

    assert ledger.tx.shape == (1, 20)
    assert ledger.mapping.empty is False
    assert ledger.metadata.empty is False

    # adding more transactions
    ledger.update(export_path)
    ledger.update(export_path)
    assert ledger.tx.shape == (3, 20)

    # update without new export
    ledger.update()
    assert ledger.tx.shape == (3, 20)


def test_metadata(output_dir: Path, export_path: Path) -> None:
    """Tests for falling back to existing metadata."""
    # init without bank_type
    with pytest.raises(Exception) as exc_info:
        ledger = Ledger(output_dir, bank_type=None)
    assert (
        str(exc_info.value)
        == "Please supply a valid BANK_TYPE! Couldn't read BANK_TYPE from metadata."
    )

    # setup existing files
    ledger = Ledger(output_dir, bank_type="dkb")
    ledger.update(export_path)
    ledger.write()

    assert ledger.metadata.empty is False
    assert ledger.metadata["bank_format"].iloc[0] == "dkb"
    assert (output_dir / "metadata.csv").exists()

    # init with bank_type
    ledger = Ledger(output_dir, bank_type=None)
    assert ledger.metadata["bank_format"].iloc[0] == "dkb"
