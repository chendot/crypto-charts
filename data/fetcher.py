"""Data fetchers with local caching for market, macro, and static data."""

from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import time
import zipfile
import requests
import pandas as pd


REQUEST_TIMEOUT = 15
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
DEFILLAMA_BASE_URL = "https://api.llama.fi"
BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_ARCHIVE_BASE_URL = "https://data.binance.vision/data/spot/monthly/klines"
FRED_GRAPH_BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
STATIC_DIR = DATA_DIR / "static"


class CacheManager:
    """Read, write, and incrementally update local CSV datasets."""

    UPDATE_INTERVAL = {
        "btc_daily": 4,
        "eth_daily": 4,
        "sol_daily": 4,
        "nasdaq_daily": 24,
        "sp500_daily": 24,
        "gold_daily": 24,
        "dxy_daily": 24,
        "us10y_daily": 24,
        "fed_funds": 168,
        "cpi": 168,
        "btc_marketcap": 24,
        "stablecoin": 24,
        "m2_supply": 168,
        "static": 999999,
    }

    FULL_HISTORY_START = {
        "btc_daily": "2018-01-01",
        "eth_daily": "2018-01-01",
        "sol_daily": "2020-01-01",
        "nasdaq_daily": "2018-01-01",
        "sp500_daily": "2018-01-01",
        "gold_daily": "2018-01-01",
        "dxy_daily": "2018-01-01",
        "us10y_daily": "2018-01-01",
        "fed_funds": "2015-01-01",
        "cpi": "2015-01-01",
        "btc_marketcap": "2018-01-01",
        "stablecoin": "2020-01-01",
        "m2_supply": "2015-01-01",
    }

    KEY_DIR = {
        "btc_daily": CACHE_DIR / "daily",
        "eth_daily": CACHE_DIR / "daily",
        "sol_daily": CACHE_DIR / "daily",
        "nasdaq_daily": CACHE_DIR / "macro",
        "sp500_daily": CACHE_DIR / "macro",
        "gold_daily": CACHE_DIR / "macro",
        "dxy_daily": CACHE_DIR / "macro",
        "us10y_daily": CACHE_DIR / "macro",
        "fed_funds": CACHE_DIR / "macro",
        "cpi": CACHE_DIR / "macro",
        "m2_supply": CACHE_DIR / "macro",
        "btc_marketcap": CACHE_DIR / "onchain",
        "stablecoin": CACHE_DIR / "onchain",
    }

    def __init__(self) -> None:
        ensure_data_directories()

    def path_for(self, key: str) -> Path:
        """Return the cache CSV path for a dataset key."""
        return self.KEY_DIR.get(key, CACHE_DIR / "daily") / f"{key}.csv"

    def needs_update(self, key: str) -> bool:
        """Return True when the cache is missing or older than the configured interval."""
        path = self.path_for(key)
        if not path.exists():
            return True

        interval_hours = self.UPDATE_INTERVAL.get(key, 24)
        age_seconds = datetime.now().timestamp() - path.stat().st_mtime
        return age_seconds >= interval_hours * 60 * 60

    def read(self, key: str) -> pd.DataFrame | None:
        """Read a local cache CSV with a normalized datetime date column."""
        path = self.path_for(key)
        if not path.exists():
            return None

        df = pd.read_csv(path)
        if "date" not in df.columns:
            return df

        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        return df.sort_values("date").reset_index(drop=True)

    def write(self, key: str, df: pd.DataFrame) -> None:
        """Write a DataFrame to cache with YYYY-MM-DD date strings."""
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        output_df = df.copy()
        if "date" in output_df.columns:
            output_df["date"] = pd.to_datetime(output_df["date"]).dt.strftime("%Y-%m-%d")
            output_df = output_df.sort_values("date").reset_index(drop=True)
        output_df.to_csv(path, index=False)

    def append(self, key: str, new_df: pd.DataFrame) -> pd.DataFrame:
        """Append new rows to local cache, dedupe by date, and keep the newest value."""
        existing_df = self.read(key)
        if existing_df is None or existing_df.empty:
            merged_df = new_df.copy()
        else:
            merged_df = pd.concat([existing_df, new_df], ignore_index=True)

        if "date" in merged_df.columns:
            merged_df["date"] = pd.to_datetime(merged_df["date"]).dt.tz_localize(None)
            merged_df = (
                merged_df.dropna(subset=["date"])
                .drop_duplicates(subset=["date"], keep="last")
                .sort_values("date")
                .reset_index(drop=True)
            )
        self.write(key, merged_df)
        stored_df = self.read(key)
        return stored_df if stored_df is not None else merged_df

    def get_last_date(self, key: str) -> str | None:
        """Return the latest cached date as YYYY-MM-DD, or None when no cache exists."""
        df = self.read(key)
        if df is None or df.empty or "date" not in df.columns:
            return None
        return pd.to_datetime(df["date"].max()).strftime("%Y-%m-%d")


