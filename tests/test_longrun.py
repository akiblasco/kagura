"""Synthetic-data checks of the ADR 0008 §9 exploratory helpers. No real KAGURA data is used."""

import math
import re

import numpy as np
import pandas as pd
import statsmodels.api as sm

from kagura import ROOT
from kagura.longrun import (
    _uecm_design,
    ar_polynomial,
    bootstrap_half_life,
    calendar_terms,
    classify,
    dols,
    fit_ardl,
    fmols,
    half_life,
    select_ardl,
    tax_adjusted,
)
from kagura.vintage import CPI_SHA256


def _months(n: int) -> pd.PeriodIndex:
    return pd.period_range("1981-01", periods=n, freq="M")


def _coint(
    rng: np.random.Generator, n: int = 500, rho: float = 0.7
) -> tuple[np.ndarray, np.ndarray]:
    """y = 1 + 0.8 x1 + 0.5 x2 + u, u AR(1), x random walks (endogenous via a shared shock)."""
    e = rng.standard_normal((n, 3))
    xs = e[:, 1:].cumsum(0)
    u = np.zeros(n)
    for t in range(1, n):
        u[t] = rho * u[t - 1] + e[t, 0] + 0.5 * e[t, 1]
    return 1 + xs @ np.array([0.8, 0.5]) + u, xs


def test_classify_recovers_i0_i1_and_i2_in_most_samples() -> None:
    hits = {"I(0)": 0, "I(1)": 0, "I(2) risk": 0}
    for seed in range(20):  # each test has ~5 % size, so single draws can misclassify
        eps = np.random.default_rng(seed).standard_normal(500)
        ar = np.zeros(500)
        for t in range(1, 500):
            ar[t] = 0.5 * ar[t - 1] + eps[t]
        for want, v in (("I(0)", ar), ("I(1)", eps.cumsum()), ("I(2) risk", eps.cumsum().cumsum())):
            hits[want] += classify(want, pd.Series(v, _months(500))).klass == want
    # I(1) needs four outcomes at once (two 5 % tests not rejecting), so ~85 % is expected;
    # P(Binomial(20, 0.85) < 13) < 0.01.
    assert min(hits.values()) >= 13, hits


def test_tax_adjustment_removes_excess_jump_permanently() -> None:
    idx = pd.period_range("1981-01", "2021-12", freq="M")
    x = pd.Series(0.1 * np.arange(len(idx)), idx)  # 0.1 per month everywhere
    x[x.index >= pd.Period("1997-04", "M")] += 2.0  # a 2-point tax jump
    adj = tax_adjusted(x)
    assert np.allclose(adj.diff().dropna(), 0.1)


def test_uecm_statistics_match_statsmodels_ols() -> None:
    rng = np.random.default_rng(2)
    y, xs = _coint(rng)
    fit = fit_ardl(y, xs, p=3, q=2)
    yv, z = _uecm_design(y, xs, 3, 2, fit.start)
    res = sm.OLS(yv, z).fit()
    assert np.allclose(fit.fitted_coef, res.params)
    assert math.isclose(fit.t, res.tvalues[1])
    r = np.zeros((3, z.shape[1]))
    r[0, 1], r[1, 2], r[2, 3] = 1, 1, 1
    assert math.isclose(fit.f_stat, float(res.f_test(r).fvalue), rel_tol=1e-9)
    assert np.allclose(fit.long_run, [0.8, 0.5], atol=0.1)  # recovers the levels relation


def test_select_ardl_finds_cointegration_and_its_absence() -> None:
    rng = np.random.default_rng(3)
    y, xs = _coint(rng)
    assert select_ardl(y, xs, max_lag=4).f_stat > 4.85  # beyond the PSS 5 % I(1) bound
    walk = rng.standard_normal((500, 3)).cumsum(0)
    assert select_ardl(walk[:, 0], walk[:, 1:], max_lag=4).f_stat < 4.85


