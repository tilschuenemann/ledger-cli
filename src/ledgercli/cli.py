"""CLI for using the Ledger."""
from collections.abc import Callable
from pathlib import Path
from typing import Any

import click

from ledgercli.bankinterface import BankInterface
from ledgercli.main import Ledger


@click.group()
def cli() -> None:
    """CLI Utility for Ledger."""
    pass


def common_options(function: Callable[..., Any]) -> Callable[..., Any]:
    """Reuse common options."""
    function = click.option(
        "-o",
        "--output-dir",
        type=click.Path(
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            path_type=Path,
        ),
        default=Path.cwd(),
        help="Specify a directory where output will get written to. Defaults to current working dir.",
    )(function)
    function = click.option(
        "-b",
        "--bank_fmt",
        type=click.Choice(BankInterface().list_bank_fmts()),
        nargs=1,
        help="Specify from which bank your export is from. If none is specified, bank_fmt falls back to its specification in metadata.csv in output_dir.",
    )(function)
    return function


@cli.command("update")
@common_options
def update_mp(output_dir: Path, bank_fmt: str | None) -> None:
    """Updates the Ledger."""
    ledger = Ledger(output_dir=output_dir, bank_fmt=bank_fmt)
    ledger.update(export_path=None)
    ledger.write()


@cli.command("import")
@common_options
@click.option(
    "-e",
    "--export_path",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        path_type=Path,
    ),
    default=None,
    help="Specify a path to an export in order to add new transactions to your ledger. If left empty, ledger will just update.",
)
def import_tx(output_dir: Path, export_path: Path, bank_fmt: str | None) -> None:
    """Imports transactions and updates the Ledger."""
    ledger = Ledger(output_dir=output_dir, bank_fmt=bank_fmt)
    ledger.update(export_path=export_path)
    ledger.write()