def ensure_data_directories() -> None:
    """Create cache and static data directories used by fetchers."""
    for directory in (
        CACHE_DIR / "daily",
        CACHE_DIR / "macro",
        CACHE_DIR / "onchain",
        STATIC_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def initialize_static_data() -> None:
    """Create permanent static data files if they are missing."""
    ensure_data_directories()
    halvings_path = STATIC_DIR / "btc_halvings.json"
    if not halvings_path.exists():
        halvings = [
            {"date": "2012-11-28", "block": 210000, "reward": 25},
            {"date": "2016-07-09", "block": 420000, "reward": 12.5},
            {"date": "2020-05-11", "block": 630000, "reward": 6.25},
            {"date": "2024-04-20", "block": 840000, "reward": 3.125},
        ]
        halvings_path.write_text(json.dumps(halvings, indent=2), encoding="utf-8")


initialize_static_data()


def _filter_date_range(df: pd.DataFrame, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Filter a date-indexed DataFrame by optional start and end boundaries."""
    filtered = df.copy()
    if filtered.empty or "date" not in filtered.columns:
        return filtered

    filtered["date"] = pd.to_datetime(filtered["date"]).dt.tz_localize(None)
    if start is not None:
        filtered = filtered[filtered["date"] >= pd.Timestamp(start)]
    if end is not None:
        filtered = filtered[filtered["date"] <= pd.Timestamp(end)]
    return filtered.sort_values("date").reset_index(drop=True)


def _ensure_price_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with stable date/price columns."""
    if df.empty and not {"date", "price"}.issubset(df.columns):
        return pd.DataFrame(
            {
                "date": pd.Series(dtype="datetime64[ns]"),
                "price": pd.Series(dtype="float64"),
            }
        )
    output_df = df[["date", "price"]].copy()
    output_df["date"] = pd.to_datetime(output_df["date"])
    return output_df


def _today_end_date() -> str:
    """Return a yfinance-friendly end date that includes the current day when available."""
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


def smart_fetch(key: str, fetch_fn) -> pd.DataFrame:
    """
    Unified cache-aware fetch entrypoint.

    fetch_fn must accept start_date and end_date and return a DataFrame with a date column.
    """
    cache = CacheManager()
    cached_df = cache.read(key)
    if not cache.needs_update(key):
        return cached_df if cached_df is not None else pd.DataFrame()

    last_date = cache.get_last_date(key)
    start_date = last_date or cache.FULL_HISTORY_START[key]
    end_date = _today_end_date()

    try:
        time.sleep(1)
        new_df = fetch_fn(start_date, end_date)
        time.sleep(1)

        if new_df is None or new_df.empty:
            raise ValueError(f"{key} returned no rows")
        if "date" not in new_df.columns:
            raise ValueError(f"{key} data must include a date column")

        if cached_df is None or cached_df.empty:
            cache.write(key, new_df)
            stored_df = cache.read(key)
            return stored_df if stored_df is not None else new_df
        return cache.append(key, new_df)
    except Exception as exc:
        print(f"Failed to update {key}: {exc}")
        return cached_df if cached_df is not None else pd.DataFrame()


def _extract_yfinance_column(download_df: pd.DataFrame, ticker: str, col: str) -> pd.Series:
    """Extract a yfinance value column from flat or MultiIndex downloads."""
    if isinstance(download_df.columns, pd.MultiIndex):
        if (col, ticker) in download_df.columns:
            return download_df[(col, ticker)]
        return download_df.xs(col, axis=1, level=0).iloc[:, 0]
    return download_df[col]


def _fetch_yfinance(ticker: str, start: str, end: str, col: str = "Close") -> pd.DataFrame:
    """Fetch a yfinance daily series and return date/price columns."""
    import yfinance as yf

    raw_df = yf.download(
        ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        timeout=30,
        progress=False,
    )
    if raw_df.empty:
        raise ValueError(f"Yahoo Finance returned no data for {ticker}")

    price = _extract_yfinance_column(raw_df, ticker, col)
    df = price.rename("price").reset_index()
    date_column = "Date" if "Date" in df.columns else df.columns[0]
    df["date"] = pd.to_datetime(df[date_column]).dt.tz_localize(None).dt.date
    return df[["date", "price"]].dropna().sort_values("date").reset_index(drop=True)


def _fetch_with_fallback(fetchers: list) -> pd.DataFrame:
    """Try fetchers in order and return the first non-empty result."""
    errors = []
    for fetcher in fetchers:
        try:
            df = fetcher()
            if df is not None and not df.empty:
                return df
            errors.append("empty result")
        except Exception as exc:
            errors.append(str(exc))
    raise RuntimeError("; ".join(errors))


def _fetch_binance_klines(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch Binance spot daily klines and return date/price/volume columns."""
    start_ms = int(pd.Timestamp(start).timestamp() * 1000)
    end_ms = int(pd.Timestamp(end).timestamp() * 1000)
    rows = []

    while start_ms < end_ms:
        response = requests.get(
            f"{BINANCE_BASE_URL}/api/v3/klines",
            params={
                "symbol": symbol,
                "interval": "1d",
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": 1000,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload:
            break
        rows.extend(payload)
        next_start_ms = int(payload[-1][0]) + 86_400_000
        if next_start_ms <= start_ms:
            break
        start_ms = next_start_ms
        time.sleep(0.2)

    if not rows:
        raise ValueError(f"Binance returned no data for {symbol}")

    df = pd.DataFrame(rows)
    result = pd.DataFrame(
        {
            "date": pd.to_datetime(df[0], unit="ms").dt.tz_localize(None).dt.date,
            "price": pd.to_numeric(df[4], errors="coerce"),
            "volume": pd.to_numeric(df[7], errors="coerce"),
        }
    )
    return result.dropna(subset=["date", "price"]).sort_values("date").reset_index(drop=True)


def _curl_fetch_bytes(url: str, max_time: str = "30") -> bytes:
    """Fetch bytes with curl, bypassing broken Python SSL paths when needed."""
    env = os.environ.copy()
    for proxy_key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
        env.pop(proxy_key, None)
    result = subprocess.run(
        ["curl", "-L", "--fail", "--silent", "--show-error", "--max-time", max_time, url],
        capture_output=True,
        check=True,
        env=env,
    )
    return result.stdout


def _month_starts(start: str, end: str) -> list[pd.Timestamp]:
    first_month = pd.Timestamp(start).to_period("M").to_timestamp()
    last_month = pd.Timestamp(end).to_period("M").to_timestamp()
    return list(pd.date_range(first_month, last_month, freq="MS"))


def _fetch_binance_archive_klines(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch Binance public monthly kline archives and return date/price/volume columns."""
    frames = []
    for month_start in _month_starts(start, end):
        month_text = month_start.strftime("%Y-%m")
        url = f"{BINANCE_ARCHIVE_BASE_URL}/{symbol}/1d/{symbol}-1d-{month_text}.zip"
        try:
            archive_bytes = _curl_fetch_bytes(url)
        except subprocess.CalledProcessError:
            continue

        with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
            csv_name = archive.namelist()[0]
            with archive.open(csv_name) as csv_file:
                df = pd.read_csv(csv_file, header=None)
        if df.empty:
            continue
        open_time = pd.to_numeric(df[0], errors="coerce")
        time_unit = "us" if open_time.dropna().median() > 10_000_000_000_000 else "ms"
        frames.append(
            pd.DataFrame(
                {
                    "date": pd.to_datetime(open_time, unit=time_unit, errors="coerce").dt.tz_localize(None).dt.date,
                    "price": pd.to_numeric(df[4], errors="coerce"),
                    "volume": pd.to_numeric(df[7], errors="coerce"),
                }
            )
        )
        time.sleep(0.1)

    if not frames:
        raise ValueError(f"Binance archive returned no data for {symbol}")

    result = pd.concat(frames, ignore_index=True)
    result["date"] = pd.to_datetime(result["date"]).dt.tz_localize(None)
    result = _filter_date_range(result, start, end)
    return result.dropna(subset=["date", "price"]).sort_values("date").reset_index(drop=True)


def _fetch_fred_series(series_id: str, start: str, end: str, column_name: str = "price") -> pd.DataFrame:
    """Fetch a public FRED CSV series and return date/value columns."""
    from io import StringIO

    params = {"id": series_id, "cosd": start, "coed": end}
    try:
        response = requests.get(FRED_GRAPH_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        csv_text = response.text
    except requests.RequestException:
        query = f"id={series_id}&cosd={start}&coed={end}"
        csv_text = _curl_fetch_bytes(f"{FRED_GRAPH_BASE_URL}?{query}").decode()

    df = pd.read_csv(StringIO(csv_text))
    value_column = series_id if series_id in df.columns else df.columns[-1]
    result = pd.DataFrame(
        {
            "date": pd.to_datetime(df["observation_date"]).dt.tz_localize(None).dt.date,
            column_name: pd.to_numeric(df[value_column].replace(".", pd.NA), errors="coerce"),
        }
    )
    return result.dropna().sort_values("date").reset_index(drop=True)


def _fetch_coingecko_market_chart_range(coin_id: str, start: str, end: str) -> pd.DataFrame:
    """Fetch CoinGecko historical price, market cap, and volume over a date range."""
    from_ts = int(pd.Timestamp(start).timestamp())
    to_ts = int(pd.Timestamp(end).timestamp())
    response = requests.get(
        f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart/range",
        params={"vs_currency": "usd", "from": from_ts, "to": to_ts},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    prices = payload.get("prices", [])
    if not prices:
        raise ValueError(f"CoinGecko returned no price data for {coin_id}")

    price_df = pd.DataFrame(prices, columns=["timestamp", "price"])
    price_df["date"] = pd.to_datetime(price_df["timestamp"], unit="ms").dt.tz_localize(None).dt.date
    result = price_df[["date", "price"]].copy()

    market_caps = payload.get("market_caps", [])
    if market_caps:
        marketcap_df = pd.DataFrame(market_caps, columns=["timestamp", "marketcap"])
        marketcap_df["date"] = pd.to_datetime(marketcap_df["timestamp"], unit="ms").dt.tz_localize(None).dt.date
        result = result.merge(marketcap_df[["date", "marketcap"]], on="date", how="left")

    volumes = payload.get("total_volumes", [])
    if volumes:
        volume_df = pd.DataFrame(volumes, columns=["timestamp", "volume"])
        volume_df["date"] = pd.to_datetime(volume_df["timestamp"], unit="ms").dt.tz_localize(None).dt.date
        result = result.merge(volume_df[["date", "volume"]], on="date", how="left")

    return (
        result.dropna(subset=["date", "price"])
        .drop_duplicates(subset=["date"], keep="last")
        .sort_values("date")
        .reset_index(drop=True)
    )


def _fetch_btc_daily(start: str, end: str) -> pd.DataFrame:
    return _fetch_with_fallback(
        [
            lambda: _fetch_binance_archive_klines("BTCUSDT", start, end),
            lambda: _fetch_binance_klines("BTCUSDT", start, end),
            lambda: _fetch_coingecko_market_chart_range("bitcoin", start, end),
            lambda: _fetch_yfinance("BTC-USD", start, end),
        ]
    )


def _fetch_eth_daily(start: str, end: str) -> pd.DataFrame:
    return _fetch_with_fallback(
        [
            lambda: _fetch_binance_archive_klines("ETHUSDT", start, end),
            lambda: _fetch_binance_klines("ETHUSDT", start, end),
            lambda: _fetch_coingecko_market_chart_range("ethereum", start, end),
            lambda: _fetch_yfinance("ETH-USD", start, end),
        ]
    )


def _fetch_sol_daily(start: str, end: str) -> pd.DataFrame:
    return _fetch_with_fallback(
        [
            lambda: _fetch_binance_archive_klines("SOLUSDT", start, end),
            lambda: _fetch_binance_klines("SOLUSDT", start, end),
            lambda: _fetch_coingecko_market_chart_range("solana", start, end),
            lambda: _fetch_yfinance("SOL-USD", start, end),
        ]
    )


def _fetch_nasdaq_daily(start: str, end: str) -> pd.DataFrame:
    return _fetch_with_fallback(
        [
            lambda: _fetch_fred_series("NASDAQCOM", start, end),
            lambda: _fetch_yfinance("^IXIC", start, end),
        ]
    )


def _fetch_sp500_daily(start: str, end: str) -> pd.DataFrame:
    return _fetch_with_fallback(
        [
            lambda: _fetch_fred_series("SP500", start, end),
            lambda: _fetch_yfinance("^GSPC", start, end),
        ]
    )


def _fetch_gold_daily(start: str, end: str) -> pd.DataFrame:
    return _fetch_with_fallback(
        [
            lambda: _fetch_binance_archive_klines("PAXGUSDT", start, end),
            lambda: _fetch_fred_series("GOLDAMGBD228NLBM", start, end),
            lambda: _fetch_yfinance("GC=F", start, end),
        ]
    )


def _fetch_dxy_daily(start: str, end: str) -> pd.DataFrame:
    return _fetch_with_fallback(
        [
            lambda: _fetch_fred_series("DTWEXBGS", start, end),
            lambda: _fetch_yfinance("DX-Y.NYB", start, end),
        ]
    )


def _fetch_us10y_daily(start: str, end: str) -> pd.DataFrame:
    return _fetch_fred_series("DGS10", start, end)


def _fetch_fed_funds(start: str, end: str) -> pd.DataFrame:
    return _fetch_fred_series("FEDFUNDS", start, end)


def _fetch_cpi(start: str, end: str) -> pd.DataFrame:
    return _fetch_fred_series("CPIAUCSL", start, end)


def _fetch_m2_supply(start: str, end: str) -> pd.DataFrame:
    return _fetch_fred_series("M2SL", start, end)


def get_btc(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached BTC daily price history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("btc_daily", _fetch_btc_daily), start, end))


def get_eth(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached ETH daily price history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("eth_daily", _fetch_eth_daily), start, end))


def get_sol(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached SOL daily price history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("sol_daily", _fetch_sol_daily), start, end))


def get_nasdaq(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached Nasdaq daily price history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("nasdaq_daily", _fetch_nasdaq_daily), start, end))


def get_sp500(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached S&P 500 daily price history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("sp500_daily", _fetch_sp500_daily), start, end))


