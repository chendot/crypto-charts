"""Base chart canvas and shared figure-level decorations."""

from __future__ import annotations

import os
from pathlib import Path

from config import theme

os.environ.setdefault("MPLCONFIGDIR", str(theme.PROJECT_ROOT / ".matplotlib-cache"))

import matplotlib.pyplot as plt


class BaseChart:
    """Create and manage a themed Matplotlib canvas."""

    def __init__(self) -> None:
        """Initialize a dark themed figure using the global canvas settings."""
        width = theme.CANVAS["width"] / theme.CANVAS["dpi"]
        height = theme.CANVAS["height"] / theme.CANVAS["dpi"]
        self.fig = plt.figure(
            figsize=(width, height),
            dpi=theme.CANVAS["dpi"],
            facecolor=theme.CANVAS["background"],
        )
        self.fig.patch.set_facecolor(theme.COLORS["background"])

    def add_axes(self, rect: list[float]) -> plt.Axes:
        """Add a themed axes at a normalized figure rectangle."""
        ax = self.fig.add_axes(rect, facecolor=theme.COLORS["background"])
        ax.tick_params(colors=theme.COLORS["text_muted"], labelsize=theme.TYPOGRAPHY["axis"]["size"])
        ax.grid(True, color=theme.COLORS["grid"], linewidth=theme.STYLE["grid_line_width"])
        for spine in ax.spines.values():
            spine.set_color(theme.COLORS["grid"])
            spine.set_linewidth(theme.STYLE["spine_width"])
        return ax

    def add_title(self, title: str, subtitle: str) -> None:
        """Add chart title and subtitle to the upper-left canvas area."""
        self.fig.text(
            theme.LAYOUT["title_x"],
            theme.LAYOUT["title_y"],
            title,
            color=theme.COLORS["text_primary"],
            fontsize=theme.TYPOGRAPHY["title"]["size"],
            fontweight=theme.TYPOGRAPHY["title"]["weight"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="left",
            va="top",
        )
        self.fig.text(
            theme.LAYOUT["title_x"],
            theme.LAYOUT["subtitle_y"],
            subtitle,
            color=theme.COLORS["text_muted"],
            fontsize=theme.TYPOGRAPHY["subtitle"]["size"],
            fontweight=theme.TYPOGRAPHY["subtitle"]["weight"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="left",
            va="top",
        )

    def add_watermark(self) -> None:
        """Add the configured account watermark to the lower-right corner."""
        self.fig.text(
            *theme.WATERMARK["position"],
            theme.WATERMARK["text"],
            color=theme.COLORS["text_hint"],
            fontsize=theme.TYPOGRAPHY["watermark"]["size"],
            fontweight=theme.TYPOGRAPHY["watermark"]["weight"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha=theme.WATERMARK["ha"],
            va=theme.WATERMARK["va"],
        )

    def add_source(self, source_text: str) -> None:
        """Add source attribution to the lower-left corner."""
        self.fig.text(
            theme.LAYOUT["source_x"],
            theme.LAYOUT["source_y"],
            source_text,
            color=theme.COLORS["text_hint"],
            fontsize=theme.TYPOGRAPHY["annotation"]["size"],
            fontweight=theme.TYPOGRAPHY["annotation"]["weight"],
            fontfamily=theme.TYPOGRAPHY["font_family"],
            ha="left",
            va="bottom",
        )

    def save(self, filename: str) -> Path:
        """Save the chart image under the configured output directory."""
        theme.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = theme.OUTPUT_DIR / filename
        self.fig.savefig(
            output_path,
            dpi=theme.CANVAS["dpi"],
            facecolor=self.fig.get_facecolor(),
            bbox_inches=None,
        )
        plt.close(self.fig)
        return output_path
