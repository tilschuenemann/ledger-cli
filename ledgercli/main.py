import pandas as pd

import argparse
import pathlib
import os
import traceback

from ledgercli.ledger import Ledger
from ledgercli.bankformat import BankFormat


def main() -> None:
    parser = argparse.ArgumentParser(prog="ledgercli")
    subparsers = parser.add_subparsers(dest="cmd")

    bankformat = subparsers.add_parser(
        "list-formats",
        help="list available bank formats for importing",
    )

    update = subparsers.add_parser("update", help="update ledger and append exports")
    update.add_argument(
        "--output_path",
        dest="output_path",
        help="path to your ledger directory. defaults to current directory.",
        type=pathlib.Path,
        nargs=1,
    )
    update.add_argument("--export_path", dest="export_path", help="path to your export", type=pathlib.Path, nargs=1)
    update.add_argument(
        "--bank_format",
        dest="bank_format",
        help="export bank format",
        type=str,
        nargs=1,
        choices=BankFormat().bank_formats,
    )

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
    elif args.cmd == "list-formats":
        BankFormat().list_bank_formats()
    elif args.cmd == "update":
        if args.output_path is None:
            output_path = pathlib.Path(os.getcwd())
            print(f"output_path set to {output_path}")
        elif args.output_path is not None and args.output_path.is_dir() is False:
            exit("please provide a directory for output_path!")
        else:
            output_path = args.output_path

        l = Ledger(output_path)

        if args.bank_format is None:
            try:
                metadata_path = output_path / "metadata.csv"
                bank_format = pd.read_csv(metadata_path)["bank_format"].iloc[0]
            except:
                print("an error occurred while trying to guess your bank_format:")
                traceback.print_exc()
                exit()

        if args.export_path is None:
            l.update()
        elif args.export_path is not None and args.bank_format is not None:
            l.update(args.export_path[0], args.bank_format[0])

        l.write()


if __name__ == "__main__":
    main()