def get_gold(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached gold futures daily price history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("gold_daily", _fetch_gold_daily), start, end))


def get_dxy(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached broad dollar index daily history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("dxy_daily", _fetch_dxy_daily), start, end))


def get_us10y(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached 10-year Treasury yield daily history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("us10y_daily", _fetch_us10y_daily), start, end))


def get_fed_funds(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached effective Fed funds monthly history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("fed_funds", _fetch_fed_funds), start, end))


def get_cpi(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached CPI monthly history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("cpi", _fetch_cpi), start, end))


def get_m2_supply(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return cached M2 money stock monthly history."""
    return _ensure_price_schema(_filter_date_range(smart_fetch("m2_supply", _fetch_m2_supply), start, end))


def _hours_since_update(key: str) -> float | None:
    path = CacheManager().path_for(key)
    if not path.exists():
        return None
    return (datetime.now().timestamp() - path.stat().st_mtime) / 3600


def refresh_all() -> None:
    """Refresh all core cached datasets in a rate-limit-friendly order."""
    crypto_datasets = [
        ("btc_daily", _fetch_btc_daily),
        ("eth_daily", _fetch_eth_daily),
        ("sol_daily", _fetch_sol_daily),
    ]
    macro_datasets = [
        ("nasdaq_daily", _fetch_nasdaq_daily),
        ("sp500_daily", _fetch_sp500_daily),
        ("gold_daily", _fetch_gold_daily),
        ("dxy_daily", _fetch_dxy_daily),
        ("us10y_daily", _fetch_us10y_daily),
        ("fed_funds", _fetch_fed_funds),
        ("cpi", _fetch_cpi),
        ("m2_supply", _fetch_m2_supply),
    ]
    datasets = crypto_datasets + macro_datasets
    cache = CacheManager()
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for index, (key, fetch_fn) in enumerate(datasets):
        before_df = cache.read(key)
        before_rows = 0 if before_df is None else len(before_df)
        before_last = cache.get_last_date(key)
        needs_update = cache.needs_update(key)

        if not needs_update:
            hours = _hours_since_update(key) or 0
            print(f"✓ {key}: 已是最新（{hours:.0f}小时前更新，共 {before_rows:,} 行）")
            skipped_count += 1
        else:
            result_df = smart_fetch(key, fetch_fn)
            after_rows = len(result_df)
            after_last = cache.get_last_date(key)
            if after_rows > before_rows or (before_rows > 0 and after_last != before_last):
                if before_last:
                    days = max((pd.Timestamp(after_last) - pd.Timestamp(before_last)).days, 0)
                    print(f"↓ {key}: 增量更新 {days} 天 → 追加成功（共 {after_rows:,} 行）")
                else:
                    print(f"↓ {key}: 全量下载 → 写入成功（共 {after_rows:,} 行）")
                success_count += 1
            elif after_rows > 0:
                print(f"✓ {key}: 已是最新（共 {after_rows:,} 行）")
                skipped_count += 1
            else:
                print(f"✗ {key}: 更新失败，使用本地缓存（共 {before_rows:,} 行）")
                failed_count += 1

        if key == crypto_datasets[-1][0]:
            time.sleep(3)
        elif index < len(datasets) - 1:
            time.sleep(2)

    print(
        f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} / "
        f"成功数: {success_count} / 跳过数: {skipped_count} / 失败数: {failed_count}"
    )


def get_price_history(coin_id: str, days: int) -> pd.DataFrame:
    """Fetch historical coin prices, using local yfinance cache for BTC and ETH."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    if coin_id == "bitcoin":
        df = get_btc(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        df["volume"] = pd.Series(0, index=df.index, dtype="float64")
        return df[["date", "price", "volume"]]
    if coin_id == "ethereum":
        df = get_eth(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        df["volume"] = pd.Series(0, index=df.index, dtype="float64")
        return df[["date", "price", "volume"]]

    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch CoinGecko price history for {coin_id}") from exc

    prices = payload.get("prices", [])
    volumes = payload.get("total_volumes", [])
    if not prices or not volumes:
        raise ValueError(f"CoinGecko returned no price or volume data for {coin_id}")

    price_df = pd.DataFrame(prices, columns=["timestamp", "price"])
    volume_df = pd.DataFrame(volumes, columns=["timestamp", "volume"])
    df = price_df.merge(volume_df, on="timestamp", how="inner")
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.tz_localize(None)
    return df[["date", "price", "volume"]]


def get_tvl(protocol: str) -> pd.DataFrame:
    """Fetch protocol TVL history from DeFiLlama."""
    url = f"{DEFILLAMA_BASE_URL}/protocol/{protocol}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch DeFiLlama TVL for {protocol}") from exc

    tvl = payload.get("tvl", [])
    if not tvl:
        raise ValueError(f"DeFiLlama returned no TVL data for {protocol}")

    df = pd.DataFrame(tvl)
    df["date"] = pd.to_datetime(df["date"], unit="s").dt.tz_localize(None)
    df = df.rename(columns={"totalLiquidityUSD": "tvl"})
    return df[["date", "tvl"]]


def get_macro_comparison(years: int = 5) -> pd.DataFrame:
    """Fetch and normalize BTC, gold, and S&P 500 price history."""
    empty_df = pd.DataFrame(columns=["date", "btc", "gold", "sp500"])

    try:
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        btc_df = get_btc(start_date, end_date).rename(columns={"price": "btc"})
        gold_df = get_gold(start_date, end_date).rename(columns={"price": "gold"})
        sp500_df = get_sp500(start_date, end_date).rename(columns={"price": "sp500"})
        if btc_df.empty or gold_df.empty or sp500_df.empty:
            raise ValueError("One or more macro comparison datasets are empty")
    except Exception as exc:
        print(f"Failed to fetch macro comparison data: {exc}")
        return empty_df

    try:
        common_start = max(btc_df["date"].min(), gold_df["date"].min(), sp500_df["date"].min())
        merged = btc_df.merge(gold_df, on="date", how="inner").merge(sp500_df, on="date", how="inner")
        merged = merged[merged["date"] >= common_start].dropna().sort_values("date").reset_index(drop=True)
        if merged.empty:
            raise ValueError("No overlapping macro comparison dates")

        base_row = merged.iloc[0]
        last_row = merged.iloc[-1]
        for column in ("btc", "gold", "sp500"):
            merged[column] = merged[column] / base_row[column] * 100

        result = merged[["date", "btc", "gold", "sp500"]].dropna().sort_values("date").reset_index(drop=True)
        result.attrs["btc_start_price"] = float(base_row["btc"])
        result.attrs["btc_end_price"] = float(last_row["btc"])
        return result
    except Exception as exc:
        print(f"Failed to normalize macro comparison data: {exc}")
        return empty_df


def get_btc_nasdaq_correlation(years: int = 5) -> pd.DataFrame:
    """Fetch BTC and Nasdaq prices, then calculate 90-day rolling return correlation."""
    empty_df = pd.DataFrame(columns=["date", "btc_price", "nasdaq_price", "correlation"])

    try:
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        btc_df = get_btc(start_date, end_date).rename(columns={"price": "btc_price"})
        nasdaq_df = get_nasdaq(start_date, end_date).rename(columns={"price": "nasdaq_price"})
        if btc_df.empty or nasdaq_df.empty:
            raise ValueError("One or more BTC/Nasdaq datasets are empty")
    except Exception as exc:
        print(f"Failed to fetch BTC/Nasdaq correlation data: {exc}")
        return empty_df

    try:
        prices = btc_df.merge(nasdaq_df, on="date", how="inner")
        prices["date"] = pd.to_datetime(prices["date"]).dt.tz_localize(None)
        prices = prices.dropna().sort_values("date").reset_index(drop=True)
        if prices.empty:
            raise ValueError("No overlapping BTC and Nasdaq dates")

        btc_returns = prices["btc_price"].pct_change()
        nasdaq_returns = prices["nasdaq_price"].pct_change()
        correlation = btc_returns.rolling(90).corr(nasdaq_returns)

        result = prices.copy()
        result["correlation"] = correlation
        result = result.dropna().reset_index(drop=True)
        return result[["date", "btc_price", "nasdaq_price", "correlation"]].sort_values("date").reset_index(drop=True)
    except Exception as exc:
        print(f"Failed to calculate BTC/Nasdaq correlation: {exc}")
        return empty_df


def get_mvrv_zscore(years: int = 5) -> pd.DataFrame:
    """Return a BTC-backed placeholder MVRV dataset until on-chain sources are added."""
    start_date = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
    df = get_btc(start_date, datetime.now().strftime("%Y-%m-%d"))
    if df.empty:
        return pd.DataFrame(columns=["date", "price", "mvrv_zscore"])
    result = df.copy()
    rolling_mean = result["price"].rolling(365, min_periods=30).mean()
    rolling_std = result["price"].rolling(365, min_periods=30).std()
    result["mvrv_zscore"] = ((result["price"] - rolling_mean) / rolling_std).fillna(0)
    return result[["date", "price", "mvrv_zscore"]]
