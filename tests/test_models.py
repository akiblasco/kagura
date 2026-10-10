"""Synthetic-data checks of the ADR 0006 H1a test. No real KAGURA data is used."""

import math

import matplotlib
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from kagura.align import build_daily
from kagura.explore import changes
from kagura.models import (
    ALPHA,
    DAILY_END,
    MONTHLY_END,
    NEW,
    REF,
    C,
    Directional,
    EraFit,
    LegTest,
    chi2_sf,
    contrast,
    era_equality,
    era_regression,
    fieller,
    h1a_test,
    hac_lag,
    leg_changes,
    leg_spread,
    monthly_changes,
    opposite_legs,
    plot_rolling_beta,
    rejects_above,
    rejects_below,
    robustness_label,
    rolling_beta,
    two_leg_regression,
)

matplotlib.use("Agg")  # headless plotting in tests


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


# --- Stage 2: secondary and descriptive analyses (ADR 0006 §6, §9.1) --------------------------

ERA_STARTS = {
    "1981–1989": "1981-01-01",
    "1990–1998": "1990-01-01",
    "1999–2012": "1999-01-01",
    REF: "2013-01-01",
    NEW: "2022-01-03",
}


def five_eras(betas: list[float], n: int = 400, noise: float = 0.5, seed: int = 0) -> pd.DataFrame:
    """Changes table with ``n`` rows in each ADR 0004 era and a known slope per era."""
    rng = np.random.default_rng(seed)
    parts = []
    for start, beta in zip(ERA_STARTS.values(), betas, strict=True):
        x = rng.normal(scale=0.05, size=n)
        y = beta * x + rng.normal(scale=noise, size=n)
        parts.append(pd.DataFrame({"date": pd.bdate_range(start, periods=n), "dfx": y, "ddiff": x}))
    return pd.concat(parts, ignore_index=True)


@pytest.mark.parametrize(
    ("df", "critical"),
    [
        (1, 3.841458820694124),
        (2, 5.991464547107979),
        (3, 7.814727903251178),
        (4, 9.487729036781154),
        (5, 11.070497693516351),
    ],
)
def test_chi2_sf_matches_published_5pct_critical_values(df: int, critical: float) -> None:
    assert chi2_sf(critical, df) == pytest.approx(0.05, rel=1e-9)
    assert chi2_sf(0.0, df) == 1.0
    assert chi2_sf(1e4, df) == 0.0  # underflows cleanly, no error


def test_chi2_sf_df1_is_two_sided_normal_p() -> None:
    for z in (0.5, 1.959964, 3.0, 8.0):
        assert chi2_sf(z**2, 1) == pytest.approx(math.erfc(z / math.sqrt(2)), rel=1e-12)
    with pytest.raises(ValueError):
        chi2_sf(1.0, 0)


def test_era_equality_matches_statsmodels_wald_test() -> None:
    ch = five_eras([6.0, 5.0, 4.0, 6.0, 3.0], seed=1)
    fit = era_regression(ch)
    w = era_equality(fit)
    assert w.df == 4  # five eras: the frozen chi2(4) test
    # Independent reference: statsmodels' own Wald test on the same HAC fit.
    res = sm.OLS(ch["dfx"].to_numpy(), fit_design(ch)).fit(
        cov_type="HAC", cov_kwds={"maxlags": fit.lag, "use_correction": False}
    )
    r = np.zeros((4, 10))
    for i in range(4):
        r[i, 2 * i + 1], r[i, 2 * i + 3] = 1.0, -1.0
    ref = res.wald_test(r, scalar=True, use_f=False)
    assert w.stat == pytest.approx(float(ref.statistic), rel=1e-8)
    assert w.p == pytest.approx(float(ref.pvalue), rel=1e-6)


def fit_design(ch: pd.DataFrame) -> np.ndarray:
    """alpha/beta columns per era in ADR 0004 order, built independently of models.py."""
    cols = []
    bounds = list(ERA_STARTS.values()) + ["2100-01-01"]
    for lo, hi in zip(bounds, bounds[1:], strict=False):
        on = ((ch["date"] >= lo) & (ch["date"] < hi)).to_numpy(dtype=float)
        cols += [on, on * ch["ddiff"].to_numpy()]
    return np.column_stack(cols)


