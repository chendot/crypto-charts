# Crypto Charts Project Spec

This project is a long-running production framework for high-quality crypto data charts published to X.
The framework supports seven recurring templates while preserving the existing dark Matplotlib visual system.

## Architecture

The project is split into three one-way layers:

- `data/`: fetches remote or static data, normalizes raw responses, validates DataFrame schemas, and manages local cache files.
- `components/`: reusable visual primitives such as canvases, lines, bars, annotations, legends, tables, and future Sankey/bump-chart helpers.
- `templates/`: chart-specific orchestration. Templates call `data` and `components`, format template copy from `config/templates.py`, and save PNG outputs.

Dependency direction is strict:

- `templates` may import `components`, `data`, and `config`.
- `components` may import `config/theme.py`.
- `data` may import standard libraries, third-party data libraries, and data-layer helpers.
- `components` must not import `data`.
- `data` must not import `components` or `templates`.

## Template Contract

Every template module under `templates/` exposes:

```python
def render(as_of: date | str | None = None, variant: str | None = None) -> Path:
    """Render a chart through the requested cutoff date and return the PNG path."""
```

Templates may add keyword-only optional context fields when a chart needs manual editorial input.
T1 supports `insight_text: str | None = None` for a human-written one-sentence annotation.
The registry helper forwards this parameter while keeping older `render(as_of, variant)` calls valid.

- `as_of` supports historical backfills and should be interpreted as an inclusive cutoff date.
- `variant` is optional and only used by templates with multiple variants, currently expected for T3.
- Output filenames must follow `{YYYY-MM-DD}_{template_id}_{optional_variant}.png`.
- Use `templates.common.output_filename()` for the filename convention.
- Template copy, frequency, dimensions, source labels, variants, and data dependencies live in `config/templates.py`.

## Data Contract

All data-layer public fetchers return normalized `pandas.DataFrame` objects.
Templates must not parse raw API responses directly.

Standard columns:

- `date`: timezone-naive daily or period timestamp used as the primary chart cutoff dimension.
- `asset`: ticker, token, or stablecoin symbol when the dataset contains multiple assets.
- `entity`: issuer, fund, protocol, venue, or other business entity.
- `ticker`: ETF ticker or market symbol when distinct from the human-readable entity.
- `chain`: blockchain name when rows are chain-specific.
- `source_chain` / `target_chain`: origin and destination chains for cross-chain flows.
- `source`: human-readable source label used for attribution.
- `flow_usd`: signed USD flow amount; positive means inflow to the target entity or chain.
- `aum_usd`: assets under management in USD.
- `price_usd`: spot price in USD.
- `normalized_price`: indexed price series, usually rebased to 100.
- `drawdown_pct`: percent drawdown from the selected entry or peak.
- `nominal_apy`, `inflation_apy`, `real_apy`: yield fields as decimal percentages, not fractions.
- `tvl_usd`: protocol or pool TVL in USD.
- `funding_rate`: funding rate as decimal percentage.
- `forward_window_days`: return horizon after a signal event.
- `forward_return_pct`: forward return as decimal percentage.
- `sector`: narrative or sector name.
- `rank`: integer rank where 1 is best or largest.
- `score`: normalized score used to rank sectors.
- `return_pct`: period return as decimal percentage.

Template-specific schema declarations live in `data/schemas.py`.

## Cache Contract

Fetchers must support local caching to avoid repeated API calls.
The preferred cache format for new datasets is local parquet under `data/cache/` because it preserves typed columns and is compact.
CSV is acceptable for debugging or source files that are naturally CSV.

Fetcher flow:

1. Resolve cache key from dataset id, cutoff date, and any variant/source parameters.
2. Read a fresh cache when available.
3. Fetch only missing or stale ranges when possible.
4. Normalize raw payloads into the public schema.
5. Validate with `data.schemas.DataFrameSchema`.
6. Write the normalized DataFrame back to cache.
7. Return only normalized columns to the template.

Data-layer exceptions live in `data/exceptions.py`.

## Visual Contract

All visual constants must come from `config/theme.py`.
Components and templates must not hardcode colors, font sizes, canvas dimensions, grid widths, or common layout coordinates.
If a new recurring visual primitive needs a new constant, add it to `config/theme.py` first.

Existing components remain the base visual grammar:

- `BaseChart`: figure creation, titles, source text, watermark, saving.
- `PriceLine`: themed price lines and extrema annotations.
- `VolumeBar`: themed volume bars.
- `Annotations`: callouts, event lines, percentage labels.

Future reusable visuals such as rank lines, Sankey nodes, and yield tables should be added under `components/`.

## Template Inventory

- T1: BTC spot ETF flow structure chart, weekly Monday.
- T2: BTC halving cycle normalized comparison, monthly start.
- T3: Historical top-buyer drawdown comparison series, monthly middle, multiple variants.
- T4: LP and staking real-yield ranking, weekly Friday.
- T5: Funding-rate extreme forward-return distribution, bimonthly month end.
- T6: Narrative sector rotation bump chart, weekly Wednesday.
- T7: Cross-chain stablecoin flow Sankey, bimonthly month end.

## CLI

Render one template with:

```bash
python scripts/render_one.py t1 --as-of 2026-05-04
```

While the scaffold is incomplete, placeholder templates raise `NotImplementedError`.

## Tests

The test suite uses `pytest`.
Current scaffold tests verify the template registry, render signatures, fetcher registry, and schema declarations.
As each template is implemented, replace placeholder expectations with fixture-backed tests that run without network access.
