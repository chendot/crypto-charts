"""Generate the perpetual DEX OI/volume quality ranking chart."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.base_chart import BaseChart
from config import theme
from utils.chart_utils import add_series_label, validate_title

import matplotlib.pyplot as plt


CHART_TITLE = "按 OI/Volume 重排：edgeX #7→#3，ApeX #5→#6"
SUBTITLE = (
    "Source: DeFiLlama derivatives | Period: 2026-05-14 snapshot | "
    "Method: OI/Vol = Current OI ÷ 30d Cumulative Volume"
)
SOURCE = "Source: DeFiLlama derivatives · Snapshot: 2026-05-14 · Units: OI/Vol %"
OUTPUT_FILENAME = "perp_dex_ranking.png"

PLATFORMS = [
    {"name": "Hyperliquid", "vol_rank": 1, "oi_vol": 5.05, "rank_change": "—"},
    {"name": "Aster", "vol_rank": 3, "oi_vol": 4.26, "rank_change": "↑"},
    {"name": "edgeX", "vol_rank": 7, "oi_vol": 2.12, "rank_change": "↑↑"},
    {"name": "Lighter", "vol_rank": 4, "oi_vol": 1.89, "rank_change": "—"},
    {"name": "Grvt", "vol_rank": 6, "oi_vol": 1.35, "rank_change": "↑"},
    {"name": "ApeX", "vol_rank": 5, "oi_vol": 0.38, "rank_change": "↓"},
]


def _bar_color(name: str) -> str:
    if name == "Hyperliquid":
        return theme.COLORS["data"]["primary"]
    if name == "edgeX":
        return theme.COLORS["content_series"]["A_lp"]
    if name == "ApeX":
        return theme.COLORS["data"]["accent"]
    return theme.COLORS["text"]["muted"]


def _rank_change_color(platform: dict[str, object]) -> str:
    name = str(platform["name"])
    if name == "edgeX":
        return theme.COLORS["content_series"]["A_lp"]
    if name == "ApeX":
        return theme.COLORS["data"]["accent"]
    return theme.COLORS["text"]["muted"]


def _style_axes(ax) -> None:
    t = theme.DESIGN_RULES["typography"]
    c = theme.DESIGN_RULES["color"]
    g = theme.DESIGN_RULES["grid"]

    for name, spine in ax.spines.items():
        spine.set_visible(name in ("left", "bottom"))
        spine.set_color(theme.COLORS["base"]["grid"])
        spine.set_linewidth(g["gridline_linewidth"])

    ax.tick_params(
        axis="x",
        colors=theme.COLORS["text"]["muted"],
        labelsize=t["tick_label_size"],
        length=0,
    )
    ax.tick_params(axis="y", length=0, labelleft=False)
    for label in ax.get_xticklabels():
        label.set_alpha(c["axis_label_alpha"])

    ax.xaxis.label.set_color(theme.COLORS["text"]["muted"])
    ax.xaxis.label.set_alpha(c["axis_label_alpha"])
    ax.xaxis.label.set_size(t["axis_label_size"])
    ax.xaxis.set_major_locator(plt.MaxNLocator(g["max_h_gridlines"]))
    ax.grid(
        axis="x",
        linestyle=g["gridline_style"],
        linewidth=g["gridline_linewidth"],
        color=theme.COLORS["base"]["grid"],
        alpha=c["gridline_alpha"],
    )
    ax.grid(axis="y", visible=False)


def _draw_y_labels(ax, y_positions: range) -> None:
    t = theme.DESIGN_RULES["typography"]
    c = theme.DESIGN_RULES["color"]
    settings = theme.PERP_DEX_RANKING
    transform = ax.get_yaxis_transform()

    for y, platform in zip(y_positions, PLATFORMS):
        name = str(platform["name"])
        ax.text(
            settings["label_name_x"],
            y,
            name,
            transform=transform,
            ha="right",
            va="center",
            fontsize=t["axis_label_size"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            color=theme.COLORS["text"]["primary"],
            clip_on=False,
        )
        ax.text(
            settings["label_rank_x"],
            y,
            f"Vol #{platform['vol_rank']}",
            transform=transform,
            ha="right",
            va="center",
            fontsize=t["tick_label_size"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            color=theme.COLORS["text"]["muted"],
            alpha=c["axis_label_alpha"],
            clip_on=False,
        )


def _draw_reference_line(ax) -> None:
    t = theme.DESIGN_RULES["typography"]
    settings = theme.PERP_DEX_RANKING
    value = settings["reference_value"]
    apex_y = len(PLATFORMS) - 1

    ax.axvline(
        value,
        color=theme.COLORS["data"]["accent"],
        linewidth=theme.STYLE["grid_line_width"],
        linestyle=theme.DESIGN_RULES["grid"]["gridline_style"],
        alpha=settings["reference_alpha"],
        zorder=1,
    )
    ax.annotate(
        f"均值 {value:.2f}%",
        xy=(value, apex_y - settings["reference_label_y_offset"]),
        xytext=settings["reference_label_offset"],
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=t["annotation_label_size"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        color=theme.COLORS["data"]["accent"],
    )


def _draw_bar_break(ax, y_positions: range) -> None:
    t = theme.DESIGN_RULES["typography"]
    settings = theme.PERP_DEX_RANKING
    y = next(y for y, platform in zip(y_positions, PLATFORMS) if platform["name"] == "Hyperliquid")
    slash_x = settings["break_x"]
    dx = settings["break_slash_dx"]
    dy = settings["break_slash_dy"]
    gap = settings["break_slash_gap"]

    for x in (slash_x - gap, slash_x + gap):
        ax.plot(
            [x - dx, x + dx],
            [y + dy, y - dy],
            color=theme.COLORS["base"]["background"],
            linewidth=settings["break_linewidth"],
            solid_capstyle="round",
            zorder=5,
        )

    ax.text(
        settings["hyperliquid_note_x"],
        y + settings["hyperliquid_note_y_offset"],
        "超出均值 59%",
        ha="left",
        va="center",
        fontsize=t["annotation_label_size"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        color=theme.COLORS["text"]["muted"],
        zorder=6,
    )


def _annotate_bars(ax, y_positions: range) -> None:
    t = theme.DESIGN_RULES["typography"]
    settings = theme.PERP_DEX_RANKING

    for y, platform in zip(y_positions, PLATFORMS):
        value = float(platform["oi_vol"])
        color = _bar_color(str(platform["name"]))
        if platform["name"] == "Hyperliquid":
            value_x = settings["hyperliquid_value_x"]
            rank_change_x = settings["hyperliquid_rank_change_x"]
        else:
            value_x = value + settings["value_offset"]
            rank_change_x = value_x + settings["rank_change_offset"]
        ax.text(
            value_x,
            y,
            f"{value:.2f}%",
            ha="left",
            va="center",
            fontsize=t["axis_label_size"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            color=color,
            clip_on=False,
        )
        ax.text(
            rank_change_x,
            y,
            str(platform["rank_change"]),
            ha="left",
            va="center",
            fontsize=t["annotation_label_size"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            color=_rank_change_color(platform),
            clip_on=False,
        )


def _display_value(platform: dict[str, object]) -> float:
    if platform["name"] == "Hyperliquid":
        return theme.PERP_DEX_RANKING["hyperliquid_display_value"]
    return float(platform["oi_vol"])


def build_chart() -> Path:
    """Build and save the perpetual DEX OI/volume ranking chart."""
    validate_title(CHART_TITLE)

    chart = BaseChart()
    chart.add_title(CHART_TITLE, SUBTITLE)
    add_series_label(chart.fig, "F_ranking")

    l = theme.DESIGN_RULES["layout"]
    chart.fig.subplots_adjust(
        left=l["margin_left"],
        right=1 - l["margin_right"],
        top=1 - l["margin_top"],
        bottom=l["margin_bottom"],
    )
    ax = chart.fig.add_subplot(111, facecolor=theme.COLORS["base"]["background"])

    settings = theme.PERP_DEX_RANKING
    y_positions = range(len(PLATFORMS))
    values = [_display_value(platform) for platform in PLATFORMS]
    colors = [_bar_color(str(platform["name"])) for platform in PLATFORMS]

    ax.barh(y_positions, values, height=settings["bar_height"], color=colors, zorder=3)
    ax.set_xlim(settings["xlim"])
    ax.set_xlabel("OI/Vol (%)")
    ax.invert_yaxis()
    ax.set_ylim(len(PLATFORMS) - settings["bar_height"], -settings["top_padding"])
    _style_axes(ax)
    _draw_y_labels(ax, y_positions)
    _draw_reference_line(ax)
    _draw_bar_break(ax, y_positions)
    _annotate_bars(ax, y_positions)

    chart.add_source(SOURCE, position=settings["source_position"])
    chart.add_watermark()
    return chart.save(OUTPUT_FILENAME, bbox_inches="tight")


if __name__ == "__main__":
    build_chart()
