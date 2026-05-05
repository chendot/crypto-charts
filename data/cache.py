"""Cache primitives for normalized DataFrame datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = PROJECT_ROOT / "data" / "cache"


class DataFrameCache:
    """Read and write normalized DataFrames using local parquet files."""

    def __init__(self, root: Path = CACHE_ROOT, file_format: str = "parquet") -> None:
        """Initialize a local cache rooted under the project data directory."""
        self.root = root
        self.file_format = file_format

    def path_for(self, dataset_id: str) -> Path:
        """Return the cache file path for a dataset id."""
        suffix = ".parquet" if self.file_format == "parquet" else ".csv"
        return self.root / f"{dataset_id}{suffix}"

    def read(self, dataset_id: str) -> pd.DataFrame:
        """Read a cached dataset as a normalized DataFrame."""
        raise NotImplementedError("Cache reading will be implemented with the first real fetcher.")

    def write(self, dataset_id: str, df: pd.DataFrame) -> Path:
        """Write a normalized DataFrame and return the cache path."""
        raise NotImplementedError("Cache writing will be implemented with the first real fetcher.")
