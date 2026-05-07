"""T6: Narrative sector rotation bump chart template."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from components.base_chart import BaseChart
from components.bump_chart import draw_bump_chart
from config import theme
from config.templates import TemplateConfig, get_template_config
from data.fetchers.narrative_rotation import get_narrative_rotation
from templates.common import normalize_as_of, output_filename


def render(
    as_of: date | str | None = None,
    variant: str | None = None,
    title: str | None = None,
) -> Path:
    """Render T6 through the requested cutoff date and return the PNG path."""
    del variant
    publish_date = normalize_as_of(as_of)
    df = get_narrative_rotation(as_of=publish_date.isoformat())
    if df.empty:
        raise ValueError("No narrative rotation data available for T6")

    template_config = get_template_config("t6")
    plot_df = _prepare_plot_df(df, template_config)
    period_count = int(plot_df.attrs.get("periods", plot_df["week"].nunique()))
    granularity = str(plot_df.attrs.get("granularity", "weekly"))
    unit = "week" if granularity == "weekly" else "day"
    argument = title or _build_argument_title(plot_df)
    subtitle = template_config.text.subtitle.format(
        weeks=period_count,
        unit=unit,
        date_range=_format_date_range(plot_df),
    )

    chart = BaseChart()
    _add_t6_title(chart, argument, subtitle)
    ax = chart.add_axes(theme.LAYOUT["t6_axes"])
    draw_bump_chart(
        ax,
        plot_df,
        category_colors=dict((template_config.visual or {}).get("category_colors", {})),
    )
    _add_t6_source(chart, template_config.text.source)
    _add_t6_watermark(chart)
    return chart.save(output_filename("t6", publish_date))


def _prepare_plot_df(df: pd.DataFrame, template_config: TemplateConfig) -> pd.DataFrame:
    """Attach visual metadata to the normalized narrative rotation rows."""
    plot_df = df.copy()
    plot_df["week"] = pd.to_datetime(plot_df["week"]).dt.tz_localize(None)
    plot_df["rank"] = pd.to_numeric(plot_df["rank"], errors="coerce").astype(int)
    visual = template_config.visual or {}
    plot_df.attrs["category_labels"] = dict(visual.get("category_labels", {}))
    for key in ("granularity", "periods", "warning"):
        if key in df.attrs:
            plot_df.attrs[key] = df.attrs[key]
    return plot_df.sort_values(["week", "rank", "category"]).reset_index(drop=True)


def _build_argument_title(df: pd.DataFrame) -> str:
    """Create an argument-first narrative title from the latest rotation regime."""
    granularity = str(df.attrs.get("granularity", "weekly"))
    streak_unit = "weeks" if granularity == "weekly" else "days"
    weeks = sorted(pd.to_datetime(df["week"]).dt.tz_localize(None).drop_duplicates())
    latest_week = weeks[-1]
    latest_df = df[df["week"] == latest_week].sort_values("rank").reset_index(drop=True)
    leader = str(latest_df.iloc[0]["category"])
    streak = _top_streak_weeks(df, leader)
    if streak >= 3:
        return f"{leader} dominates — {streak} {streak_unit} at the top"

    if len(weeks) < 2:
        return f"{leader} sets the pace as the narrative board takes shape"

    previous_df = df[df["week"] == weeks[-2]][["category", "rank"]].rename(columns={"rank": "previous_rank"})
    current_df = latest_df[["category", "rank"]].rename(columns={"rank": "current_rank"})
    merged = current_df.merge(previous_df, on="category", how="left")
    merged["change"] = merged["previous_rank"] - merged["current_rank"]

    if merged["change"].abs().max() < 2:
        return "Narratives hold steady — no rotation this week"

    rising_star = str(merged.sort_values(["change", "current_rank"], ascending=[False, True]).iloc[0]["category"])
    fading = str(merged.sort_values(["change", "current_rank"], ascending=[True, True]).iloc[0]["category"])
    return f"{rising_star} takes the lead as {fading} fades"


def _top_streak_weeks(df: pd.DataFrame, leader: str) -> int:
    """Return the consecutive number of weeks the current leader stayed at rank 1."""
    streak = 0
    for week in sorted(pd.to_datetime(df["week"]).dt.tz_localize(None).drop_duplicates(), reverse=True):
        week_df = df[df["week"] == week].sort_values("rank")
        if week_df.empty or str(week_df.iloc[0]["category"]) != leader:
            break
        streak += 1
    return streak


def _format_date_range(df: pd.DataFrame) -> str:
    """Format the chart subtitle date range from the available weekly history."""
    start = pd.to_datetime(df["week"].min()).tz_localize(None)
    end = pd.to_datetime(df["week"].max()).tz_localize(None)
    if start == end:
        return end.strftime("%b %d, %Y")
    if start.year == end.year:
        return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
    return f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"


def _add_t6_title(chart: BaseChart, title: str, subtitle: str) -> None:
    """Add a T6 title with restrained Messari-like spacing."""
    title_size = theme.TYPOGRAPHY["title"]["size"]
    subtitle_y = theme.LAYOUT["subtitle_y"]
    display_title = title
    if len(title) > 54:
        title_size = 20
    if len(title) > 40 and " — " in title:
        display_title = title.replace(" — ", "\n— ", 1)
        subtitle_y = 0.84
        title_size = 18
    elif len(title) > 64 and " as " in title:
        display_title = title.replace(" as ", " as\n", 1)
        subtitle_y = 0.84
        title_size = 18

    chart.fig.text(
        theme.LAYOUT["title_x"],
        theme.LAYOUT["title_y"],
        display_title,
        color=theme.COLORS["text_primary"],
        fontsize=title_size,
        fontweight=theme.TYPOGRAPHY["title"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="top",
        linespacing=1.0,
    )
    chart.fig.text(
        theme.LAYOUT["title_x"],
        subtitle_y,
        subtitle,
        color=theme.COLORS["text_muted"],
        fontsize=theme.TYPOGRAPHY["subtitle"]["size"],
        fontweight=theme.TYPOGRAPHY["subtitle"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="top",
    )


def _add_t6_source(chart: BaseChart, source_text: str) -> None:
    """Add subdued source text for T6."""
    chart.fig.text(
        theme.LAYOUT["source_x"],
        theme.LAYOUT["source_y"],
        source_text,
        color="#4A5568",
        fontsize=max(theme.TYPOGRAPHY["annotation"]["size"] - 1, 7),
        fontweight=theme.TYPOGRAPHY["annotation"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="bottom",
    )


def _add_t6_watermark(chart: BaseChart) -> None:
    """Add subdued watermark text for T6."""
    chart.fig.text(
        *theme.WATERMARK["position"],
        theme.WATERMARK["text"],
        color="#4A5568",
        fontsize=max(theme.TYPOGRAPHY["watermark"]["size"] - 1, 7),
        fontweight=theme.TYPOGRAPHY["watermark"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha=theme.WATERMARK["ha"],
        va=theme.WATERMARK["va"],
    )
