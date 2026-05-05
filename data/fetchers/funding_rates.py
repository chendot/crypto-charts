"""Normalized data fetcher for funding-rate extreme outcome charts."""

from __future__ import annotations

from datetime import date

import pandas as pd


def get_funding_rate_extremes(as_of: date | str | None = None) -> pd.DataFrame:
    """Return normalized funding-rate extreme events and forward returns."""
    raise NotImplementedError("Funding-rate extreme fetching is not implemented yet.")
