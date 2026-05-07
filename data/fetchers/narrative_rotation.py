"""Normalized data fetcher for narrative sector rotation bump charts."""

from __future__ import annotations

from datetime import date

import pandas as pd

from data.fetchers.coingecko_categories import fetch_category_rankings

def get_narrative_rotation(as_of: date | str | None = None) -> pd.DataFrame:
    """Return normalized category ranking rows with daily fallback during cold start."""
    df = fetch_category_rankings(weeks=8, use_cache=True, granularity="weekly")
    if df["week"].nunique() < 8:
        df = fetch_category_rankings(weeks=8, use_cache=True, granularity="daily")
    if as_of is None:
        return df
    cutoff = pd.Timestamp(as_of).tz_localize(None).normalize()
    return df[df["week"] <= cutoff].reset_index(drop=True)
