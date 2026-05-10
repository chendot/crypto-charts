"""Grouped ETF flow bars with zero-aligned cumulative net-flow overlay."""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from config import theme


def draw_grouped_bars_with_cumulative(
    ax: Axes,
    df: pd.DataFrame,
    *,
    featured_issuers: tuple[str, ...],
    issuer_colors: dict[str, str],
    date_column: str = "date",
    category_column: str = "ticker",
    value_column: str = "flow_usd",
) -> None:
    """Draw daily ETF flow bars and a zero-aligned cumulative net-flow overlay."""
    if df.empty:
        raise ValueError("ETF flow chart requires at least one row")

    plot_df = _prepare_plot_frame(
        df,
        date_column,
        category_column,
        value_column,
        featured_issuers=featured_issuers,
    )
    categories = (*featured_issuers, "Others")
    dates = list(plot_df.index)
    positions = np.arange(len(dates))
    cumulative = plot_df[list(categories)].sum(axis=1).cumsum()

    line_ax = ax.twinx()
    l_min, l_max, r_min, r_max = align_dual_axes(
        float(plot_df[list(categories)].min().min()),
        float(plot_df[list(categories)].max().max()),
        float(cumulative.min()),
        float(cumulative.max()),
    )
    ax.set_ylim(l_min, l_max)
    line_ax.set_ylim(r_min, r_max)

    _style_left_axis(ax)
    _style_right_axis(line_ax)
    _draw_zero_line(ax)
    _draw_cumulative_line(line_ax, cumulative, positions)
    _draw_daily_bars(ax, plot_df, positions, categories, issuer_colors)

    ax.set_xticks(positions)
    ax.set_xticklabels([pd.Timestamp(item).strftime("%m/%d") for item in dates])
    ax.set_xlim(-0.5, len(positions) - 0.5)
    line_ax.set_xlim(ax.get_xlim())
    _annotate_low_point(line_ax, cumulative, positions)
    ax.yaxis.set_major_formatter(FuncFormatter(_format_signed_flow_axis))
    line_ax.yaxis.set_major_formatter(FuncFormatter(_format_signed_flow_axis))
    _set_right_axis_ticks(line_ax)
    _align_right_tick_labels(line_ax)
    _add_legend(ax, categories)


def _draw_daily_bars(
    ax: Axes,
    plot_df: pd.DataFrame,
    positions: np.ndarray,
    categories: tuple[str, ...],
    issuer_colors: dict[str, str],
) -> None:
    """Draw equal-width grouped bars on a numeric x axis."""
    bar_width = min(theme.STYLE["etf_bar_width"] * 1.25, 0.18)
    offset_start = -bar_width * (len(categories) - 1) / 2

    for index, category in enumerate(categories):
        ax.bar(
            positions + offset_start + index * bar_width,
            plot_df[category].to_numpy(),
            width=bar_width,
            color=issuer_colors[category],
            alpha=0.85,
            edgecolor="none",
            label=category,
            zorder=3,
        )


def _draw_cumulative_line(ax: Axes, cumulative: pd.Series, positions: np.ndarray) -> None:
    """Draw the cumulative flow line on the right axis."""
    ax.plot(
        positions,
        cumulative.to_numpy(),
        color=theme.COLORS["etf"]["cumulative"],
        alpha=0.6,
        linewidth=1.2,
        linestyle="-",
        marker=None,
        label="Cumulative net flow",
        zorder=2,
    )


