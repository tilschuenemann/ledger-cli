from pathlib import Path
import pandas as pd
import datetime
import csv


class Transaction:
    def __init__(self, 
        amount: float, 
        recipient: str, 
        date: datetime.datetime,
        recipient_clean: str=None,
        label1: str=None,
        label2: str=None,
        label3: str=None,
        occurence: int=None,
        amount_custom: float=0,
        date_custom: datetime.datetime=None,
        recipient_clean_custom: str=None,
        label1_custom: str=None,
        label2_custom: str=None,
        label3_custom: str=None ,
        occurence_custom: int=None,
    ):
        self.amount = amount
        self.recipient = recipient
        self.date = date
        self.recipient_clean = recipient_clean
        self.label1 = label1
        self.label2 = label2
        self.label3 = label3
        self.occurence = occurence
        self.amount_custom = amount_custom
        self.date_custom = date_custom
        self.recipient_clean_custom = recipient_clean_custom
        self.label1_custom = label1_custom
        self.label2_custom = label2_custom
        self.label3_custom = label3_custom
        self.occurence_custom = occurence_custom

    def __iter__(self):
        return iter(
            [
                self.amount,
                self.date,
                self.recipient,
                self.recipient_clean,
                self.label1,
                self.label2,
                self.label3,
                self.occurence,
                self.amount_custom,
                self.date_custom,
                self.recipient_clean_custom,
                self.label1_custom,
                self.label2_custom,
                self.label3_custom,
                self.occurence_custom
            ]
        )


class Mapping:
    def __init__(self, recipient: str,recipient_clean:str=None, label1: str=None,label2: str=None,label3: str=None, occurence: int=0): 
        self.recipient = recipient
        self.recipient_clean = recipient_clean
        self.label1 = label1
        self.label2 = label2
        self.label3 = label3
        self.occurence = occurence

    def __iter__(self):
        return iter(
            [
                self.recipient,
                self.recipient_clean,
                self.label1,
                self.label2,
                self.label3,
                self.occurence,
            ]
        )


class Ledger:
    def write(self, fname: str, output_path: Path, header: list, content, dialect:str="excel"):
        tmp_path = output_path / fname
        if fname!= ".ledger":
            with open(tmp_path, "w") as f:
                writer = csv.writer(f,dialect=dialect)
                writer.writerow(header)
                writer.writerows(content)
        else:
            with open(tmp_path, "w") as f:
                writer = csv.DictWriter(f, ["starting_balance"],dialect=dialect)
                writer.writeheader()
                writer.writerow(self.metadata)


    def write_metadata(self, output_path: Path):
        header = ["starting_balance"]
        self.write(fname=".ledger", output_path=output_path, header=header,content="blub")

    def write_ledger(self, output_path: Path):
        header=        [
                        "amount",
                        "date",
                        "recipient",
                        "recipient_clean",
                        "label1",
                        "label2",
                        "label3",
                        "occurence",
                        "amount_custom",
                        "date_custom",
                        "recipient_clean_custom",
                        "label1_custom",
                        "label2_custom",
                        "label3_custom",
                        "occurence_custom"
                        ]
        self.write(fname="ledger.csv", output_path=output_path, content=self.transactions, header=header)
            

    def write_mappingtable(self, output_path: Path):
        header = [
                "recipient",
                "recipient_clean",
                "label1",
                "label2",
                "label3",
                "occurence",
            ]
        self.write(fname="mappingtable.csv", output_path=output_path, content=self.mappings, header=header)
        
    def append_ledger(self, export: Path):
        pass
        # TODO
        # read old ledger transactions,
        # create set from recipients
        # update maptab
        # read current ledger, add transactions (direction here?)


            
            
    def update_mappings(self):
        # TODO double nested loop not good
        for mapping in self.mappings:
            for transaction in self.transactions:
                if transaction.recipient == mapping.recipient:
                    transaction.recipient_clean = mapping.recipient_clean
                    transaction.label1 = mapping.label1
                    transaction.label2 = mapping.label2
                    transaction.label3 = mapping.label3
                    transaction.occurence = mapping.occurence

    def __init__(self, output_path: Path, export_path: Path=None):
        self.transactions = []
        self.mappings = []
        self.metadata = dict({"starting_balance": 0})

        # create or update ledger
        tmp_ledger = output_path / "ledger.csv"
        if tmp_ledger.exists() is True:
            with open(tmp_ledger) as stream:
                reader = csv.reader(stream,dialect="excel")
                next(reader, None)
                for row in reader:
                    self.transactions.append(Transaction(*row))
        else:
            df = pd.read_csv(
                export_path,
                sep=";",
                decimal=",",
                thousands=".",
                parse_dates=["Buchungstag", "Wertstellung"],
                dayfirst=True,
                encoding="latin1",
                skiprows=6,
            )

            for index, row in df.iterrows():
                tmp_date = row["Buchungstag"]
                tmp_amount = row["Betrag (EUR)"]
                tmp_recipient = row["Auftraggeber / Begünstigter"]
                self.transactions.append(
                    Transaction(amount=tmp_amount, recipient=tmp_recipient, date=tmp_date)
                )
            header = pd.read_csv(
                export_path,
                sep=";",
                decimal=",",
                thousands=".",
                encoding="latin1",
                skiprows=4,
                nrows=1,
                header=None,
            )
            end_balance = float(
                (
                    header.iloc[0, 1]
                    .replace(" EUR", "")
                    .replace(".", "")
                    .replace(",", ".")
                )
            )
            self.metadata["starting_balance"] = end_balance - df["Betrag (EUR)"].sum()

        # create ledger dotfile
        tmp_ldot = output_path / ".ledger"
        if tmp_ldot.exists() is True:
            with open(tmp_ldot) as stream:
                reader = csv.DictReader(stream)
                for row in reader:
                    self.metadata["starting_balance"] = row["starting_balance"]
        else:
            pass

        # create or read mapping table from output dir
        tmp_maptab = output_path / "mappingtable.csv"
        if tmp_maptab.exists() is True:
            with open(tmp_maptab) as stream:
                reader = csv.reader(stream,dialect="excel")
                next(reader, None)
                for row in reader:
                    self.mappings.append(Mapping(*row))
        else:
            for transaction in self.transactions:
                self.mappings.append(Mapping(recipient=transaction.recipient))

        self.update_mappings()
        self.write_ledger(output_path)
        self.write_mappingtable(output_path)
        self.write_metadata(output_path)
