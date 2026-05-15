"""Generate the perpetual DEX volume vs open-interest quality scatter chart."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.base_chart import BaseChart
from config import theme
from utils.chart_utils import add_series_label, validate_title

from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter, NullLocator


CHART_TITLE = "成交量排名 ≠ 持仓质量"
SUBTITLE = (
    "Source: DeFiLlama derivatives | Period: 2026-05-14 snapshot | "
    "Method: OI/Vol = Current OI ÷ 30d Cumulative Volume"
)
SOURCE = "Source: DeFiLlama derivatives · Snapshot: 2026-05-14 · Units: $b"
OUTPUT_FILENAME = "perp_dex_scatter.png"

PLATFORMS = {
    "Hyperliquid": {"vol_30d": 176.4, "oi": 8.905},
    "Aster": {"vol_30d": 52.5, "oi": 2.236},
    "edgeX": {"vol_30d": 45.0, "oi": 0.953},
    "Lighter": {"vol_30d": 39.9, "oi": 0.755},
    "Grvt": {"vol_30d": 37.5, "oi": 0.506},
    "ApeX": {"vol_30d": 35.8, "oi": 0.137},
}


def _point_color(name: str) -> str:
    if name == "Hyperliquid":
        return theme.COLORS["data"]["primary"]
    if name == "edgeX":
        return theme.COLORS["content_series"]["A_lp"]
    if name == "ApeX":
        return theme.COLORS["data"]["accent"]
    return theme.COLORS["text"]["muted"]


def _point_size(name: str) -> int:
    sizes = theme.PERP_DEX_SCATTER["marker_sizes"]
    return sizes["featured"] if name == "Hyperliquid" else sizes["default"]


def _annotation_detail(name: str, values: dict[str, float]) -> tuple[str | None, str]:
    if name == "Hyperliquid":
        return f"OI/Vol {values['oi'] / values['vol_30d']:.2%}", theme.COLORS["text"]["muted"]
    if name == "edgeX":
        return "成交量#7 → OI质量#3", theme.COLORS["content_series"]["A_lp"]
    if name == "ApeX":
        return f"OI/Vol {values['oi'] / values['vol_30d']:.2%}", theme.COLORS["text"]["muted"]
    return None, theme.COLORS["text"]["muted"]


def _style_axes(ax) -> None:
    t = theme.DESIGN_RULES["typography"]
    c = theme.DESIGN_RULES["color"]
    g = theme.DESIGN_RULES["grid"]
    settings = theme.PERP_DEX_SCATTER

    for name, spine in ax.spines.items():
        spine.set_visible(name in ("left", "bottom"))
        spine.set_color(theme.COLORS["base"]["grid"])
        spine.set_linewidth(g["gridline_linewidth"])

    ax.tick_params(
        axis="both",
        colors=theme.COLORS["text"]["muted"],
        labelsize=t["tick_label_size"],
        length=0,
    )
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_alpha(c["axis_label_alpha"])
        label.set_zorder(settings["tick_label_zorder"])

    ax.xaxis.label.set_color(theme.COLORS["text"]["muted"])
    ax.xaxis.label.set_alpha(c["axis_label_alpha"])
    ax.xaxis.label.set_size(t["axis_label_size"])
    ax.yaxis.label.set_color(theme.COLORS["text"]["muted"])
    ax.yaxis.label.set_alpha(c["axis_label_alpha"])
    ax.yaxis.label.set_size(t["axis_label_size"])
    ax.grid(
        axis="both",
        linestyle=g["gridline_style"],
        linewidth=g["gridline_linewidth"],
        color=theme.COLORS["base"]["grid"],
        alpha=c["gridline_alpha"],
    )


def _format_b_tick(value: float) -> str:
    return f"${value:g}b"


def _apply_log_ticks(ax) -> None:
    settings = theme.PERP_DEX_SCATTER
    ax.xaxis.set_major_locator(FixedLocator(settings["x_ticks"]))
    ax.xaxis.set_major_formatter(NullFormatter())
    ax.yaxis.set_major_locator(FixedLocator(settings["y_ticks"]))
    ax.yaxis.set_major_formatter(FixedFormatter([_format_b_tick(value) for value in settings["y_ticks"]]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_minor_locator(NullLocator())


def _draw_x_tick_labels(ax) -> None:
    t = theme.DESIGN_RULES["typography"]
    c = theme.DESIGN_RULES["color"]
    settings = theme.PERP_DEX_SCATTER

    first_tick = settings["x_ticks"][0]
    for value in settings["x_ticks"]:
        ax.text(
            value,
            settings["x_tick_label_y"],
            _format_b_tick(value),
            transform=ax.get_xaxis_transform(),
            ha="left" if value == first_tick else "center",
            va="top",
            fontsize=t["tick_label_size"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            color=theme.COLORS["text"]["muted"],
            alpha=c["axis_label_alpha"],
            clip_on=False,
            zorder=settings["tick_label_zorder"],
        )


def _draw_reference_line(ax) -> None:
    t = theme.DESIGN_RULES["typography"]
    c = theme.DESIGN_RULES["color"]
    settings = theme.PERP_DEX_SCATTER
    (x_start, y_start), (x_end, y_end) = settings["reference_points"]

    ax.plot(
        [x_start, x_end],
        [y_start, y_end],
        color=theme.COLORS["data"]["accent"],
        linewidth=theme.STYLE["grid_line_width"],
        linestyle=theme.DESIGN_RULES["grid"]["gridline_style"],
        alpha=settings["reference_alpha"],
        zorder=1,
    )
    ax.annotate(
        "OI/Vol = 3%",
        xy=(x_end, y_end),
        xytext=settings["reference_label_offset"],
        textcoords="offset points",
        ha="right",
        va="bottom",
        fontsize=t["tick_label_size"],
        fontstyle="italic",
        fontfamily=theme.TYPOGRAPHY["font_family"],
        color=theme.COLORS["data"]["accent"],
        alpha=c["axis_label_alpha"],
    )


def _annotate_point(ax, name: str, values: dict[str, float]) -> None:
    t = theme.DESIGN_RULES["typography"]
    settings = theme.PERP_DEX_SCATTER
    x = values["vol_30d"]
    y = values["oi"]
    x_offset, y_offset = settings["annotation_offsets"][name]
    ha = "left" if x_offset >= 0 else "right"

    ax.annotate(
        name,
        xy=(x, y),
        xytext=(x_offset, y_offset),
        textcoords="offset points",
        ha=ha,
        va="center",
        fontsize=t["annotation_label_size"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        color=theme.COLORS["text"]["primary"],
    )

    detail, color = _annotation_detail(name, values)
    if detail is None:
        return

    ax.annotate(
        detail,
        xy=(x, y),
        xytext=(x_offset, y_offset + settings["annotation_line_gap"]),
        textcoords="offset points",
        ha=ha,
        va="center",
        fontsize=t["annotation_label_size"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        color=color,
    )


def build_chart() -> Path:
    """Build and save the perpetual DEX ranking illusion chart."""
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

    settings = theme.PERP_DEX_SCATTER
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(settings["xlim"])
    ax.set_ylim(settings["ylim"])
    _apply_log_ticks(ax)
    ax.set_xlabel("30d Volume ($b)", labelpad=settings["x_label_pad"])
    ax.set_ylabel("Open Interest ($b)")
    _style_axes(ax)
    _draw_reference_line(ax)

    for name, values in PLATFORMS.items():
        ax.scatter(
            values["vol_30d"],
            values["oi"],
            s=_point_size(name),
            color=_point_color(name),
            zorder=3,
        )
        _annotate_point(ax, name, values)

    _draw_x_tick_labels(ax)
    chart.add_source(SOURCE, position=theme.PERP_DEX_SCATTER["source_position"])
    chart.add_watermark()
    return chart.save(OUTPUT_FILENAME, bbox_inches="tight")


if __name__ == "__main__":
    build_chart()
