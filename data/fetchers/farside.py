"""Farside Investors fetcher for BTC spot ETF fund-flow data."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re

from bs4 import BeautifulSoup
import pandas as pd
import requests

from data.exceptions import DataFetchError
from data.schemas import ETF_FLOW_SCHEMA


FARSIDE_BTC_ETF_URL = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
CACHE_PATH = Path(__file__).resolve().parents[1] / "cache" / "farside_btc_etf_flows.csv"
REQUEST_TIMEOUT = 20
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
FLOW_TICKERS = ("IBIT", "FBTC", "BITB", "ARKB", "BTCO", "EZBC", "BRRR", "HODL", "BTCW", "MSBT", "GBTC", "BTC")
ENTITY_BY_TICKER = {
    "IBIT": "BlackRock IBIT",
    "FBTC": "Fidelity FBTC",
    "BITB": "Bitwise BITB",
    "ARKB": "ARK 21Shares ARKB",
    "BTCO": "Invesco Galaxy BTCO",
    "EZBC": "Franklin EZBC",
    "BRRR": "Valkyrie BRRR",
    "HODL": "VanEck HODL",
    "BTCW": "WisdomTree BTCW",
    "MSBT": "Morgan Stanley MSBT",
    "GBTC": "Grayscale GBTC",
    "BTC": "Grayscale BTC",
}


def fetch_etf_flows(end_date: str | None, days: int = 7, use_cache: bool = True) -> pd.DataFrame:
    """
    Return normalized BTC spot ETF flow rows from Farside Investors.

    Farside reports values in US$m. This fetcher normalizes them to signed USD
    values in the `flow_usd` column and returns a long DataFrame matching the
    ETF flow schema declared in `data.schemas`.
    """
    cutoff = _normalize_end_date(end_date)
    cached_df = _read_cache() if use_cache else None
    if cached_df is not None and not cached_df.empty:
        cached_df["date"] = pd.to_datetime(cached_df["date"]).dt.tz_localize(None)
        if cached_df["date"].max() >= cutoff:
            return _filter_window(cached_df, cutoff, days)

    try:
        response = requests.get(FARSIDE_BTC_ETF_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        if cached_df is not None and not cached_df.empty:
            return _filter_window(cached_df, cutoff, days)
        raise DataFetchError("Failed to fetch Farside BTC ETF flow table") from exc

    df = parse_farside_btc_etf_html(response.text)
    _write_cache(df)
    return _filter_window(df, cutoff, days)


def parse_farside_btc_etf_html(html: str) -> pd.DataFrame:
    """Parse the Farside all-data HTML table into normalized ETF flow rows."""
    soup = BeautifulSoup(html, "html.parser")
    table = _find_flow_table(soup)
    rows = []
    header = None

    for tr in table.find_all("tr"):
        cells = [_clean_text(cell.get_text(" ", strip=True)) for cell in tr.find_all(["th", "td"])]
        if not cells:
            continue
        if "Date" in cells and "IBIT" in cells:
            header = cells
            continue
        if header is None or not _looks_like_date(cells[0]):
            continue

        row = dict(zip(header, cells))
        parsed_date = pd.to_datetime(row["Date"], format="%d %b %Y", errors="coerce")
        if pd.isna(parsed_date):
            continue
        for ticker in FLOW_TICKERS:
            if ticker not in row:
                continue
            rows.append(
                {
                    "date": parsed_date.normalize(),
                    "entity": ENTITY_BY_TICKER.get(ticker, ticker),
                    "ticker": ticker,
                    "asset": "BTC",
                    "flow_usd": _parse_usd_millions(row[ticker]),
                    "aum_usd": float("nan"),
                    "source": "Farside Investors",
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        raise DataFetchError("Farside BTC ETF flow table contained no parsable rows")
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df["flow_usd"] = pd.to_numeric(df["flow_usd"], errors="coerce").fillna(0.0)
    df = df.sort_values(["date", "ticker"]).reset_index(drop=True)
    ETF_FLOW_SCHEMA.validate(df)
    return df


def _find_flow_table(soup: BeautifulSoup):
    """Return the HTML table containing Date and IBIT columns."""
    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True)
        if "Date" in text and "IBIT" in text and "GBTC" in text:
            return table
    raise DataFetchError("Could not find Farside BTC ETF flow table")


def _normalize_end_date(end_date: str | None) -> pd.Timestamp:
    """Return a timezone-naive cutoff timestamp."""
    if end_date is None:
        return pd.Timestamp(date.today()).normalize()
    return pd.Timestamp(end_date).tz_localize(None).normalize()


def _filter_window(df: pd.DataFrame, cutoff: pd.Timestamp, days: int) -> pd.DataFrame:
    """Filter cached or freshly fetched rows to the requested cutoff window."""
    output_df = df.copy()
    output_df["date"] = pd.to_datetime(output_df["date"]).dt.tz_localize(None)
    start = cutoff - pd.Timedelta(days=days)
    return (
        output_df[(output_df["date"] >= start) & (output_df["date"] <= cutoff)]
        .sort_values(["date", "ticker"])
        .reset_index(drop=True)
    )


def _read_cache() -> pd.DataFrame | None:
    """Read the normalized Farside cache when present."""
    if not CACHE_PATH.exists():
        return None
    df = pd.read_csv(CACHE_PATH)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    return df.sort_values(["date", "ticker"]).reset_index(drop=True)


def _write_cache(df: pd.DataFrame) -> None:
    """Write the normalized Farside cache as CSV for portable test fixtures."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_df = df.copy()
    output_df["date"] = pd.to_datetime(output_df["date"]).dt.strftime("%Y-%m-%d")
    output_df.to_csv(CACHE_PATH, index=False)


def _clean_text(value: str) -> str:
    """Normalize whitespace from an HTML table cell."""
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def _looks_like_date(value: str) -> bool:
    """Return True when a Farside row label looks like a daily date."""
    return bool(re.match(r"^\d{1,2} [A-Za-z]{3} \d{4}$", value))


def _parse_usd_millions(value: str) -> float:
    """Parse Farside US$m cell text into signed USD."""
    cleaned = _clean_text(value).replace(",", "")
    if cleaned in {"", "-", "–"}:
        return 0.0
    sign = -1 if cleaned.startswith("(") and cleaned.endswith(")") else 1
    cleaned = cleaned.strip("()")
    return sign * float(cleaned) * 1_000_000
