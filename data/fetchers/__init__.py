"""Source: fetcher registry; dataset: template fetcher entrypoints; update frequency: per template run."""

from __future__ import annotations

from data.fetchers.etf_flows import get_etf_flows
from data.fetchers.funding_rates import get_funding_rate_extremes
from data.fetchers.halving_cycles import get_halving_cycles
from data.fetchers.narrative_rotation import get_narrative_rotation
from data.fetchers.real_yields import get_real_yields
from data.fetchers.stablecoin_flows import get_stablecoin_flows
from data.fetchers.top_buyer import get_top_buyer_drawdowns


FETCHERS = {
    "t1": get_etf_flows,
    "t2": get_halving_cycles,
    "t3": get_top_buyer_drawdowns,
    "t4": get_real_yields,
    "t5": get_funding_rate_extremes,
    "t6": get_narrative_rotation,
    "t7": get_stablecoin_flows,
}
