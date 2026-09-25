"""Align the long table onto analytical calendars without look-ahead.

Run with ``uv run python -m kagura.align`` (``make data`` runs it after ingestion).
Writes data/processed/daily.csv and data/processed/monthly.csv.
See docs/decisions/0003-time-alignment.md for every timing rule used here.
"""

from __future__ import annotations

import pandas as pd

from kagura import DATA_PROCESSED
from kagura.data import load

# Daily market series joined onto the USD/JPY calendar.
MARKET = ["us_2y", "us_10y", "fed_funds", "jgb_2y", "jgb_10y", "brent", "vix"]

# A market value older than this is treated as missing rather than carried.
# ponytail: "5 business days" implemented as 7 calendar days; no holiday calendar needed.
MAX_CARRY = pd.Timedelta(days=7)

# Monthly series: offset from the first day of the reference month to the day it is
# assumed known. Fixed conservative approximations, not historical release dates.
AVAILABLE_AFTER = {
    "us_cpi": pd.DateOffset(months=1, days=14),  # 15th of the following month
    # ponytail: deliberately late, so older years' later releases are never used early.
    "jp_cpi": pd.DateOffset(months=2, days=-1),  # last day of the following month
    "jp_call_rate": pd.DateOffset(months=1),  # monthly average, known once the month ends
}


def _series(long: pd.DataFrame, name: str) -> pd.DataFrame:
    s = long.loc[long["series"] == name, ["date", "value"]]
    return s.rename(columns={"value": name}).reset_index(drop=True)


def build_daily(long: pd.DataFrame) -> pd.DataFrame:
    """One row per USD/JPY observation day. Other markets take their latest value dated on or
    before that day, at most MAX_CARRY old; ``<name>_carried`` marks values from an earlier day.

    ``<name>_change_carried`` marks rows whose one-row change touches a carried value: the
    carried rows themselves and the first row after them, whose change spans the closure."""
    out = _series(long, "usdjpy")
    for name in MARKET:
        s = _series(long, name).assign(obs_date=lambda d: d["date"])
        out = pd.merge_asof(out, s, on="date", tolerance=MAX_CARRY)
        out[f"{name}_carried"] = out[name].notna() & (out["obs_date"] != out["date"])
        out = out.drop(columns="obs_date")
    for name, us, jp in (("diff_2y", "us_2y", "jgb_2y"), ("diff_10y", "us_10y", "jgb_10y")):
        out[name] = out[us] - out[jp]
        out[f"{name}_carried"] = out[f"{us}_carried"] | out[f"{jp}_carried"]
    for name in [*MARKET, "diff_2y", "diff_10y"]:
        carried = out[f"{name}_carried"]
        out[f"{name}_change_carried"] = carried | carried.shift(1, fill_value=False)
    return out


def build_monthly(long: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """One row per month: the last daily row of the month, plus the latest monthly releases
    available on that date. ``<name>_month`` is the reference month of the value used."""
    # Daily-change flags say nothing about month-to-month changes; keep only level flags.
    daily = daily.drop(columns=daily.filter(like="_change_carried").columns)
    out = daily.groupby(daily["date"].dt.to_period("M")).tail(1).reset_index(drop=True)
    last = out["date"].iloc[-1]
    if last < pd.offsets.BMonthEnd().rollforward(last):
        out = out.iloc[:-1]  # the current month is not over; its "month-end" value is not one
    for name, lag in AVAILABLE_AFTER.items():
        s = _series(long, name)
        s = s.assign(available=s["date"] + lag).rename(columns={"date": f"{name}_month"})
        out = pd.merge_asof(out, s, left_on="date", right_on="available").drop(columns="available")
    return out


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    long = load()
    daily = build_daily(long)
    monthly = build_monthly(long, daily)
    daily.to_csv(DATA_PROCESSED / "daily.csv", index=False, date_format="%Y-%m-%d")
    monthly.to_csv(DATA_PROCESSED / "monthly.csv", index=False, date_format="%Y-%m-%d")
    return daily, monthly


if __name__ == "__main__":
    daily, monthly = build()
    for label, df in (("daily", daily), ("monthly", monthly)):
        print(f"{label}: {len(df)} rows, {df['date'].min():%Y-%m-%d}..{df['date'].max():%Y-%m-%d}")
    print("share of non-missing values carried:")
    for name in MARKET:
        print(f"  {name:10s} {daily[f'{name}_carried'].sum() / daily[name].notna().sum():.2%}")
