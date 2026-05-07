"""CoinGecko fetcher for tracked crypto category weekly rankings."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import logging

import pandas as pd
import requests

from data.exceptions import DataFetchError
from data.schemas import NARRATIVE_ROTATION_SCHEMA


COINGECKO_CATEGORIES_URL = "https://api.coingecko.com/api/v3/coins/categories"
CACHE_PATH = Path(__file__).resolve().parents[1] / "cache" / "coingecko_categories_history.parquet"
REQUEST_TIMEOUT = 20
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
}
TRACKED_CATEGORIES = (
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
)
TRACKED_CATEGORY_SET = set(TRACKED_CATEGORIES)
LOGGER = logging.getLogger(__name__)


def fetch_category_rankings(
    weeks: int = 8,
    use_cache: bool = True,
    granularity: str = "weekly",
) -> pd.DataFrame:
    """
    Return weekly tracked CoinGecko category rankings from local snapshot history.

    The upstream categories endpoint only exposes current snapshots, so this
    fetcher builds a history by appending one normalized snapshot per fetch day
    into a local parquet cache.
    """
    cached_df = _read_cache() if use_cache else None
    snapshot_date = pd.Timestamp(date.today()).normalize()

    if use_cache and _has_snapshot_for_date(cached_df, snapshot_date):
        history_df = cached_df
    else:
        snapshot_df = _fetch_snapshot(snapshot_date)
        history_df = _merge_history(cached_df, snapshot_df)
        _write_cache(history_df)

    result = _build_period_rankings(history_df, weeks, granularity=granularity)
    unit = "week" if granularity == "weekly" else "day"
    available_periods = result["week"].nunique()
    if available_periods < weeks:
        message = f"Only {available_periods} {unit}(s) available in CoinGecko category history; requested {weeks}."
        LOGGER.warning(message)
        result.attrs["warning"] = message
    result.attrs["granularity"] = granularity
    result.attrs["periods"] = int(available_periods)
    NARRATIVE_ROTATION_SCHEMA.validate(result)
    return result


def _fetch_snapshot(snapshot_date: pd.Timestamp) -> pd.DataFrame:
    """Fetch the current CoinGecko category snapshot and normalize tracked rows."""
    try:
        response = requests.get(
            COINGECKO_CATEGORIES_URL,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DataFetchError("Failed to fetch CoinGecko category snapshot") from exc

    payload = response.json()
    if not isinstance(payload, list):
        raise DataFetchError("CoinGecko category snapshot returned an unexpected payload")

    rows = []
    for item in payload:
        name = item.get("name")
        if name not in TRACKED_CATEGORY_SET:
            continue
        rows.append(
            {
                "date": snapshot_date,
                "category": name,
                "price_change_7d": float("nan"),
                "market_cap": _to_float(item.get("market_cap")),
            }
        )

    df = pd.DataFrame(rows, columns=("date", "category", "price_change_7d", "market_cap"))
    if df.empty:
        raise DataFetchError("CoinGecko category snapshot contained no tracked categories")
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df["price_change_7d"] = pd.to_numeric(df["price_change_7d"], errors="coerce")
    df["market_cap"] = pd.to_numeric(df["market_cap"], errors="coerce")
    return df.sort_values(["date", "category"]).reset_index(drop=True)


def _build_period_rankings(history_df: pd.DataFrame, periods: int, granularity: str) -> pd.DataFrame:
    """Collapse snapshot history into daily or weekly last-observation rankings."""
    if history_df is None or history_df.empty:
        empty = pd.DataFrame(columns=NARRATIVE_ROTATION_SCHEMA.columns)
        empty["week"] = pd.to_datetime(empty.get("week", pd.Series(dtype="datetime64[ns]")))
        return empty

    if granularity == "daily":
        period_dates = (
            history_df[["date"]]
            .drop_duplicates()
            .rename(columns={"date": "snapshot_date"})
            .sort_values("snapshot_date")
            .reset_index(drop=True)
        )
    elif granularity == "weekly":
        period_dates = (
            history_df.assign(period=history_df["date"].dt.to_period("W-SUN"))
            .groupby("period", as_index=False)["date"]
            .max()
            .rename(columns={"date": "snapshot_date"})
            .sort_values("snapshot_date")
            .reset_index(drop=True)
        )
    else:
        raise ValueError(f"Unsupported granularity: {granularity}")
    if periods > 0:
        period_dates = period_dates.tail(periods)

    period_df = history_df.merge(period_dates, left_on="date", right_on="snapshot_date", how="inner")
    period_df = (
        period_df[["snapshot_date", "category", "price_change_7d", "market_cap"]]
        .rename(columns={"snapshot_date": "week"})
        .drop_duplicates(subset=["week", "category"], keep="last")
        .sort_values(["week", "category"])
        .reset_index(drop=True)
    )
    period_df["price_change_7d"] = (
        period_df.groupby("category")["market_cap"].pct_change() * 100.0
    )
    period_df["rank"] = (
        period_df.groupby("week")["price_change_7d"]
        .rank(method="first", ascending=False, na_option="bottom")
        .astype(int)
    )
    period_df = period_df[["week", "category", "price_change_7d", "market_cap", "rank"]]
    period_df["week"] = pd.to_datetime(period_df["week"]).dt.tz_localize(None)
    return period_df.sort_values(["week", "rank", "category"]).reset_index(drop=True)


def _merge_history(cached_df: pd.DataFrame | None, snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """Append the latest snapshot and keep one row per category per day."""
    if cached_df is None or cached_df.empty:
        merged_df = snapshot_df.copy()
    else:
        merged_df = pd.concat([cached_df, snapshot_df], ignore_index=True)
    merged_df["date"] = pd.to_datetime(merged_df["date"]).dt.tz_localize(None)
    merged_df = merged_df.drop_duplicates(subset=["date", "category"], keep="last")
    return merged_df.sort_values(["date", "category"]).reset_index(drop=True)


def _read_cache() -> pd.DataFrame | None:
    """Read the normalized CoinGecko category history cache when present."""
    if not CACHE_PATH.exists():
        return None
    df = pd.read_parquet(CACHE_PATH)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    return df.sort_values(["date", "category"]).reset_index(drop=True)


def _write_cache(df: pd.DataFrame) -> None:
    """Write the normalized category snapshot history to parquet."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_df = df.copy()
    output_df["date"] = pd.to_datetime(output_df["date"]).dt.tz_localize(None)
    output_df.to_parquet(CACHE_PATH, index=False)


def _has_snapshot_for_date(df: pd.DataFrame | None, snapshot_date: pd.Timestamp) -> bool:
    """Return True when the history already contains a snapshot for the given day."""
    if df is None or df.empty:
        return False
    return bool((pd.to_datetime(df["date"]).dt.tz_localize(None) == snapshot_date).any())


def _to_float(value: object) -> float:
    """Convert an API value to float, preserving missing values as NaN."""
    return pd.to_numeric(value, errors="coerce")
