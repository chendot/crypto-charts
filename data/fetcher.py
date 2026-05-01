"""Data fetchers for CoinGecko market history and DeFiLlama TVL."""

from __future__ import annotations

import requests
import pandas as pd


REQUEST_TIMEOUT = 15
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
DEFILLAMA_BASE_URL = "https://api.llama.fi"


def get_price_history(coin_id: str, days: int) -> pd.DataFrame:
    """Fetch historical coin prices and volumes from CoinGecko."""
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

