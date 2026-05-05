"""Standard DataFrame schema declarations for chart data contracts."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from data.exceptions import DataSchemaError


@dataclass(frozen=True)
class DataFrameSchema:
    """A minimal schema contract for normalized DataFrame outputs."""

    name: str
    columns: tuple[str, ...]

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return df when required columns exist, otherwise raise DataSchemaError."""
        missing = [column for column in self.columns if column not in df.columns]
        if missing:
            raise DataSchemaError(f"{self.name} missing required columns: {missing}")
        return df


ETF_FLOW_SCHEMA = DataFrameSchema(
    name="etf_flow",
    columns=("date", "entity", "asset", "flow_usd", "aum_usd", "source"),
)
HALVING_CYCLE_SCHEMA = DataFrameSchema(
    name="halving_cycle",
    columns=("date", "cycle", "days_from_halving", "price_usd", "normalized_price"),
)
TOP_BUYER_DRAWDOWN_SCHEMA = DataFrameSchema(
    name="top_buyer_drawdown",
    columns=("date", "cycle", "entry_date", "price_usd", "drawdown_pct", "days_since_entry"),
)
REAL_YIELD_SCHEMA = DataFrameSchema(
    name="real_yield",
    columns=("date", "protocol", "chain", "category", "nominal_apy", "inflation_apy", "real_apy", "tvl_usd"),
)
FUNDING_EXTREME_SCHEMA = DataFrameSchema(
    name="funding_extreme",
    columns=("date", "asset", "exchange", "funding_rate", "forward_window_days", "forward_return_pct"),
)
NARRATIVE_ROTATION_SCHEMA = DataFrameSchema(
    name="narrative_rotation",
    columns=("date", "sector", "rank", "score", "return_pct"),
)
STABLECOIN_FLOW_SCHEMA = DataFrameSchema(
    name="stablecoin_flow",
    columns=("date", "source_chain", "target_chain", "asset", "flow_usd", "source"),
)


TEMPLATE_SCHEMAS = {
    "t1": ETF_FLOW_SCHEMA,
    "t2": HALVING_CYCLE_SCHEMA,
    "t3": TOP_BUYER_DRAWDOWN_SCHEMA,
    "t4": REAL_YIELD_SCHEMA,
    "t5": FUNDING_EXTREME_SCHEMA,
    "t6": NARRATIVE_ROTATION_SCHEMA,
    "t7": STABLECOIN_FLOW_SCHEMA,
}
