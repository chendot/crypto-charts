"""Reusable visual component for compact ranked metric tables."""

from __future__ import annotations

import pandas as pd
from matplotlib.axes import Axes


class RankingTable:
    """Render a themed ranking table for protocols, assets, or sectors."""

    def draw(self, ax: Axes, df: pd.DataFrame, value_column: str) -> None:
        """Draw a ranked table using the supplied value column."""
        raise NotImplementedError("Ranking table rendering is not implemented yet.")
