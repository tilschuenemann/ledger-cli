# Features

## File Overview

Running `ledger-cli` successfully creates the following files:

`transactions.csv` - the heart of this program; contains all of your transactions and is used as base for individual custom values and creating the other transaction files.

`mapping.csv` lists all current recipients and allows you to enter clean names and custom labels.

`metadata.csv` contains the current bank_format, which will be read so that you don't have it enter it when running. It also contains the starting_balance for the historical view.

`tx_coalesced.csv` is a copy of transaction.csv, but all fields will be coalesced with their custom twin.

`tx_distributed.csv` is a copy of tx_coalesced.csv, but all transaction will be distributed via their occurence.

`history.csv`

```{eval-rst}
.. warning:: Only changes in transactions.csv, mapping.csv and metadata.csv are persisted.

             Working in tx_coalesced.csv, tx_distributed.csv or history.csv will be overwritten!
```

## Mapping Table

You're able to provide three different labels, a clean recipient name
and an occurence for each unique recipient in `mapping.csv`:

| recipient       | recipient_clean | label1    | label2 | label3 | occurence |
| --------------- | --------------- | --------- | ------ | ------ | --------- |
| grocerystore+++ | Grocery Store   | Groceries |        |        |           |

`mapping.csv` is read and mapped onto the ledger everytime you use `ledger-cli`.

## Custom Values and Coalescing

For the majority of the data columns in the transactions.csv there is a _\_custom_-suffixed twin:

| amount | amount_custom |
| ------ | ------------- |
| -50    |               |
| -10    | 5             |

`ledger-cli` writes a _transactions_coalesced.csv_, where every pair is merged.
_\_custom_-values take precedence.

Custom values can be provided for these columns:

- amount
- date
- recipient_clean
- label1
- label2
- label3
- occurence

## Support for different providers

Ledger works with a simple base format (date, amount and recipient column). As long as your banks export can be transformed
into a pandas dataframe with these columns, it can be supported!

Currently available providers:

- DKB
- Sparkasse

[Feel free to create a pull request if your bank is missing!](https://github.com/tilschuenemann/ledger-cli/pulls)

## Occurance

### Distribution

Certain transactions occur once every now and then and might dilute meaningful interpretation: You pay a yearly insurance bill, which then only shows in January. You'd like it to show up every month with 1/12 of the original amount. `ledger-cli` allows you to do exactly that!

In the occurence column can enter a the amount of months your transaction should be distributed among:

| amount | date       | recipient       | ... | occurence |
| ------ | ---------- | --------------- | --- | --------- |
| -60    | 2022-01-15 | insurance comp. | ... | `12`      |

After updating the ledger, the result will be visibile in `transactions_distributed.csv` and determining average fixed costs per month will be easy:

| amount | date       | recipient       | ... | occurence |
| ------ | ---------- | --------------- | --- | --------- |
| -5     | 2022-01-01 | insurance comp. | ... | 1         |
| -5     | 2022-02-01 | insurance comp. | ... | 1         |
| ...    | ...        | ...             | ... | ...       |
| -5     | 2022-12-01 | insurance comp. | ... | 1         |

Note that the original date will be set to the start of the month as well.

Using a negative integer will distribute the transaction into the past, starting from
the original dates month.

### Fixed & Variable Costs

Setting occurance to 1 or -1 won't distribute the transaction, but it will now be counted as a fixed expenses occuring for this month.
Transactions with occurence 0 are treated as variable transactions.

## Historical View

Another export is the `history.csv`, where you'll find your day-to-day spendings and
your daily balance (incase your bank exports feature a starting or end balance).

| date       | amount | balance |
| ---------- | ------ | ------- |
| 2022-01-01 | -10    | 90      |
| 2022-01-02 | 120    | 210     |
| 2021-01-05 | -5     | 205     |

If you're bank doesn't provide any means of calculating a balance, you can write it manually in the _metadata.csv_ (this will be considered after running `ledgerlci update` again):

| starting_balance | bank_format |
| ---------------- | ----------- |
| **100**          | dkb         |
