"""Generate a 5-year indexed BTC, gold, and S&P 500 comparison chart."""

from __future__ import annotations

from datetime import datetime, timedelta
import sys
from pathlib import Path

import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.annotations import Annotations
from components.base_chart import BaseChart
from config import theme
from data.fetcher import get_macro_comparison


EVENTS = [
    ("2021-05-19", "China\nBan"),
    ("2021-11-10", "BTC ATH"),
    ("2022-11-08", "FTX Collapse"),
    ("2024-01-10", "BTC ETF"),
]

Y_TICKS = [20, 50, 100, 200, 500, 1000, 2000, 5000]


def _format_pct(value: float) -> str:
    return f"+{value:,.0f}%"


def rebase_to_five_year_window(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to a strict five-year window and re-index all series to 100."""
    start_date = pd.Timestamp(datetime.now() - timedelta(days=365 * 5)).normalize()
    rebased_df = df[df["date"] >= start_date].dropna().sort_values("date").reset_index(drop=True)
    if rebased_df.empty:
        raise RuntimeError("No macro comparison data after the forced 5-year start date.")

    base_row = rebased_df.iloc[0]
    for column in ("btc", "gold", "sp500"):
        rebased_df[column] = rebased_df[column] / base_row[column] * 100
    rebased_df.attrs.update(df.attrs)
    return rebased_df


def build_chart() -> Path:
    """Build and save the 5-year macro comparison chart."""
    df = get_macro_comparison(years=5)
    if df.empty:
        raise RuntimeError("Macro comparison data is empty.")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = rebase_to_five_year_window(df)

    btc_start = df.attrs["btc_start_price"]
    btc_end = df.attrs["btc_end_price"]
    print(f"起始日期: {df['date'].iloc[0]}")
    print(f"BTC 起始价: ${btc_start:.0f}")
    print(f"BTC 终点价: ${btc_end:.0f}")
    print(f"BTC 涨幅: {(btc_end / btc_start - 1) * 100:.0f}%")
    print(f"BTC 归一化最低值: {df['btc'].min():.1f}")

    chart = BaseChart()
    ax = chart.add_axes(theme.LAYOUT["macro_axes"])

    ax.set_yscale("log")
    ax.set_yticks(Y_TICKS)
    data_max = df[["btc", "gold", "sp500"]].max().max()
    ax.set_ylim(bottom=18, top=max(Y_TICKS[-1], data_max * 1.12))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{int(value):,}" if value in Y_TICKS else ""))
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=9)

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", labelsize=8)

    btc_line, = ax.plot(
        df["date"],
        df["btc"],
        color=theme.COLORS["btc_line"],
        linewidth=2.2,
        zorder=4,
        label="BTC",
    )
    gold_line, = ax.plot(
        df["date"],
        df["gold"],
        color=theme.COLORS["gold_line"],
        linewidth=1.8,
        zorder=3,
        label="Gold",
    )
    sp500_line, = ax.plot(
        df["date"],
        df["sp500"],
        color=theme.COLORS["sp500_line"],
        linewidth=1.8,
        zorder=3,
        label="S&P 500",
    )

    ax.legend(
        handles=[btc_line, gold_line, sp500_line],
        loc="upper left",
        bbox_to_anchor=(0.01, 0.80),
        facecolor=theme.COLORS["surface"],
        edgecolor=theme.COLORS["grid"],
        fontsize=9,
        labelcolor=theme.COLORS["text_primary"],
        framealpha=1.0,
    )

    annotations = Annotations()
    x_min = df["date"].min()
    x_max = df["date"].max()
    for date_text, label in EVENTS:
        event_date = pd.Timestamp(date_text)
        if not x_min <= event_date <= x_max:
            continue
        annotations.add_event_line(
            ax,
            event_date,
            label,
            line_color=theme.COLORS["text_hint"],
            line_width=0.8,
            linestyle="--",
            text_color=theme.COLORS["text_muted"],
            fontsize=8,
            rotation=0,
        )

    ax.text(
        0.01,
        0.02,
        "Log scale  ·  Base = 100",
        transform=ax.transAxes,
        color=theme.COLORS["text_hint"],
        fontsize=8,
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="bottom",
    )

    last_date = df["date"].iloc[-1]
    for column, label, color, y_offset in (
        ("gold", "Gold", theme.COLORS["gold_line"], 10),
        ("sp500", "S&P", theme.COLORS["sp500_line"], 0),
        ("btc", "BTC", theme.COLORS["btc_line"], -10),
    ):
        pct = df[column].iloc[-1] - 100
        ax.annotate(
            f"{label} {_format_pct(pct)}",
            xy=(last_date, df[column].iloc[-1]),
            xytext=(8, y_offset),
            textcoords="offset points",
            color=color,
            fontsize=9,
            fontweight="bold",
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="left",
            va="center",
        )

    chart.fig.text(
        theme.LAYOUT["macro_title_x"],
        theme.LAYOUT["macro_title_y"],
        "BTC vs Gold vs S&P 500",
        color=theme.COLORS["text_primary"],
        fontsize=22,
        fontweight="bold",
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="top",
    )
    chart.fig.text(
        theme.LAYOUT["macro_title_x"],
        theme.LAYOUT["macro_subtitle_y"],
        "5-Year Indexed Performance (Base = 100)",
        color=theme.COLORS["text_muted"],
        fontsize=11,
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="top",
    )

    btc_pct = df["btc"].iloc[-1] - 100
    chart.fig.text(
        theme.LAYOUT["macro_callout_center"][0],
        theme.LAYOUT["macro_callout_center"][1],
        f"BTC\n{_format_pct(btc_pct)}",
        color=theme.COLORS["primary"],
        fontsize=24,
        fontweight="bold",
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="center",
        va="center",
    )
    chart.fig.text(
        theme.LAYOUT["macro_callout_center"][0],
        theme.LAYOUT["macro_callout_center"][1] - 0.09,
        "5Y Performance",
        color=theme.COLORS["text_muted"],
        fontsize=10,
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="center",
        va="center",
    )

    chart.fig.text(
        theme.LAYOUT["macro_source_x"],
        theme.LAYOUT["macro_source_y"],
        "Source: Yahoo Finance",
        color=theme.COLORS["text_hint"],
        fontsize=8,
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="bottom",
    )
    chart.fig.text(
        theme.LAYOUT["macro_watermark_x"],
        theme.LAYOUT["macro_watermark_y"],
        theme.WATERMARK["text"],
        color=theme.COLORS["text_hint"],
        fontsize=8,
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="right",
        va="bottom",
    )

    return chart.save("macro_comparison_5y.png")


if __name__ == "__main__":
    build_chart()
