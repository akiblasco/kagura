"""Synthetic-data checks of the ADR 0006 H1a test. No real KAGURA data is used."""

import math

import numpy as np
import pandas as pd
import pytest

from kagura.align import build_daily
from kagura.explore import changes
from kagura.models import (
    ALPHA,
    DAILY_END,
    NEW,
    REF,
    C,
    Directional,
    EraFit,
    contrast,
    era_regression,
    fieller,
    h1a_test,
    hac_lag,
    rejects_above,
    rejects_below,
)


def synthetic(
    beta_ref: float,
    beta_new: float,
    n_ref: int = 2000,
    n_new: int = 1000,
    noise: float = 0.5,
    sd_x: tuple[float, float] = (0.03, 0.07),
    seed: int = 0,
) -> pd.DataFrame:
    """Changes table with a known slope per era: dfx = 0.01 + beta * ddiff + noise."""
    rng = np.random.default_rng(seed)
    parts = []
    for start, n, beta, sx in (
        ("2013-01-01", n_ref, beta_ref, sd_x[0]),
        ("2022-01-03", n_new, beta_new, sd_x[1]),
    ):
        x = rng.normal(scale=sx, size=n)
        y = 0.01 + beta * x + rng.normal(scale=noise, size=n)
        parts.append(pd.DataFrame({"date": pd.bdate_range(start, periods=n), "dfx": y, "ddiff": x}))
    return pd.concat(parts, ignore_index=True)


def manual_newey_west(x: np.ndarray, e: np.ndarray, lag: int) -> np.ndarray:
    """Textbook Newey–West (1987) sandwich, Bartlett weights 1 - l/(lag+1), no correction."""
    s = x * e[:, None]
    meat = s.T @ s
    for lv in range(1, lag + 1):
        gamma = s[lv:].T @ s[:-lv]
        meat += (1 - lv / (lag + 1)) * (gamma + gamma.T)
    bread = np.linalg.inv(x.T @ x)
    return np.asarray(bread @ meat @ bread)


# --- regression mechanics ---------------------------------------------------------------------


def test_hac_lag_rule() -> None:
    assert C == pytest.approx(1.959964, abs=1e-6)
    assert hac_lag(100) == 4
    assert hac_lag(548) == 5  # monthly robustness, ADR 0006 §4.4
    assert hac_lag(10_279) == 11  # daily primary


def test_coefficients_match_separate_era_ols_and_r2_is_squared_correlation() -> None:
    ch = synthetic(6.0, 3.0)
    fit = era_regression(ch)
    for era, rows in ((REF, ch.iloc[:2000]), (NEW, ch.iloc[2000:])):
        slope, intercept = np.polyfit(rows["ddiff"], rows["dfx"], 1)
        assert fit.beta(era) == pytest.approx(slope, rel=1e-10)
        assert fit.params[f"alpha:{era}"] == pytest.approx(intercept, rel=1e-8)
        assert fit.r2[era] == pytest.approx(rows["dfx"].corr(rows["ddiff"]) ** 2, rel=1e-10)
    assert fit.n.to_dict() == {REF: 2000, NEW: 1000}
    assert fit.lag == hac_lag(3000)


def test_hac_covariance_matches_manual_newey_west() -> None:
    rng = np.random.default_rng(3)
    ch = synthetic(5.0, 4.0, n_ref=300, n_new=200, seed=3)
    # AR(1) errors with a variance shift, so HAC and plain OLS covariances differ.
    e = np.zeros(len(ch))
    for t in range(1, len(ch)):
        e[t] = 0.4 * e[t - 1] + rng.normal(scale=0.3 if t < 300 else 0.8)
    ch["dfx"] = 5.0 * ch["ddiff"] + e
    fit = era_regression(ch)
    on_ref = (np.arange(len(ch)) < 300).astype(float)
    x = np.column_stack([on_ref, on_ref * ch["ddiff"], 1 - on_ref, (1 - on_ref) * ch["ddiff"]])
    b = np.linalg.lstsq(x, ch["dfx"].to_numpy(), rcond=None)[0]
    expected = manual_newey_west(x, ch["dfx"].to_numpy() - x @ b, hac_lag(len(ch)))
    order = [f"alpha:{REF}", f"beta:{REF}", f"alpha:{NEW}", f"beta:{NEW}"]
    np.testing.assert_allclose(fit.cov.loc[order, order].to_numpy(), expected, rtol=1e-8)


