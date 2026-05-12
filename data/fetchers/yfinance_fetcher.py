"""Source: Yahoo Finance via yfinance; dataset: multi-asset daily prices; update frequency: daily."""

from __future__ import annotations

from datetime import date, timedelta
import time

import pandas as pd
import yfinance as yf

from data.exceptions import DataFetchError
from data.fetchers.base import BaseFetcher


class MultiAssetPriceFetcher(BaseFetcher):
    """Fetch BTC, SPY, GLD, and DXY daily adjusted closes."""

    source_id = "prices"
    dataset_id = "multi_asset"
    TICKERS = {"BTC-USD": "btc", "SPY": "spy", "GLD": "gld", "DX-Y.NYB": "dxy"}

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        """Fetch daily adjusted closes and normalize the date index."""
        yf_end = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        series_by_column = {}
        failures = []
        for ticker, column in self.TICKERS.items():
            ticker_df = _download_with_retry(ticker, start, yf_end)
            if ticker_df.empty:
                failures.append(ticker)
                continue
            close_series = _extract_close(ticker_df, ticker)
            if close_series is None or close_series.dropna().empty:
                failures.append(ticker)
                continue
            series_by_column[column] = close_series.rename(column)

        if not series_by_column:
            raise DataFetchError(f"Yahoo Finance returned no rows for {start} to {end}: {', '.join(failures)}")

        output_df = pd.concat(series_by_column.values(), axis=1).reset_index()
        date_column = output_df.columns[0]
        output_df = output_df.rename(columns={date_column: "timestamp"})
        for column in self.TICKERS.values():
            if column not in output_df.columns:
                output_df[column] = pd.NA
            output_df[column] = pd.to_numeric(output_df[column], errors="coerce")
        if output_df[list(self.TICKERS.values())].dropna(how="all").empty:
            raise DataFetchError(f"Yahoo Finance returned no usable price columns for {start} to {end}")
        output_df["timestamp"] = pd.to_datetime(output_df["timestamp"], utc=True).dt.tz_convert(None).dt.normalize()
        return output_df[["timestamp", "btc", "spy", "gld", "dxy"]].sort_values("timestamp").reset_index(drop=True)

    def fetch_latest(self) -> pd.DataFrame:
        """Fetch the latest roughly seven days of prices."""
        end = date.today()
        start = end - timedelta(days=7)
        return self.fetch_range(start.isoformat(), end.isoformat())


def _download_with_retry(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download one ticker with a small exponential backoff."""
    for attempt in range(3):
        df = yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            group_by="column",
            threads=False,
        )
        if not df.empty:
            return df
        if attempt < 2:
            time.sleep(2**attempt)
    return pd.DataFrame()


def _extract_close(df: pd.DataFrame, ticker: str) -> pd.Series | None:
    """Return a close-price series from yfinance output."""
    if isinstance(df.columns, pd.MultiIndex):
        if "Close" in df.columns.get_level_values(0):
            close_df = df["Close"]
            if isinstance(close_df, pd.DataFrame):
                return close_df[ticker] if ticker in close_df.columns else close_df.iloc[:, 0]
            return close_df
        if "Close" in df.columns.get_level_values(-1):
            close_df = df.xs("Close", axis=1, level=-1)
            if isinstance(close_df, pd.DataFrame):
                return close_df[ticker] if ticker in close_df.columns else close_df.iloc[:, 0]
            return close_df
        return None
    if "Close" not in df.columns:
        return None
    return df["Close"]
