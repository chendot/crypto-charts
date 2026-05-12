"""Tests for the parquet-backed data fetcher layer."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data import registry, validate
from data.fetchers.base import BaseFetcher


class DummyFetcher(BaseFetcher):
    """Source: tests; dataset: dummy rows; update frequency: test-only."""

    source_id = "tests"
    dataset_id = "dummy"

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        del start, end
        return pd.DataFrame({"timestamp": [pd.Timestamp("2026-05-01")], "value": [1.0]})

    def fetch_latest(self) -> pd.DataFrame:
        return self.fetch_range("2026-05-01", "2026-05-01")


def test_base_fetcher_append_is_idempotent(monkeypatch, tmp_path) -> None:
    """Appending the same timestamp twice keeps one cached row."""
    import data.fetchers.base as base

    monkeypatch.setattr(base, "CACHE_ROOT", tmp_path)
    fetcher = DummyFetcher()
    df = pd.DataFrame({"timestamp": ["2026-05-01"], "value": [42.0]})

    first_df = fetcher.append(df)
    second_df = fetcher.append(df)

    assert len(first_df) == 1
    assert second_df.equals(first_df)
    assert fetcher.cache_path.exists()


def test_validate_check_detects_stale_data(monkeypatch) -> None:
    """Validation reports stale data when the latest timestamp lags by more than two days."""
    df = pd.DataFrame({"timestamp": [pd.Timestamp("2026-05-01")], "value": [1.0]})

    report = validate.check(df, "tests.dummy")

    assert any(issue.startswith("stale: last=2026-05-01") for issue in report["issues"])


def test_registry_get_raises_data_not_ready_on_cache_miss(monkeypatch) -> None:
    """Registry access tells callers how to backfill a missing cache."""
    class MissingFetcher(DummyFetcher):
        def load_cache(self):
            return None

    monkeypatch.setitem(registry._fetchers, "tests.missing", MissingFetcher())
    registry.get.cache_clear()

    with pytest.raises(registry.DataNotReadyError, match="python -m data.scheduler backfill --dataset tests.missing"):
        registry.get("tests.missing")


def test_registry_get_returns_copy_and_scheduler_clears_cache(monkeypatch) -> None:
    """Registry callers cannot mutate cached DataFrames across scheduler updates."""
    from data import scheduler

    class MutableFetcher(DummyFetcher):
        calls = 0

        def load_cache(self):
            self.calls += 1
            return pd.DataFrame({"timestamp": [pd.Timestamp("2026-05-01")], "value": [float(self.calls)]})

        def update(self):
            return pd.DataFrame({"timestamp": [pd.Timestamp("2026-05-02")], "value": [99.0]})

    fetcher = MutableFetcher()
    monkeypatch.setitem(registry._fetchers, "tests.mutable", fetcher)
    monkeypatch.setattr(scheduler, "_fetchers", {"tests.mutable": fetcher})
    registry.get.cache_clear()

    first_df = registry.get("tests.mutable")
    first_df.loc[0, "value"] = -1.0
    second_df = registry.get("tests.mutable")
    assert second_df.loc[0, "value"] == 1.0

    scheduler.main(["update"])
    third_df = registry.get("tests.mutable")
    assert third_df.loc[0, "value"] == 2.0


def test_multi_asset_price_fetcher_raises_on_empty_download(monkeypatch) -> None:
    """A failed yfinance download must not be persisted as a successful empty cache."""
    from data.exceptions import DataFetchError
    from data.fetchers import yfinance_fetcher

    monkeypatch.setattr(yfinance_fetcher.yf, "download", lambda *args, **kwargs: pd.DataFrame())

    with pytest.raises(DataFetchError, match="Yahoo Finance returned no rows"):
        yfinance_fetcher.MultiAssetPriceFetcher().fetch_range("2020-01-01", "2020-01-02")
