import click
from click import Context
from pathlib import Path
from ledgercli.bankinterface import BankInterface
from ledgercli.main import Ledger


@click.group()
def cli() -> None:
    pass


@click.command()
@click.option(
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
    help="Specify a directory where output will get written to. Defaults to current working dir."
)
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
    default=Path().cwd(),
    help="Specify a path to an export in order to add new transactions to your ledger. If left empty, ledger will just update."
)
@click.option("-b", "--btype", type=click.Choice(BankInterface().list_bank_formats()), nargs=1, help="Specify from which bank your export is from. If none is specified, bank_format will be read from metadata in output_dir.")
def update(output_dir: Path, export_path: Path | None, btype: str | None) -> None:

    l = Ledger(output_dir=output_dir, bank_type=btype)
    l.update(export_path=export_path)
    l.write()


cli.add_command(update)


if __name__ == "__main__":
    cli()
