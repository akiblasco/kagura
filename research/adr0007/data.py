"""ADR 0007 samples: rows, regressors and candidate grids, checked against the frozen counts.

Every cell's T and candidate count must equal `eligible_ranges.csv` (ADR 0007 §3.3), so the
rows used here are exactly the rows the ADR froze. Lag-augmented rows follow §4.2: a row is
used only if it and its p previous rows of the USD/JPY calendar pass the ADR 0004 rule.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from kagura import breaks
from kagura.explore import changes, load_daily, load_monthly
from kagura.h1a import verify_checksums
from kagura.models import DAILY_END, MONTHLY_END, hac_lag

GRID = Path(__file__).parents[1] / "methodology/adr0007-break-grid/eligible_ranges.csv"
SAMPLES = {"full": "1981-01-01", "recent": "2013-01-01"}


@dataclass(frozen=True)
class Cell:
    spec: str  # primary, V1, V2, V3, lag
    sample: str
    eps: float
    p: int
    dates: pd.Series
    y: np.ndarray
    xm: np.ndarray
    names: tuple[str, ...]
    h: int
    month_grid: list[int]  # month-start candidates (all rows for monthly data)
    lags: int  # ADR 0006 §4.4 Bartlett lag for this sample's T

    @property
    def n_obs(self) -> int:
        return len(self.y)

    def eligible(self, grid: list[int] | None = None) -> list[int]:
        g = self.month_grid if grid is None else grid
        return [b for b in g if self.h <= b <= self.n_obs - self.h]


def _daily(
    maturity: str, timing: str, p: int, start: str
) -> tuple[pd.Series, np.ndarray, np.ndarray, tuple[str, ...]]:
    ch = changes(load_daily(), maturity, timing)
    ch = ch[ch["date"] <= DAILY_END].reset_index(drop=True)
    cols, names = ["ddiff"], ["const", "dd"]
    for i in range(1, p + 1):
        ch[f"ddiff_l{i}"], ch[f"dfx_l{i}"] = ch["ddiff"].shift(i), ch["dfx"].shift(i)
        cols += [f"ddiff_l{i}", f"dfx_l{i}"]
        names += [f"dd_l{i}", f"ds_l{i}"]
    d = ch.dropna(subset=["dfx", *cols])
    d = d[d["date"] >= pd.Timestamp(start)].reset_index(drop=True)
    xm = np.column_stack([np.ones(len(d)), d[cols].to_numpy(float)])
    return d["date"], d["dfx"].to_numpy(float), xm, tuple(names)


def _monthly(
    maturity: str, start: str
) -> tuple[pd.Series, np.ndarray, np.ndarray, tuple[str, ...]]:
    m = load_monthly()
    m = m[m["date"] <= MONTHLY_END]
    d = m.assign(
        dfx=100 * np.log(m["usdjpy"]).diff(), dd=(m[f"us_{maturity}"] - m[f"jgb_{maturity}"]).diff()
    )
    d = d[d["date"] >= pd.Timestamp(start)].dropna(subset=["dfx", "dd"]).reset_index(drop=True)
    xm = np.column_stack([np.ones(len(d)), d["dd"].to_numpy(float)])
    return d["date"], d["dfx"].to_numpy(float), xm, ("const", "dd")


SPECS = {
    "primary": ("daily", "2y", "same-day"),
    "V1": ("daily", "2y", "lagged"),
    "V2": ("daily", "10y", "same-day"),
    "V3": ("monthly", "2y", "month-end"),
    "lag": ("daily", "2y", "same-day"),
}


def cell(spec: str, sample: str, eps: float, p: int = 0) -> Cell:
    verify_checksums()  # frozen H1a inputs (ADR 0006 §9.2)
    data, maturity, timing = SPECS[spec]
    if data == "daily":
        dates, y, xm, names = _daily(maturity, timing, p, SAMPLES[sample])
        grid = breaks.month_starts(dates.to_numpy())
    else:
        dates, y, xm, names = _monthly(maturity, SAMPLES[sample])
        grid = list(range(1, len(y)))
    n_obs = len(y)
    c = Cell(
        spec, sample, eps, p, dates, y, xm, names, math.floor(eps * n_obs), grid, hac_lag(n_obs)
    )
    _check(c, data, maturity, timing)
    return c


def _check(c: Cell, data: str, maturity: str, timing: str) -> None:
    grid_name = "month-start" if data == "daily" else "month"
    for r in csv.DictReader(GRID.open()):
        if (
            r["data"],
            r["maturity"],
            r["timing"],
            int(r["lags"]),
            r["sample"],
            float(r["eps"]),
        ) == (data, maturity, timing, c.p, c.sample, c.eps) and r["grid"] == grid_name:
            got = (c.n_obs, c.h, len(c.eligible()), str(c.dates.iloc[c.eligible()[0]].date()))
            want = (int(r["T"]), int(r["h"]), int(r["n_candidates"]), r["first_eligible"])
            if got != want:
                raise AssertionError(f"{c.spec} {c.sample} {c.eps} p={c.p}: {got} != frozen {want}")
            return
    raise AssertionError(f"no frozen row for {c.spec} {c.sample} {c.eps} p={c.p}")
