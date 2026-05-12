"""Source: DefiLlama API; dataset: selected stablecoin category TVL trend; update frequency: daily."""

from __future__ import annotations

from datetime import date, timedelta
import time
from typing import Any

import pandas as pd
import requests

from data.exceptions import DataFetchError
from data.fetchers.base import BaseFetcher


API_BASE_URL = "https://api.llama.fi"
STABLECOINS_BASE_URL = "https://stablecoins.llama.fi"
REQUEST_TIMEOUT = 30
START_DATE = "2020-01-01"

REPRESENTATIVE_PROTOCOLS = {
    "ondo-finance": {"name": "Ondo", "category": "RWA"},
    "mountain-protocol": {"name": "Mountain", "category": "RWA"},
    "makerdao": {"name": "MakerDAO RWA", "category": "RWA"},
    "ethena": {"name": "Ethena", "category": "Basis_Trading"},
    "aave-v3": {"name": "Aave V3", "category": "Lending"},
    "compound-finance": {"name": "Compound", "category": "Lending"},
}
MAKERDAO_RWA_TOKENS = {"USDY", "SDAI"}
GROUP_COLUMNS = ["RWA", "Basis_Trading", "Lending"]
OUTPUT_COLUMNS = [
    "date",
    *GROUP_COLUMNS,
    "total_supply",
    "RWA_pct",
    "Basis_Trading_pct",
    "Lending_pct",
    "selected_total",
    "selected_total_pct",
]


class StablecoinCategoryTrendFetcher(BaseFetcher):
    """Fetch selected stablecoin category trend proxies from DefiLlama."""

    source_id = ""
    dataset_id = "stablecoin_category_trend"

    def fetch(self, start: str = START_DATE, end: str | None = None) -> pd.DataFrame:
        """Fetch, cache, and return the requested date-indexed output."""
        end_date = end or date.today().isoformat()
        cache_df = self.fetch_range(start, end_date)
        if cache_df.empty:
            raise DataFetchError("Stablecoin category trend fetch returned no rows")
        cache_df.to_parquet(self.cache_path, index=False)
        return _to_output_contract(cache_df)

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        """Fetch the monthly dataset and return cache-compatible timestamp rows."""
        protocol_monthly = _fetch_protocol_monthly_series()
        total_supply = _fetch_total_supply_history()
        category_df = _aggregate_categories(protocol_monthly)
        df = category_df.join(total_supply, how="inner")
        df = df[df["total_supply"].notna() & (df["total_supply"] > 0)]
        df = df[df.index >= pd.Timestamp(START_DATE)]
        df = df[(df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))]
        if df.empty:
            raise DataFetchError("Stablecoin category trend fetch returned no rows after filtering")

        for column in GROUP_COLUMNS:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0).astype(float)
            df[f"{column}_pct"] = df[column] / df["total_supply"] * 100
        df["selected_total"] = df[GROUP_COLUMNS].sum(axis=1)
        df["selected_total_pct"] = df["selected_total"] / df["total_supply"] * 100

        output_df = df.reset_index().rename(columns={"date": "timestamp"})
        for column in OUTPUT_COLUMNS[1:]:
            output_df[column] = pd.to_numeric(output_df[column], errors="coerce").astype(float)
        return output_df[["timestamp", *OUTPUT_COLUMNS[1:]]].sort_values("timestamp").reset_index(drop=True)

    def fetch_latest(self) -> pd.DataFrame:
        """Fetch the latest roughly one month of monthly data."""
        end = date.today()
        start = end - timedelta(days=45)
        return self.fetch_range(start.isoformat(), end.isoformat())


def _fetch_protocol_monthly_series() -> pd.DataFrame:
    """Fetch and month-end resample all representative protocol series."""
    series_by_slug = {}
    for slug in REPRESENTATIVE_PROTOCOLS:
        payload = _get_json_with_retry(f"{API_BASE_URL}/protocol/{slug}")
        series = _extract_makerdao_rwa_series(payload) if slug == "makerdao" else _extract_tvl_series(payload)
        if not series.empty:
            series_by_slug[f"tvl_{slug}"] = series.resample("ME").last()
        time.sleep(0.5)

    if not series_by_slug:
        raise DataFetchError("DefiLlama protocol histories contained no TVL rows")

    df = pd.concat(series_by_slug.values(), axis=1, keys=series_by_slug.keys())
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(None).normalize()
    df.index.name = "date"
    return df.sort_index()


def _extract_tvl_series(payload: Any) -> pd.Series:
    """Extract daily total TVL from a protocol payload."""
    tvl_points = payload.get("tvl", []) if isinstance(payload, dict) else []
    rows = []
    for point in tvl_points:
        if not isinstance(point, dict):
            continue
        rows.append(
            {
                "date": pd.to_datetime(point.get("date"), unit="s", utc=True, errors="coerce"),
                "value": point.get("totalLiquidityUSD"),
            }
        )
    return _series_from_rows(rows)


