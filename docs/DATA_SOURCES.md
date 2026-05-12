# Data Sources

All registered datasets are cached as parquet files under `data/cache/{source_id}/{dataset_id}.parquet`.
Timestamps are stored as tz-naive UTC dates normalized to `00:00:00`.

| Dataset key | Source URL | Coverage start | Columns | Update frequency | Known limitations |
| --- | --- | --- | --- | --- | --- |
| `prices.multi_asset` | `yfinance.download()` for `BTC-USD`, `SPY`, `GLD`, `DX-Y.NYB` | `2020-01-01` default backfill | `timestamp`, `btc`, `spy`, `gld`, `dxy` | Daily | Yahoo Finance symbols can change or have delayed market data. |
| `onchain.coinmetrics_btc` | `https://community-api.coinmetrics.io/v4/timeseries/asset-metrics` | `2020-01-01`; verified through `2026-05-11` in local cache | `timestamp`, `PriceUSD`, `CapMVRVCur`, `IssTotUSD`, `HashRate`, `AdrActCnt` | Daily | Local quality check on `2026-05-12`: `PriceUSD`, `CapMVRVCur`, and `IssTotUSD` each had `0.0%` NaN over 2,323 rows. Community API availability can still vary by metric. |
| `defi.protocol_revenue` | `https://api.llama.fi/overview/fees` | Snapshot-only from first run | `timestamp`, `protocol`, `daily_revenue_usd` | Daily | Endpoint exposes current protocol overview; history is built by daily local snapshots. |
| `defi.tvl` | `https://api.llama.fi/v2/historicalChainTvl` | API-provided historical coverage | `timestamp`, `chain`, `tvl_usd` | Daily | Chain naming and historical depth are controlled by DefiLlama. |
| `derivatives.funding_rates` | `https://open-api.coinglass.com/public/v2/funding` | API-provided recent coverage | `timestamp`, `symbol`, `funding_rate`, `open_interest_usd` | 8-hour snapshots | Requires `COINGLASS_API_KEY`; free tier is rate-limited and may return limited history. |
| `market.categories` | `https://api.coingecko.com/api/v3/coins/categories` | Snapshot-only from first run | `timestamp`, `id`, `name`, `market_cap`, `volume_24h`, `market_cap_change_24h`, `top_3_coins` | Daily | CoinGecko exposes current category snapshots; history is built by daily local snapshots. |

Run `python -m data.scheduler backfill --dataset <key>` to initialize one cache, or omit `--dataset` to attempt every registered dataset.
