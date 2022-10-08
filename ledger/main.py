import ledger
import argparse
import pathlib
import os


def main():
    parser = argparse.ArgumentParser(prog="ledger-cli")
    parser.add_argument(dest="output_path", type=pathlib.Path, required=False, nargs=1)
    parser.add_argument(dest="export_path", type=pathlib.Path, required=False, nargs=1)

    args = parser.parse_args()
    if args.output_path[0] is None:
        args.output_path[0] = pathlib.Path(os.getcwd())
    elif args.output_path.isdir() is False:
        print("provided output_folder is a file. please provide a folder!")

    # TODO check export_path is None?
    ledger.ledger.Ledger(args.output_path[0], args.export_path[0])


if __name__ == "__main__":
    main()
