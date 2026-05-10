"""Price line component with high-low annotations and themed fill."""

from __future__ import annotations

import matplotlib.dates as mdates
import pandas as pd
from matplotlib.axes import Axes

from config import theme


class PriceLine:
    """Render a themed crypto price line."""

    def draw(self, ax: Axes, dates: pd.Series, prices: pd.Series) -> None:
        """Draw prices with a soft area fill and high/low labels."""
        ax.plot(
            dates,
            prices,
            color=theme.COLORS["data"]["primary"],
            linewidth=theme.STYLE["line_width"],
        )
        baseline = prices.min()
        self._draw_gradient_fill(ax, dates, prices, baseline)
        self._annotate_extrema(ax, dates, prices)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=theme.AXES["max_date_ticks"]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter(theme.AXES["date_format"]))

    def _draw_gradient_fill(self, ax: Axes, dates: pd.Series, prices: pd.Series, baseline: float) -> None:
        """Approximate a vertical gradient with repeated fill bands."""
        steps = theme.STYLE["fill_steps"]
        alpha_step = theme.STYLE["fill_alpha"] / steps
        for step in range(steps):
            lower_weight = step / steps
            upper_weight = (step + 1) / steps
            lower = baseline + (prices - baseline) * lower_weight
            upper = baseline + (prices - baseline) * upper_weight
            ax.fill_between(
                dates,
                lower,
                upper,
                color=theme.COLORS["data"]["primary"],
                alpha=alpha_step * (step + 1),
                linewidth=theme.STYLE["fill_line_width"],
            )

    def _annotate_extrema(self, ax: Axes, dates: pd.Series, prices: pd.Series) -> None:
        """Mark and label the highest and lowest prices in the visible series."""
        extrema = [
            (prices.idxmax(), "High", theme.COLORS["data"]["accent"], theme.STYLE["high_annotation_offset"]),
            (prices.idxmin(), "Low", theme.COLORS["data"]["down"], theme.STYLE["low_annotation_offset"]),
        ]
        for idx, label, color, offset in extrema:
            date = dates.loc[idx]
            price = prices.loc[idx]
            ax.scatter(
                [date],
                [price],
                s=theme.STYLE["marker_size"],
                color=color,
                zorder=theme.STYLE["marker_zorder"],
            )
            ax.annotate(
                f"{label} ${price:,.0f}",
                xy=(date, price),
                xytext=offset,
                textcoords="offset points",
                color=color,
                fontsize=theme.TYPOGRAPHY["annotation"]["size"],
                fontweight=theme.TYPOGRAPHY["annotation"]["weight"],
                fontfamily=theme.TYPOGRAPHY["font_family"],
                ha="center",
                va="bottom",
            )
