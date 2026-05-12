"""Tests for the DefiLlama stablecoin DeFi ratio fetcher."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.fetchers import stablecoin_defi_ratio
from tests.fixtures.stablecoin_defi_ratio_fixtures import PROTOCOL_PAYLOADS, PROTOCOLS_PAYLOAD, TOTAL_SUPPLY_PAYLOAD


EXPECTED_COLUMNS = [
    "date",
    "RWA",
    "Basis_Trading",
    "Lending",
    "DEX",
    "Bridge",
    "Other",
    "total_supply",
    "RWA_pct",
    "Basis_Trading_pct",
    "Lending_pct",
    "DEX_pct",
    "Bridge_pct",
    "Other_pct",
    "defi_total",
    "defi_total_pct",
]
GROUP_COLUMNS = ["RWA", "Basis_Trading", "Lending", "DEX", "Bridge", "Other"]


class Response:
    """Minimal requests response test double."""

    def __init__(self, payload) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


@pytest.fixture()
def stablecoin_df(monkeypatch, tmp_path) -> pd.DataFrame:
    """Return the fetcher output using mocked DefiLlama payloads."""
    import data.fetchers.base as base

    def fake_get(url: str, *args, **kwargs):
        del args, kwargs
        if url.endswith("/protocols"):
            return Response(PROTOCOLS_PAYLOAD)
        if url.endswith("/stablecoincharts/all"):
            return Response(TOTAL_SUPPLY_PAYLOAD)
        slug = url.rsplit("/", 1)[-1]
        return Response(PROTOCOL_PAYLOADS[slug])

    monkeypatch.setattr(base, "CACHE_ROOT", tmp_path)
    monkeypatch.setattr(stablecoin_defi_ratio.requests, "get", fake_get)
    monkeypatch.setattr(stablecoin_defi_ratio.time, "sleep", lambda seconds: None)

    df = stablecoin_defi_ratio.fetch()
    assert (tmp_path / "stablecoin_defi_ratio.parquet").exists()
    return df


def test_columns_present(stablecoin_df: pd.DataFrame) -> None:
    """All expected output columns exist."""
    assert list(stablecoin_df.columns) == EXPECTED_COLUMNS


def test_date_range(stablecoin_df: pd.DataFrame) -> None:
    """Output dates stay within the requested usable history window."""
    assert stablecoin_df.index.min() >= pd.Timestamp("2022-01-01")
    assert stablecoin_df.index.max() <= pd.Timestamp(date.today())


def test_pct_bounds(stablecoin_df: pd.DataFrame) -> None:
    """Percentage columns are bounded to 0-100 percentage points."""
    pct_columns = [column for column in stablecoin_df.columns if column.endswith("_pct")]
    assert stablecoin_df[pct_columns].ge(0).all().all()
    assert stablecoin_df[pct_columns].le(100).all().all()


def test_defi_total_consistency(stablecoin_df: pd.DataFrame) -> None:
    """Defi total equals the sum of the group columns."""
    expected_total = stablecoin_df[GROUP_COLUMNS].sum(axis=1)
    pd.testing.assert_series_equal(stablecoin_df["defi_total"], expected_total, check_names=False)


def test_no_all_zero_rows(stablecoin_df: pd.DataFrame) -> None:
    """No retained row has zero stablecoin TVL across every group."""
    assert not stablecoin_df[GROUP_COLUMNS].eq(0).all(axis=1).any()
