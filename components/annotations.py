"""Figure and axes annotations for crypto chart highlights."""

from __future__ import annotations

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from config import theme


class Annotations:
    """Add themed callouts, event markers, and percentage changes."""

    def add_callout(self, fig: Figure, value: str, label: str, position: tuple[float, float]) -> None:
        """Add a large headline metric with a muted label."""
        fig.text(
            position[0],
            position[1],
            value,
            color=theme.COLORS["text_primary"],
            fontsize=theme.TYPOGRAPHY["callout"]["size"],
            fontweight=theme.TYPOGRAPHY["callout"]["weight"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="left",
            va="top",
        )
        fig.text(
            position[0],
            position[1] - theme.STYLE["callout_label_gap"],
            label,
            color=theme.COLORS["text_muted"],
            fontsize=theme.TYPOGRAPHY["annotation"]["size"],
            fontweight=theme.TYPOGRAPHY["annotation"]["weight"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="left",
            va="top",
        )

    def add_event_line(self, ax: Axes, date: pd.Timestamp, label: str) -> None:
        """Add a vertical event line and label on an axes."""
        ax.axvline(
            date,
            color=theme.COLORS["accent"],
            linewidth=theme.STYLE["event_line_width"],
            linestyle="--",
        )
        y_top = ax.get_ylim()[1]
        ax.annotate(
            label,
            xy=(date, y_top),
            xytext=(0, -theme.STYLE["annotation_offset_points"]),
            textcoords="offset points",
            color=theme.COLORS["accent"],
            fontsize=theme.TYPOGRAPHY["annotation"]["size"],
            fontweight=theme.TYPOGRAPHY["annotation"]["weight"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="center",
            va="top",
        )

    def add_pct_change(self, fig: Figure, pct: float, position: tuple[float, float]) -> None:
        """Add a percentage change badge colored by direction."""
        color = theme.COLORS["up"] if pct >= 0 else theme.COLORS["down"]
        fig.text(
            position[0],
            position[1],
            f"{pct:+.2f}%",
            color=color,
            fontsize=theme.TYPOGRAPHY["subtitle"]["size"],
            fontweight=theme.TYPOGRAPHY["title"]["weight"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="left",
            va="top",
        )