def _extract_makerdao_rwa_series(payload: Any) -> pd.Series:
    """Prefer MakerDAO RWA-like token TVL, falling back to full TVL."""
    token_series = _extract_token_filtered_series(payload, MAKERDAO_RWA_TOKENS)
    if not token_series.empty and token_series.sum() > 0:
        return token_series
    return _extract_tvl_series(payload)


def _extract_token_filtered_series(payload: Any, token_symbols: set[str]) -> pd.Series:
    """Extract daily TVL by summing selected token symbols from tokensInUsd."""
    tokens_in_usd = payload.get("tokensInUsd", []) if isinstance(payload, dict) else []
    rows = []
    for point in tokens_in_usd:
        if not isinstance(point, dict):
            continue
        tokens = point.get("tokens")
        if not isinstance(tokens, dict):
            continue
        value = sum(_coerce_float(amount) for symbol, amount in tokens.items() if _normalize_symbol(symbol) in token_symbols)
        rows.append({"date": pd.to_datetime(point.get("date"), unit="s", utc=True, errors="coerce"), "value": value})
    return _series_from_rows(rows)


def _series_from_rows(rows: list[dict[str, Any]]) -> pd.Series:
    """Return a normalized daily series from date/value rows."""
    if not rows:
        return pd.Series(dtype="float64")
    df = pd.DataFrame(rows).dropna(subset=["date"])
    if df.empty:
        return pd.Series(dtype="float64")
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert(None).dt.normalize()
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0.0).astype(float)
    return df.groupby("date")["value"].last().sort_index()


def _aggregate_categories(protocol_monthly: pd.DataFrame) -> pd.DataFrame:
    """Sum selected protocol TVL into category columns."""
    filled_df = protocol_monthly.ffill().fillna(0.0)
    category_series = {}
    for category in GROUP_COLUMNS:
        columns = [
            f"tvl_{slug}"
            for slug, metadata in REPRESENTATIVE_PROTOCOLS.items()
            if metadata["category"] == category and f"tvl_{slug}" in filled_df.columns
        ]
        category_series[category] = filled_df[columns].sum(axis=1) if columns else pd.Series(0.0, index=filled_df.index)
    df = pd.DataFrame(category_series, index=filled_df.index).fillna(0.0)
    df.index.name = "date"
    return df


def _fetch_total_supply_history() -> pd.Series:
    """Fetch and month-end resample total stablecoin supply."""
    payload = _get_json_with_retry(f"{STABLECOINS_BASE_URL}/stablecoincharts/all")
    if not isinstance(payload, list):
        raise DataFetchError("DefiLlama stablecoin supply history returned an unexpected payload")

    rows = []
    for point in payload:
        if not isinstance(point, dict):
            continue
        total = point.get("totalCirculatingUSD", {})
        pegged_usd = total.get("peggedUSD") if isinstance(total, dict) else None
        rows.append({"date": pd.to_datetime(point.get("date"), unit="s", utc=True, errors="coerce"), "value": pegged_usd})

    series = _series_from_rows(rows)
    if series.empty:
        raise DataFetchError("DefiLlama stablecoin supply history contained no rows")
    monthly = series.resample("ME").last().dropna().rename("total_supply")
    monthly.index = pd.to_datetime(monthly.index, utc=True).tz_convert(None).normalize()
    monthly.index.name = "date"
    return monthly.astype(float)


def _get_json_with_retry(url: str) -> Any:
    """Fetch JSON with three attempts and exponential backoff."""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (2**attempt))
    raise DataFetchError(f"Failed to fetch DefiLlama data from {url}") from last_error


def _normalize_symbol(symbol: object) -> str:
    """Normalize DefiLlama token keys for exact token symbol matching."""
    return str(symbol).split(":")[-1].strip().upper()


def _coerce_float(value: object) -> float:
    """Return a finite float or zero for bad numeric values."""
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return 0.0
    return float(numeric)


def _to_output_contract(df: pd.DataFrame) -> pd.DataFrame:
    """Return the requested date-indexed DataFrame shape."""
    output_df = df.rename(columns={"timestamp": "date"}).copy()
    output_df["date"] = pd.to_datetime(output_df["date"], utc=True).dt.tz_convert(None).dt.normalize()
    output_df = output_df[OUTPUT_COLUMNS].sort_values("date").reset_index(drop=True)
    output_df.index = pd.DatetimeIndex(output_df["date"], name="date")
    return output_df


def fetch(start: str = START_DATE, end: str | None = None) -> pd.DataFrame:
    """Fetch, cache, and return selected stablecoin category trends."""
    return StablecoinCategoryTrendFetcher().fetch(start=start, end=end)
