# Crypto Charts

Dark, professional crypto data charts for publishing on X via `@koalada18`.

This repo is a Matplotlib-based chart production framework. It keeps visual rules,
data access, template metadata, and editorial strategy centralized so recurring
charts can be regenerated without drifting in style or structure.

## What It Does

- Renders X-ready PNGs at `1200 x 675` and `150 DPI`.
- Uses a shared nested theme in `config/theme.py` for colors, typography, layout,
  axis rules, watermarks, ETF palettes, and content-series metadata.
- Provides reusable visual components for price lines, volume bars, annotations,
  bump charts, ETF flow bars, ranking tables, Sankey-style structures, and base
  chart creation.
- Separates data fetching from rendering, with local cache support under
  `data/cache/`.
- Supports a template registry for recurring chart series through
  `config/templates.py` and `scripts/render_one.py`.
- Keeps content positioning and chart-selection rules in `docs/`.

## Project Structure

```text
config/       Theme constants and registered template metadata
components/   Reusable Matplotlib visual primitives
data/         Fetchers, cache helpers, schemas, exceptions, and static data
charts/       Legacy/single-chart script entrypoints
templates/    Registered recurring templates T1-T7
scripts/      CLI helpers, including render_one.py
docs/         Strategy notes and topic library
tests/        Pytest suite with fixture-backed smoke tests
output/       Generated PNGs, ignored by git
```

## Current Template Status

| ID | Template | Status |
| --- | --- | --- |
| T1 | BTC Spot ETF Flow Structure | Implemented |
| T2 | BTC Halving Cycle Normalized Comparison | Scaffold |
| T3 | Historical Top-Buyer Drawdown Comparison | Scaffold |
| T4 | LP and Staking Real-Yield Ranking | Scaffold |
| T5 | Funding-Rate Extremes Forward Return Distribution | Scaffold |
| T6 | Narrative Sector Rotation Bump Chart | Implemented |
| T7 | Cross-Chain Stablecoin Flow Sankey | Scaffold |

Placeholder templates intentionally raise `NotImplementedError` until implemented.

## Setup

Use the project virtualenv:

```bash
venv/bin/pip install -r requirements.txt
```

The repo ignores generated output, Matplotlib cache files, and data caches.

## Render Charts

Render a registered template:

```bash
venv/bin/python scripts/render_one.py t1 --as-of 2026-05-04
```

Optional manual title override for supported templates:

```bash
venv/bin/python scripts/render_one.py t1 --as-of 2026-05-04 --title "Custom title"
```

Run legacy standalone chart scripts:

```bash
venv/bin/python charts/btc_30d.py
venv/bin/python charts/macro_comparison_5y.py
venv/bin/python charts/btc_nasdaq_correlation.py
```

Generated images are written to `output/`.

## Validate

Run the full test suite:

```bash
venv/bin/pytest -q
```

Current expected result:

```text
28 passed
```

Useful extra checks:

```bash
rg 'COLORS\["(background|surface|grid|primary|accent|mint|rose|up|down|btc_line|gold_line|sp500_line|correlation_line|text_primary|text_muted|text_hint|label_muted|ma7|ma30|ibit|fbtc|bitb|arkb|gbtc|others|cumulative)"\]' config components charts templates tests CHART_SPEC.md
git diff --check
```

The `rg` command should return no code references to old flat color paths. The
documentation may mention an old path only as an explicit "do not use" example.

## Theme Rules

All shared visual constants live in `config/theme.py`.

Use nested color references:

```python
theme.COLORS["base"]["background"]
theme.COLORS["data"]["primary"]
theme.COLORS["text"]["muted"]
theme.COLORS["etf"]["ibit"]
```

Do not use old flat paths such as `theme.COLORS["primary"]`.

For ETF flow charts, use `theme.ETF_FLOW` so IBIT, FBTC, BITB, ARKB, GBTC,
Others, and cumulative-flow colors stay aligned with the central palette.

## Development Workflow

1. Decide whether the chart is a registered recurring template or a standalone
   script.
2. Confirm the content series or exception slot in `docs/STRATEGY.md` and
   `CHART_SPEC.md`.
3. Add or reuse fetchers in `data/`; rendering code should not parse raw API
   responses directly.
4. Put reusable drawing behavior in `components/`.
5. Put template orchestration in `templates/` and metadata in
   `config/templates.py`.
6. Read colors, typography, spacing, and export rules from `config/theme.py`.
7. Add or update focused tests, preferably fixture-backed and network-free.
8. Run `venv/bin/pytest -q` and render affected charts.

## Reference Docs

- `CHART_SPEC.md`: visual rules, content-series rules, and chart prompts.
- `PROJECT_SPEC.md`: architecture, data/cache contracts, and template contract.
- `TEMPLATE_SPEC.md`: template planning notes.
- `docs/STRATEGY.md`: account positioning and content strategy.
- `docs/观点库.md`: topic and viewpoint library.
