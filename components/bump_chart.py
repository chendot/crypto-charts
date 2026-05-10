"""Reusable visual component for rank-over-time bump charts."""

from __future__ import annotations

import math

from matplotlib import colors as mcolors
import pandas as pd
from matplotlib.axes import Axes

from config import theme


def draw_bump_chart(
    ax: Axes,
    df: pd.DataFrame,
    highlight_top: int = 3,
    highlight_bottom: int = 2,
    category_colors: dict | None = None,
) -> None:
    """Draw a Messari-style rank-over-time bump chart."""
    if df.empty:
        raise ValueError("Bump chart requires at least one row")

    plot_df = df.copy()
    plot_df["week"] = pd.to_datetime(plot_df["week"]).dt.tz_localize(None)
    plot_df["rank"] = pd.to_numeric(plot_df["rank"], errors="coerce")
    plot_df = plot_df.sort_values(["week", "rank", "category"]).reset_index(drop=True)

    weeks = sorted(plot_df["week"].drop_duplicates())
    x_positions = {week: index for index, week in enumerate(weeks)}
    latest_week = weeks[-1]
    latest_df = plot_df[plot_df["week"] == latest_week].sort_values("rank").reset_index(drop=True)
    latest_ranks = dict(zip(latest_df["category"], latest_df["rank"]))
    categories = list(latest_df["category"])
    label_map = dict(plot_df.attrs.get("category_labels", {}))

    _style_axes(ax, len(weeks))
    ax.set_xticklabels([pd.Timestamp(week).strftime("%m/%d") for week in weeks])

    for category in reversed(categories):
        category_df = plot_df[plot_df["category"] == category].sort_values("week")
        xs = [x_positions[week] for week in category_df["week"]]
        ys = category_df["rank"].astype(float).tolist()
        style = _series_style(
            category,
            latest_ranks,
            highlight_top=highlight_top,
            highlight_bottom=highlight_bottom,
            category_colors=category_colors or {},
        )
        ax.plot(
            xs,
            ys,
            color=style["line_color"],
            linewidth=style["linewidth"],
            alpha=style["alpha"],
            marker="o",
            markersize=style["markersize"],
            markerfacecolor=style["markerfacecolor"],
            markeredgecolor=style["line_color"],
            markeredgewidth=style["markeredgewidth"],
            solid_capstyle="round",
            zorder=style["zorder"],
        )

    _draw_right_labels(
        ax,
        plot_df,
        latest_df,
        x_positions,
        label_map=label_map,
        highlight_top=highlight_top,
        category_colors=category_colors or {},
    )


def _draw_right_labels(
    ax: Axes,
    plot_df: pd.DataFrame,
    latest_df: pd.DataFrame,
    x_positions: dict[pd.Timestamp, int],
    *,
    label_map: dict[str, str],
    highlight_top: int,
    category_colors: dict[str, str],
) -> None:
    """Render right-edge labels and move indicators without overlapping."""
    categories = latest_df["category"].tolist()
    current_positions = {row["category"]: float(row["rank"]) for _, row in latest_df.iterrows()}
    adjusted_positions = _adjust_label_positions([current_positions[category] for category in categories])
    latest_week = pd.to_datetime(latest_df["week"].iloc[0]).tz_localize(None)
    previous_weeks = sorted(plot_df["week"].drop_duplicates())
    previous_week = previous_weeks[-2] if len(previous_weeks) > 1 else None
    previous_ranks = {}
    if previous_week is not None:
        previous_df = plot_df[plot_df["week"] == previous_week]
        previous_ranks = dict(zip(previous_df["category"], previous_df["rank"]))

    label_x = x_positions[latest_week] + theme.STYLE["bump_label_offset_x"]
    arrow_x = x_positions[latest_week] + theme.STYLE["bump_arrow_offset_x"]
    for category, y_position in zip(categories, adjusted_positions):
        is_top = int(current_positions[category]) <= highlight_top
        base_color = category_colors.get(category, theme.COLORS["data"]["primary"])
        label_color = base_color if is_top else theme.COLORS["text"]["label_muted"]
        font_size = 9 if is_top else 8
        font_weight = theme.TYPOGRAPHY["title"]["weight"] if is_top else theme.TYPOGRAPHY["annotation"]["weight"]
        ax.text(
            label_x,
            y_position,
            label_map.get(category, category),
            color=label_color,
            fontsize=font_size,
            fontweight=font_weight,
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="left",
            va="center",
            zorder=6,
        )
        arrow = _rank_change_arrow(previous_ranks.get(category), current_positions[category])
        if arrow:
            ax.text(
                arrow_x,
                y_position,
                arrow,
                color=theme.COLORS["data"]["mint"] if arrow == "↑" else theme.COLORS["data"]["rose"],
                fontsize=font_size,
                fontweight=theme.TYPOGRAPHY["title"]["weight"],
                fontfamily=theme.TYPOGRAPHY["font_family"],
                ha="left",
                va="center",
                zorder=6,
            )