def test_fmols_and_dols_recover_known_coefficients() -> None:
    rng = np.random.default_rng(4)
    y, xs = _coint(rng, n=2000)
    for fit in (fmols(y, xs), dols(y, xs)):
        assert np.allclose(fit.coef[1:], [0.8, 0.5], atol=0.05)
        assert np.all(np.abs(fit.coef[1:] - [0.8, 0.5]) < 4 * fit.se[1:])


def test_ar_polynomial_and_half_life() -> None:
    assert half_life(np.array([0.5])) == 1.0
    assert half_life(np.array([0.9])) == math.ceil(math.log(0.5) / math.log(0.9))
    assert half_life(np.array([1.0])) == math.inf
    # UECM Δy = -0.1 y_{t-1} + 0.3 Δy_{t-1} implies y_t = 1.2 y_{t-1} - 0.3 y_{t-2}
    rng = np.random.default_rng(5)
    y, x = np.zeros(3000), rng.standard_normal((3000, 1)).cumsum(0)
    e = rng.standard_normal(3000)
    for t in range(2, 3000):
        y[t] = 1.2 * y[t - 1] - 0.3 * y[t - 2] + e[t]
    a = ar_polynomial(fit_ardl(y, x, p=2, q=1))
    assert np.allclose(a, [1.2, -0.3], atol=0.05)


def test_bootstrap_half_life_covers_truth() -> None:
    rng = np.random.default_rng(6)
    n = 400
    x = rng.standard_normal((n, 1)).cumsum(0)
    y, e = np.zeros(n), rng.standard_normal(n)
    for t in range(1, n):
        y[t] = 0.9 * y[t - 1] + 0.1 * x[t - 1, 0] + e[t]  # half-life 7 months
    fit = fit_ardl(y, x, p=1, q=1)
    hl = bootstrap_half_life(y, x, fit, draws=199, seed=1)
    lo, hi = np.quantile(hl, [0.05, 0.95])
    assert lo <= 7 <= hi


def test_cpi_checksums_are_exactly_the_adr_0008_table() -> None:
    adr = (ROOT / "docs/decisions/0008-h1b-long-run-protocol.md").read_text()
    for rel, digest in CPI_SHA256.items():
        assert re.search(rf"\| {re.escape(rel)} \| `{digest}`", adr), rel


def test_calendar_terms_place_seasonal_and_lagged_tax_impulses() -> None:
    idx = pd.period_range("1981-01", "2021-12", freq="M")
    z = calendar_terms(idx, p=2, qs=(3, 1), tax_lags="q0")
    assert z.shape == (len(idx), 11 + 4 * 3)  # 11 centred months + 4 tax months x q_x = 3
    assert np.allclose(z[:, :11].mean(0), 0)
    hits = idx[z[:, 11:].sum(1) > 0].astype(str).tolist()
    assert hits[:3] == ["1989-04", "1989-05", "1989-06"] and len(hits) == 12
    assert calendar_terms(idx, p=2, qs=(3, 1), tax_lags="none").shape[1] == 11


def test_independent_orders_and_extra_terms_match_statsmodels() -> None:
    rng = np.random.default_rng(7)
    y, xs = _coint(rng, n=492)
    idx = pd.period_range("1981-01", periods=492, freq="M")
    extra = calendar_terms(idx, p=2, qs=(3, 1), tax_lags="q0")
    fit = fit_ardl(y, xs, p=2, q=(3, 1), start=12, extra=extra)
    yv, z = _uecm_design(y, xs, 2, (3, 1), 12)
    ex = extra[12:]
    res = sm.OLS(yv, np.column_stack([z, ex[:, np.abs(ex).sum(0) > 0]])).fit()
    assert z.shape[1] == 1 + 3 + 1 + 3 + 1  # const, levels, one Δy lag, 3 Δx1, 1 Δx2
    assert np.allclose(fit.fitted_coef, res.params) and fit.nobs == 480
    r = np.zeros((3, len(res.params)))
    r[0, 1], r[1, 2], r[2, 3] = 1, 1, 1
    assert math.isclose(fit.f_stat, float(res.f_test(r).fvalue), rel_tol=1e-9)
