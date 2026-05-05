"""Compatibility wrapper for BTC spot ETF flow fetchers."""

from __future__ import annotations

import pandas as pd

from data.fetchers.farside import fetch_etf_flows


def get_etf_flows(as_of: str | None = None) -> pd.DataFrame:
    """Return normalized BTC ETF flow rows through the requested cutoff date."""
    return fetch_etf_flows(end_date=as_of)
