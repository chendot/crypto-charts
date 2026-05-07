"""Smoke tests for implemented chart templates."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import theme
from data.schemas import NARRATIVE_ROTATION_SCHEMA
from components.flow_bars import align_dual_axes
from data.fetchers import farside
from templates.t1_etf_flow import render


def test_t1_renders_png_from_cached_farside_fixture(monkeypatch, tmp_path) -> None:
    """Verify T1 can render a PNG using fixture-backed cached Farside data."""
    fixture_html = (PROJECT_ROOT / "tests" / "fixtures" / "farside_btc_etf_flow_sample.html").read_text()
    cache_path = tmp_path / "farside_btc_etf_flows.csv"

    class Response:
        text = fixture_html

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(farside, "CACHE_PATH", cache_path)
    monkeypatch.setattr(farside.requests, "get", lambda *args, **kwargs: Response())
    monkeypatch.setattr(theme, "OUTPUT_DIR", tmp_path)

    output_path = render(as_of="2026-05-04")

    assert output_path.exists()
    assert output_path.name == "2026-05-04_t1.png"
    assert output_path.stat().st_size > 0


def test_t6_renders_png_from_fixture_history(monkeypatch, tmp_path) -> None:
    """Verify T6 can render a PNG from fixture-backed narrative rotation data."""
    from templates import t6_narrative_rotation

    weeks = pd.to_datetime(
        [
            "2026-03-18",
            "2026-03-25",
            "2026-04-01",
            "2026-04-08",
            "2026-04-15",
            "2026-04-22",
            "2026-04-29",
            "2026-05-05",
        ]
    )
    rankings = {
        "AI & Big Data": [3, 3, 2, 2, 2, 1, 1, 1],
        "Real World Assets": [2, 2, 4, 4, 4, 4, 5, 6],
        "DePIN": [6, 5, 3, 3, 1, 2, 2, 2],
        "Meme": [1, 1, 1, 1, 3, 5, 7, 8],
        "Layer 2": [5, 6, 6, 5, 5, 6, 6, 5],
        "Gaming": [8, 8, 8, 8, 8, 8, 8, 7],
        "Liquid Staking": [4, 4, 5, 6, 6, 7, 4, 4],
        "Decentralized Exchange": [7, 7, 7, 7, 7, 3, 3, 3],
        "Stablecoins": [10, 10, 10, 10, 10, 10, 10, 10],
        "Restaking": [9, 9, 9, 9, 9, 9, 9, 9],
    }
    rows = []
    for category, rank_series in rankings.items():
        for week, rank in zip(weeks, rank_series):
            rows.append(
                {
                    "week": week,
                    "category": category,
                    "price_change_7d": float(11 - rank),
                    "market_cap": float(1_000_000_000 - rank * 10_000_000),
                    "rank": rank,
                }
            )
    fixture_df = pd.DataFrame(rows).sort_values(["week", "rank", "category"]).reset_index(drop=True)
    NARRATIVE_ROTATION_SCHEMA.validate(fixture_df)

    monkeypatch.setattr(t6_narrative_rotation, "get_narrative_rotation", lambda as_of=None: fixture_df)
    monkeypatch.setattr(theme, "OUTPUT_DIR", tmp_path)

    output_path = t6_narrative_rotation.render(as_of="2026-05-05")

    assert output_path.exists()
    assert output_path.name == "2026-05-05_t6.png"
    assert output_path.stat().st_size > 0


def test_align_dual_axes_all_inflow() -> None:
    """Verify zero alignment for a cumulative all-inflow week."""
    _assert_aligned(align_dual_axes(-20_000_000, 140_000_000, 40_000_000, 420_000_000))


def test_align_dual_axes_all_outflow() -> None:
    """Verify zero alignment for a cumulative all-outflow week."""
    _assert_aligned(align_dual_axes(-180_000_000, 10_000_000, -620_000_000, -80_000_000))


def test_align_dual_axes_reversal_week() -> None:
    """Verify zero alignment for the current reversal-style data shape."""
    _assert_aligned(align_dual_axes(-263_200_000, 629_800_000, -490_500_000, 162_800_000))


def _assert_aligned(ranges: tuple[float, float, float, float]) -> None:
    """Assert both axis ranges put zero on the same relative y position."""
    l_lo, l_hi, r_lo, r_hi = ranges
    left_zero = (-l_lo) / (l_hi - l_lo)
    right_zero = (-r_lo) / (r_hi - r_lo)
    assert abs(left_zero - right_zero) < 0.001
    assert l_lo < 0 < l_hi
    assert r_lo < 0 < r_hi
