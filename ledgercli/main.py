import pandas as pd

import argparse
import pathlib
import os

import ledgercli.ledger


def main() -> None:
    parser = argparse.ArgumentParser(prog="ledger-cli")
    parser.add_argument(dest="output_path", type=pathlib.Path, required=False, nargs=1)
    parser.add_argument(dest="export_path", type=pathlib.Path, required=False, nargs=1)
    parser.add_argument(dest="bank_format", type=str, required=False, nargs=1)
    args = parser.parse_args()
    output_path = args.output_path[0]
    export_path = args.export_path[0]
    bank_format = args.bank_format[0]

    if output_path is None:
        output_path = pathlib.Path(os.getcwd())
    elif output_path.isdir() is False:
        print("provided output_folder is a file. please provide a folder!")

    if bank_format is None:
        metadata_path = output_path / "metadata.csv"
        bank_format = pd.read_csv(metadata_path)["bank_format"].iloc[0]

    ledger.ledger.Ledger(output_path, export_path, bank_format)


if __name__ == "__main__":
    main()
