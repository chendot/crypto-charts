"""One-off enrichment: add BTC month-end price to stablecoin category trend parquet."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "stablecoin_category_trend.parquet"
LOCAL_BTC_CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "daily" / "btc_daily.csv"
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
REQUEST_TIMEOUT = 30


def main() -> int:
    trend_df = _load_trend_cache(CACHE_PATH)
    btc_df = _fetch_btc_monthly_price()
    updated_df = _merge_btc_price(trend_df, btc_df)
    updated_df.to_parquet(CACHE_PATH, index=False)

    print(updated_df[["date", "Lending_pct", "btc_price"]].tail(12).to_string(index=False))
    print(f"\nshape: {updated_df.shape}")
    has_no_nan = updated_df.loc[updated_df["date"] >= pd.Timestamp("2020-01-01"), "btc_price"].notna().all()
    print(f"btc_price has no NaN after 2020-01-01: {has_no_nan}")
    if not has_no_nan:
        return 1
    return 0


def _load_trend_cache(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing cache: {path}")

    df = pd.read_parquet(path)
    if "date" in df.columns:
        date_values = df["date"]
        output_df = df.drop(columns=["date"]).copy()
    elif "timestamp" in df.columns:
        date_values = df["timestamp"]
        output_df = df.drop(columns=["timestamp"]).copy()
    else:
        date_values = df.index
        output_df = df.reset_index(drop=True).copy()

    output_df.insert(0, "date", _normalize_date(date_values))
    return output_df.sort_values("date").reset_index(drop=True)


def _fetch_btc_monthly_price() -> pd.DataFrame:
    try:
        payload = _get_coingecko_payload()
    except requests.HTTPError as exc:
        response = exc.response
        if response is None or response.status_code != 401:
            raise
        print("CoinGecko public API rejected days=max; falling back to local BTC daily cache.")
        return _load_local_btc_monthly_price()

    prices = payload.get("prices", []) if isinstance(payload, dict) else []
    if not prices:
        raise ValueError("CoinGecko response contained no prices")

    df = pd.DataFrame(prices, columns=["timestamp_ms", "btc_price"])
    df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True, errors="coerce").dt.tz_convert(None).dt.normalize()
    df["btc_price"] = pd.to_numeric(df["btc_price"], errors="coerce").astype(float)
    return _monthly_price(df)


def _load_local_btc_monthly_price() -> pd.DataFrame:
    if not LOCAL_BTC_CACHE_PATH.exists():
        raise FileNotFoundError(f"Missing local BTC cache: {LOCAL_BTC_CACHE_PATH}")
    df = pd.read_csv(LOCAL_BTC_CACHE_PATH)
    df = df.rename(columns={"price": "btc_price"})
    df["date"] = _normalize_date(df["date"])
    df["btc_price"] = pd.to_numeric(df["btc_price"], errors="coerce").astype(float)
    return _monthly_price(df)


def _monthly_price(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["date", "btc_price"]).sort_values("date")
    monthly = df.set_index("date")["btc_price"].resample("ME").last().ffill().rename("btc_price")
    monthly.index = _normalize_date(monthly.index)
    return monthly.reset_index().rename(columns={"index": "date"})


def _get_coingecko_payload() -> Any:
    params = {"vs_currency": "usd", "days": "max", "interval": "daily"}
    response = requests.get(COINGECKO_URL, params=params, timeout=REQUEST_TIMEOUT)
    if response.status_code == 429:
        time.sleep(60)
        response = requests.get(COINGECKO_URL, params=params, timeout=REQUEST_TIMEOUT)
    if response.status_code == 401:
        public_params = {"vs_currency": "usd", "days": "max"}
        response = requests.get(COINGECKO_URL, params=public_params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 429:
            time.sleep(60)
            response = requests.get(COINGECKO_URL, params=public_params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _merge_btc_price(trend_df: pd.DataFrame, btc_df: pd.DataFrame) -> pd.DataFrame:
    output_df = trend_df.drop(columns=["btc_price"], errors="ignore").merge(btc_df, on="date", how="left")
    output_df["btc_price"] = pd.to_numeric(output_df["btc_price"], errors="coerce").ffill().astype(float)
    return output_df.sort_values("date").reset_index(drop=True)


def _normalize_date(values: object) -> pd.Series:
    dates = pd.to_datetime(values, utc=True, errors="coerce")
    return pd.Series(dates).dt.tz_convert(None).dt.normalize()


if __name__ == "__main__":
    raise SystemExit(main())
