"""Viz Streamlit App."""

import calendar
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from ledgercli.main import Ledger
from ledgercli.plotter import Plotter


def main(output_dir: str) -> None:
    """Creates the streamlit app."""
    st.set_page_config(layout="wide")
    st.write(
        "<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True
    )
    st.write(
        """<style>
        .css-1gx893w{{
                        padding-top: 0px;
                    }}
        .css-1vq4p4l{{
                        padding-top: 0px;
                    }}
        </style>""",
        unsafe_allow_html=True,
    )

    config = {"displayModeBar": False}

    # ledger setup
    ledger = Ledger(output_dir=Path(output_dir), bank=None)
    ledger.update()

    bases = {
        0: "TX",
        1: "TX_C",
        2: "TX_D",
    }

    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            # generate options
            reportstart_options = {
                99: "All",
                0: "Current Month",
                3: "Last 3 Months",
                6: "Last 6 Months",
                12: "Last 12 Months",
            }
            year_options = set(ledger.tx["date"].dt.year)

            # generate filters
            time_base = st.selectbox(
                "Time Unit", ["week", "month", "quarter", "year"], index=1
            )
            report_start = st.selectbox(
                "Timeframe",
                options=reportstart_options.keys(),
                format_func=lambda x: reportstart_options.get(x),
            )
            years = st.multiselect("Year", options=year_options)
            quarters = st.multiselect(
                "Quarter",
                options=range(1, 5),
                format_func=lambda x: f"Q{x}",
            )
            months = st.multiselect(
                "Month",
                options=range(1, 13),
                format_func=lambda x: calendar.month_name[x],
            )
            weeks = st.multiselect("Week", options=range(1, 54))

        with col2:
            # generate options
            type_options = ["Income", "Expense"]
            fixedvar_options = ["Fixed", "Variable"]
            recipient_options = sorted(ledger.tx_c["recipient"].unique())
            gen_labels_options = []
            for label in ["label1", "label2", "label3"]:
                gen_labels_options.append(
                    ledger.tx[[label, "amount"]]
                    .groupby([label], as_index=False)["amount"]
                    .sum()
                    .sort_values(by="amount")[label]
                )
            label1_options, label2_options, label3_options = gen_labels_options

            # create filters
            current_base = st.selectbox(
                "Calculation Base",
                options=bases.keys(),
                format_func=lambda x: bases.get(x),
                index=2,
            )
            types = st.multiselect("Type", options=type_options)
            fixed_var = st.multiselect("Cost Type", options=fixedvar_options)
            recipients = st.multiselect("Recipient [TX_C]", options=recipient_options)
            labels1 = st.multiselect("Label1", options=label1_options)
            labels2 = st.multiselect("Label2", options=label2_options)
            labels3 = st.multiselect("Label3", options=label3_options)

    # change filter behavior:
    # empty filter will be replaced with default options for better selection behavior
    quarters = range(1, 5) if len(quarters) == 0 else quarters
    months = range(1, 13) if len(months) == 0 else months
    weeks = range(1, 54) if len(weeks) == 0 else weeks

    filters = [labels1, labels2, labels3, recipients, fixed_var, types, years]
    options = [
        label1_options,
        label2_options,
        label3_options,
        recipient_options,
        fixedvar_options,
        type_options,
        year_options,
    ]
    results = []
    for f, o in zip(filters, options, strict=True):
        f = o if len(f) == 0 else f
        results.append(f)
    labels1, labels2, labels3, recipients, fixed_var, types, years = results

    # set cutoff date for reporting
    if report_start == 0:
        t_start = pd.Timestamp.today().floor("D") - pd.offsets.MonthBegin()
    elif report_start < 99:
        t_start = pd.Timestamp.today() - pd.offsets.MonthBegin(n=report_start)
    else:
        t_start = ledger.tx["date"].min()

    # create plotter and render all plots based on parameters
    pl = Plotter(
        current_base=current_base,
        ledger=ledger,
        years=years,
        quarters=quarters,
        months=months,
        weeks=weeks,
        types=types,
        t_start=t_start,
        labels1=labels1,
        labels2=labels2,
        labels3=labels3,
        fixed_var=fixed_var,
        time_base=time_base,
        recipients=recipients,
    )
    (
        net,
        netio,
        fixed_var,
        hist,
        topn_inc,
        topn_exp,
        lab1,
        lab2,
        lab3,
    ) = pl.render_plots()

    # kpis
    col1, col2, col3 = st.columns(3)

    with col1:
        total_net = ledger.tx[ledger.tx["date"] >= t_start]["amount"].sum()
        st.metric("Net Income", f"{total_net:,.0f} €".replace(",", "."))
    with col2:
        current_account = ledger.history["balance"].iloc[-1]
        st.metric("Current Bank Account", f"{current_account:,.0f} €".replace(",", "."))
    with col3:
        df = pl._get_base("tx")
        df = pl.filter_by_time(df)
        df = pl.filter_by_content(df)
        fixed_sum = df[(df["cost_type"] == "Fixed") & (df["type"] == "Expense")][
            "amount"
        ].sum()
        total = df[df["type"] == "Expense"]["amount"].sum()
        fixed_share = (fixed_sum / total) * 100
        st.metric("Fixed Costs / Expenses", f"{fixed_share:.0f} %")

    # streamlit page layout
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(net, config=config)
    with col2:
        st.plotly_chart(netio, config=config)
    with col3:
        st.plotly_chart(hist, config=config)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(lab1, config=config)
    with col2:
        st.plotly_chart(lab2, config=config)
    with col3:
        st.plotly_chart(lab3, config=config)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(topn_exp, config=config)
    with col2:
        st.plotly_chart(topn_inc, config=config)

    st.plotly_chart(fixed_var, config=config)

    # show tx
    tab = pl._get_base("tx")
    tab["date"] = tab["date"].dt.date
    for col in ["label1", "label2", "label3"]:
        tab[col] = tab[col].replace("nan", "")

    tab = (
        tab[["date", "recipient", "amount", "label1", "label2", "label3"]]
        .sort_values(by=["date"])
        .reset_index(drop=True)
    )
    st.dataframe(tab.style.format({"amount": "{:.2f}"}), use_container_width=True)


if __name__ == "__main__":
    main(sys.argv[1])
