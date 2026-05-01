"""Generate a BTC 30-day price and volume chart for X publishing."""

from __future__ import annotations

from datetime import timedelta
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.annotations import Annotations
from components.base_chart import BaseChart
from components.price_line import PriceLine
from components.volume_bar import VolumeBar
from config import theme
from data.fetcher import get_price_history


def normalize_daily_history(df):
    """Collapse intraday duplicate rows into one daily observation."""
    daily_df = df.copy()
    daily_df["date"] = daily_df["date"].dt.floor(theme.DATA_RULES["market_history_frequency"])
    return (
        daily_df.groupby("date", as_index=False)
        .agg(theme.DATA_RULES["daily_duplicate_aggregation"])
        .sort_values("date")
        .reset_index(drop=True)
    )


def build_chart() -> Path:
    """Build and save the BTC 30-day market chart."""
    df = normalize_daily_history(get_price_history("bitcoin", 30))
    current_price = df["price"].iloc[-1]
    pct_change = (current_price / df["price"].iloc[0] - 1) * 100

    chart = BaseChart()
    chart.add_title("Bitcoin 30D Market Structure", "BTC price trend and daily spot volume")

    price_ax = chart.add_axes(theme.LAYOUT["price_axes"])
    volume_ax = chart.add_axes(theme.LAYOUT["volume_axes"])
    price_ax.tick_params(labelbottom=False)

    PriceLine().draw(price_ax, df["date"], df["price"])
    VolumeBar().draw(volume_ax, df["date"], df["volume"], df["price"])
    common_xlim = (
        df["date"].min(),
        df["date"].iloc[-1] + timedelta(days=theme.AXES["right_padding_days"]),
    )
    price_ax.set_xlim(common_xlim)
    volume_ax.set_xlim(common_xlim)

    annotations = Annotations()
    annotations.add_callout(
        chart.fig,
        f"${current_price:,.0f}",
        "Current BTC price",
        tuple(theme.LAYOUT["callout_default"]),
    )
    annotations.add_pct_change(chart.fig, pct_change, tuple(theme.LAYOUT["pct_default"]))

    chart.add_source("Source: CoinGecko")
    chart.add_watermark()
    return chart.save("btc_30d.png")


if __name__ == "__main__":
    build_chart()
