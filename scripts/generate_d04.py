"""Generate chart D-04: Lending stablecoin share vs BTC cycle."""

from __future__ import annotations

import os
from pathlib import Path
import math

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/crypto-charts-matplotlib")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib import transforms
from matplotlib.ticker import FixedLocator, FixedFormatter
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "cache" / "stablecoin_category_trend.parquet"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "D04_lending_btc_cycle.png"

BACKGROUND = "#0A0E1A"
PRIMARY = "#4FC3F7"
ACCENT = "#FFD166"
TEXT_PRIMARY = "#E8EAF0"
TEXT_MUTED = "#8A8FA8"
GRID = "#2A2E3A"
REFERENCE = "#3A3E4A"

WIDTH_PX = 1200
HEIGHT_PX = 675
DPI = 150


def main() -> int:
    _configure_fonts()
    df = _load_data()

    fig, ax1 = plt.subplots(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI)
    fig.patch.set_facecolor(BACKGROUND)
    ax1.set_facecolor(BACKGROUND)
    ax2 = ax1.twinx()
    ax2.set_facecolor(BACKGROUND)

    _style_axes(ax1, ax2, df)
    _plot_lines(ax1, ax2, df)
    _add_reference_lines(ax1)
    _add_titles(fig)
    _add_legend(ax1, ax2)
    _add_footer(fig)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=DPI, bbox_inches="tight", facecolor=BACKGROUND, pad_inches=0.05)
    plt.close(fig)
    _ensure_canvas_size(OUTPUT_PATH)

    print(f"Saved: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Lending_pct range: {df['Lending_pct'].min():.1f}% – {df['Lending_pct'].max():.1f}%")
    print(f"BTC price range: ${df['btc_price'].min():,.0f} – ${df['btc_price'].max():,.0f}")
    return 0


