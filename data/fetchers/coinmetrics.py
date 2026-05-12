"""Source: Coin Metrics Community API; dataset: BTC on-chain metrics; update frequency: daily."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import requests

from data.fetchers.base import BaseFetcher


class CoinMetricsFetcher(BaseFetcher):
    """Fetch BTC community asset metrics from Coin Metrics."""

    source_id = "onchain"
    dataset_id = "coinmetrics_btc"
    BASE_URL = "https://community-api.coinmetrics.io/v4"
    METRICS = ["PriceUSD", "CapMVRVCur", "IssTotUSD", "HashRate", "AdrActCnt"]

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        """Fetch and paginate Coin Metrics BTC asset metrics."""
        rows: list[dict] = []
        params = {
            "assets": "btc",
            "metrics": ",".join(self.METRICS),
            "start_time": start,
            "end_time": end,
            "page_size": 10000,
        }
        while True:
            response = requests.get(f"{self.BASE_URL}/timeseries/asset-metrics", params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            rows.extend(payload.get("data", []))
            token = payload.get("next_page_token")
            if not token:
                break
            params = {"next_page_token": token}

        output_rows = []
        for row in rows:
            normalized = {"timestamp": row.get("time")}
            for metric in self.METRICS:
                normalized[metric] = pd.to_numeric(row.get(metric), errors="coerce")
            output_rows.append(normalized)

        df = pd.DataFrame(output_rows, columns=["timestamp", *self.METRICS])
        if df.empty:
            return df
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(None).dt.normalize()
        return df.sort_values("timestamp").reset_index(drop=True)

    def fetch_latest(self) -> pd.DataFrame:
        """Fetch the latest roughly seven days of on-chain metrics."""
        end = date.today()
        start = end - timedelta(days=7)
        return self.fetch_range(start.isoformat(), end.isoformat())
