"""Tests for tmdbasyncmovies CLI."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from ledgercli.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create temporary directory."""
    d = tmp_path / "output_dir"
    d.mkdir()
    return d


def test_import(runner: CliRunner, output_dir: Path) -> None:
    """Test CLI import function."""
    result = runner.invoke(
        cli,
        [
            "import",
            "-b",
            "dkb",
            "-o",
            str(output_dir),
            "-e",
            str(Path("tests/dkb_sample.csv")),
        ],
    )
    assert result.exit_code == 0
    assert result.exception is None

    for f in ["transactions.csv", "metadata.csv", "mapping.csv"]:
        assert (output_dir / f).exists()


def test_update(runner: CliRunner, output_dir: Path) -> None:
    """Test CLI update function."""
    result = runner.invoke(
        cli,
        [
            "import",
            "-b",
            "dkb",
            "-o",
            str(output_dir),
            "-e",
            str(Path("tests/dkb_sample.csv")),
        ],
    )
    result = runner.invoke(
        cli,
        [
            "update",
            "-b",
            "dkb",
            "-o",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0
    assert result.exception is None
