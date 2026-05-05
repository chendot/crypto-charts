"""Normalized data fetcher for historical top-buyer drawdown charts."""

from __future__ import annotations

from datetime import date

import pandas as pd


def get_top_buyer_drawdowns(as_of: date | str | None = None, variant: str | None = None) -> pd.DataFrame:
    """Return normalized drawdown rows for the requested top-buyer variant."""
    raise NotImplementedError("Top-buyer drawdown fetching is not implemented yet.")
