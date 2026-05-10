"""T1: BTC spot ETF flow structure chart."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from matplotlib.font_manager import FontProperties

from components.base_chart import BaseChart
from components.flow_bars import draw_grouped_bars_with_cumulative
from config import theme
from config.templates import TemplateConfig, get_template_config
from data.fetchers.farside import fetch_etf_flows
from templates.common import normalize_as_of, output_filename


def render(
    as_of: date | str | None = None,
    variant: str | None = None,
    title: str | None = None,
) -> Path:
    """Render T1 through the requested cutoff date and return the PNG path."""
    del variant
    publish_date = normalize_as_of(as_of)
    flow_end_date = _completed_flow_end_date(publish_date)
    df = fetch_etf_flows(end_date=flow_end_date.isoformat(), days=14, use_cache=True)
    week_df = _last_trading_dates(df, trading_days=5)
    if week_df.empty:
        raise ValueError("No BTC ETF flow data available for T1")

    template_config = get_template_config("t1")
    start_date = week_df["date"].min().strftime("%b %d")
    end_date = week_df["date"].max().strftime("%b %d, %Y")
    cumulative = _daily_cumulative_flow(week_df)
    total_flow = float(cumulative.iloc[-1])
    argument = title or _build_argument_title(week_df, cumulative)

    chart = BaseChart()
    _add_t1_title(
        chart,
        template_config.text.title.format(argument=argument, as_of=publish_date.isoformat()),
        template_config.text.subtitle.format(start_date=start_date, end_date=end_date, as_of=publish_date.isoformat()),
    )
    ax = chart.add_axes(theme.LAYOUT["etf_axes"])
    draw_grouped_bars_with_cumulative(ax, week_df, **_flow_visual_config(template_config))

    _add_net_flow_callout(chart, total_flow)
    _add_t1_source(chart, template_config.text.source)
    _add_t1_watermark(chart)
    return chart.save(output_filename("t1", publish_date))


def _completed_flow_end_date(publish_date: date) -> date:
    """Return the latest completed flow date for a weekly publishing cutoff."""
    timestamp = pd.Timestamp(publish_date)
    if timestamp.weekday() == 0:
        return (timestamp - pd.Timedelta(days=3)).date()
    if timestamp.weekday() == 5:
        return (timestamp - pd.Timedelta(days=1)).date()
    if timestamp.weekday() == 6:
        return (timestamp - pd.Timedelta(days=2)).date()
    return publish_date


def _last_trading_dates(df: pd.DataFrame, trading_days: int) -> pd.DataFrame:
    """Keep the latest requested number of dates with available ETF flow rows."""
    working_df = df.copy()
    working_df["date"] = pd.to_datetime(working_df["date"]).dt.tz_localize(None)
    dates = sorted(working_df["date"].drop_duplicates())
    selected_dates = dates[-trading_days:]
    return working_df[working_df["date"].isin(selected_dates)].sort_values(["date", "ticker"]).reset_index(drop=True)


def _daily_cumulative_flow(df: pd.DataFrame) -> pd.Series:
    """Return cumulative daily net flow for the selected trading window."""
    daily_flow = df.groupby("date")["flow_usd"].sum().sort_index()
    return daily_flow.cumsum()


def _build_argument_title(df: pd.DataFrame, cumulative: pd.Series) -> str:
    """Create an argument-first title from weekly cumulative-flow structure."""
    del df
    low_point = float(cumulative.min())
    net_flow = float(cumulative.iloc[-1])

    if low_point < -200_000_000 and net_flow > 0:
        return (
            f"Week started {_format_signed_usd(low_point)}, ended {_format_signed_usd(net_flow)}. "
            "IBIT did the heavy lifting."
        )
    if net_flow > 0:
        return f"Strong week: BTC ETFs pulled in {_format_signed_usd(net_flow)} across 5 days."
    return f"Outflow week: BTC ETFs shed {_format_signed_usd(net_flow)}. GBTC led the selling."


def _flow_visual_config(template_config: TemplateConfig) -> dict[str, object]:
    """Return T1 flow grouping and color configuration."""
    visual_config = template_config.visual or {}
    return {
        "featured_issuers": tuple(visual_config.get("featured_issuers", theme.ETF_FLOW["featured_funds"])),
        "issuer_colors": dict(
            visual_config.get(
                "issuer_colors",
                theme.ETF_FLOW["colors"],
            )
        ),
    }


def _add_t1_title(chart: BaseChart, title: str, subtitle: str) -> None:
    """Add a T1 title with length-aware sizing and CJK fallback for overrides."""
    display_title = title
    subtitle_y = theme.LAYOUT["subtitle_y"]
    title_size = theme.TYPOGRAPHY["title"]["size"]
    if len(title) > 58:
        display_title = title.replace(". IBIT", ".\nIBIT", 1)
        title_size = 18
        subtitle_y = 0.82
    elif len(title) > 54:
        title_size = 17

    chart.fig.text(
        theme.LAYOUT["title_x"],
        theme.LAYOUT["title_y"],
        display_title.replace("$", r"\$"),
        color=theme.COLORS["text"]["primary"],
        fontsize=title_size,
        fontweight=theme.TYPOGRAPHY["title"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        fontproperties=_font_properties_for(title),
        ha="left",
        va="top",
        linespacing=1.0,
    )
    chart.fig.text(
        theme.LAYOUT["title_x"],
        subtitle_y,
        subtitle,
        color="#8899AA",
        fontsize=theme.TYPOGRAPHY["subtitle"]["size"],
        fontweight=theme.TYPOGRAPHY["subtitle"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="left",
        va="top",
    )


def _font_properties_for(text: str) -> FontProperties | None:
    """Return a local CJK-capable font when manual title overrides need one."""
    if text.isascii():
        return None
    for font_path in (
        Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
        Path("/System/Library/Fonts/CJKSymbolsFallback.ttc"),
    ):
        if font_path.exists():
            return FontProperties(fname=str(font_path), weight=theme.TYPOGRAPHY["title"]["weight"])
    return None


def _add_net_flow_callout(chart: BaseChart, total_flow: float) -> None:
    """Add the headline net-flow number in the right-side reserved margin."""
    chart.fig.text(
        theme.WATERMARK["position"][0],
        theme.LAYOUT["etf_callout"][1],
        _format_signed_usd(total_flow),
        color=theme.COLORS["data"]["primary"] if total_flow >= 0 else theme.COLORS["data"]["down"],
        fontsize=theme.TYPOGRAPHY["callout"]["size"],
        fontweight=theme.TYPOGRAPHY["callout"]["weight"],
        fontfamily=theme.TYPOGRAPHY["font_family"],
        ha="right",
        va="top",
    )


def _add_t1_source(chart: BaseChart, source_text: str) -> None:
    """Add subdued source text for the Messari-style T1 layout."""
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


def _add_t1_watermark(chart: BaseChart) -> None:
    """Add subdued watermark text for the Messari-style T1 layout."""
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


def _format_signed_usd(value: float) -> str:
    """Format a signed USD amount in millions or billions for the callout."""
    sign = "+" if value >= 0 else "-"
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"{sign}${absolute / 1_000_000_000:,.1f}B"
    return f"{sign}${absolute / 1_000_000:,.0f}M"
