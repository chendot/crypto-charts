"""Fixtures for stablecoin DeFi ratio fetcher tests."""

from __future__ import annotations

import calendar
from datetime import datetime, timezone


def unix_timestamp(year: int, month: int, day: int) -> int:
    """Return a UTC unix timestamp for a fixture date."""
    return calendar.timegm(datetime(year, month, day, tzinfo=timezone.utc).timetuple())


PROTOCOLS_PAYLOAD = [
    {"slug": "rwa-vault", "name": "RWA Vault", "category": "RWA", "tvl": 5_000_000, "stablecoins": ["rwa-usd"]},
    {"slug": "basis-desk", "name": "Basis Desk", "category": "Basis Trading", "tvl": 4_000_000, "stablecoins": ["basis-usd"]},
    {"slug": "lend-core", "name": "Lend Core", "category": "Lending", "tvl": 8_000_000},
    {"slug": "cdp-core", "name": "CDP Core", "category": "CDP", "tvl": 3_000_000},
    {"slug": "swap-core", "name": "Swap Core", "category": "Dexs", "tvl": 6_000_000},
    {"slug": "bridge-core", "name": "Bridge Core", "category": "Bridge", "tvl": 2_000_000},
    {"slug": "yield-box", "name": "Yield Box", "category": "Yield", "tvl": 2_500_000},
    {"slug": "too-small", "name": "Too Small", "category": "RWA", "tvl": 999_999},
]


PROTOCOL_PAYLOADS = {
    "rwa-vault": {
        "tokensInUsd": [
            {"date": unix_timestamp(2022, 1, 15), "tokens": {"USDC": 1_000_000, "ETH": 500_000}},
            {"date": unix_timestamp(2022, 2, 15), "tokens": {"USDT": 1_500_000, "DAI": 500_000}},
            {"date": unix_timestamp(2023, 1, 15), "tokens": {"USDM": 3_000_000}},
        ]
    },
    "basis-desk": {
        "tokensInUsd": [
            {"date": unix_timestamp(2022, 1, 15), "tokens": {"USDE": 500_000}},
            {"date": unix_timestamp(2022, 2, 15), "tokens": {"USDE": 1_000_000}},
            {"date": unix_timestamp(2023, 1, 15), "tokens": {"FDUSD": 2_000_000}},
        ]
    },
    "lend-core": {
        "tokensInUsd": [
            {"date": unix_timestamp(2022, 1, 15), "tokens": {"USDC": 2_000_000}},
            {"date": unix_timestamp(2022, 2, 15), "tokens": {"USDT": 2_500_000}},
            {"date": unix_timestamp(2023, 1, 15), "tokens": {"DAI": 4_000_000}},
        ]
    },
    "cdp-core": {
        "tokensInUsd": [
            {"date": unix_timestamp(2022, 1, 15), "tokens": {"FRAX": 500_000}},
            {"date": unix_timestamp(2022, 2, 15), "tokens": {"LUSD": 600_000}},
            {"date": unix_timestamp(2023, 1, 15), "tokens": {"crvUSD": 1_000_000}},
        ]
    },
    "swap-core": {
        "tokensInUsd": [
            {"date": unix_timestamp(2022, 1, 15), "tokens": {"USDC": 1_000_000}},
            {"date": unix_timestamp(2022, 2, 15), "tokens": {"USDC": 1_200_000}},
            {"date": unix_timestamp(2023, 1, 15), "tokens": {"USDT": 2_000_000}},
        ]
    },
    "bridge-core": {
        "tokensInUsd": [
            {"date": unix_timestamp(2022, 1, 15), "tokens": {"USDP": 300_000}},
            {"date": unix_timestamp(2022, 2, 15), "tokens": {"PYUSD": 500_000}},
            {"date": unix_timestamp(2023, 1, 15), "tokens": {"GUSD": 1_000_000}},
        ]
    },
    "yield-box": {
        "tokensInUsd": [
            {"date": unix_timestamp(2022, 1, 15), "tokens": {"MIM": 700_000}},
            {"date": unix_timestamp(2022, 2, 15), "tokens": {"sUSD": 800_000}},
            {"date": unix_timestamp(2023, 1, 15), "tokens": {"alUSD": 1_200_000}},
        ]
    },
}


TOTAL_SUPPLY_PAYLOAD = [
    {"date": unix_timestamp(2022, 1, 31), "totalCirculatingUSD": {"peggedUSD": 100_000_000}},
    {"date": unix_timestamp(2022, 2, 28), "totalCirculatingUSD": {"peggedUSD": 120_000_000}},
    {"date": unix_timestamp(2023, 1, 31), "totalCirculatingUSD": {"peggedUSD": 150_000_000}},
]
