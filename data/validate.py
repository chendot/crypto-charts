"""Source: local cache validator; dataset: registered parquet datasets; update frequency: every cache read."""

from __future__ import annotations

import pandas as pd


def check(df: pd.DataFrame, dataset_key: str) -> dict:
    """Return validation metadata and data-quality issues for a dataset."""
    issues: list[str] = []
    result = {"dataset": dataset_key, "rows": int(len(df)), "issues": issues}
    if "timestamp" not in df.columns:
        issues.append('missing "timestamp" column')
        return result

    timestamps = pd.to_datetime(df["timestamp"], errors="coerce")
    if timestamps.dt.tz is not None:
        timestamps = timestamps.dt.tz_convert(None)
    timestamps = timestamps.dropna().sort_values()
    if not timestamps.empty:
        ordered = list(timestamps)
        median_gap = timestamps.diff().dropna().median()
        if pd.isna(median_gap) or median_gap <= pd.Timedelta(0):
            threshold = pd.Timedelta(days=3)
        else:
            threshold = max(pd.Timedelta(days=3), median_gap * 5)
        for previous, current in zip(ordered, ordered[1:]):
            if current - previous > threshold:
                issues.append(f"time gap >{threshold}: {previous.date()} to {current.date()}")

        today = pd.Timestamp.now("UTC").tz_convert(None).normalize()
        last = timestamps.max().normalize()
        lag = int((today - last).days)
        if lag > 2:
            issues.append(f"stale: last={last.date()}, lag={lag}d")

    numeric_df = df.select_dtypes(include="number")
    for column in numeric_df.columns:
        series = pd.to_numeric(numeric_df[column], errors="coerce").dropna()
        if len(series) < 2:
            continue
        std = series.std(ddof=0)
        if std == 0 or pd.isna(std):
            continue
        count = int(((series - series.mean()).abs() / std > 5).sum())
        if count:
            issues.append(f"z-score >5: {column} count={count}")

    for column in df.columns:
        pct = float(df[column].isna().mean()) if len(df) else 0.0
        if pct > 0.2:
            issues.append(f"nan >20%: {column} pct={pct:.1%}")

    return result