def test_contrast_bounds_and_pvalues_by_hand() -> None:
    fit = era_regression(synthetic(6.0, 4.0, seed=5))
    d = h1a_test(fit).delta
    n, r = f"beta:{NEW}", f"beta:{REF}"
    var = (
        fit.covariance(n, n)
        + (2 / 3) ** 2 * fit.covariance(r, r)
        - 2 * (2 / 3) * fit.covariance(n, r)
    )
    assert d.estimate == pytest.approx(fit.beta(NEW) - (2 / 3) * fit.beta(REF))
    assert d.se == pytest.approx(math.sqrt(var))
    assert (d.lower, d.upper) == pytest.approx((d.estimate - C * d.se, d.estimate + C * d.se))
    z = d.estimate / d.se
    assert d.p_below == pytest.approx(0.5 * math.erfc(-z / math.sqrt(2)))
    assert d.p_above == pytest.approx(1 - d.p_below)


# --- decision outcomes ------------------------------------------------------------------------


def test_known_positive_slopes_are_recovered() -> None:
    r = h1a_test(era_regression(synthetic(5.0, 5.0, noise=0.2)))
    assert r.gate
    assert r.beta_ref.lower < 5.0 < r.beta_ref.upper
    assert r.beta_new.lower < 5.0 < r.beta_new.upper
    assert r.implied_100bp_narrowing[REF] == pytest.approx(-r.beta_ref.estimate)


def test_material_decline_is_supported() -> None:
    r = h1a_test(era_regression(synthetic(6.0, 2.0, noise=0.2)))
    assert r.outcome == "supported"
    assert r.delta.upper < 0 and r.delta.p_below < ALPHA
    assert r.absolute_change.estimate == pytest.approx(r.beta_new.estimate - r.beta_ref.estimate)
    assert r.relative_change == pytest.approx(r.beta_new.estimate / r.beta_ref.estimate - 1)


@pytest.mark.parametrize("beta_new", [6.0, 9.0])  # unchanged, and an increase
def test_no_material_decline_is_ruled_out(beta_new: float) -> None:
    r = h1a_test(era_regression(synthetic(6.0, beta_new, noise=0.2)))
    assert r.outcome == "ruled out"
    assert r.delta.lower > 0 and r.delta.p_above < ALPHA


def test_negative_new_slope_counts_as_material_decline() -> None:
    r = h1a_test(era_regression(synthetic(6.0, -3.0, noise=0.2)))
    assert r.beta_new.upper < 0
    assert r.outcome == "supported"
    assert r.relative_change < -1
    assert r.implied_100bp_narrowing[NEW] > 0


def test_decline_of_exactly_one_third_is_inconclusive_with_noisy_data() -> None:
    r = h1a_test(era_regression(synthetic(6.0, 4.0, noise=1.0, seed=11)))
    assert r.gate
    assert r.delta.lower < 0 < r.delta.upper
    assert r.outcome == "inconclusive"


@pytest.mark.parametrize("beta_ref", [0.0, -4.0])
def test_gate_fails_for_zero_or_negative_reference(beta_ref: float) -> None:
    r = h1a_test(era_regression(synthetic(beta_ref, 2.0, noise=1.0)))
    assert not r.gate
    assert r.beta_ref.lower <= 0 and r.beta_ref.p_above >= ALPHA
    assert r.outcome == "not assessable"


def test_gate_failure_overrides_a_significant_s() -> None:
    # beta_ref ~ 0 and beta_new strongly negative: S rejects, but the gate decides.
    r = h1a_test(era_regression(synthetic(0.0, -8.0, noise=1.0)))
    assert r.s_rejects and not r.gate
    assert r.outcome == "not assessable"


def test_s_and_r_never_both_reject_and_bounds_agree_with_pvalues() -> None:
    rng = np.random.default_rng(42)
    for seed in range(150):
        br, bn = rng.uniform(-2, 8), rng.uniform(-4, 10)
        r = h1a_test(era_regression(synthetic(br, bn, n_ref=200, n_new=100, noise=0.6, seed=seed)))
        assert not (r.s_rejects and r.r_rejects)
        assert r.s_rejects == (r.delta.upper < 0)
        assert r.r_rejects == (r.delta.lower > 0)
        assert r.gate == (r.beta_ref.lower > 0)
        for d in (r.delta, r.beta_ref, *r.sensitivity.values()):
            assert d.p_below + d.p_above == pytest.approx(1.0)


def test_one_sided_rejection_rates_at_the_boundary() -> None:
    # True delta = 0 (a decline of exactly 1/3): S and R should each reject ~2.5%.
    s = r_ = 0
    reps = 400
    for seed in range(reps):
        res = h1a_test(
            era_regression(synthetic(6.0, 4.0, n_ref=400, n_new=200, noise=0.6, seed=seed))
        )
        s += res.s_rejects
        r_ += res.r_rejects
    for rate in (s / reps, r_ / reps):
        # Gross check only: 400 reps cannot pin size precisely (Monte Carlo se ~0.8pp).
        assert 0.005 <= rate <= 0.05


