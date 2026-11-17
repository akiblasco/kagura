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


def test_f_test_one_break_homoskedastic_equals_chow_form() -> None:
    # robust = 0, hetvar = 0 (mbreaks pvdel): s2 = S1 / T, Wald = (S0 - S1) / s2,
    # F = (T - 2q) / T * Wald.
    rng = np.random.default_rng(3)
    n_obs = 200
    x = rng.normal(size=n_obs)
    xm = np.column_stack([np.ones(n_obs), x])
    y = x * np.where(np.arange(n_obs) < 100, 1.0, 1.6) + rng.normal(size=n_obs)
    parts = breaks.global_partitions(y, xm, 30, 1)
    s0, s1 = parts[0].ssr, parts[1].ssr
    expected = (n_obs - 4) / n_obs * (s0 - s1) / (s1 / n_obs)
    cov = breaks.Cov(robust=False, hetvar=False)
    assert breaks.f_test(y, xm, parts[1].breaks, cov) == pytest.approx(expected, rel=1e-10)


def test_bartlett_lrv_matches_statsmodels() -> None:
    # mbreaks' jhatpr divides the kernel-weighted sum by n - d; S_hac_simple returns the sum.
    from statsmodels.stats.sandwich_covariance import S_hac_simple

    rng = np.random.default_rng(5)
    n_obs = 500
    xm = np.column_stack([np.ones(n_obs), rng.normal(size=n_obs)])
    e = np.convolve(rng.normal(size=n_obs + 3), [1, 0.5, 0.25], "valid")[:n_obs]
    got = breaks.lrv(xm, e, breaks.Cov(lags=6)) * (n_obs - 2)
    ref = S_hac_simple(xm * e[:, None], nlags=6)
    np.testing.assert_allclose(got, ref, rtol=1e-10)


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


def test_r_crosscheck_reference_files() -> None:
    # ADR 0007 §9.2: compares with the committed R output; R itself is not run here.
    path = GRID_DIR / "r-crosscheck" / "compare.py"
    spec = importlib.util.spec_from_file_location("compare", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = mod.compare()
    status = [r["status"] for r in rows]
    assert "FAIL" not in status
    assert status.count("pass") == 359 and status.count("convention") == 40


def test_limit_dp_matches_brute_force() -> None:
    from kagura import breaksim as bs

    rng = np.random.default_rng(11)
    n_obs, h, q = 60, 9, 2
    cand = sorted(rng.choice(np.arange(1, n_obs), size=25, replace=False).tolist())
    rows = np.array([0, *[c for c in cand if h <= c <= n_obs - h], n_obs])
    lam = rows / n_obs
    valid = rows[None, :] - rows[:, None] >= h
    p = np.concatenate(
        [np.zeros((3, 1, q)), np.cumsum(rng.normal(size=(3, len(lam) - 1, q)), 1)], 1
    )
    got = bs.supf_from_paths(p, lam, valid, 2)
    for k in (1, 2):
        for r in range(3):
            vals = []
            for bs_ in itertools.combinations(range(1, len(lam) - 1), k):
                e = [0, *bs_, len(lam) - 1]
                if all(rows[b] - rows[a] >= h for a, b in zip(e[:-1], e[1:], strict=True)):
                    s = sum(
                        float(np.sum((p[r, b] - p[r, a]) ** 2)) / (lam[b] - lam[a])
                        for a, b in zip(e[:-1], e[1:], strict=True)
                    )
                    vals.append((s - float(np.sum(p[r, -1] ** 2))) / k)
            assert got[r, k - 1] == pytest.approx(max(vals), rel=1e-12)


def test_robust_bg_equals_statsmodels_hc0_wald() -> None:
    from kagura import breaksim as bs

    rng = np.random.default_rng(2)
    n_obs = 300
    xm = np.column_stack([np.ones(n_obs), rng.normal(size=n_obs)])
    e = rng.normal(size=n_obs) * (1 + np.abs(xm[:, 1]))
    w, pv = bs.robust_bg(e, xm, lags=4)
    lagm = np.column_stack([np.concatenate([np.zeros(i), e[:-i]]) for i in range(1, 5)])
    fit = sm.OLS(e, np.column_stack([xm, lagm])).fit(cov_type="HC0")
    ref = fit.wald_test(np.eye(6)[2:], scalar=True, use_f=False)
    assert w == pytest.approx(float(ref.statistic), rel=1e-10)
    assert pv == pytest.approx(float(ref.pvalue), rel=1e-8)


def test_wf_bootstrap_matches_direct_computation() -> None:
    from kagura import breaksim as bs

    rng = np.random.default_rng(4)
    n_obs, h = 120, 18
    xm = np.column_stack([np.ones(n_obs), rng.normal(size=n_obs), rng.normal(size=n_obs)])
    y = xm @ [0.1, 1.0, -0.5] + rng.normal(size=n_obs) * (1 + 0.5 * np.abs(xm[:, 1]))
    cand = list(range(10, 110, 5))
    res = bs.wf_sup_wald(y, xm, (), cand, h, reps=7, seed=9)

    def ew_wald(yv: np.ndarray, c: int, meat_resid: np.ndarray | None) -> float:
        parts = []
        for sl in (slice(0, c), slice(c, n_obs)):
            z, yy = xm[sl], yv[sl]
            b = np.linalg.solve(z.T @ z, z.T @ yy)
            u = (yy - z @ b) if meat_resid is None else meat_resid[sl]
            qi = np.linalg.inv(z.T @ z)
            parts.append((b, qi @ (z.T * u**2) @ z @ qi))
        d = parts[0][0] - parts[1][0]
        return float(d @ np.linalg.solve(parts[0][1] + parts[1][1], d))

    ok = [c for c in cand if h <= c <= n_obs - h]
    stat = max(ew_wald(y, c, None) for c in ok)
    assert res.stat == pytest.approx(stat, rel=1e-9)
    b0 = np.linalg.lstsq(xm, y, rcond=None)[0]
    uhat = y - xm @ b0
    nu = np.random.default_rng(9).choice(np.array([-1.0, 1.0]), size=(n_obs, 7))
    for r in range(7):
        ystar = xm @ b0 + uhat * nu[:, r]
        ref = max(ew_wald(ystar, c, uhat) for c in ok)
        assert res.boot[r] == pytest.approx(ref, rel=1e-9)