def _style_axes(ax: Axes, week_count: int) -> None:
    """Apply shared Midnight Blueprint styling to the bump chart axes."""
    ax.grid(False)
    ax.set_facecolor(theme.COLORS["base"]["background"])
    ax.set_ylim(0.5, 10.5)
    ax.invert_yaxis()
    ax.set_yticks(range(1, 11))
    ax.set_yticklabels([_ordinal(rank) for rank in range(1, 11)])
    ax.set_xticks(range(week_count))
    ax.tick_params(axis="x", colors=theme.COLORS["text"]["muted"], labelsize=theme.TYPOGRAPHY["axis"]["size"], length=0)
    ax.tick_params(axis="y", colors=theme.COLORS["text"]["muted"], labelsize=theme.TYPOGRAPHY["axis"]["size"], length=0, pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(theme.COLORS["base"]["grid"])
    ax.spines["bottom"].set_linewidth(0.8)
    ax.set_xlim(-0.15, max(week_count - 1, 0) + 1.35)


def _series_style(
    category: str,
    latest_ranks: dict[str, int],
    *,
    highlight_top: int,
    highlight_bottom: int,
    category_colors: dict[str, str],
) -> dict[str, object]:
    """Return line and marker styling for one category series."""
    rank = int(latest_ranks[category])
    base_color = category_colors.get(category, theme.COLORS["data"]["primary"])
    if rank <= highlight_top:
        return {
            "line_color": base_color,
            "linewidth": 2.5,
            "alpha": 1.0,
            "markersize": 5,
            "markerfacecolor": base_color,
            "markeredgewidth": 0.0,
            "zorder": 4,
        }
    if rank > len(latest_ranks) - highlight_bottom:
        faded_color = _blend_with_background(base_color, 0.55)
        return {
            "line_color": faded_color,
            "linewidth": 1.0,
            "alpha": 0.3,
            "markersize": 3,
            "markerfacecolor": theme.COLORS["base"]["background"],
            "markeredgewidth": 0.9,
            "zorder": 2,
        }
    faded_color = _blend_with_background(base_color, 0.38)
    return {
        "line_color": faded_color,
        "linewidth": 1.2,
        "alpha": 0.5,
        "markersize": 3,
        "markerfacecolor": theme.COLORS["base"]["background"],
        "markeredgewidth": 0.9,
        "zorder": 3,
    }


def _adjust_label_positions(positions: list[float]) -> list[float]:
    """Space label positions apart to avoid right-edge overlap."""
    if not positions:
        return []
    gap = theme.STYLE["bump_label_min_gap"]
    adjusted = positions[:]
    for index in range(1, len(adjusted)):
        adjusted[index] = max(adjusted[index], adjusted[index - 1] + gap)
    for index in range(len(adjusted) - 2, -1, -1):
        adjusted[index] = min(adjusted[index], adjusted[index + 1] - gap)
    for index, position in enumerate(adjusted):
        adjusted[index] = min(max(position, 1.0), 10.0)
    return adjusted


def _rank_change_arrow(previous_rank: float | None, current_rank: float) -> str:
    """Return an arrow when a category moved materially week over week."""
    if previous_rank is None or math.isnan(float(previous_rank)):
        return ""
    delta = float(previous_rank) - float(current_rank)
    if delta >= 2:
        return "↑"
    if delta <= -2:
        return "↓"
    return ""


def _ordinal(value: int) -> str:
    """Format a small positive integer as an English ordinal."""
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def _blend_with_background(color: str, mix: float) -> str:
    """Blend a category color toward the chart background for lower emphasis."""
    base_rgb = mcolors.to_rgb(color)
    background_rgb = mcolors.to_rgb(theme.COLORS["base"]["background"])
    blended = tuple((1 - mix) * channel + mix * background for channel, background in zip(base_rgb, background_rgb))
    return mcolors.to_hex(blended)
