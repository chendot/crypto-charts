"""Fixtures for selected stablecoin category trend fetcher tests."""

from __future__ import annotations

import calendar
from datetime import datetime, timezone


def unix_timestamp(year: int, month: int, day: int) -> int:
    """Return a UTC unix timestamp for a fixture date."""
    return calendar.timegm(datetime(year, month, day, tzinfo=timezone.utc).timetuple())


def tvl_points(values: list[tuple[int, int, int, float]]) -> list[dict[str, float | int]]:
    """Return DefiLlama-like TVL points."""
    return [{"date": unix_timestamp(year, month, day), "totalLiquidityUSD": value} for year, month, day, value in values]


PROTOCOL_PAYLOADS = {
    "ondo-finance": {
        "tvl": tvl_points(
            [
                (2020, 1, 15, 0.0),
                (2020, 2, 15, 0.0),
                (2022, 12, 15, 20_000_000.0),
                (2023, 1, 15, 50_000_000.0),
                (2023, 2, 15, 75_000_000.0),
            ]
        )
    },
    "mountain-protocol": {
        "tvl": tvl_points(
            [
                (2020, 1, 15, 0.0),
                (2022, 12, 15, 5_000_000.0),
                (2023, 1, 15, 12_000_000.0),
                (2023, 2, 15, 18_000_000.0),
            ]
        )
    },
    "makerdao": {
        "tvl": tvl_points(
            [
                (2020, 1, 15, 100_000_000.0),
                (2022, 12, 15, 150_000_000.0),
                (2023, 1, 15, 180_000_000.0),
                (2023, 2, 15, 200_000_000.0),
            ]
        ),
        "tokensInUsd": [
            {"date": unix_timestamp(2020, 1, 15), "tokens": {"SDAI": 10_000_000.0, "USDC": 99_000_000.0}},
            {"date": unix_timestamp(2022, 12, 15), "tokens": {"USDY": 30_000_000.0, "DAI": 120_000_000.0}},
            {"date": unix_timestamp(2023, 1, 15), "tokens": {"SDAI": 35_000_000.0, "USDY": 15_000_000.0}},
            {"date": unix_timestamp(2023, 2, 15), "tokens": {"SDAI": 45_000_000.0, "USDY": 25_000_000.0}},
        ],
    },
    "ethena": {
        "tvl": tvl_points(
            [
                (2023, 1, 15, 25_000_000.0),
                (2023, 2, 15, 80_000_000.0),
            ]
        )
    },
    "aave-v3": {
        "tvl": tvl_points(
            [
                (2020, 1, 15, 50_000_000.0),
                (2020, 2, 15, 55_000_000.0),
                (2022, 12, 15, 250_000_000.0),
                (2023, 1, 15, 300_000_000.0),
                (2023, 2, 15, 325_000_000.0),
            ]
        )
    },
    "compound-finance": {
        "tvl": tvl_points(
            [
                (2020, 1, 15, 40_000_000.0),
                (2020, 2, 15, 44_000_000.0),
                (2022, 12, 15, 150_000_000.0),
                (2023, 1, 15, 160_000_000.0),
                (2023, 2, 15, 170_000_000.0),
            ]
        )
    },
}


TOTAL_SUPPLY_PAYLOAD = [
    {"date": unix_timestamp(2020, 1, 31), "totalCirculatingUSD": {"peggedUSD": 5_000_000_000.0}},
    {"date": unix_timestamp(2020, 2, 29), "totalCirculatingUSD": {"peggedUSD": 5_200_000_000.0}},
    {"date": unix_timestamp(2022, 12, 31), "totalCirculatingUSD": {"peggedUSD": 100_000_000_000.0}},
    {"date": unix_timestamp(2023, 1, 31), "totalCirculatingUSD": {"peggedUSD": 110_000_000_000.0}},
    {"date": unix_timestamp(2023, 2, 28), "totalCirculatingUSD": {"peggedUSD": 120_000_000_000.0}},
]