def test_era_equality_detects_unequal_slopes_and_accepts_equal_ones() -> None:
    assert era_equality(era_regression(five_eras([6.0, 6.0, 6.0, 6.0, 2.0], seed=2))).rejects
    equal = era_equality(era_regression(five_eras([5.0] * 5, seed=3)))
    assert not equal.rejects and equal.df == 4


def test_era_equality_requires_all_five_eras() -> None:
    with pytest.raises(ValueError, match="all five eras"):
        era_equality(era_regression(synthetic(6.0, 4.0)))  # only ref and new
    four = five_eras([6.0, 5.0, 4.0, 6.0, 3.0])
    with pytest.raises(ValueError, match="all five eras"):
        era_equality(era_regression(four[four["date"] >= "1990-01-01"].reset_index(drop=True)))


def within_se(fit: EraFit, name: str, truth: float, k: float = 4.0) -> bool:
    """Estimate within k HAC standard errors of the true value (a 4-se miss is ~1 in 16,000)."""
    return abs(float(fit.params[name]) - truth) < k * math.sqrt(fit.covariance(name, name))


# two-leg decomposition


def leg_daily(n: int = 300, holiday: bool = True, seed: int = 8) -> pd.DataFrame:
    """Aligned daily table (via build_daily) in the ref and new eras, with Tokyo holidays."""
    rng = np.random.default_rng(seed)
    days = list(pd.bdate_range("2021-01-04", periods=n)) + list(
        pd.bdate_range("2022-03-01", periods=n)
    )
    us = 1.0 + rng.normal(scale=0.05, size=len(days)).cumsum()
    jgb = 0.2 + rng.normal(scale=0.02, size=len(days)).cumsum()
    dus, djgb = np.diff(us, prepend=us[0]), np.diff(jgb, prepend=jgb[0])
    dfx = 5.0 * dus - 2.0 * djgb + rng.normal(scale=0.2, size=len(days))  # in %
    fx = 110 * np.exp(np.cumsum(dfx) / 100)
    skip = {days[30], days[n + 40]} if holiday else set()
    rows = [(d, "usdjpy", f) for d, f in zip(days, fx, strict=True)]
    rows += [(d, "us_2y", u) for d, u in zip(days, us, strict=True)]
    rows += [(d, "jgb_2y", j) for d, j in zip(days, jgb, strict=True) if d not in skip]
    return build_daily(pd.DataFrame(rows, columns=["date", "series", "value"]))


def test_leg_changes_reproduce_the_primary_differential_and_exclusions() -> None:
    daily = leg_daily()
    legs, ch = leg_changes(daily, "2y"), changes(daily, "2y", "same-day")
    pd.testing.assert_series_equal(legs["dus"] - legs["djgb"], ch["ddiff"], check_names=False)
    pd.testing.assert_series_equal(legs["dfx"].isna(), ch["dfx"].isna(), check_names=False)
    assert legs["dfx"].isna().sum() == 1 + 4  # first row, and 2 rows per holiday


def test_two_leg_recovers_known_coefficients_and_tests_opposite_signs() -> None:
    fit = two_leg_regression(leg_changes(leg_daily(), "2y"))
    for e in (REF, NEW):
        assert within_se(fit, f"beta_us:{e}", 5.0)
        assert within_se(fit, f"beta_jp:{e}", -2.0)
    tests = opposite_legs(fit)
    assert set(tests) == {REF, NEW}
    for t in tests.values():  # 5 + (-2) != 0
        assert t.identified and t.wald is not None and t.total is not None
        assert t.wald.df == 1 and t.wald.rejects
        assert t.wald.stat == pytest.approx((t.total.estimate / t.total.se) ** 2)
    assert fit.n.sum() == 2 * 300 - 1 - 4
    assert math.isnan(fit.r2[REF])  # not defined for the two-leg fit


