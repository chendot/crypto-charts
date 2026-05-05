"""Central metadata registry for long-running crypto chart templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class TemplateText:
    """Title, subtitle, and source text templates for one chart template."""

    title: str
    subtitle: str
    source: str


@dataclass(frozen=True)
class TemplateConfig:
    """Operational metadata for a chart template."""

    template_id: str
    name: str
    frequency: str
    module: str
    default_size: tuple[int, int]
    data_dependencies: tuple[str, ...]
    variants: tuple[str, ...]
    text: TemplateText
    notes: str
    visual: Mapping[str, object] | None = None


TEMPLATES: Mapping[str, TemplateConfig] = {
    "t1": TemplateConfig(
        template_id="t1",
        name="BTC Spot ETF Flow Structure",
        frequency="weekly Monday",
        module="templates.t1_etf_flow",
        default_size=(1200, 675),
        data_dependencies=("farside_btc_etf_flows",),
        variants=(),
        text=TemplateText(
            title="{argument}",
            subtitle="BTC spot ETF fund flows, {start_date} to {end_date}",
            source="Source: Farside Investors",
        ),
        notes="Weekly five-trading-day BTC spot ETF flow structure chart.",
        visual={
            "featured_issuers": ("IBIT", "FBTC", "GBTC"),
            "issuer_colors": {
                "IBIT": "#4FC3F7",
                "FBTC": "#FFD166",
                "GBTC": "#EF5350",
                "Others": "#8899AA",
            },
        },
    ),
    "t2": TemplateConfig(
        template_id="t2",
        name="BTC Halving Cycle Normalized Comparison",
        frequency="TODO: monthly start",
        module="templates.t2_halving_cycles",
        default_size=(1200, 675),
        data_dependencies=("TODO: btc_price", "TODO: btc_halvings"),
        variants=(),
        text=TemplateText(
            title="TODO: BTC halving cycle title for {as_of}",
            subtitle="TODO: normalized cycle subtitle",
            source="TODO: source attribution",
        ),
        notes="TODO: define normalization window and cycle anchors.",
    ),
    "t3": TemplateConfig(
        template_id="t3",
        name="Historical Top Buyer Drawdown Comparison",
        frequency="TODO: monthly middle",
        module="templates.t3_top_buyer_drawdowns",
        default_size=(1200, 675),
        data_dependencies=("TODO: btc_price",),
        variants=("TODO: variant_a", "TODO: variant_b"),
        text=TemplateText(
            title="TODO: top buyer comparison title for {as_of}",
            subtitle="TODO: drawdown subtitle",
            source="TODO: source attribution",
        ),
        notes="TODO: define variants, peak windows, and holding-period metrics.",
    ),
    "t4": TemplateConfig(
        template_id="t4",
        name="LP and Staking Real Yield Ranking",
        frequency="TODO: weekly Friday",
        module="templates.t4_real_yield_ranking",
        default_size=(1200, 675),
        data_dependencies=("TODO: protocol_yields", "TODO: inflation"),
        variants=(),
        text=TemplateText(
            title="TODO: LP/staking real yield title for {as_of}",
            subtitle="TODO: real yield ranking subtitle",
            source="TODO: source attribution",
        ),
        notes="TODO: define protocol list and real-yield formula.",
    ),
    "t5": TemplateConfig(
        template_id="t5",
        name="Funding Rate Extremes Forward Return Distribution",
        frequency="TODO: bimonthly month end",
        module="templates.t5_funding_extremes",
        default_size=(1200, 675),
        data_dependencies=("TODO: funding_rates", "TODO: forward_returns"),
        variants=(),
        text=TemplateText(
            title="TODO: funding extremes title for {as_of}",
            subtitle="TODO: forward return distribution subtitle",
            source="TODO: source attribution",
        ),
        notes="TODO: define extreme threshold and forward return horizons.",
    ),
    "t6": TemplateConfig(
        template_id="t6",
        name="Narrative Sector Rotation Bump Chart",
        frequency="TODO: weekly Wednesday",
        module="templates.t6_narrative_rotation",
        default_size=(1200, 675),
        data_dependencies=("TODO: sector_returns",),
        variants=(),
        text=TemplateText(
            title="TODO: narrative rotation title for {as_of}",
            subtitle="TODO: sector rank subtitle",
            source="TODO: source attribution",
        ),
        notes="TODO: define narrative taxonomy and ranking metric.",
    ),
    "t7": TemplateConfig(
        template_id="t7",
        name="Cross-Chain Stablecoin Flow Sankey",
        frequency="TODO: bimonthly month end",
        module="templates.t7_stablecoin_sankey",
        default_size=(1200, 675),
        data_dependencies=("TODO: stablecoin_bridge_flows",),
        variants=(),
        text=TemplateText(
            title="TODO: stablecoin flow title for {as_of}",
            subtitle="TODO: cross-chain flow subtitle",
            source="TODO: source attribution",
        ),
        notes="TODO: define chains, bridges, and net-flow windows.",
    ),
}


def get_template_config(template_id: str) -> TemplateConfig:
    """Return the centralized configuration for a template id."""
    normalized_id = template_id.lower()
    if normalized_id not in TEMPLATES:
        raise KeyError(f"Unknown template id: {template_id}")
    return TEMPLATES[normalized_id]