def _annotate_low_point(ax: Axes, cumulative: pd.Series, positions: np.ndarray) -> None:
    """Annotate the actual cumulative low point."""
    cumulative_values = cumulative.to_numpy(dtype=float)
    low_position = int(np.nanargmin(cumulative_values))
    low_value = float(cumulative_values[low_position])
    low_date = cumulative.index[low_position]
    ax.annotate(
        f"{pd.Timestamp(low_date).strftime('%m/%d')} {_format_signed_flow(low_value)}",
        xy=(positions[low_position], low_value),
        xytext=(-14, 12),
        textcoords="offset points",
        color=theme.COLORS["etf"]["gbtc"],
        fontsize=max(theme.TYPOGRAPHY["annotation"]["size"] - 1, 7),
        fontweight=theme.TYPOGRAPHY["title"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="right",
        va="bottom",
        zorder=4,
    )
    final_position = len(cumulative_values) - 1
    final_value = float(cumulative_values[final_position])
    ax.annotate(
        _format_signed_flow(final_value),
        xy=(positions[final_position], final_value),
        xytext=(10, 0),
        textcoords="offset points",
        color=theme.COLORS["etf"]["cumulative"],
        fontsize=max(theme.TYPOGRAPHY["annotation"]["size"] - 1, 7),
        fontweight=theme.TYPOGRAPHY["annotation"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="center",
        zorder=4,
    )


def _prepare_plot_frame(
    df: pd.DataFrame,
    date_column: str,
    category_column: str,
    value_column: str,
    *,
    featured_issuers: tuple[str, ...],
) -> pd.DataFrame:
    """Collapse ETF flow rows into featured issuers plus Others by date."""
    working_df = df.copy()
    featured = set(featured_issuers)
    working_df["plot_category"] = working_df[category_column].where(
        working_df[category_column].isin(featured),
        "Others",
    )
    categories = (*featured_issuers, "Others")
    pivot = working_df.pivot_table(
        index=date_column,
        columns="plot_category",
        values=value_column,
        aggfunc="sum",
        fill_value=0.0,
    )
    pivot.index = pd.to_datetime(pivot.index).tz_localize(None)
    return pivot.reindex(columns=categories, fill_value=0.0).sort_index()


def _draw_zero_line(ax: Axes) -> None:
    """Draw a zero baseline shared by both aligned axes."""
    ax.axhline(
        0,
        color=theme.COLORS["text"]["hint"],
        linewidth=0.5,
        zorder=1,
    )


def align_dual_axes(
    l_min: float,
    l_max: float,
    r_min: float,
    r_max: float,
    pad: float = 0.15,
) -> tuple[float, float, float, float]:
    """Return full-data ranges whose zero lines align without clipping the cumulative line."""
    unit = 1_000_000
    l_min_m = l_min / unit
    l_max_m = l_max / unit
    r_min_m = r_min / unit
    r_max_m = r_max / unit

    l_pad = max((l_max_m - l_min_m) * pad, 50)
    l_lo = l_min_m - l_pad
    l_hi = l_max_m + l_pad

    r_pad = max((r_max_m - r_min_m) * pad, 50)
    r_lo_raw = r_min_m - r_pad
    r_hi_raw = r_max_m + r_pad

    left_zero = (-l_lo) / (l_hi - l_lo)
    right_zero = (-r_lo_raw) / (r_hi_raw - r_lo_raw)
    zero_frac = min(max(left_zero, right_zero), 0.999)
    l_lo, l_hi = _expand_range_to_zero_frac(l_lo, l_hi, zero_frac)
    r_lo, r_hi = _expand_range_to_zero_frac(r_lo_raw, r_hi_raw, zero_frac)

    left_zero = (-l_lo) / (l_hi - l_lo)
    right_zero = (-r_lo) / (r_hi - r_lo)
    assert abs(left_zero - right_zero) < 0.001, f"零线未对齐: left={left_zero:.4f}, right={right_zero:.4f}"
    return l_lo * unit, l_hi * unit, r_lo * unit, r_hi * unit


def _expand_range_to_zero_frac(lo: float, hi: float, zero_frac: float) -> tuple[float, float]:
    """Expand a range so zero sits at zero_frac while preserving all data."""
    lo_required = -zero_frac * hi / (1 - zero_frac)
    hi_required = (-lo) * (1 - zero_frac) / zero_frac
    return min(lo, lo_required), max(hi, hi_required)


def _style_left_axis(ax: Axes) -> None:
    """Style the primary daily-flow axis."""
    ax.tick_params(axis="y", colors=theme.COLORS["text"]["muted"], labelsize=theme.TYPOGRAPHY["axis"]["size"])
    ax.tick_params(axis="x", colors=theme.COLORS["text"]["muted"], labelsize=theme.TYPOGRAPHY["axis"]["size"], length=0)
    ax.grid(True, axis="y", color=theme.COLORS["base"]["grid"], linewidth=0.5)
    ax.grid(False, axis="x")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(theme.COLORS["text"]["hint"])
    ax.spines["bottom"].set_color(theme.COLORS["text"]["hint"])
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)


def _style_right_axis(ax: Axes) -> None:
    """Style the secondary cumulative-flow axis."""
    tick_size = max(theme.TYPOGRAPHY["axis"]["size"] - 1, 7)
    ax.tick_params(axis="y", colors=theme.COLORS["text"]["muted"], labelsize=tick_size, length=0, pad=-32)
    for label in ax.get_yticklabels():
        label.set_horizontalalignment("left")
    ax.grid(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)


def _set_right_axis_ticks(ax: Axes) -> None:
    """Only show the right-axis zero tick to avoid cross-axis value comparisons."""
    ax.set_yticks([0.0])


def _align_right_tick_labels(ax: Axes) -> None:
    """Keep right-axis labels inside the plot so they do not collide with callouts."""
    labels = ax.get_yticklabels()
    for label in labels:
        label.set_horizontalalignment("left")


def _add_legend(ax: Axes, categories: tuple[str, ...]) -> None:
    """Place issuer and cumulative-flow legend items inside the chart."""
    cumulative_handle = Line2D(
        [0],
        [0],
        color=theme.COLORS["etf"]["cumulative"],
        alpha=0.6,
        linewidth=1.2,
        linestyle="-",
        label="Cumulative net flow",
    )
    ax.legend(
        handles=[*ax.containers, cumulative_handle],
        labels=(*categories, "Cumulative net flow"),
        loc="upper left",
        frameon=False,
        labelcolor=theme.COLORS["text"]["muted"],
        fontsize=max(theme.TYPOGRAPHY["annotation"]["size"] - 1, 7),
        ncols=5,
        borderaxespad=0.6,
        columnspacing=0.7,
        handlelength=1.2,
        handletextpad=0.35,
    )


def _format_signed_flow_axis(value: float, _position: int) -> str:
    """Format y-axis flow values as signed USD amounts."""
    if abs(value) < 1e-9:
        return "$0M"
    return _format_signed_flow(value)


def _format_signed_flow(value: float) -> str:
    """Format a signed ETF flow amount for direct line annotations."""
    sign = "+" if value >= 0 else "-"
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"{sign}${absolute / 1_000_000_000:,.1f}B"
    return f"{sign}${absolute / 1_000_000:,.0f}M"
