"""ADR 0007 §9.1 Python checks for `kagura.breaks`."""

import importlib.util
import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from kagura import breaks

GRID_DIR = Path(__file__).parents[1] / "research/methodology/adr0007-break-grid"


def test_dp_matches_brute_force_on_candidate_subset() -> None:
    rng = np.random.default_rng(7)
    n_obs, h = 240, 30
    x = rng.normal(size=n_obs)
    xm = np.column_stack([np.ones(n_obs), x])
    beta = np.where(np.arange(n_obs) < 90, 1.0, np.where(np.arange(n_obs) < 170, -0.5, 2.0))
    y = xm[:, 0] * 0.3 + beta * x + rng.normal(size=n_obs)
    cand = sorted(rng.choice(np.arange(1, n_obs), size=60, replace=False).tolist())
    parts = breaks.global_partitions(y, xm, h, 2, cand)
    ok = [b for b in cand if h <= b <= n_obs - h]
    for m in (1, 2):
        best = min(
            (
                sum(breaks.segment_ssr(y, xm, a, b) for a, b in breaks.regime_bounds(bs, n_obs)),
                bs,
            )
            for bs in itertools.combinations(ok, m)
            if all(b - a >= h for a, b in breaks.regime_bounds(bs, n_obs))
        )
        assert parts[m].breaks == best[1]
        assert parts[m].ssr == pytest.approx(best[0], abs=1e-10)


def test_nile_fixture() -> None:
    # Zeileis et al. (2003) §4.1: h = 15 %, BIC picks m = 1, strucchange breakpoint 28
    # (1898), i.e. first new-regime row 28 (0-based) = 1899; means 1097.75 and 849.9722.
    nile = sm.datasets.nile.load_pandas().data
    y = nile["volume"].to_numpy(float)
    assert y.mean() == pytest.approx(919.35)
    n_obs = len(y)
    xm = np.ones((n_obs, 1))
    parts = breaks.global_partitions(y, xm, math.floor(0.15 * n_obs), 5)
    assert breaks.select(parts, n_obs, q=1)["bic"] == 1
    (b,) = parts[1].breaks
    assert b == 28 and int(nile["year"].iloc[b]) == 1899
    assert y[:b].mean() == pytest.approx(1097.75)
    assert y[b:].mean() == pytest.approx(849.9722, abs=1e-4)


def test_known_two_break_slope_dgp() -> None:
    # §9.1 "known breaks": dates recovered within one month start in most replications.
    dates = pd.bdate_range("2000-01-03", periods=1500).to_numpy()
    cand = breaks.month_starts(dates)
    true = (cand[20], cand[45])
    hits, m2 = 0, 0
    for seed in range(20):
        rng = np.random.default_rng(seed)
        n_obs = len(dates)
        x = rng.normal(size=n_obs)
        t = np.arange(n_obs)
        slope = np.select([t < true[0], t < true[1]], [1.0, 0.0], 1.0)
        y = slope * x + rng.normal(size=n_obs)
        xm = np.column_stack([np.ones(n_obs), x])
        parts = breaks.global_partitions(y, xm, math.floor(0.15 * n_obs), 5, cand)
        got = parts[2].breaks
        hits += all(abs(cand.index(g) - cand.index(s)) <= 1 for g, s in zip(got, true, strict=True))
        m2 += 2 in breaks.select(parts, n_obs, q=2).values()
    assert hits >= 16 and m2 >= 16


def test_sup_f_one_break_equals_chow_form() -> None:
    # For k = 1 and homoskedastic errors, Wald = (S0 - S1) / s2 with s2 = S1 / (T - 2q).
    rng = np.random.default_rng(3)
    n_obs = 200
    x = rng.normal(size=n_obs)
    xm = np.column_stack([np.ones(n_obs), x])
    y = x * np.where(np.arange(n_obs) < 100, 1.0, 1.6) + rng.normal(size=n_obs)
    parts = breaks.global_partitions(y, xm, 30, 1)
    s0, s1 = parts[0].ssr, parts[1].ssr
    expected = (n_obs - 4) / n_obs * (s0 - s1) / (s1 / (n_obs - 4))
    assert breaks.sup_f(y, xm, parts[1]) == pytest.approx(expected, rel=1e-10)


def test_month_start_grid_reproduces_eligible_ranges() -> None:
    csv = pd.read_csv(GRID_DIR / "eligible_ranges.csv")
    spec = importlib.util.spec_from_file_location("er", GRID_DIR / "eligible_ranges.py")
    assert spec and spec.loader
    er = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(er)
        daily = er.load_daily()
    except FileNotFoundError:
        pytest.skip("frozen daily data not present")
    rows = csv[(csv["data"] == "daily") & (csv["grid"] == "month-start")]
    checked = 0
    for r in rows.to_dict("records"):
        d = er.daily_dates(daily, r["maturity"], r["timing"], int(r["lags"]))
        d = d[d >= pd.Timestamp(er.SAMPLES[str(r["sample"])])].reset_index(drop=True)
        n_obs, h = len(d), math.floor(float(r["eps"]) * len(d))
        ok = [b for b in breaks.month_starts(d.to_numpy()) if h <= b <= n_obs - h]
        assert (n_obs, h, len(ok)) == (r["T"], r["h"], r["n_candidates"])
        assert str(d.iloc[ok[0]].date()) == r["first_eligible"]
        assert str(d.iloc[ok[-1]].date()) == r["last_eligible"]
        checked += 1
    assert checked == len(rows) > 0
