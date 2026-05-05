"""Reusable visual component for rank-over-time bump charts."""

from __future__ import annotations

import pandas as pd
from matplotlib.axes import Axes


class BumpChart:
    """Render a themed bump chart for sector or narrative rotation."""

    def draw(self, ax: Axes, df: pd.DataFrame, entity_column: str = "sector") -> None:
        """Draw rank changes over time for each entity in the DataFrame."""
        raise NotImplementedError("Bump chart rendering is not implemented yet.")
