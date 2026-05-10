"""Generate BTC vs Nasdaq 90-day rolling correlation chart."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib-cache"))

import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, FormatStrFormatter
import pandas as pd

from components.annotations import Annotations
from components.base_chart import BaseChart
from config import theme
from data.fetcher import get_btc_nasdaq_correlation


EVENTS = [
    ("2020-03-01", "COVID"),
    ("2022-01-01", "Fed Hike"),
    ("2022-11-08", "FTX"),
    ("2024-01-10", "BTC ETF"),
]

CORRELATION_TICKS = [-0.2, 0, 0.2, 0.4, 0.6, 0.8, 1.0]


def _current_state(value: float) -> tuple[str, str]:
    if value > 0.5:
        return "Moves Like Tech", theme.COLORS["data"]["down"]
    if value >= 0:
        return "Weakly Correlated", theme.COLORS["data"]["accent"]
    return "Digital Gold Mode", theme.COLORS["data"]["primary"]


def _format_btc_price(value: float, _position: int) -> str:
    return f"${value / 1_000:.0f}K"


def build_chart() -> Path:
    """Build and save the BTC/Nasdaq rolling correlation chart."""
    df = get_btc_nasdaq_correlation(years=5)
    if df.empty:
        raise RuntimeError("BTC/Nasdaq correlation data is empty.")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna().sort_values("date").reset_index(drop=True)

    print(f"相关性最高点: {df['correlation'].max():.2f}")
    print(f"相关性最低点: {df['correlation'].min():.2f}")
    print(f"当前30日均值: {df['correlation'].tail(30).mean():.2f}")

    chart = BaseChart()
    ax1 = chart.add_axes(theme.LAYOUT["correlation_axes"])
    ax2 = chart.add_axes(theme.LAYOUT["correlation_btc_axes"])

    ax1.plot(
        df["date"],
        df["correlation"],
        color=theme.COLORS["data"]["quaternary"],
        linewidth=2.0,
        label="90D Rolling Correlation",
        zorder=4,
    )
    ax1.fill_between(
        df["date"],
        0.5,
        df["correlation"],
        where=df["correlation"] > 0.5,
        color=theme.COLORS["data"]["down"],
        alpha=0.12,
        interpolate=True,
        linewidth=0,
    )
    ax1.fill_between(
        df["date"],
        0,
        df["correlation"],
        where=(df["correlation"] >= 0) & (df["correlation"] <= 0.5),
        color=theme.COLORS["data"]["accent"],
        alpha=0.08,
        interpolate=True,
        linewidth=0,
    )
    ax1.fill_between(
        df["date"],
        0,
        df["correlation"],
        where=df["correlation"] < 0,
        color=theme.COLORS["data"]["primary"],
        alpha=0.08,
        interpolate=True,
        linewidth=0,
    )

    ax1.set_ylim(-0.2, 1.0)
    ax1.set_yticks(CORRELATION_TICKS)
    ax1.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax1.set_ylabel("")
    ax1.tick_params(axis="x", labelbottom=False)
    ax1.axhline(0.5, color=theme.COLORS["data"]["down"], linestyle="--", linewidth=0.8)
    ax1.axhline(0, color=theme.COLORS["text"]["muted"], linestyle="--", linewidth=0.6)
    ax1.text(
        0.01,
        0.5,
        "High Correlation",
        transform=ax1.get_yaxis_transform(),
        color=theme.COLORS["data"]["down"],
        fontsize=8,
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="bottom",
    )

    ax2.plot(
        df["date"],
        df["btc_price"],
        color=theme.COLORS["data"]["primary"],
        linewidth=1.2,
        alpha=0.7,
        zorder=3,
    )
    ax2.fill_between(
        df["date"],
        df["btc_price"].min(),
        df["btc_price"],
        color=theme.COLORS["data"]["primary"],
        alpha=0.06,
        linewidth=0,
    )
    ax2.yaxis.set_major_formatter(FuncFormatter(_format_btc_price))
    ax2.set_ylabel("")
    ax2.grid(True, color=theme.COLORS["base"]["grid"], linewidth=theme.STYLE["grid_line_width"])

    x_min = df["date"].min()
    x_max = df["date"].max()
    ax1.set_xlim(x_min, x_max)
    ax2.set_xlim(x_min, x_max)
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=theme.AXES["max_date_ticks"]))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.tick_params(axis="x", labelsize=8)

    annotations = Annotations()
    for date_text, label in EVENTS:
        event_date = pd.Timestamp(date_text)
        if not x_min <= event_date <= x_max:
            continue
        annotations.add_event_line(
            ax1,
            event_date,
            label,
            line_color=theme.COLORS["text"]["hint"],
            line_width=0.8,
            linestyle="--",
            text_color=theme.COLORS["text"]["muted"],
            fontsize=8,
        )

    legend = ax1.legend(
        loc="upper left",
        facecolor=theme.COLORS["base"]["surface"],
        edgecolor=theme.COLORS["base"]["grid"],
        fontsize=9,
        labelcolor=theme.COLORS["text"]["primary"],
        framealpha=1.0,
    )
    for line in legend.get_lines():
        line.set_linewidth(2.0)

    chart.add_title(
        "BTC vs Nasdaq Correlation",
        "90-Day Rolling · Is BTC a Tech Stock or Digital Gold?",
    )

    current_value = df["correlation"].tail(30).mean()
    current_label, current_color = _current_state(current_value)
    chart.fig.text(
        theme.LAYOUT["correlation_callout"][0],
        theme.LAYOUT["correlation_callout"][1],
        f"{current_value:.2f}",
        color=current_color,
        fontsize=theme.TYPOGRAPHY["callout"]["size"],
        fontweight=theme.TYPOGRAPHY["callout"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="top",
    )
    chart.fig.text(
        theme.LAYOUT["correlation_callout"][0],
        theme.LAYOUT["correlation_callout"][1] - 0.075,
        current_label,
        color=current_color,
        fontsize=11,
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="top",
    )

    chart.add_source("Source: Yahoo Finance")
    chart.add_watermark()
    return chart.save("btc_nasdaq_correlation.png")


if __name__ == "__main__":
    build_chart()
