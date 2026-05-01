"""Volume bar component with up/down coloring."""

from __future__ import annotations

import matplotlib.dates as mdates
from matplotlib.ticker import FixedLocator, FuncFormatter
import pandas as pd
from matplotlib.axes import Axes

from config import theme


class VolumeBar:
    """Render crypto volume bars colored by price direction."""

    def draw(self, ax: Axes, dates: pd.Series, volumes: pd.Series, prices: pd.Series) -> None:
        """Draw volume bars using up/down colors based on price changes."""
        changes = prices.diff().fillna(0)
        colors = [theme.COLORS["up"] if change >= 0 else theme.COLORS["down"] for change in changes]
        ax.bar(dates, volumes, color=colors, alpha=theme.STYLE["bar_alpha"], width=theme.STYLE["bar_width"])
        ax.grid(False)
        self._apply_weekly_date_ticks(ax, dates)
        ax.set_yticks(theme.AXES["volume_ticks"])
        ax.xaxis.set_major_formatter(mdates.DateFormatter(theme.AXES["date_format"]))
        ax.yaxis.set_major_formatter(FuncFormatter(self._format_volume))
        ax.yaxis.offsetText.set_visible(False)
        ax.tick_params(
            axis="y",
            color=theme.COLORS["grid"],
            width=theme.STYLE["volume_tick_line_width"],
        )
        ax.tick_params(
            axis="x",
            labelsize=theme.AXES["volume_date_label_size"],
            colors=theme.COLORS["text_muted"],
        )
        for label in ax.get_xticklabels():
            label.set_ha("center")

    def _apply_weekly_date_ticks(self, ax: Axes, dates: pd.Series) -> None:
        """Show weekly Monday ticks and drop the final tick when it crowds the right edge."""
        date_min = pd.to_datetime(dates.min()).to_pydatetime()
        date_max = pd.to_datetime(dates.max()).to_pydatetime()
        weekly_locator = mdates.WeekdayLocator(byweekday=theme.AXES["volume_tick_weekday"])
        tick_values = weekly_locator.tick_values(date_min, date_max)
        right_edge = mdates.date2num(date_max)
        filtered_ticks = [
            tick for tick in tick_values if right_edge - tick >= theme.AXES["volume_right_skip_days"]
        ]
        ax.xaxis.set_major_locator(FixedLocator(filtered_ticks))

    @staticmethod
    def _format_volume(value: float, _position: int) -> str:
        """Format volume ticks in billions of dollars."""
        scaled_value = value / theme.AXES["volume_unit_divisor"]
        return f"${scaled_value:.{theme.AXES['volume_decimals']}f}{theme.AXES['volume_unit_suffix']}"
