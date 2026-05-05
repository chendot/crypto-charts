"""Tests for normalized fetcher schemas used by chart templates."""

from __future__ import annotations

import sys
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


@pytest.mark.parametrize("template_id", sorted(set(FETCHERS) - {"t1"}))
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
