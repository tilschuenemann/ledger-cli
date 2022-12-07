import calendar
from datetime import datetime
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dateutil.relativedelta import relativedelta

from ledgercli.main import Ledger


# streamlit settings
st.set_page_config(layout="wide")
st.write(
    "<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True)

# ledger setup
output_dir = Path("/home/til/03_code/ledgercli-private/newver")
l = Ledger(output_dir=output_dir, bank_type=None)
l.update()

base_map = {
    0: "TX",
    1: "TX_C",
    2: "TX_D",
}

# filters
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    year_options = set(l.tx["date"].dt.year)
    YEARS = st.multiselect("Year", options=year_options)
    YEARS = year_options if len(YEARS) == 0 else YEARS

    type_options = ["Income", "Expense"]
    TYPES = st.multiselect("Type", options=type_options)
    TYPES = type_options if len(TYPES) == 0 else TYPES

    TX_BASE = st.selectbox("Select maximum base for plots:", options=range(0, 3),
                           format_func=lambda x: base_map.get(x), index=2)


with col2:
    pretty_quarter = {}
    for x in range(1, 5):
        pretty_quarter[x] = f"Q{x}"
    QUARTERS = st.multiselect("Quarter", options=pretty_quarter.keys(), format_func=lambda x: pretty_quarter.get(x))
    QUARTERS = pretty_quarter.keys() if len(QUARTERS) == 0 else QUARTERS

    label1_options = l.tx[["label1", "amount"]].groupby(["label1"], as_index=False)[
        "amount"].sum().sort_values(by="amount")["label1"]
    LABELS1 = st.multiselect("Label1", options=label1_options)
    LABELS1 = label1_options if len(LABELS1) == 0 else LABELS1

    TIME_BASE = st.selectbox("Select time unit:", ["week", "month", "quarter", "year"], index=1)


with col3:
    pretty_month = {}
    for x in range(1, 13):
        pretty_month[x] = calendar.month_name[x]
    MONTHS = st.multiselect("Month", options=pretty_month.keys(), format_func=lambda x: pretty_month.get(x))
    MONTHS = pretty_month.keys() if len(MONTHS) == 0 else MONTHS
    label2_options = l.tx[["label2", "amount"]].groupby(["label2"], as_index=False)[
        "amount"].sum().sort_values(by="amount")["label2"]
    LABELS2 = st.multiselect("Label2", options=label2_options)
    LABELS2 = label1_options if len(LABELS2) == 0 else LABELS2


with col4:
    week_options = range(1, 54)
    WEEKS = st.multiselect("Week", options=week_options)
    WEEKS = week_options if len(WEEKS) == 0 else WEEKS

    label3_options = l.tx[["label3", "amount"]].groupby(["label3"], as_index=False)[
        "amount"].sum().sort_values(by="amount")["label3"]
    LABELS3 = st.multiselect("Label3", options=label3_options)
    LABELS3 = label3_options if len(LABELS3) == 0 else LABELS3


with col5:
    CURRENT_MONTH = st.button("Current Month")
    LAST_3MONTHS = st.button("Last 3 Months")
    LAST_6MONTHS = st.button("Last 6 Months")
    LAST_12MONTHS = st.button("Last 12 Months")
    RESET = st.button("Reset")


def _get_min_base_id(plot_type: str) -> int:
    """Determines the minimum id for a given plot and the current TX_BASE.

    Args:
      plot_type:

    Returns:

    """
    plot_base = {
        "net": 2,
        "netio": 2,
        "label": 2,
        "label_net": 2,
        "fixed_var": 2,
        "topn_var": 1,
        "tx": 1,
    }
    return min(plot_base[plot_type], TX_BASE)


def get_base(plot_type: str) -> pd.DataFrame:
    highest_base = _get_min_base_id(plot_type=plot_type)

    if highest_base == 2:
        df = l.tx_d.copy()
    elif highest_base == 1:
        df = l.tx_c.copy()
    else:
        df = l.tx.copy()

    return filter_base(df)


def filter_base(df: pd.DataFrame) -> pd.DataFrame:
    if CURRENT_MONTH:
        T_START = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif LAST_3MONTHS:
        T_START = datetime.now() - relativedelta(months=3)
    elif LAST_6MONTHS:
        T_START = datetime.now() - relativedelta(months=6)
    elif LAST_12MONTHS:
        T_START = datetime.now() - relativedelta(months=12)
    else:
        T_START = df["date"].min()

    df = df[(df["year_num"].isin(YEARS))
            & (df["month_num"].isin(MONTHS))
            & (df["quarter_num"].isin(QUARTERS))
            & (df["week_num"].isin(WEEKS))
            & (df["label1"].isin(LABELS1))
            & (df["label2"].isin(LABELS2))
            & (df["label3"].isin(LABELS3))
            & (df["type"].isin(TYPES))
            & (df["date"] >= T_START)]
    return df


# kpis
st.markdown("-----")
col1, col2, col3 = st.columns(3)
with col1:
    df = get_base("tx")
    total_net = df["amount"].sum()
    st.metric("Net Income", f"{total_net:.0f} €")
with col2:
    current_account = l.history["balance"].iloc[-1]
    st.metric("Current Bank Account", f"{current_account:.0f} €")
with col3:
    pass
st.markdown("-----")

# plotting functions
TYPE_COLORS = dict({"Income": "#33ee33", "Expense": "#ee3333"})
OCC_COLORS = dict({"Variable": "#eeee33", "Fixed": "#33eeee"})


def _init_type(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp["type"] = np.where(tmp["amount"] > 0, "Income", "Expense")
    return tmp


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


# streamlit page layout
col1, col2, col3 = st.columns(3)
with col1:
    st.write(plot_net(TIME_BASE))
    st.write(plot_label("label1"))

with col2:
    st.write(plot_netio(TIME_BASE))
    st.write(plot_label("label2"))

with col3:
    st.write(plot_history())
    st.write(plot_label("label3"))


col1, col2 = st.columns(2)
with col1:
    st.write(plot_topn_var(income=False))

with col2:
    st.write(plot_topn_var(income=True))

st.write(plot_fixed_variable(TIME_BASE))

st.write(plot_label_net("label1", TIME_BASE))

df = get_base("tx")
st.write(df[["amount", "date", "recipient", "label1", "label2", "label3"]].sort_values(by=['date']))