def test_opposite_legs_does_not_reject_a_pure_differential() -> None:
    rng = np.random.default_rng(9)
    n = 800
    dates = list(pd.bdate_range("2013-01-01", periods=n)) + list(
        pd.bdate_range("2022-01-03", periods=n)
    )
    dus, djgb = rng.normal(scale=0.05, size=2 * n), rng.normal(scale=0.05, size=2 * n)
    dfx = 4.0 * (dus - djgb) + rng.normal(scale=0.3, size=2 * n)
    fit = two_leg_regression(pd.DataFrame({"date": dates, "dfx": dfx, "dus": dus, "djgb": djgb}))
    for e, t in opposite_legs(fit).items():
        assert t.wald is not None and t.total is not None
        assert not t.wald.rejects, e
        assert t.total.lower < 0 < t.total.upper
        b = fit.params[f"beta_us:{e}"] + fit.params[f"beta_jp:{e}"]
        se = math.sqrt(
            fit.covariance(f"beta_us:{e}", f"beta_us:{e}")
            + fit.covariance(f"beta_jp:{e}", f"beta_jp:{e}")
            + 2 * fit.covariance(f"beta_us:{e}", f"beta_jp:{e}")
        )
        assert t.wald.stat == pytest.approx((b / se) ** 2)  # includes 2 Cov(us, jp)
        assert t.total.se == pytest.approx(se)


def test_nearly_constant_leg_is_identified_but_visibly_imprecise() -> None:
    rng = np.random.default_rng(10)
    n = 500
    dates = list(pd.bdate_range("2013-01-01", periods=n)) + list(
        pd.bdate_range("2022-01-03", periods=n)
    )
    dus = rng.normal(scale=0.05, size=2 * n)
    djgb = np.where(np.arange(2 * n) < n, 1e-4, 0.05) * rng.normal(size=2 * n)
    legs = pd.DataFrame(
        {
            "date": dates,
            "dfx": 4 * dus + rng.normal(scale=0.3, size=2 * n),
            "dus": dus,
            "djgb": djgb,
        }
    )
    fit = two_leg_regression(legs)
    se_ref = math.sqrt(fit.covariance(f"beta_jp:{REF}", f"beta_jp:{REF}"))
    se_new = math.sqrt(fit.covariance(f"beta_jp:{NEW}", f"beta_jp:{NEW}"))
    assert math.isfinite(se_ref) and se_ref > 100 * se_new  # pinned leg: imprecise, not broken
    ref = opposite_legs(fit)[REF]
    assert ref.identified and ref.total is not None and ref.wald is not None
    # The truth (beta_jp = 0, so beta_us + beta_jp = 4) is far from 0, yet the test cannot
    # reject: the interval is what shows the non-rejection is uninformative.
    assert not ref.wald.rejects and ref.total.upper - ref.total.lower > 100
    spread = leg_spread(legs)
    sd = spread["sd_djgb"].to_dict()
    assert sd[REF] < 1e-3 < sd[NEW]
    assert spread["n"].tolist() == [n, n]


def constant_leg_legs(n: int = 500, seed: int = 16) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = list(pd.bdate_range("2013-01-01", periods=n)) + list(
        pd.bdate_range("2022-01-03", periods=n)
    )
    dus, djgb = rng.normal(scale=0.05, size=2 * n), rng.normal(scale=0.05, size=2 * n)
    dfx = 4 * dus - 3 * djgb + rng.normal(scale=0.3, size=2 * n)
    return pd.DataFrame({"date": dates, "dfx": dfx, "dus": dus, "djgb": djgb})


def test_constant_leg_is_reported_unidentified_not_silently_tested() -> None:
    legs = constant_leg_legs()
    legs.loc[:499, "djgb"] = 0.0  # JGB leg exactly pinned in the reference era
    fit = two_leg_regression(legs)
    assert f"beta_jp:{REF}" not in fit.params.index  # not estimated from rounding noise
    assert within_se(fit, f"beta_us:{REF}", 4.0)  # the US leg is still identified there
    tests = opposite_legs(fit)
    assert tests[REF] == LegTest(False, None, None)  # explicit: no estimate, no test
    new_wald = tests[NEW].wald
    assert tests[NEW].identified and new_wald is not None and new_wald.rejects
    assert within_se(fit, f"beta_jp:{NEW}", -3.0)


