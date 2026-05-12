"""Source: CoinGecko API; dataset: crypto market categories; update frequency: daily."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import requests

from data.fetchers.base import BaseFetcher
from data.fetchers.coingecko_categories import COINGECKO_CATEGORIES_URL, REQUEST_HEADERS


class CoinGeckoFetcher(BaseFetcher):
    """Fetch daily CoinGecko category market snapshots."""

    source_id = "market"
    dataset_id = "categories"

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        """Fetch today's category snapshot and return it when it falls in range."""
        snapshot_date = pd.Timestamp.now("UTC").tz_convert(None).normalize()
        if snapshot_date < pd.Timestamp(start) or snapshot_date > pd.Timestamp(end):
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "id",
                    "name",
                    "market_cap",
                    "volume_24h",
                    "market_cap_change_24h",
                    "top_3_coins",
                ]
            )
        response = requests.get(
            COINGECKO_CATEGORIES_URL,
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        rows = []
        for item in payload if isinstance(payload, list) else []:
            rows.append(
                {
                    "timestamp": snapshot_date,
                    "id": str(item.get("id", "")),
                    "name": str(item.get("name", "")),
                    "market_cap": pd.to_numeric(item.get("market_cap"), errors="coerce"),
                    "volume_24h": pd.to_numeric(item.get("volume_24h"), errors="coerce"),
                    "market_cap_change_24h": pd.to_numeric(item.get("market_cap_change_24h"), errors="coerce"),
                    "top_3_coins": ",".join(str(coin) for coin in item.get("top_3_coins", [])[:3]),
                }
            )
        return pd.DataFrame(
            rows,
            columns=["timestamp", "id", "name", "market_cap", "volume_24h", "market_cap_change_24h", "top_3_coins"],
        ).sort_values(["timestamp", "market_cap"], ascending=[True, False]).reset_index(drop=True)

    def fetch_latest(self) -> pd.DataFrame:
        """Fetch today's market category snapshot."""
        end = date.today()
        start = end - timedelta(days=7)
        return self.fetch_range(start.isoformat(), end.isoformat())
