import pandas as pd
import numpy as np
import plotly.express as px

from ledgercli.viz import get_base, _get_min_base_id

base_map = {
    0: "TX",
    1: "TX_C",
    2: "TX_D",
}


def plot_net(datecol: str):
    df = get_base("net")
    base_title = base_map[_get_min_base_id("net")]

    df = df.groupby(datecol, as_index=False)["amount"].sum()
    df = _init_type(df)
    return px.bar(
        df, datecol, "amount", color="type", title=f"Net per {datecol} [{base_title}]", color_discrete_map=TYPE_COLORS
    )


def plot_netio(datecol: str):
    df = get_base("netio")
    base_title = base_map[_get_min_base_id("netio")]

    df = _init_type(df)
    df["amount"] = abs(df["amount"])
    df = df.groupby([datecol, "type"], as_index=False)["amount"].sum()
    return px.bar(
        df,
        datecol,
        "amount",
        color="type",
        barmode="group",
        title=f"Income / Expense per {datecol} [{base_title}]",
        color_discrete_map=TYPE_COLORS,
    )


def plot_history():
    fig = px.line(l.history, "date", "balance", title="Daily Balance [TX]")
    fig.update_yaxes(rangemode="tozero")
    return fig


def plot_label(label: str):
    df = get_base("label")
    base_title = base_map[_get_min_base_id("label")]

    df = (
        df.groupby([label], as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    ).copy()
    df = _init_type(df)
    return px.bar(
        df, "amount", label, color="type", title=f"{label} Overview [{base_title}]", color_discrete_map=TYPE_COLORS
    )


def plot_topn_var(income: bool):

    df = get_base("topn_var")
    base_title = base_map[_get_min_base_id("topn_var")]

    if income:
        title = f"Top 10 Variable Income [{base_title}]"
        colors = [TYPE_COLORS["Income"]]
        ltype = "Income"
    else:
        title = f"Top 10 Variable Expenses [{base_title}]"
        colors = [TYPE_COLORS["Expense"]]
        ltype = "Expense"

    df = df[(pd.isna(df["occurence"])) & (df["type"] == ltype)].sort_values("amount", ascending=income).tail(10)

    df["tmp_index"] = sorted(np.arange(1, df.shape[0] + 1), reverse=True)
    df["recipient"] = df["tmp_index"].astype(str) + ". " + df["recipient"]
    return px.bar(
        df,
        "amount",
        "recipient",
        orientation="h",
        color_discrete_sequence=colors,
        title=title,
    )


def plot_fixed_variable(datecol: str):

    df = get_base("fixed_var")
    base_title = base_map[_get_min_base_id("fixed_var")]

    df = _init_type(df)
    df = df[df["type"] == "Expense"]
    df["occurence"] = df["occurence"].fillna(0)
    df["cost_type"] = np.where(df["occurence"] == 0, "Variable", "Fixed")
    df = df[df["type"] == "Expense"].groupby([datecol, "cost_type"], as_index=False)["amount"].sum()
    return px.bar(
        df,
        datecol,
        "amount",
        color="cost_type",
        barmode="group",
        color_discrete_map=OCC_COLORS,
        title=f"Variable & Fixed Expenses [{base_title}]",
    )


def plot_label_net(label: str, datecol: str):
    df = get_base("label_net")
    base_title = base_map[_get_min_base_id("label_net")]

    df = df.groupby([label, datecol], as_index=False)["amount"].sum()
    df = _init_type(df)
    fig = px.bar(
        df,
        datecol,
        "amount",
        color=label,
        title=f"{label} by {datecol}s [TX D]",
        color_discrete_map=TYPE_COLORS,
        barmode="group",
    )
    return fig
