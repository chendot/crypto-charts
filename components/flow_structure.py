"""Reusable visual component for fund-flow structure charts."""

from __future__ import annotations

import pandas as pd
from matplotlib.axes import Axes


class FlowStructure:
    """Render grouped flow bars or blocks using shared theme constants."""

    def draw(self, ax: Axes, df: pd.DataFrame) -> None:
        """Draw a fund-flow structure visualization on the provided axes."""
        raise NotImplementedError("Flow structure rendering is not implemented yet.")
