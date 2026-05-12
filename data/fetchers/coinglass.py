"""Source: CoinGlass API; dataset: BTC funding rates; update frequency: 8-hour snapshots."""

from __future__ import annotations

from datetime import date, timedelta
import os
import time

import pandas as pd
import requests

from data.fetchers.base import BaseFetcher


class CoinGlassFetcher(BaseFetcher):
    """Fetch BTC funding and open-interest data from CoinGlass."""

    source_id = "derivatives"
    dataset_id = "funding_rates"

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        """Fetch BTC 8-hour funding observations."""
        api_key = os.environ.get("COINGLASS_API_KEY")
        if not api_key:
            raise EnvironmentError("COINGLASS_API_KEY")

        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        limit = max(1, min(4500, int(((end_ts - start_ts).days + 1) * 3)))
        response = requests.get(
            "https://open-api.coinglass.com/public/v2/funding",
            params={"symbol": "BTC", "time_type": "h8", "limit": limit},
            headers={"coinglassSecret": api_key, "accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        time.sleep(0.5)
        payload = response.json()
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        if isinstance(data, dict):
            data = data.get("data", data.get("list", data.get("items", [])))

        rows = []
        for item in data or []:
            timestamp_value = item.get("time") or item.get("timestamp") or item.get("t")
            rows.append(
                {
                    "timestamp": pd.to_datetime(timestamp_value, unit="ms", utc=True, errors="coerce"),
                    "symbol": str(item.get("symbol", "BTC")),
                    "funding_rate": pd.to_numeric(item.get("fundingRate") or item.get("funding_rate") or item.get("rate"), errors="coerce"),
                    "open_interest_usd": pd.to_numeric(item.get("openInterest") or item.get("open_interest_usd") or item.get("oiUsd"), errors="coerce"),
                }
            )
        df = pd.DataFrame(rows, columns=["timestamp", "symbol", "funding_rate", "open_interest_usd"])
        if df.empty:
            return df
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(None).dt.normalize()
        return df[(df["timestamp"] >= start_ts) & (df["timestamp"] <= end_ts)].sort_values("timestamp").reset_index(drop=True)

    def fetch_latest(self) -> pd.DataFrame:
        """Fetch the latest roughly seven days of derivatives data."""
        end = date.today()
        start = end - timedelta(days=7)
        return self.fetch_range(start.isoformat(), end.isoformat())