def test_collinear_legs_leave_both_slopes_unidentified() -> None:
    legs = constant_leg_legs()
    legs.loc[:499, "djgb"] = -legs.loc[:499, "dus"]  # JGB moves exactly opposite to the US
    fit = two_leg_regression(legs)
    assert not {f"beta_us:{REF}", f"beta_jp:{REF}"} & set(fit.params.index)
    assert not opposite_legs(fit)[REF].identified
    assert opposite_legs(fit)[NEW].identified


def test_primary_regression_still_errors_on_rank_deficiency() -> None:
    # Unlike the descriptive two-leg fit, the confirmatory regression never drops columns.
    ch = synthetic(6.0, 4.0)
    ch.loc[ch["date"] < "2022-01-01", "ddiff"] = 0.0
    with pytest.raises(ValueError, match="rank deficient"):
        era_regression(ch)


# rolling beta


def test_rolling_beta_exact_slope_and_80pct_rule() -> None:
    rng = np.random.default_rng(11)
    x = rng.normal(scale=0.05, size=400)
    ch = pd.DataFrame(
        {"date": pd.bdate_range("2013-01-01", periods=400), "dfx": 0.1 + 3.0 * x, "ddiff": x}
    )
    ch.loc[10:39, "ddiff"] = np.nan  # 30 excluded rows
    rb = rolling_beta(ch, 100)
    # Window ending at row 118 covers rows 19..118: 21 excluded, 79 usable (< 80) → not
    # reported. Ending at 119: 20 excluded, exactly 80 usable → reported.
    assert math.isnan(rb["beta"].iloc[118])
    assert rb["beta"].iloc[119] == pytest.approx(3.0) and rb["n"].iloc[119] == 80
    done = rb.dropna(subset=["beta"])
    np.testing.assert_allclose(done["beta"], 3.0, rtol=1e-9)
    np.testing.assert_allclose(done["r2"], 1.0, rtol=1e-9)


def test_rolling_beta_matches_window_ols_with_noise() -> None:
    ch = synthetic(6.0, 4.0, n_ref=500, n_new=300, seed=12)
    ch.loc[[50, 51, 52, 700], "ddiff"] = np.nan
    rb = rolling_beta(ch, 250)
    for end in (300, 499, 620, 799):
        w = ch.iloc[end - 249 : end + 1].dropna()
        slope = np.polyfit(w["ddiff"], w["dfx"], 1)[0]
        assert rb["beta"].iloc[end] == pytest.approx(slope, rel=1e-9)
        assert rb["r2"].iloc[end] == pytest.approx(w["dfx"].corr(w["ddiff"]) ** 2, rel=1e-9)


def test_rolling_beta_flat_window_is_nan_and_sample_end_applies() -> None:
    ch = synthetic(6.0, 4.0, n_ref=300, n_new=300)
    ch.loc[:299, "ddiff"] = 0.0
    rb = rolling_beta(ch, 250)
    assert rb["beta"].iloc[249:300].isna().all()  # zero-variance windows: NaN, never inf
    assert not np.isinf(rb["beta"]).any()
    late = pd.DataFrame({"date": pd.bdate_range("2026-09-14", periods=5), "dfx": 1.0, "ddiff": 1.0})
    tail = rolling_beta(pd.concat([ch, late], ignore_index=True), 250)
    assert tail["date"].max() <= pd.Timestamp(DAILY_END)


def test_plot_rolling_beta_draws_both_windows() -> None:
    import matplotlib.pyplot as plt

    ch = synthetic(6.0, 4.0, n_ref=1500, n_new=800)
    ch.loc[600:900, "ddiff"] = np.nan  # windows over this block fail the 80% rule
    fig = plot_rolling_beta(ch)
    top, bottom = fig.axes
    assert len(top.get_lines()) >= 2 and len(bottom.get_lines()) >= 2
    # Unreported windows are plotted as NaN, so the line breaks instead of bridging the gap.
    one_year = np.asarray(top.get_lines()[0].get_ydata(), dtype=float)
    assert np.isnan(one_year[700:900]).all() and np.isfinite(one_year[-1])
    plt.close(fig)


# monthly robustness (R2)


def month_ends(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="BME")


