"""Source: local parquet registry; dataset: registered chart datasets; update frequency: daily."""

from __future__ import annotations

from functools import lru_cache
import warnings

import pandas as pd

from data import validate
from data.fetchers.base import BaseFetcher
from data.fetchers.coingecko import CoinGeckoFetcher
from data.fetchers.coinglass import CoinGlassFetcher
from data.fetchers.coinmetrics import CoinMetricsFetcher
from data.fetchers.defillama import DefiLlamaFetcher
from data.fetchers.yfinance_fetcher import MultiAssetPriceFetcher


class DataNotReadyError(FileNotFoundError):
    """Raised when a registered cache has not been materialized yet."""


_fetchers: dict[str, BaseFetcher] = {
    "prices.multi_asset": MultiAssetPriceFetcher(),
    "onchain.coinmetrics_btc": CoinMetricsFetcher(),
    "defi.protocol_revenue": DefiLlamaFetcher(dataset="protocol_revenue"),
    "defi.tvl": DefiLlamaFetcher(dataset="tvl"),
    "derivatives.funding_rates": CoinGlassFetcher(),
    "market.categories": CoinGeckoFetcher(),
}


def get(dataset_key: str) -> pd.DataFrame:
    """Load a cached dataset by key, validating before returning."""
    return _get_cached(dataset_key).copy()


@lru_cache(maxsize=64)
def _get_cached(dataset_key: str) -> pd.DataFrame:
    """Load and cache a validated dataset by key."""
    if dataset_key not in _fetchers:
        raise KeyError(f"Unknown dataset: {dataset_key}")
    df = _fetchers[dataset_key].load_cache()
    if df is None:
        raise DataNotReadyError(
            f"Cache empty for '{dataset_key}'. Run: python -m data.scheduler backfill --dataset {dataset_key}"
        )

    report = validate.check(df, dataset_key)
    for issue in report["issues"]:
        warnings.warn(f"{dataset_key}: {issue}", RuntimeWarning, stacklevel=2)
    return df


get.cache_clear = _get_cached.cache_clear
get.cache_info = _get_cached.cache_info


def list_datasets() -> list[str]:
    """Return registered dataset keys."""
    return list(_fetchers.keys())
