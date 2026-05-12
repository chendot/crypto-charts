"""Source: DefiLlama API; dataset: monthly stablecoin DeFi ratio; update frequency: daily."""

from __future__ import annotations

from collections import defaultdict
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
MIN_STABLECOIN_TVL_USD = 1_000_000
START_DATE = "2022-01-01"

STABLECOIN_SYMBOLS = {
    "USDT",
    "USDC",
    "DAI",
    "USDE",
    "FRAX",
    "LUSD",
    "CRVUSD",
    "GHO",
    "PYUSD",
    "USDM",
    "USDS",
    "FDUSD",
    "TUSD",
    "BUSD",
    "GUSD",
    "USDP",
    "HUSD",
    "SUSD",
    "ALUSD",
    "MIM",
}
GROUP_COLUMNS = ["RWA", "Basis_Trading", "Lending", "DEX", "Bridge", "Other"]
OUTPUT_COLUMNS = [
    "date",
    *GROUP_COLUMNS,
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


class StablecoinDefiRatioFetcher(BaseFetcher):
    """Fetch monthly stablecoin TVL by DefiLlama protocol category."""

    source_id = ""
    dataset_id = "stablecoin_defi_ratio"

    def fetch(self, start: str = START_DATE, end: str | None = None) -> pd.DataFrame:
        """Fetch, cache, and return the date-indexed output contract."""
        end_date = end or date.today().isoformat()
        cache_df = self.fetch_range(start, end_date)
        if cache_df.empty:
            raise DataFetchError("Stablecoin DeFi ratio fetch returned no rows")
        cache_df.to_parquet(self.cache_path, index=False)
        return _to_output_contract(cache_df)

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        """Fetch the monthly dataset and return cache-compatible timestamp rows."""
        protocol_universe = _build_protocol_universe()
        if not protocol_universe:
            raise DataFetchError("DefiLlama protocol snapshot contained no qualifying stablecoin protocols")

        grouped_monthly = _aggregate_protocol_histories(protocol_universe)
        total_supply = _fetch_total_supply_history()
        df = grouped_monthly.join(total_supply, how="inner")
        df = df[df["total_supply"].notna() & (df["total_supply"] > 0)]
        df = df[df.index >= pd.Timestamp(START_DATE)]
        df = df[(df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))]
        if df.empty:
            raise DataFetchError("Stablecoin DeFi ratio fetch returned no rows after filtering")

        for column in GROUP_COLUMNS:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0).astype(float)
            df[f"{column}_pct"] = df[column] / df["total_supply"] * 100
        df["defi_total"] = df[GROUP_COLUMNS].sum(axis=1)
        df["defi_total_pct"] = df["defi_total"] / df["total_supply"] * 100

        output_df = df.reset_index().rename(columns={"date": "timestamp"})
        for column in [*GROUP_COLUMNS, "total_supply", *[f"{column}_pct" for column in GROUP_COLUMNS], "defi_total", "defi_total_pct"]:
            output_df[column] = pd.to_numeric(output_df[column], errors="coerce").astype(float)
        return output_df[["timestamp", *OUTPUT_COLUMNS[1:]]].sort_values("timestamp").reset_index(drop=True)

    def fetch_latest(self) -> pd.DataFrame:
        """Fetch the latest roughly one month of monthly data."""
        end = date.today()
        start = end - timedelta(days=45)
        return self.fetch_range(start.isoformat(), end.isoformat())


def _build_protocol_universe() -> dict[str, list[str]]:
    """Return qualifying protocol slugs grouped into chart categories."""
    payload = _get_json_with_retry(f"{API_BASE_URL}/protocols")
    if not isinstance(payload, list):
        raise DataFetchError("DefiLlama protocol snapshot returned an unexpected payload")

    grouped_slugs: dict[str, list[str]] = defaultdict(list)
    for item in payload:
        if not isinstance(item, dict):
            continue
        stablecoin_tvl = _current_protocol_filter_value(item)
        slug = item.get("slug")
        if stablecoin_tvl <= MIN_STABLECOIN_TVL_USD or not slug:
            continue
        group = _map_category(item.get("category"))
        grouped_slugs[group].append(str(slug))

    return {group: sorted(slugs) for group, slugs in grouped_slugs.items()}


def _current_protocol_filter_value(item: dict[str, Any]) -> float:
    """Return current protocol size for the Step 1 universe filter.

    DefiLlama previously exposed ``stablecoinTvl`` on /protocols. The current
    payload exposes only issuer metadata in ``stablecoins`` and no numeric
    stablecoin-specific snapshot for lending/DEX protocols, so ``tvl`` is the
    broad fallback before Step 2 computes the actual stablecoin proxy.
    """
    stablecoin_tvl = _coerce_float(item.get("stablecoinTvl"))
    if stablecoin_tvl > 0:
        return stablecoin_tvl
    return _coerce_float(item.get("tvl"))


