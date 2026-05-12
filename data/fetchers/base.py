"""Source: local parquet cache; dataset: base fetcher contract; update frequency: daily."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path

import pandas as pd


CACHE_ROOT = Path(__file__).parent.parent / "cache"


class BaseFetcher(ABC):
    """Abstract fetcher with append-only parquet caching."""

    source_id: str
    dataset_id: str

    @abstractmethod
    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        """Fetch a date range and return rows with a normalized timestamp column."""

    @abstractmethod
    def fetch_latest(self) -> pd.DataFrame:
        """Fetch the latest roughly seven days of data."""

    @property
    def cache_path(self) -> Path:
        """Return the parquet cache path for this dataset."""
        # FINAL — do not override
        path = CACHE_ROOT / self.source_id / f"{self.dataset_id}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def load_cache(self) -> pd.DataFrame | None:
        """Return the cached DataFrame, or None when absent."""
        # FINAL — do not override
        if not self.cache_path.exists():
            return None
        df = pd.read_parquet(self.cache_path)
        if "timestamp" in df.columns:
            df["timestamp"] = _normalize_timestamp(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def append(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """Append rows idempotently and persist parquet."""
        # FINAL — do not override
        clean_new_df = _clean_for_cache(new_df)
        existing_df = self.load_cache()
        if existing_df is None or existing_df.empty:
            merged_df = clean_new_df
        elif clean_new_df.empty:
            merged_df = existing_df
        else:
            merged_df = pd.concat([existing_df, clean_new_df], ignore_index=True)

        if "timestamp" not in merged_df.columns:
            raise ValueError("DataFrame must contain a 'timestamp' column")

        merged_df["timestamp"] = _normalize_timestamp(merged_df["timestamp"])
        merged_df = (
            merged_df.dropna(subset=["timestamp"])
            .drop_duplicates(subset=["timestamp"], keep="last")
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        merged_df.to_parquet(self.cache_path, index=False)
        return merged_df

    def backfill(self, start: str = "2020-01-01") -> pd.DataFrame:
        """Fetch all rows from start through today."""
        # FINAL — do not override
        today = date.today().isoformat()
        df = self.fetch_range(start, today)
        clean_df = _clean_for_cache(df)
        clean_df.to_parquet(self.cache_path, index=False)
        return clean_df

    def update(self) -> pd.DataFrame:
        """Refresh cache from the latest cached date."""
        # FINAL — do not override
        cached_df = self.load_cache()
        if cached_df is None or cached_df.empty:
            return self.backfill()

        last_date = pd.to_datetime(cached_df["timestamp"].max()).strftime("%Y-%m-%d")
        today = date.today().isoformat()
        new_df = self.fetch_range(last_date, today)
        return self.append(new_df)


def _normalize_timestamp(values: object) -> pd.Series:
    """Return tz-naive UTC normalized timestamps."""
    timestamps = pd.to_datetime(values, utc=True, errors="coerce")
    return pd.Series(timestamps).dt.tz_convert(None).dt.normalize()


def _clean_for_cache(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize timestamp and reject nested object values before parquet writes."""
    output_df = df.copy()
    if "timestamp" not in output_df.columns:
        raise ValueError("DataFrame must contain a 'timestamp' column")
    output_df["timestamp"] = _normalize_timestamp(output_df["timestamp"])
    for column in output_df.columns:
        if column == "timestamp":
            continue
        if output_df[column].map(lambda value: isinstance(value, (dict, list, tuple, set))).any():
            raise ValueError(f"Column '{column}' contains nested objects")
    return output_df.sort_values("timestamp").reset_index(drop=True)
