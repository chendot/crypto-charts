"""Tests for the selected stablecoin category trend fetcher."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.fetchers import stablecoin_category_trend
from tests.fixtures.stablecoin_category_trend_fixtures import PROTOCOL_PAYLOADS, TOTAL_SUPPLY_PAYLOAD


EXPECTED_COLUMNS = [
    "date",
    "RWA",
    "Basis_Trading",
    "Lending",
    "total_supply",
    "RWA_pct",
    "Basis_Trading_pct",
    "Lending_pct",
    "selected_total",
    "selected_total_pct",
]
USD_COLUMNS = ["RWA", "Basis_Trading", "Lending", "total_supply", "selected_total"]
PCT_COLUMNS = ["RWA_pct", "Basis_Trading_pct", "Lending_pct", "selected_total_pct"]


class Response:
    """Minimal requests response test double."""

    def __init__(self, payload) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


@pytest.fixture()
def category_trend_df(monkeypatch, tmp_path) -> pd.DataFrame:
    """Return fetcher output using mocked DefiLlama payloads."""
    import data.fetchers.base as base

    def fake_get(url: str, *args, **kwargs):
        del args, kwargs
        if url.endswith("/stablecoincharts/all"):
            return Response(TOTAL_SUPPLY_PAYLOAD)
        slug = url.rsplit("/", 1)[-1]
        return Response(PROTOCOL_PAYLOADS[slug])

    monkeypatch.setattr(base, "CACHE_ROOT", tmp_path)
    monkeypatch.setattr(stablecoin_category_trend.requests, "get", fake_get)
    monkeypatch.setattr(stablecoin_category_trend.time, "sleep", lambda seconds: None)

    df = stablecoin_category_trend.fetch()
    assert (tmp_path / "stablecoin_category_trend.parquet").exists()
    return df


def test_columns_present(category_trend_df: pd.DataFrame) -> None:
    """All expected output columns exist."""
    assert list(category_trend_df.columns) == EXPECTED_COLUMNS


def test_date_range(category_trend_df: pd.DataFrame) -> None:
    """Output dates stay within the requested usable history window."""
    assert category_trend_df.index.min() >= pd.Timestamp("2020-01-01")
    assert category_trend_df.index.max() <= pd.Timestamp(date.today())


def test_pct_bounds(category_trend_df: pd.DataFrame) -> None:
    """Percentage columns are bounded to 0-100 percentage points."""
    assert category_trend_df[PCT_COLUMNS].ge(0).all().all()
    assert category_trend_df[PCT_COLUMNS].le(100).all().all()


def test_selected_total_consistency(category_trend_df: pd.DataFrame) -> None:
    """Selected total equals RWA plus Basis Trading plus Lending."""
    expected_total = category_trend_df[["RWA", "Basis_Trading", "Lending"]].sum(axis=1)
    pd.testing.assert_series_equal(category_trend_df["selected_total"], expected_total, check_names=False)


def test_no_negative_values(category_trend_df: pd.DataFrame) -> None:
    """USD columns are never negative."""
    assert category_trend_df[USD_COLUMNS].ge(0).all().all()


def test_ethena_zero_before_2023(category_trend_df: pd.DataFrame) -> None:
    """Basis Trading is zero before Ethena existed."""
    before_2023 = category_trend_df.index < pd.Timestamp("2023-01-01")
    assert category_trend_df.loc[before_2023, "Basis_Trading"].eq(0).all()
