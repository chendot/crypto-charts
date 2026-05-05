"""Normalized data fetcher for BTC halving cycle comparison charts."""

from __future__ import annotations

from datetime import date

import pandas as pd


def get_halving_cycles(as_of: date | str | None = None) -> pd.DataFrame:
    """Return normalized BTC halving cycle price rows through the cutoff date."""
    raise NotImplementedError("BTC halving cycle fetching is not implemented yet.")