def test_monthly_changes_dates_values_gaps_and_carried_flags() -> None:
    dates = month_ends("1980-11-01", "2026-10-31")
    rng = np.random.default_rng(13)
    monthly = pd.DataFrame(
        {
            "date": dates,
            "usdjpy": 100 * np.exp(rng.normal(scale=0.02, size=len(dates)).cumsum()),
            "diff_2y": rng.normal(size=len(dates)).cumsum(),
            "diff_2y_carried": True,  # must be ignored (§9.1)
        }
    )
    gap = monthly.index[monthly["date"] == pd.Timestamp("2005-06-30")][0]
    monthly.loc[gap, "diff_2y"] = np.nan
    ch = monthly_changes(monthly.sample(frac=1, random_state=0), "2y")  # unsorted input
    assert ch["date"].min() == pd.Timestamp("1981-01-30")  # Jan 1981 change uses Dec 1980
    assert ch["date"].max() == pd.Timestamp("2026-08-31") <= pd.Timestamp(MONTHLY_END)
    i = ch.index[ch["date"] == pd.Timestamp("1990-03-30")][0]
    fx = monthly.set_index("date")["usdjpy"].to_dict()
    expected = 100 * math.log(fx[pd.Timestamp("1990-03-30")] / fx[pd.Timestamp("1990-02-28")])
    assert ch["dfx"].to_numpy()[i] == pytest.approx(expected)
    gaps = ch.loc[ch["ddiff"].isna(), "date"].dt.strftime("%Y-%m").tolist()
    assert gaps == ["2005-06", "2005-07"]  # no bridging over the missing month
    assert ch["dfx"].notna().all()


def test_monthly_changes_feed_the_primary_regression_with_month_end_eras() -> None:
    dates = month_ends("1980-12-01", "2026-08-31")
    rng = np.random.default_rng(14)
    dd = rng.normal(scale=0.2, size=len(dates))
    dfx = 4.0 * dd + rng.normal(scale=1.0, size=len(dates))
    monthly = pd.DataFrame(
        {"date": dates, "usdjpy": 200 * np.exp(np.cumsum(dfx) / 100), "diff_2y": np.cumsum(dd)}
    )
    ch = monthly_changes(monthly, "2y")
    fit = era_regression(ch)
    assert fit.n[REF] == 108 and fit.n[NEW] == 56  # 2013-01..2021-12, 2022-01..2026-08
    assert fit.lag == hac_lag(len(ch)) == 5
    assert within_se(fit, f"beta:{REF}", 4.0)
    assert h1a_test(fit).outcome in {"supported", "ruled out", "inconclusive", "not assessable"}


# robustness R1 (lagged US leg) and R3 (10Y) through the unchanged primary functions


def test_lagged_and_ten_year_variants_run_through_primary_functions() -> None:
    rng = np.random.default_rng(15)
    n = 400
    days = list(pd.bdate_range("2020-06-01", periods=n)) + list(
        pd.bdate_range("2022-01-03", periods=n)
    )
    us = 2.0 + rng.normal(scale=0.06, size=2 * n).cumsum()
    jgb = 0.5 + rng.normal(scale=0.03, size=2 * n).cumsum()
    lag_diff = np.zeros(2 * n)  # (us[t-1] - us[t-2]) - (jgb[t] - jgb[t-1])
    lag_diff[2:] = (us[1:-1] - us[:-2]) - (jgb[2:] - jgb[1:-1])
    dfx = 4.0 * lag_diff + rng.normal(scale=0.1, size=2 * n)
    fx = 110 * np.exp(np.cumsum(dfx) / 100)
    rows = [(d, "usdjpy", f) for d, f in zip(days, fx, strict=True)]
    rows += [(d, "us_10y", u) for d, u in zip(days, us, strict=True)]
    rows += [(d, "jgb_10y", j) for i, (d, j) in enumerate(zip(days, jgb, strict=True)) if i != 500]
    daily = build_daily(pd.DataFrame(rows, columns=["date", "series", "value"]))

    lagged = changes(daily, "10y", "lagged")
    fit = era_regression(lagged)
    assert within_se(fit, f"beta:{REF}", 4.0) and within_se(fit, f"beta:{NEW}", 4.0)
    # Rows: 2n minus 2 (no lagged change at the start) minus 2 (JGB holiday and the row after).
    assert fit.nobs == lagged.dropna().shape[0] == 2 * n - 2 - 2
    assert h1a_test(fit).outcome == "ruled out"  # beta unchanged across eras
    # The same-day variant is a different estimand. Only the shared JGB leg links it to this
    # DGP: beta = 4 Var(djgb) / (Var(dus) + Var(djgb)) = 4 * 0.03^2 / (0.06^2 + 0.03^2) = 0.8.
    same_day = era_regression(changes(daily, "10y", "same-day"))
    assert within_se(same_day, f"beta:{REF}", 0.8) and within_se(same_day, f"beta:{NEW}", 0.8)


