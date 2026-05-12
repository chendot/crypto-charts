"""Source: DefiLlama API; dataset: protocol revenue and chain TVL; update frequency: daily."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import requests

from data.fetchers.base import BaseFetcher


class DefiLlamaFetcher(BaseFetcher):
    """Fetch DefiLlama revenue snapshots or historical chain TVL."""

    source_id = "defi"

    def __init__(self, dataset: str = "protocol_revenue") -> None:
        """Set the target DefiLlama dataset."""
        self.dataset_id = dataset

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        """Fetch the configured DefiLlama dataset and filter to the requested range."""
        if self.dataset_id == "tvl":
            return self._fetch_tvl(start, end)
        return self._fetch_protocol_revenue(start, end)

    def fetch_latest(self) -> pd.DataFrame:
        """Fetch the latest roughly seven days of DefiLlama data."""
        end = date.today()
        start = end - timedelta(days=7)
        return self.fetch_range(start.isoformat(), end.isoformat())

    def _fetch_protocol_revenue(self, start: str, end: str) -> pd.DataFrame:
        response = requests.get("https://api.llama.fi/overview/fees", params={"excludeTotalDataChart": "false"}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        protocols = payload.get("protocols", []) if isinstance(payload, dict) else []
        snapshot_date = pd.Timestamp.now("UTC").tz_convert(None).normalize()
        rows = []
        for item in protocols:
            protocol = item.get("displayName") or item.get("name") or item.get("module")
            revenue = item.get("dailyRevenue") or item.get("dailyFees") or item.get("revenue24h")
            if protocol is None:
                continue
            rows.append(
                {
                    "timestamp": snapshot_date,
                    "protocol": str(protocol),
                    "daily_revenue_usd": pd.to_numeric(revenue, errors="coerce"),
                }
            )
        df = pd.DataFrame(rows, columns=["timestamp", "protocol", "daily_revenue_usd"])
        return _filter_range(df, start, end)

    def _fetch_tvl(self, start: str, end: str) -> pd.DataFrame:
        response = requests.get("https://api.llama.fi/v2/historicalChainTvl", timeout=30)
        response.raise_for_status()
        payload = response.json()
        rows = []
        if isinstance(payload, list):
            if payload and "date" in payload[0]:
                for point in payload:
                    rows.append(
                        {
                            "timestamp": pd.to_datetime(point.get("date"), unit="s", utc=True, errors="coerce"),
                            "chain": "all",
                            "tvl_usd": pd.to_numeric(point.get("tvl") or point.get("totalLiquidityUSD"), errors="coerce"),
                        }
                    )
            else:
                for chain_item in payload:
                    chain = chain_item.get("name") or chain_item.get("chain")
                    for point in chain_item.get("tvl", []):
                        rows.append(
                            {
                                "timestamp": pd.to_datetime(point.get("date"), unit="s", utc=True, errors="coerce"),
                                "chain": str(chain),
                                "tvl_usd": pd.to_numeric(point.get("totalLiquidityUSD") or point.get("tvl"), errors="coerce"),
                            }
                        )
        df = pd.DataFrame(rows, columns=["timestamp", "chain", "tvl_usd"])
        return _filter_range(df, start, end)


def _filter_range(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Normalize timestamps and filter a DataFrame to inclusive dates."""
    if df.empty:
        return df
    output_df = df.copy()
    output_df["timestamp"] = pd.to_datetime(output_df["timestamp"], utc=True).dt.tz_convert(None).dt.normalize()
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    return output_df[(output_df["timestamp"] >= start_ts) & (output_df["timestamp"] <= end_ts)].sort_values("timestamp").reset_index(drop=True)
