"""Plotter."""

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from ledgercli.main import Ledger


class Plotter:
    """Plotter."""

    PLOT_BASE = {
        "net": 2,
        "netio": 2,
        "label": 2,
        "label_net": 2,
        "fixed_var": 2,
        "topn_var": 1,
        "tx": 1,
    }
    BASES = {
        0: "TX",
        1: "TX_C",
        2: "TX_D",
    }

    NEUTRAL = "#bd93f9"
    INCOME = "#50fa7b"
    EXPENSE = "#ff5555"
    VARIABLE = "#f1fa8c"
    FIXED = "#8be9fd"
    BG = "rgba(0,0,0,0)"
    GRID = "#44475a"
    ZERO_LINE = "#44475a"

    def __init__(
        self,
        current_base: int,
        ledger: Ledger,
        years: list[int],
        quarters: list[int],
        months: list[int],
        weeks: list[int],
        types: list[str],
        t_start: list[str],
        labels1: list[str],
        labels2: list[str],
        labels3: list[str],
        fixed_var: list[str],
        time_base: str,
        recipients: list[str],
    ):
        """Initializes Plotter."""
        self.CURRENT_BASE = current_base
        self.ledger = ledger
        self.TIME_BASE = time_base
        self.T_START = t_start

        # time filters
        self.YEARS = years
        self.QUARTERS = quarters
        self.MONTHS = months
        self.WEEKS = weeks

        # content filters
        self.RECIPIENTS = recipients
        self.LABELS1 = labels1
        self.LABELS2 = labels2
        self.LABELS3 = labels3
        self.TYPES = types
        self.FIXED_VAR = fixed_var

    def _type_colors(self) -> dict[str, str]:
        return {"Income": self.INCOME, "Expense": self.EXPENSE}

    def _fixedvar_colors(self) -> dict[str, str]:
        return {"Variable": self.VARIABLE, "Fixed": self.FIXED}

    def _get_base(self, plot_type: str) -> pd.DataFrame:
        """Returns Ledger transaction according to current minimal base.

        Args:
          plot_type:

        Returns:
          ledger transactions
        """
        min_base = self._get_min_base_id(plot_type=plot_type)
        if min_base == 2:
            df = self.ledger.tx_d.copy()
        elif min_base == 1:
            df = self.ledger.tx_c.copy()
        else:
            df = self.ledger.tx.copy()
        return df

    def _get_min_base_id(self, plot_type: str) -> int:
        """Gets minimal base for each plot type in regards to current base.

        Args:
          plot_type:

        Returns:
          int
        """
        return min(self.PLOT_BASE[plot_type], self.CURRENT_BASE)

    def filter_by_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds date columns for display and filters based on current time filters.

        Args:
          df: df to filter
        Returns:
          filtered df
        """
        for col in ["week", "month", "quarter", "year"]:
            df[col] = (
                pd.to_datetime(df["date"])
                .dt.to_period(col.upper()[0])
                .dt.to_timestamp()
            )
        df["year_num"] = df["date"].dt.year
        df["quarter_num"] = df["date"].dt.quarter
        df["month_num"] = df["date"].dt.month
        df["week_num"] = df["date"].dt.isocalendar().week

        df = df[
            (df["year_num"].isin(self.YEARS))
            & (df["month_num"].isin(self.MONTHS))
            & (df["quarter_num"].isin(self.QUARTERS))
            & (df["week_num"].isin(self.WEEKS))
            & (df["date"] >= self.T_START)
        ]

        return df

    def filter_by_content(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filters df based on content.

        Args:
          df: df to filter

        Returns:
          filtered df
        """
        df["type"] = np.where(df["amount"] > 0, "Income", "Expense")
        df["occurence"] = df["occurence"].fillna(0)
        df["cost_type"] = np.where(df["occurence"] == 0, "Variable", "Fixed")

        df = df[
            (df["label1"].isin(self.LABELS1))
            & (df["label2"].isin(self.LABELS2))
            & (df["label3"].isin(self.LABELS3))
            & (df["type"].isin(self.TYPES))
            & (df["cost_type"].isin(self.FIXED_VAR))
            & (df["recipient"].isin(self.RECIPIENTS))
        ]
        return df

    def _regen_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Regenerates type column for a given df.

        Args:
          df: dataframe

        Returns:
          df with updated type column
        """
        df["type"] = np.where(df["amount"] > 0, "Income", "Expense")
        return df

    def plot_net(self, datecol: str) -> Figure:
        """Plots net amount per datecol.

        Args:
          datecol: either week, month, quarter or year

        Returns:
          net plot
        """
        df = self._get_base("net")
        df = self.filter_by_time(df)
        df = self.filter_by_content(df)
        base_title = self.BASES[self._get_min_base_id("net")]

        df = df.groupby(datecol, as_index=False)["amount"].sum()
        df = self._regen_type(df)
        fig = px.bar(
            df,
            datecol,
            "amount",
            color="type",
            title=f"Net per {datecol} [{base_title}]",
            color_discrete_map=self._type_colors(),
        )
        return fig

    def plot_netio(self, datecol: str) -> Figure:
        """Plots income / expenses per datecol.

        Args:
          datecol: either week, month, quarter or year

        Returns:
          netio plot
        """
        df = self._get_base("netio")
        df = self.filter_by_time(df)
        df = self.filter_by_content(df)
        base_title = self.BASES[self._get_min_base_id("netio")]

        df = self._regen_type(df)
        df["amount"] = abs(df["amount"])
        df = df.groupby([datecol, "type"], as_index=False)["amount"].sum()
        fig = px.bar(
            df,
            datecol,
            "amount",
            color="type",
            barmode="group",
            title=f"Income / Expense per {datecol} [{base_title}]",
            color_discrete_map=self._type_colors(),
        )
        return fig

    def plot_history(self) -> Figure:
        """Plots history.

        Returns:
          history plot
        """
        df = self.ledger.history
        df = self.filter_by_time(df)
        fig = px.area(
            df,
            "date",
            "balance",
            title="Daily Balance [TX]",
            color_discrete_sequence=[self.NEUTRAL],
        )
        fig.update_yaxes(rangemode="tozero")
        return fig

    def plot_label(self, label: str) -> Figure:
        """Plots an ordered bar chart based on supplied label.

        Args:
          label: either label1, label2, label3

        Returns:
          label plot
        """
        df = self._get_base("label")
        df = self.filter_by_time(df)
        df = self.filter_by_content(df)
        base_title = self.BASES[self._get_min_base_id("label")]

        df = (
            df.groupby([label], as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        ).copy()
        df = self._regen_type(df)
        fig = px.bar(
            df,
            "amount",
            label,
            color="type",
            title=f"{label} Overview [{base_title}]",
            color_discrete_map=self._type_colors(),
        )

        return fig

    def plot_topn_var(self, income: bool) -> Figure:
        """Plots top 10 transactions, either income or expenses, as an ordered bar chart.

        Args:
          income: whether to show topn income transactions

        Returns:
          topn plot
        """
        df = self._get_base("topn_var")
        df = self.filter_by_time(df)
        df = self.filter_by_content(df)
        base_title = self.BASES[self._get_min_base_id("topn_var")]

        if income:
            title = f"Top 10 Income [{base_title}]"
            colors = [self.INCOME]
            ltype = "Income"
        else:
            title = f"Top 10 Expenses [{base_title}]"
            colors = [self.EXPENSE]
            ltype = "Expense"

        df = df[df["type"] == ltype].sort_values("amount", ascending=income).tail(10)
        df["tmp_index"] = sorted(np.arange(1, df.shape[0] + 1), reverse=True)
        df["recipient"] = df["tmp_index"].astype(str) + ". " + df["recipient"]
        fig = px.bar(
            df,
            "amount",
            "recipient",
            orientation="h",
            color_discrete_sequence=colors,
            title=title,
        )

        return fig

    def plot_fixed_variable(self, datecol: str) -> Figure:
        """Plots amount of expenses grouped by datecol and cost_type.

        Args:
          datecol: either week, month, quarter or year

        Returns:
          fixed variable plot
        """
        df = self._get_base("fixed_var")
        df = self.filter_by_time(df)
        df = self.filter_by_content(df)
        base_title = self.BASES[self._get_min_base_id("fixed_var")]

        df = self._regen_type(df)
        df = (
            df[df["type"] == "Expense"]
            .groupby([datecol, "cost_type"], as_index=False)["amount"]
            .sum()
        )
        fig = px.bar(
            df,
            datecol,
            "amount",
            color="cost_type",
            barmode="group",
            color_discrete_map=self._fixedvar_colors(),
            title=f"Variable & Fixed Expenses [{base_title}]",
        )
        return fig

    def _style_plot(self, fig: Figure, horizontal: bool = True) -> Figure:
        """Styles given plot.

        Makes background transparent, hides legend, removes bar outline, only displays a partial grid, colours
        grid- and zerolines, adds € suffix to amount axis.

        Args:
          fig: plot to style
          horizontal: whether amount is on x-axis

        Returns:
          fig: styled plot
        """
        fig.update_layout(
            paper_bgcolor=self.BG,
            plot_bgcolor=self.BG,
            showlegend=False,
            margin=dict(l=50, r=50, t=100, b=50),
        )

        fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
        if horizontal:
            fig.update_xaxes(
                showgrid=False,
                title=None,
                tickformatstops=[dict(dtickrange=[None, 86400000], value="%d %b %Y")],
            )
            fig.update_yaxes(
                dict(ticksuffix="€"),
                showgrid=True,
                gridwidth=1,
                gridcolor=self.GRID,
                zeroline=True,
                zerolinewidth=1,
                zerolinecolor=self.ZERO_LINE,
                title=None,
            )
        else:
            fig.update_xaxes(
                dict(ticksuffix="€"),
                showgrid=True,
                gridwidth=1,
                gridcolor=self.GRID,
                zeroline=True,
                zerolinewidth=1,
                zerolinecolor=self.ZERO_LINE,
                title=None,
            )
            fig.update_yaxes(showgrid=False, title=None)
        return fig

    def render_plots(self) -> list[Figure]:
        """Render all plots."""
        net = self.plot_net(self.TIME_BASE)
        netio = self.plot_netio(self.TIME_BASE)
        hist = self.plot_history()
        fixed_var = self.plot_fixed_variable(self.TIME_BASE)
        hori = [net, netio, fixed_var, hist]
        hori = [self._style_plot(fig, horizontal=True) for fig in hori]

        topn_inc = self.plot_topn_var(True)
        topn_exp = self.plot_topn_var(False)
        lab1 = self.plot_label("label1")
        lab2 = self.plot_label("label2")
        lab3 = self.plot_label("label3")
        vert = [topn_inc, topn_exp, lab1, lab2, lab3]
        vert = [self._style_plot(fig, horizontal=False) for fig in vert]

        figs = [*hori, *vert]
        return figs