def test_sensitivity_thresholds_use_their_own_weights() -> None:
    fit = era_regression(synthetic(6.0, 4.0))
    r = h1a_test(fit)
    for decline, d in r.sensitivity.items():
        assert d.estimate == pytest.approx(fit.beta(NEW) - (1 - decline) * fit.beta(REF))
    assert set(r.sensitivity) == {0.25, 0.5}


# --- Fieller set for the relative change ------------------------------------------------------


def in_fieller(ratio: float, fit: EraFit) -> bool:
    """Direct check of the Fieller inequality at one ratio value."""
    n, r = f"beta:{NEW}", f"beta:{REF}"
    lhs = (fit.beta(NEW) - ratio * fit.beta(REF)) ** 2
    vnn, vrr, vnr = fit.covariance(n, n), fit.covariance(r, r), fit.covariance(n, r)
    return lhs <= C**2 * (vnn - 2 * ratio * vnr + ratio**2 * vrr)


@pytest.mark.parametrize(("beta_ref", "noise"), [(6.0, 0.5), (0.3, 1.0)])
def test_fieller_set_matches_brute_force(beta_ref: float, noise: float) -> None:
    fit = era_regression(synthetic(beta_ref, 3.0, noise=noise, seed=2))
    intervals = fieller(fit)
    for ratio in np.linspace(-60, 60, 4001):
        inside = any(lo <= ratio <= hi for lo, hi in intervals)
        assert inside == in_fieller(float(ratio), fit), ratio


def test_fieller_bounded_exactly_when_reference_is_significant() -> None:
    strong = h1a_test(era_regression(synthetic(6.0, 3.0, noise=0.5)))
    assert strong.gate and len(strong.relative_change_set) == 1
    lo, hi = strong.relative_change_set[0]
    assert math.isfinite(lo) and math.isfinite(hi) and lo < strong.relative_change < hi

    weak = h1a_test(era_regression(synthetic(0.0, 3.0, noise=1.0)))
    assert not weak.gate
    assert any(math.isinf(b) for iv in weak.relative_change_set for b in iv)


# --- data handling ----------------------------------------------------------------------------


def test_missing_and_holiday_rows_are_dropped_and_rest_treated_as_consecutive() -> None:
    rng = np.random.default_rng(7)
    days = list(pd.bdate_range("2021-06-01", periods=150)) + list(
        pd.bdate_range("2022-03-01", periods=150)
    )
    us = 1.0 + rng.normal(scale=0.05, size=len(days)).cumsum()
    fx = 110 * np.exp((rng.normal(scale=0.005, size=len(days))).cumsum())
    holidays = {days[20], days[200]}  # one Tokyo holiday in each era
    long = pd.DataFrame(
        [(d, "usdjpy", f) for d, f in zip(days, fx, strict=True)]
        + [(d, "us_2y", u) for d, u in zip(days, us, strict=True)]
        + [(d, "jgb_2y", 0.1) for d in days if d not in holidays],
        columns=["date", "series", "value"],
    )
    ch = changes(build_daily(long), "2y", "same-day")
    assert ch["excluded"].sum() == 4  # each holiday row and the row after it

    fit = era_regression(ch)
    usable = ch.dropna(subset=["dfx", "ddiff"])
    assert fit.nobs == len(usable) == len(days) - 1 - 4  # first row has no change
    # The same rows, re-indexed as if consecutive, give an identical fit.
    again = era_regression(usable.reset_index(drop=True))
    pd.testing.assert_series_equal(fit.params, again.params)
    pd.testing.assert_frame_equal(fit.cov, again.cov)


def test_rows_outside_eras_and_after_sample_end_are_ignored() -> None:
    ch = synthetic(6.0, 4.0, n_ref=300, n_new=300)
    early = pd.DataFrame(
        {"date": pd.bdate_range("1975-01-01", periods=50), "dfx": 9.0, "ddiff": 1.0}
    )
    late = pd.DataFrame(
        {"date": pd.bdate_range("2026-09-14", periods=20), "dfx": 9.0, "ddiff": 1.0}
    )
    full = pd.concat([early, ch, late], ignore_index=True)
    assert late["date"].min() > pd.Timestamp(DAILY_END)
    pd.testing.assert_series_equal(era_regression(full).params, era_regression(ch).params)