# --- review additions -------------------------------------------------------------------------


def test_stage1_numbers_unchanged_by_stage2_refactor() -> None:
    # Pinned from the committed Stage 1 module (9bf1df9) on this synthetic draw.
    r = h1a_test(era_regression(synthetic(6.0, 4.0, seed=21)))
    assert r.beta_ref.estimate == pytest.approx(6.493531793802314, rel=1e-12)
    assert r.beta_ref.se == pytest.approx(0.37867031326016565, rel=1e-12)
    assert r.delta.estimate == pytest.approx(-0.3344283851962002, rel=1e-12)
    assert r.delta.se == pytest.approx(0.32706304012302495, rel=1e-12)
    assert r.delta.p_below == pytest.approx(0.15326750869594918, rel=1e-12)
    assert (r.outcome, r.lag) == ("inconclusive", 8)


def test_rolling_counts_at_sample_start_and_inside_windows() -> None:
    rng = np.random.default_rng(17)
    x = rng.normal(scale=0.05, size=600)
    ch = pd.DataFrame(
        {"date": pd.bdate_range("1981-01-01", periods=600), "dfx": 2.0 * x, "ddiff": x}
    )
    ch.loc[[300, 301], "dfx"] = np.nan  # missing FX also removes the row from the window
    rb = rolling_beta(ch, 250)
    # Partial windows at the sample start report once 200 usable rows exist (ADR 0004 rule).
    assert math.isnan(rb["beta"].iloc[198]) and rb["n"].iloc[198] == 199
    assert rb["beta"].iloc[199] == pytest.approx(2.0) and rb["n"].iloc[199] == 200
    assert rb["n"].iloc[249] == 250 and rb["n"].iloc[400] == 248
    assert rb["n"].iloc[551] == 250  # rows 300 and 301 have left the window


def test_monthly_changes_reject_missing_or_duplicate_months() -> None:
    dates = month_ends("1980-12-01", "2026-08-31")
    monthly = pd.DataFrame({"date": dates, "usdjpy": 100.0, "diff_2y": 1.0})
    with pytest.raises(ValueError, match="one per calendar month"):
        monthly_changes(monthly.drop(index=100), "2y")  # a whole month row absent
    with pytest.raises(ValueError, match="one per calendar month"):
        monthly_changes(pd.concat([monthly, monthly.iloc[[5]]]), "2y")
    assert len(monthly_changes(monthly, "2y")) == len(dates) - 1  # Dec 1980 is the base


def test_robustness_results_cannot_stand_in_for_the_primary() -> None:
    primary = h1a_test(era_regression(synthetic(6.0, 2.0, noise=0.2)))
    same = h1a_test(era_regression(synthetic(6.0, 2.0, noise=0.2, seed=1)), spec="R1")
    other = h1a_test(era_regression(synthetic(6.0, 6.0, noise=0.2)), spec="R2")
    r3 = h1a_test(era_regression(synthetic(6.0, 2.0, noise=0.2, seed=2)), spec="R3")
    assert primary.spec == "primary" and primary.outcome == "supported"
    assert robustness_label(primary, [same, r3, other]) == "sensitive to R2 (ruled out)"
    r2 = h1a_test(era_regression(synthetic(6.0, 2.0, noise=0.2, seed=3)), spec="R2")
    assert robustness_label(primary, [same, r2, r3]) == "robust"
    with pytest.raises(ValueError, match="primary"):
        robustness_label(same, [primary, r2, r3])
    with pytest.raises(ValueError, match="exactly one"):
        robustness_label(primary, [same, r3])