def _configure_fonts() -> None:
    candidates = ["PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
    available = {font.name for font in font_manager.fontManager.ttflist}
    chosen = next((font for font in candidates if font in available), "DejaVu Sans")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [chosen, *candidates]
    plt.rcParams["axes.unicode_minus"] = False


def _load_data() -> pd.DataFrame:
    df = pd.read_parquet(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.tz_convert(None).dt.normalize()
    df["Lending_pct"] = pd.to_numeric(df["Lending_pct"], errors="coerce")
    df["btc_price"] = pd.to_numeric(df["btc_price"], errors="coerce")
    df = df.dropna(subset=["date", "Lending_pct", "btc_price"]).sort_values("date")
    return df[df["date"] >= pd.Timestamp("2021-01-01")].reset_index(drop=True)


def _style_axes(ax1, ax2, df: pd.DataFrame) -> None:
    ax1.set_ylim(0, 20)
    ax1.set_yticks([0, 5, 10, 15, 20])
    ax1.set_ylabel("稳定币存入Lending占全链总量 (%)", color=PRIMARY, fontsize=9, labelpad=14)
    ax1.tick_params(axis="y", colors=PRIMARY, labelsize=8)

    btc_ticks = [20_000, 50_000, 100_000]
    btc_axis_min = max(1.0, float(df["btc_price"].min()) * 0.75)
    ax2.set_ylim(math.log10(btc_axis_min), math.log10(150_000))
    ax2.yaxis.set_major_locator(FixedLocator([math.log10(value) for value in btc_ticks]))
    ax2.yaxis.set_major_formatter(FixedFormatter(["$20K", "$50K", "$100K"]))
    ax2.set_ylabel("BTC 价格 (USD, 对数刻度)", color=ACCENT, fontsize=9, labelpad=14)
    ax2.tick_params(axis="y", colors=ACCENT, labelsize=8)

    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.tick_params(axis="x", colors=TEXT_MUTED, labelsize=8, rotation=30)

    ax1.grid(axis="y", color=GRID, linewidth=0.5, alpha=0.5)
    ax1.grid(axis="x", visible=False)
    ax2.grid(False)

    for ax in (ax1, ax2):
        for spine in ax.spines.values():
            spine.set_color(GRID)
            spine.set_linewidth(0.8)

    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax1.tick_params(axis="x", color=GRID)


def _plot_lines(ax1, ax2, df: pd.DataFrame) -> None:
    ax1.plot(df["date"], df["Lending_pct"], color=PRIMARY, linewidth=2.0, zorder=3, label="稳定币存入Lending占比")
    ax1.fill_between(df["date"], df["Lending_pct"], 0, color=PRIMARY, alpha=0.13, zorder=2)
    ax2.plot(df["date"], df["btc_price"].map(math.log10), color=ACCENT, linewidth=1.5, linestyle="--", zorder=2, label="BTC价格")
    ax1.set_xlim(df["date"].min(), df["date"].max())


def _add_reference_lines(ax1) -> None:
    references = [
        ("2021-03-31", "牛市中段\nLending 12.3%", TEXT_MUTED, 2.0, 0),
        ("2022-12-31", "熊市底部\nLending 1.5%", TEXT_MUTED, 2.5, 0),
        ("2025-09-30", "牛市顶部\nLending 15.6%", ACCENT, 2.0, 0),
        ("2026-04-30", "当前\nLending 4.8%", TEXT_MUTED, 4.2, -8),
    ]
    for date_text, label, color, y_value, x_offset in references:
        x = pd.Timestamp(date_text)
        ax1.axvline(x, color=REFERENCE, linewidth=0.8, linestyle=":", zorder=1)
        offset = transforms.ScaledTranslation(x_offset / 72, 0, ax1.figure.dpi_scale_trans)
        ax1.text(
            x,
            y_value,
            label,
            transform=ax1.transData + offset,
            ha="right" if label.startswith("当前") else "center",
            va="bottom",
            fontsize=8,
            color=color,
            fontweight="bold" if color == ACCENT else "normal",
            zorder=4,
        )


def _add_titles(fig) -> None:
    fig.text(
        0.08,
        0.955,
        "稳定币不是BTC的弹药库——它是杠杆的温度计",
        ha="left",
        va="top",
        fontsize=15,
        color=TEXT_PRIMARY,
        fontweight="bold",
    )
    fig.text(
        0.08,
        0.915,
        "Aave V3 + Compound 稳定币存入TVL占全链总量 vs BTC月末价格｜数据：DeFiLlama · 本地BTC缓存｜2021-01 至 2026-04",
        ha="left",
        va="top",
        fontsize=8,
        color=TEXT_MUTED,
    )


def _add_legend(ax1, ax2) -> None:
    handles_1, labels_1 = ax1.get_legend_handles_labels()
    handles_2, labels_2 = ax2.get_legend_handles_labels()
    legend = ax1.legend(
        handles_1 + handles_2,
        labels_1 + labels_2,
        loc="upper left",
        frameon=True,
        facecolor=BACKGROUND,
        edgecolor=GRID,
        fontsize=9,
    )
    for text in legend.get_texts():
        text.set_color(TEXT_MUTED)


def _add_footer(fig) -> None:
    fig.text(
        0.965,
        0.012,
        "@koalada18",
        ha="right",
        va="bottom",
        fontsize=8,
        color=TEXT_MUTED,
        family="monospace",
    )


def _ensure_canvas_size(path: Path) -> None:
    """Pad tight-bbox output back to the requested publication canvas."""
    try:
        from PIL import Image
    except ImportError:
        return

    image = Image.open(path).convert("RGB")
    if image.size == (WIDTH_PX, HEIGHT_PX):
        return

    canvas = Image.new("RGB", (WIDTH_PX, HEIGHT_PX), BACKGROUND)
    x = max((WIDTH_PX - image.width) // 2, 0)
    y = max((HEIGHT_PX - image.height) // 2, 0)
    canvas.paste(image, (x, y))
    canvas.save(path)


if __name__ == "__main__":
    raise SystemExit(main())