def test_era_boundaries_follow_adr_0004_dates() -> None:
    # 2021-12-31 belongs to the reference era, 2022-01-03 (first 2022 trading day) to new,
    # and 2026-09-11 (the fixed sample end) is still included.
    ch = synthetic(6.0, 4.0, n_ref=300, n_new=300)
    edge = pd.DataFrame(
        {
            "date": pd.to_datetime(["2021-12-31", "2026-09-11"]),
            "dfx": [0.0, 0.0],
            "ddiff": [0.01, 0.01],
        }
    )
    full = pd.concat([ch, edge], ignore_index=True).sort_values("date", ignore_index=True)
    fit = era_regression(full)
    assert fit.n.to_dict() == {REF: 301, NEW: 301}


def test_missing_era_or_constant_regressor_is_an_error() -> None:
    only_ref = synthetic(6.0, 4.0).iloc[:2000]
    with pytest.raises(ValueError, match="lacks"):
        h1a_test(era_regression(only_ref))
    flat = synthetic(6.0, 4.0)
    flat.loc[flat["date"] >= "2022-01-01", "ddiff"] = 0.0
    with pytest.raises(ValueError, match="rank deficient"):
        era_regression(flat)
    one_row = pd.concat([synthetic(6.0, 4.0).iloc[:2000], synthetic(6.0, 4.0).iloc[[2000]]])
    with pytest.raises(ValueError, match="rank deficient"):
        era_regression(one_row)
    with pytest.raises(ValueError, match="no usable rows"):
        era_regression(flat.assign(dfx=np.nan))


def test_unsorted_or_duplicate_dates_are_rejected() -> None:
    ch = synthetic(6.0, 4.0, n_ref=100, n_new=100)
    with pytest.raises(ValueError, match="strictly increasing"):
        era_regression(ch.iloc[::-1])
    with pytest.raises(ValueError, match="strictly increasing"):
        era_regression(pd.concat([ch, ch.iloc[[-1]]], ignore_index=True))


# --- numerical edge cases ---------------------------------------------------------------------


def directional(estimate: float, se: float) -> Directional:
    return Directional(estimate, se, estimate - C * se, estimate + C * se, 0.0, 0.0)


def test_bound_exactly_zero_is_not_a_rejection() -> None:
    at_zero = Directional(-1.0, 0.5, -2.0, 0.0, 0.025, 0.975)
    assert not rejects_below(at_zero)
    assert not rejects_above(Directional(1.0, 0.5, 0.0, 2.0, 0.975, 0.025))
    assert rejects_below(directional(-1.0, 0.5)) and not rejects_above(directional(-1.0, 0.5))


def test_upper_tail_p_value_keeps_precision() -> None:
    fit = era_regression(synthetic(6.0, 6.0, noise=0.8))
    d = contrast(fit, {f"beta:{REF}": 1.0})
    z = d.estimate / d.se
    assert 9 < z < 30  # 1 - cdf(z) rounds to exactly 0 here; cdf(-z) does not
    assert 0 < d.p_above < 1e-15
    assert d.p_above == pytest.approx(0.5 * math.erfc(z / math.sqrt(2)), rel=1e-9)


def test_degenerate_covariance_is_an_error() -> None:
    fit = era_regression(synthetic(6.0, 4.0, n_ref=200, n_new=200))
    zero = EraFit(fit.params, fit.cov * 0.0, fit.n, fit.r2, fit.lag)
    with pytest.raises(ValueError, match="not positive"):
        contrast(zero, {f"beta:{REF}": 1.0})


@pytest.mark.parametrize("scale", [1.0, 1 + 1e-9, 1 - 1e-9, 1e3])
def test_fieller_near_the_bounded_unbounded_boundary(scale: float) -> None:
    # Choose V_rr so that a = b_ref^2 - C^2 V_rr is ~0 (scale 1), tiny +/-, or very negative.
    fit = era_regression(synthetic(6.0, 3.0, seed=4))
    r = f"beta:{REF}"
    cov = fit.cov.copy()
    cov.loc[r, r] = scale * fit.beta(REF) ** 2 / C**2
    near = EraFit(fit.params, cov, fit.n, fit.r2, fit.lag)
    intervals = fieller(near)
    for lo, hi in intervals:
        assert lo <= hi
    for ratio in np.concatenate([np.linspace(-50, 50, 2001), [-1e6, 1e6]]):
        inside = any(lo <= ratio <= hi for lo, hi in intervals)
        assert inside == in_fieller(float(ratio), near), ratio


def test_r2_is_nan_not_inf_when_dfx_is_constant_in_an_era() -> None:
    ch = synthetic(6.0, 4.0, n_ref=300, n_new=300)
    ch.loc[ch["date"] < "2022-01-01", "dfx"] = 0.25  # no FX variation in the reference era
    fit = era_regression(ch)
    assert math.isnan(fit.r2[REF])
    assert 0 < fit.r2[NEW] < 1
