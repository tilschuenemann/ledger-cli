[[_TOC_]]

# ledger-cli

ledger-cli takes your banks csv statements, generates reports in a transparent format
and serves as an interface for data visualisation.

# Installation

```bash
pip install ledgercli
```

# Usage

Creating the initial ledger in the current directory:

```bash
ledgercli export.csv --bank "dkb"
```

Appending newer exports:

```bash
ledgercli appendage.csv
```

Updating mappingtable.csv, rewriting ledger, history.csv, ledger_distributed.csv, ledger_coalesced.csv:

```bash
ledgercli update
```

# Features

### Mapping Table

You're given the ability to provide three different labels, a clean recipient name
and an occurence for each recipient in your ledger:

| recipient       | recipient_clean | label1    | label2 | label3 | occurence |
| --------------- | --------------- | --------- | ------ | ------ | --------- |
| grocerystore+++ | Grocery Store   | Groceries |        |        | 0         |

mappingtable.csv is read and mapped onto the ledger everytime you use the ledger-cli.

### Custom Values and Coalescing

For the majority of the data columns in the ledger.csv there is a "\_custom"-suffixed twin:

| amount | amount_custom | ... |
| ------ | ------------- | --- |
| -50    |               | ... |
| -10    | 5             | ... |

Ledger writes a transactions_coalesced.csv, where every pair is merged. "\_custom"
values take precedence.

Custom values can be provided for these columns:

- amount
- date
- recipient_clean
- label1
- label2
- label3
- occurence

### Support for different providers

Ledger works with a simple base format (date, amount and recipient column) and
can be adapted to read exports from other providers than DKB too.

Currently available providers:

- DKB

[Feel free to create a pull request!](ww.google.de)

### Distribution of frequent events

Certain transactions occur once every now and then and might dilute meaningful interpretation, eg. an insurance bill only at the
start of the year:

| amount | date       | recipient       | ... | occurence |
| ------ | ---------- | --------------- | --- | --------- |
| -60    | 2022-01-15 | insurance comp. | ... | **12**    |

Determining average fixed costs per month is now very easy, as you can distribute this transaction 12
months into the future, starting from the current month:

| amount | date       | recipient       | ... | occurence |
| ------ | ---------- | --------------- | --- | --------- |
| -5     | 2022-01-01 | insurance comp. | ... | 12        |
| -5     | 2022-02-01 | insurance comp. | ... | 12        |
| ...    | ...        | ...             | ... | ...       |
| -5     | 2022-12-01 | insurance comp. | ... | 12        |

Note that the original date will be set to the start of the month as well.

Using a negative integer will distribute the transaction into the past, starting from
the original dates month.

Integers 0, 1, -1 don't get affected by this. I personally use 1 and -1 to mark
transactions which have a fixed-cost character but don't appear frequently (eg. groceries).

### Historical View

Another export is the history.csv, where you'll find your day-to-day spendings and
your daily balance (incase your bank exports feature a starting or end balance).

| date       | amount | balance |
| ---------- | ------ | ------- |
| 2022-01-01 | -10    | 90      |
| 2022-01-02 | 120    | 210     |
| 2021-01-05 | -5     | 205     |

If you're bank doesn't provide any means of calculating a balance, you can write it manually in the metadata.csv:

| starting_balance | bank_format |
| ---------------- | ----------- |
| **100**          | dkb         |

# Developer Documentation

All internal dataframes get initialised empty with correct datatypes.

The functions for filling the dataframes are called in this order:

1.  ledger

    1.a mapping_table (depends on recipients)

    1.b transactions_coalesced

    1.c transactions_distributed

2.  metadata

    2.a history (depends on starting_balance)

### Ledger object

The initial Ledger object can be created like this:

```python
from pathlib import Path
from ledgercli.ledger import Ledger

output_path = Path("path/to/output_folder")
export_path = Path("path/to/export.csv")
bank="yourbankformat"

l = Ledger(output_path=output_path, export_path=export_path, bank=bank)
```

Writing to disk:

```python
l.write()
```

Appending another export:

```python
appendage_path = Path("path/to/another_export.csv")
l = Ledger(output_path=output_path, export_path=appendage_path, bank=bank)
```

Updating your Ledger object after you made modifications to the files in the output_folder:

```python
l = Ledger(output_path=output_path, export_path=None)
```
