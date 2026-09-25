"""Download source series and build one tidy long table.

Run with ``make data``. Raw downloads are kept unchanged in data/raw/ as the
audit trail; the parsed result is data/processed/series_long.csv with columns
date, series, value. See docs/decisions/0002-data-sources.md.
"""

from __future__ import annotations

import io
import json
import ssl
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime

import certifi
import pandas as pd

from kagura import DATA_PROCESSED, DATA_RAW

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
MOF = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/{}"
BIS = "https://stats.bis.org/api/v1/data/WS_LONG_CPI/{}/all?format=csv"

COLUMNS = ["date", "series", "value"]


def parse_fred(text: str, name: str) -> pd.DataFrame:
    """FRED CSV: header ``observation_date,<ID>``; holidays are rows with an empty value."""
    df = pd.read_csv(io.StringIO(text), parse_dates=["observation_date"])
    df.columns = pd.Index(["date", "value"])
    df["series"] = name
    return df.dropna(subset=["value"])[COLUMNS]


def parse_mof(text: str, name: str) -> pd.DataFrame:
    """MOF JGB CSV: title line, header ``Date,1Y,2Y,...``, ``-`` for missing, text footer."""
    df = pd.read_csv(io.StringIO(text), skiprows=1, na_values=["-"])
    df = df[df["Date"].str.match(r"^\d{4}/\d{1,2}/\d{1,2}$", na=False)].copy()
    df["date"] = pd.to_datetime(df["Date"], format="%Y/%m/%d")
    parts = []
    for tenor in ("2Y", "10Y"):
        part = df[["date"]].assign(series=f"{name}_{tenor.lower()}", value=df[tenor].astype(float))
        parts.append(part.dropna(subset=["value"]))
    return pd.concat(parts)[COLUMNS]


def parse_bis(text: str, name: str) -> pd.DataFrame:
    """BIS SDMX CSV: ``TIME_PERIOD`` like ``1946-08`` and ``OBS_VALUE``; stamp the month start."""
    df = pd.read_csv(io.StringIO(text))
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df["TIME_PERIOD"], format="%Y-%m"),
            "series": name,
            "value": df["OBS_VALUE"].astype(float),
        }
    )
    return out.dropna(subset=["value"])[COLUMNS]


Parser = Callable[[str, str], pd.DataFrame]

# name -> (url, parser). Names are the values of the ``series`` column.
SOURCES: dict[str, tuple[str, Parser]] = {
    "usdjpy": (FRED.format("DEXJPUS"), parse_fred),
    "us_2y": (FRED.format("DGS2"), parse_fred),
    "us_10y": (FRED.format("DGS10"), parse_fred),
    "fed_funds": (FRED.format("DFF"), parse_fred),
    "jp_call_rate": (FRED.format("IRSTCI01JPM156N"), parse_fred),
    "us_cpi": (FRED.format("CPIAUCSL"), parse_fred),
    "brent": (FRED.format("DCOILBRENTEU"), parse_fred),
    "vix": (FRED.format("VIXCLS"), parse_fred),
    "jp_cpi": (BIS.format("M.JP.628"), parse_bis),
    # Two files produce jgb_2y and jgb_10y: history through last month, then the current month.
    "jgb": (MOF.format("historical/jgbcme_all.csv"), parse_mof),
    "jgb_current": (MOF.format("jgbcme.csv"), parse_mof),
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "kagura-research/0.1"})
    # python.org builds on macOS ship without a CA bundle; certifi supplies one everywhere.
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        return bytes(resp.read())


def build() -> pd.DataFrame:
    manifest: dict[str, dict[str, str | int]] = {}
    frames = []
    for name, (url, parser) in SOURCES.items():
        raw = fetch(url)
        (DATA_RAW / f"{name}.csv").write_bytes(raw)
        downloaded_at = datetime.now(UTC).isoformat()
        manifest[name] = {"url": url, "downloaded_at": downloaded_at, "bytes": len(raw)}
        # The MOF footer contains Shift-JIS bytes; the data rows are ASCII, so replace is safe.
        text = raw.decode("utf-8-sig", errors="replace")
        frames.append(parser(text, "jgb" if name == "jgb_current" else name))
    (DATA_RAW / "manifest.json").write_text(json.dumps(manifest, indent=2))

    long = pd.concat(frames, ignore_index=True)
    # The current-month MOF file may overlap the history file; keep the later download.
    long = long.drop_duplicates(subset=["series", "date"], keep="last")
    long = long.sort_values(["series", "date"]).reset_index(drop=True)
    long.to_csv(DATA_PROCESSED / "series_long.csv", index=False, date_format="%Y-%m-%d")
    return long


def load() -> pd.DataFrame:
    return pd.read_csv(DATA_PROCESSED / "series_long.csv", parse_dates=["date"])


if __name__ == "__main__":
    summary = build().groupby("series")["date"].agg(["min", "max", "count"])
    print(summary.to_string())