def _map_category(category: object) -> str:
    """Map DefiLlama categories to the stablecoin ratio groups."""
    category_text = str(category or "")
    if category_text == "RWA":
        return "RWA"
    if category_text == "Basis Trading":
        return "Basis_Trading"
    if category_text in {"Lending", "CDP", "Risk Curators"}:
        return "Lending"
    if category_text in {"Dexes", "Dexs"}:
        return "DEX"
    if category_text == "Bridge":
        return "Bridge"
    return "Other"


def _aggregate_protocol_histories(protocol_universe: dict[str, list[str]]) -> pd.DataFrame:
    """Sum monthly stablecoin proxy TVL across protocols in each group."""
    monthly_by_group: dict[str, list[pd.Series]] = {column: [] for column in GROUP_COLUMNS}
    for group, slugs in protocol_universe.items():
        for slug in slugs:
            payload = _get_json_with_retry(f"{API_BASE_URL}/protocol/{slug}")
            series = _extract_protocol_stablecoin_series(payload)
            if not series.empty:
                monthly_by_group[group].append(series.resample("ME").last())
            time.sleep(0.3)

    group_series = {}
    for group in GROUP_COLUMNS:
        series_list = monthly_by_group[group]
        if not series_list:
            group_series[group] = pd.Series(dtype="float64")
            continue
        group_series[group] = pd.concat(series_list, axis=1).fillna(0.0).sum(axis=1).rename(group)

    df = pd.concat(group_series.values(), axis=1).fillna(0.0)
    if df.empty:
        raise DataFetchError("DefiLlama protocol histories contained no stablecoin token rows")
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(None).normalize()
    df.index.name = "date"
    return df.reindex(columns=GROUP_COLUMNS, fill_value=0.0)


def _extract_protocol_stablecoin_series(payload: Any) -> pd.Series:
    """Extract a daily stablecoin TVL proxy from a protocol payload."""
    tokens_in_usd = payload.get("tokensInUsd", []) if isinstance(payload, dict) else []
    rows = []
    for point in tokens_in_usd:
        if not isinstance(point, dict):
            continue
        token_values = point.get("tokens")
        if not isinstance(token_values, dict):
            continue
        value = sum(
            _coerce_float(amount)
            for symbol, amount in token_values.items()
            if _normalize_symbol(symbol) in STABLECOIN_SYMBOLS
        )
        rows.append({"date": pd.to_datetime(point.get("date"), unit="s", utc=True, errors="coerce"), "value": value})

    if not rows:
        return pd.Series(dtype="float64")
    df = pd.DataFrame(rows).dropna(subset=["date"])
    if df.empty:
        return pd.Series(dtype="float64")
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert(None).dt.normalize()
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0.0).astype(float)
    return df.groupby("date")["value"].sum().sort_index()


def _normalize_symbol(symbol: object) -> str:
    """Normalize DefiLlama token keys for exact stablecoin symbol matching."""
    return str(symbol).split(":")[-1].strip().upper()


def _coerce_float(value: object) -> float:
    """Return a finite float or zero for bad token values."""
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return 0.0
    return float(numeric)


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
        rows.append({"date": pd.to_datetime(point.get("date"), unit="s", utc=True, errors="coerce"), "total_supply": pegged_usd})

    df = pd.DataFrame(rows).dropna(subset=["date"])
    if df.empty:
        raise DataFetchError("DefiLlama stablecoin supply history contained no rows")
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert(None).dt.normalize()
    df["total_supply"] = pd.to_numeric(df["total_supply"], errors="coerce")
    monthly = df.set_index("date")["total_supply"].resample("ME").last().dropna()
    monthly.index = pd.to_datetime(monthly.index, utc=True).tz_convert(None).normalize()
    monthly.index.name = "date"
    return monthly.astype(float)


def _get_json_with_retry(url: str) -> Any:
    """Fetch JSON with three attempts and exponential backoff on HTTP errors."""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)
    raise DataFetchError(f"Failed to fetch DefiLlama data from {url}") from last_error


def _to_output_contract(df: pd.DataFrame) -> pd.DataFrame:
    """Return the requested date-indexed DataFrame shape."""
    output_df = df.rename(columns={"timestamp": "date"}).copy()
    output_df["date"] = pd.to_datetime(output_df["date"], utc=True).dt.tz_convert(None).dt.normalize()
    output_df = output_df[OUTPUT_COLUMNS].sort_values("date").reset_index(drop=True)
    output_df.index = pd.DatetimeIndex(output_df["date"], name="date")
    return output_df


def fetch(start: str = START_DATE, end: str | None = None) -> pd.DataFrame:
    """Fetch, cache, and return monthly stablecoin DeFi ratios."""
    return StablecoinDefiRatioFetcher().fetch(start=start, end=end)
