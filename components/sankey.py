"""Reusable visual component for cross-chain flow Sankey diagrams."""

from __future__ import annotations

import pandas as pd
from matplotlib.axes import Axes


class SankeyDiagram:
    """Render a themed Sankey-style flow diagram."""

    def draw(self, ax: Axes, df: pd.DataFrame) -> None:
        """Draw source-to-target flows from a normalized flow DataFrame."""
        raise NotImplementedError("Sankey rendering is not implemented yet.")
