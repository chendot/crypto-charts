"""Tests for normalized fetcher schemas used by chart templates."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.fetchers import FETCHERS
from data.schemas import TEMPLATE_SCHEMAS


def test_fetcher_registry_matches_schema_registry() -> None:
    """Verify every template fetcher has a matching schema contract."""
    assert set(FETCHERS) == set(TEMPLATE_SCHEMAS)


@pytest.mark.parametrize("template_id", sorted(set(FETCHERS) - {"t1", "t6"}))
def test_fetcher_placeholders_raise_not_implemented(template_id: str) -> None:
    """Verify scaffolded fetchers fail explicitly until real data sources are added."""
    with pytest.raises(NotImplementedError):
        FETCHERS[template_id](as_of="2026-01-01")


@pytest.mark.parametrize("template_id,schema", sorted(TEMPLATE_SCHEMAS.items()))
def test_schema_accepts_required_columns(template_id: str, schema) -> None:
    """Verify each schema accepts a DataFrame containing its standard columns."""
    del template_id
    df = pd.DataFrame(columns=schema.columns)
    assert schema.validate(df) is df


def test_farside_fetcher_uses_cache_without_second_request(monkeypatch, tmp_path) -> None:
    """Verify repeated Farside fetches for the same period use local cache."""
    from data.fetchers import farside

    fixture_html = (PROJECT_ROOT / "tests" / "fixtures" / "farside_btc_etf_flow_sample.html").read_text()
    calls = {"count": 0}

    class Response:
        text = fixture_html

        def raise_for_status(self) -> None:
            return None

    def fake_get(*args, **kwargs):
        del args, kwargs
        calls["count"] += 1
        return Response()

    monkeypatch.setattr(farside, "CACHE_PATH", tmp_path / "farside_btc_etf_flows.csv")
    monkeypatch.setattr(farside.requests, "get", fake_get)

    first_df = farside.fetch_etf_flows("2026-05-01", use_cache=True)
    second_df = farside.fetch_etf_flows("2026-05-01", use_cache=True)

    assert calls["count"] == 1
    assert not first_df.empty
    assert second_df.equals(first_df)


def test_coingecko_category_fetcher_uses_cache_without_second_request(monkeypatch, tmp_path) -> None:
    """Verify repeated CoinGecko fetches on the same day reuse the parquet cache."""
    from data.fetchers import coingecko_categories
    from data.schemas import NARRATIVE_ROTATION_SCHEMA

    prior_cache_df = pd.DataFrame(
        {
            "date": [pd.Timestamp("2026-04-29")] * 10,
            "category": [
                "AI & Big Data",
                "Real World Assets",
                "DePIN",
                "Meme",
                "Layer 2",
                "Gaming",
                "Liquid Staking",
                "Decentralized Exchange",
                "Stablecoins",
                "Restaking",
            ],
            "price_change_7d": [float("nan")] * 10,
            "market_cap": [950.0, 880.0, 700.0, 710.0, 590.0, 495.0, 398.0, 290.0, 200.0, 98.0],
        }
    )
    fixture_payload = [
        {"id": "ai-big-data", "name": "AI & Big Data", "market_cap": 1000.0, "market_cap_change_24h": 5.0},
        {"id": "real-world-assets-rwa", "name": "Real World Assets", "market_cap": 900.0, "market_cap_change_24h": 3.0},
        {"id": "depin", "name": "DePIN", "market_cap": 800.0, "market_cap_change_24h": 8.0},
        {"id": "meme-token", "name": "Meme", "market_cap": 700.0, "market_cap_change_24h": -2.0},
        {"id": "layer-2", "name": "Layer 2", "market_cap": 600.0, "market_cap_change_24h": 1.5},
        {"id": "gaming", "name": "Gaming", "market_cap": 500.0, "market_cap_change_24h": 0.5},
        {"id": "liquid-staking", "name": "Liquid Staking", "market_cap": 400.0, "market_cap_change_24h": 2.0},
        {"id": "dex", "name": "Decentralized Exchange", "market_cap": 300.0, "market_cap_change_24h": 4.0},
        {"id": "stablecoins", "name": "Stablecoins", "market_cap": 200.0, "market_cap_change_24h": 0.0},
        {"id": "restaking", "name": "Restaking", "market_cap": 100.0, "market_cap_change_24h": 6.0},
        {"id": "ignored", "name": "Ignored Category", "market_cap": 999.0, "market_cap_change_24h": 99.0},
    ]
    calls = {"count": 0}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return fixture_payload

    def fake_get(*args, **kwargs):
        del args, kwargs
        calls["count"] += 1
        return Response()

    class FakeDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 5, 6)

    cache_path = tmp_path / "coingecko_categories_history.parquet"
    prior_cache_df.to_parquet(cache_path, index=False)

    monkeypatch.setattr(coingecko_categories, "CACHE_PATH", cache_path)
    monkeypatch.setattr(coingecko_categories.requests, "get", fake_get)
    monkeypatch.setattr(coingecko_categories, "date", FakeDate)

    first_df = coingecko_categories.fetch_category_rankings(weeks=8, use_cache=True)
    second_df = coingecko_categories.fetch_category_rankings(weeks=8, use_cache=True)

    assert calls["count"] == 1
    assert len(first_df) == 20
    assert second_df.equals(first_df)
    latest_week_df = first_df[first_df["week"] == pd.Timestamp("2026-05-06")].reset_index(drop=True)
    assert latest_week_df.loc[latest_week_df["rank"] == 1, "category"].iloc[0] == "DePIN"
    assert latest_week_df.loc[latest_week_df["category"] == "AI & Big Data", "price_change_7d"].iloc[0] > 0
    assert NARRATIVE_ROTATION_SCHEMA.validate(first_df) is first_df


def test_coingecko_category_fetcher_returns_existing_history_when_weeks_insufficient(monkeypatch, tmp_path) -> None:
    """Verify the fetcher keeps partial history and surfaces a warning in attrs."""
    from data.fetchers import coingecko_categories

    cache_df = pd.DataFrame(
        {
            "date": [pd.Timestamp("2026-04-30"), pd.Timestamp("2026-04-30")],
            "category": ["AI & Big Data", "DePIN"],
            "price_change_7d": [1.0, 2.0],
            "market_cap": [100.0, 200.0],
        }
    )
    cache_path = tmp_path / "coingecko_categories_history.parquet"
    cache_df.to_parquet(cache_path, index=False)

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return [
                {"id": "ai-big-data", "name": "AI & Big Data", "market_cap": 150.0, "market_cap_change_24h": 3.0},
                {"id": "depin", "name": "DePIN", "market_cap": 250.0, "market_cap_change_24h": 4.0},
            ]

    class FakeDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 5, 6)

    monkeypatch.setattr(coingecko_categories, "CACHE_PATH", cache_path)
    monkeypatch.setattr(coingecko_categories.requests, "get", lambda *args, **kwargs: Response())
    monkeypatch.setattr(coingecko_categories, "date", FakeDate)

    df = coingecko_categories.fetch_category_rankings(weeks=8, use_cache=True)

    assert set(df.columns) == set(("week", "category", "price_change_7d", "market_cap", "rank"))
    assert "warning" in df.attrs
    assert "requested 8" in df.attrs["warning"]


def test_narrative_rotation_fetcher_falls_back_to_daily_when_weekly_history_is_short(monkeypatch) -> None:
    """Verify T6 fetcher switches to daily snapshots during cold start."""
    from data.fetchers import narrative_rotation

    calls: list[str] = []
    weekly_df = pd.DataFrame(
        {
            "week": [pd.Timestamp("2026-05-07")] * 2,
            "category": ["AI & Big Data", "DePIN"],
            "price_change_7d": [1.0, 2.0],
            "market_cap": [100.0, 200.0],
            "rank": [2, 1],
        }
    )
    weekly_df.attrs["granularity"] = "weekly"
    weekly_df.attrs["periods"] = 1
    daily_df = pd.DataFrame(
        {
            "week": [
                pd.Timestamp("2026-05-06"),
                pd.Timestamp("2026-05-06"),
                pd.Timestamp("2026-05-07"),
                pd.Timestamp("2026-05-07"),
            ],
            "category": ["AI & Big Data", "DePIN", "AI & Big Data", "DePIN"],
            "price_change_7d": [float("nan"), float("nan"), 1.0, 2.0],
            "market_cap": [95.0, 180.0, 100.0, 200.0],
            "rank": [1, 2, 2, 1],
        }
    )
    daily_df.attrs["granularity"] = "daily"
    daily_df.attrs["periods"] = 2

    def fake_fetch_category_rankings(*, weeks, use_cache, granularity):
        del weeks, use_cache
        calls.append(granularity)
        return weekly_df if granularity == "weekly" else daily_df

    monkeypatch.setattr(narrative_rotation, "fetch_category_rankings", fake_fetch_category_rankings)

    result = narrative_rotation.get_narrative_rotation(as_of="2026-05-07")

    assert calls == ["weekly", "daily"]
    assert result["week"].nunique() == 2
    assert result.attrs["granularity"] == "daily"
