"""Normalized data fetcher for cross-chain stablecoin flow Sankey charts."""

from __future__ import annotations

from datetime import date

import pandas as pd


def get_stablecoin_flows(as_of: date | str | None = None) -> pd.DataFrame:
    """Return normalized cross-chain stablecoin flow rows through the cutoff date."""
    raise NotImplementedError("Stablecoin flow fetching is not implemented yet.")
