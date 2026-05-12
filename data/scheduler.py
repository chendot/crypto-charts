"""Source: scheduler CLI; dataset: registered parquet datasets; update frequency: manual or daily."""

from __future__ import annotations

import argparse
from datetime import date

import pandas as pd

from data.registry import _fetchers, get


def main(argv: list[str] | None = None) -> int:
    """Run the data scheduler CLI."""
    parser = argparse.ArgumentParser(description="Manage crypto-charts data caches")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backfill_parser = subparsers.add_parser("backfill")
    backfill_parser.add_argument("--dataset", choices=sorted(_fetchers))
    subparsers.add_parser("update")
    subparsers.add_parser("status")

    args = parser.parse_args(argv)
    if args.command == "backfill":
        keys = [args.dataset] if args.dataset else list(_fetchers)
        _run_many(keys, mode="backfill")
        get.cache_clear()
    elif args.command == "update":
        _run_many(list(_fetchers), mode="update")
        get.cache_clear()
    elif args.command == "status":
        _print_status()
    return 0


def _run_many(keys: list[str], mode: str) -> None:
    """Run backfill or update for each dataset and continue after errors."""
    for key in keys:
        fetcher = _fetchers[key]
        try:
            if mode == "backfill":
                fetcher.backfill()
            else:
                fetcher.update()
        except Exception as exc:
            print(f"✗ {key}: {exc}")
        else:
            print(f"✓ {key}")


def _print_status() -> None:
    """Print cache status without calling external APIs."""
    today = pd.Timestamp(date.today()).normalize()
    for key, fetcher in _fetchers.items():
        try:
            df = fetcher.load_cache()
            if df is None or df.empty or "timestamp" not in df.columns:
                print(f"{key}: rows=0 min=None max=None lag=None")
                continue
            timestamps = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
            min_ts = timestamps.min().date()
            max_ts_value = timestamps.max()
            max_ts = max_ts_value.date()
            lag = int((today - max_ts_value.normalize()).days)
            print(f"{key}: rows={len(df)} min={min_ts} max={max_ts} lag={lag}d")
        except Exception as exc:
            print(f"{key}: error={exc}")


if __name__ == "__main__":
    raise SystemExit(main())
