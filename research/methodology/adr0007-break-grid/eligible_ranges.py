"""Usable rows and eligible break-date candidates for ADR 0007 §3.3. Counting only: no
regression, no break statistic.

Convention: a break date is the FIRST row of the new regime. With n usable rows and
h = floor(eps * n), a candidate row k (0-based) is eligible if both regimes have at least h
rows: h <= k <= n - h.

Grids:
- "month-start": the first usable row of each calendar month (primary, multi-break);
- "daily": every usable row (single-break sensitivity);
- monthly data (variant V3): every month-end row, so the two grids coincide.

Run from the repository root:
    uv run python research/methodology/adr0007-break-grid/eligible_ranges.py
Writes eligible_ranges.csv next to this file.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from kagura.explore import changes, load_daily, load_monthly
from kagura.h1a import verify_checksums
from kagura.models import DAILY_END, MONTHLY_END

SAMPLES = {"full": "1981-01-01", "recent": "2013-01-01"}  # ADR 0007 §3.1
EPS = (0.15, 0.10, 0.05)  # ADR 0007 §3.2
M = 5  # maximum breaks in every cell
LAGS = range(1, 6)  # lag-augmented p = 1..5 (ADR 0007 §6.2)
OUT = Path(__file__).with_name("eligible_ranges.csv")


def daily_dates(daily: pd.DataFrame, maturity: str, timing: str, p: int) -> pd.Series:
    """Dates of rows usable by the static (p = 0) or lag-augmented (p lags) model. Lags are
    previous rows of the USD/JPY calendar and must themselves pass the ADR 0004 rule."""
    ch = changes(daily, maturity, timing)
    ch = ch[ch["date"] <= DAILY_END].reset_index(drop=True)
    need = ["dfx", "ddiff"]
    for i in range(1, p + 1):
        ch[f"dfx_l{i}"], ch[f"ddiff_l{i}"] = ch["dfx"].shift(i), ch["ddiff"].shift(i)
        need += [f"dfx_l{i}", f"ddiff_l{i}"]
    return ch.dropna(subset=need)["date"].reset_index(drop=True)


def monthly_dates(monthly: pd.DataFrame, maturity: str) -> pd.Series:
    m = monthly[monthly["date"] <= MONTHLY_END]
    d = m.assign(
        dfx=100 * np.log(m["usdjpy"]).diff(), dd=(m[f"us_{maturity}"] - m[f"jgb_{maturity}"]).diff()
    )
    d = d[d["date"] >= SAMPLES["full"]]
    return d.dropna(subset=["dfx", "dd"])["date"].reset_index(drop=True)


def eligible(dates: pd.Series, eps: float, grid: str) -> dict[str, object]:
    n = len(dates)
    h = math.floor(eps * n)
    k = np.arange(n)
    if grid == "month-start":
        months = dates.dt.to_period("M")
        cand = k[(months != months.shift()).to_numpy()]
        cand = cand[cand > 0]  # the sample's first row cannot start a new regime
    else:
        cand = k[1:]
    ok = cand[(cand >= h) & (cand <= n - h)]
    years = (dates.iloc[-1] - dates.iloc[0]).days / 365.25
    return {
        "T": n,
        "first_row": dates.iloc[0].date(),
        "last_row": dates.iloc[-1].date(),
        "h": h,
        "h_years": round(h * years / n, 2),
        "n_candidates": len(ok),
        "first_eligible": dates.iloc[ok[0]].date(),
        "last_eligible": dates.iloc[ok[-1]].date(),
        "max_breaks_feasible": min(M, math.floor(n / h) - 1),
    }


def main() -> None:
    verify_checksums()
    daily, monthly = load_daily(), load_monthly()
    rows = []
    for maturity in ("2y", "10y"):
        for timing in ("same-day", "lagged"):
            for p in (0, *LAGS):
                if p and (maturity, timing) != ("2y", "same-day"):
                    continue  # lag augmentation is run on the primary variant only (§4.3)
                dates = daily_dates(daily, maturity, timing, p)
                for sample, start in SAMPLES.items():
                    d = dates[dates >= start].reset_index(drop=True)
                    for eps in EPS:
                        for grid in ("month-start", "daily"):
                            rows.append(
                                {
                                    "data": "daily",
                                    "maturity": maturity,
                                    "timing": timing,
                                    "lags": p,
                                    "sample": sample,
                                    "eps": eps,
                                    "grid": grid,
                                    **eligible(d, eps, grid),
                                }
                            )
        dates = monthly_dates(monthly, maturity)
        for sample, start in SAMPLES.items():
            d = dates[dates >= start].reset_index(drop=True)
            for eps in EPS:
                rows.append(
                    {
                        "data": "monthly",
                        "maturity": maturity,
                        "timing": "month-end",
                        "lags": 0,
                        "sample": sample,
                        "eps": eps,
                        "grid": "month",
                        **eligible(d, eps, "daily"),
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
