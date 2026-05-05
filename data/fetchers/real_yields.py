"""Normalized data fetcher for LP and staking real-yield ranking charts."""

from __future__ import annotations

from datetime import date

import pandas as pd


def get_real_yields(as_of: date | str | None = None) -> pd.DataFrame:
    """Return normalized protocol-level nominal and real yield rows."""
    raise NotImplementedError("LP and staking real-yield fetching is not implemented yet.")
