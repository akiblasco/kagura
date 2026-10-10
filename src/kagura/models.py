"""H1a formal test: era-interacted OLS with Newey–West HAC errors and directional tests.

Every constant here is frozen by docs/decisions/0006-h1-formal-testing-protocol.md (§4–§5).
Do not tune them after seeing results; record any new specification in a new ADR instead.

Input is a changes table with columns ``date``, ``dfx`` (% log change of USD/JPY) and
``ddiff`` (pp change of the differential), as produced by ``kagura.explore.changes``. Rows
where either change is missing (ADR 0004 exclusions, holidays, gaps) are dropped and the
remaining rows are treated as consecutive for HAC (ADR 0006 §4.4, assumption A9). Rows after
the fixed sample end (§9.2) or outside the ADR 0004 eras are dropped. Each row is assigned to
an era by its own date, i.e. the end date of its change.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.figure import Figure

from kagura import SAMPLE_START
from kagura.explore import (
    COLORS,
    ERAS,
    MIN_SHARE,
    MUTED,
    WINDOWS,
    _events,
    _figure,
    era_of,
)

# --- frozen specification (ADR 0006) ---------------------------------------------------------

ALPHA = 0.025  # one-sided level for the gate, S and R (§5.1, §8)
C = NormalDist().inv_cdf(1 - ALPHA)  # 1.959964
MATERIAL = 1 / 3  # preselected operational definition of a material decline (§5)
SENSITIVITY = (1 / 4, 1 / 2)  # reported thresholds; never enter the decision (§5.2)
REF, NEW = "2013–2021", "2022–"  # era labels from ADR 0004 / kagura.explore.ERAS
DAILY_END = "2026-09-11"  # fixed sample end, daily (§9.2)
MONTHLY_END = "2026-08-31"  # fixed sample end, monthly: last month 2026-08 (§9.2)
WALD_ALPHA = 0.05  # secondary tests, unadjusted (§6.1, §8)

Outcome = Literal["not assessable", "supported", "ruled out", "inconclusive"]
# "primary" is the only confirmatory specification; R1-R3 are robustness variants (§9.1).
Spec = Literal["primary", "R1", "R2", "R3"]


def hac_lag(n: int) -> int:
    """Newey–West lag rule frozen in ADR 0006 §4.4: floor(4 * (n/100)^(2/9))."""
    return int(math.floor(4 * (n / 100) ** (2 / 9)))


# --- era-interacted regression (§4.3) ---------------------------------------------------------


@dataclass(frozen=True)
class EraFit:
    """Fully era-interacted OLS: dfx = sum_e 1[e] * (alpha_e + beta_e * ddiff) + e.

    ``params`` and ``cov`` are indexed by "<label>:<era>" ("alpha", "beta", or the two-leg
    labels). ``cov`` is the Newey–West HAC covariance with ``lag`` lags and no small-sample
    correction. ``r2`` is NaN where undefined (and for the two-leg fit, where §6.3 reports
    only coefficients and Wald tests)."""

    params: pd.Series
    cov: pd.DataFrame
    n: pd.Series  # rows used per era
    r2: pd.Series  # beta_e^2 * Var_e(ddiff) / Var_e(dfx), descriptive (§4.3); NaN if undefined
    lag: int

    @property
    def nobs(self) -> int:
        return int(self.n.sum())

    def beta(self, era: str) -> float:
        return float(self.params[f"beta:{era}"])

    def covariance(self, a: str, b: str) -> float:
        names = list(self.cov.index)
        return float(self.cov.to_numpy()[names.index(a), names.index(b)])


def _usable(ch: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Rows used by every era regression: complete ``dfx`` and ``columns``, on or before
    DAILY_END, inside an ADR 0004 era. Dates must be strictly increasing, since HAC lags follow
    row order. Returns (rows, their era, eras present in ADR 0004 order)."""
    if not ch["date"].is_monotonic_increasing or ch["date"].duplicated().any():
        raise ValueError("dates must be strictly increasing")
    d = ch.loc[ch["date"] <= DAILY_END, ["date", "dfx", *columns]].dropna()
    era = era_of(d["date"])
    d, era = d[era.notna()], era[era.notna()]
    eras = [e for e in ERAS if (era == e).any()]
    if not eras:
        raise ValueError("no usable rows in any era")
    return d, era, eras


def _era_ols(
    ch: pd.DataFrame, regressors: dict[str, str], omit: frozenset[str] = frozenset()
) -> tuple[pd.DataFrame, pd.Series, list[str], pd.Series, pd.DataFrame, int]:
    """Era-interacted OLS of ``dfx`` on an intercept and ``regressors`` ({label: column}).

    Shared by the §4.3 regression and the §6.3 two-leg decomposition; rows as in ``_usable``,
    treated as consecutive. Columns named in ``omit`` ("<label>:<era>") are left out; only the
    two-leg fit uses this, for slopes that are not identified in an era. Any remaining rank
    deficiency is an error. Returns (rows used, their era, eras, params, HAC cov, lag)."""
    d, era, eras = _usable(ch, list(regressors.values()))
    cols = {}
    for e in eras:
        on = (era == e).to_numpy(dtype=float)
        cols[f"alpha:{e}"] = on
        for label, col in regressors.items():
            if f"{label}:{e}" not in omit:
                cols[f"{label}:{e}"] = on * d[col].to_numpy()
    x = pd.DataFrame(cols, index=d.index)
    if np.linalg.matrix_rank(x.to_numpy()) < x.shape[1]:
        raise ValueError(
            "design is rank deficient: an era has a constant regressor or too few rows"
        )

    lag = hac_lag(len(d))
    res = sm.OLS(d["dfx"], x).fit(
        cov_type="HAC", cov_kwds={"maxlags": lag, "use_correction": False}, use_t=False
    )
    params = pd.Series(res.params, index=x.columns)
    cov = pd.DataFrame(res.cov_params(), index=x.columns, columns=x.columns)
    return d, era, eras, params, cov, lag


def era_regression(ch: pd.DataFrame) -> EraFit:
    """Estimate the §4.3 regression on every era with data (see ``_era_ols`` for row rules)."""
    d, era, eras, params, cov, lag = _era_ols(ch, {"beta": "ddiff"})
    g = d.groupby(era)
    n = g.size().reindex(eras)
    var_y, var_x = g["dfx"].var().reindex(eras), g["ddiff"].var().reindex(eras)
    betas = pd.Series([params[f"beta:{e}"] for e in eras], index=eras)
    # R² is undefined when dfx is constant within an era: report NaN, never inf.
    r2 = betas**2 * var_x / var_y.where(var_y > 0)
    return EraFit(params, cov, n, r2, lag)


# --- directional tests (§5.1) -----------------------------------------------------------------


@dataclass(frozen=True)
class Directional:
    """One linear contrast with its one-sided 97.5% bounds and one-sided p-values.

    ``lower``/``upper`` are the one-sided 97.5% bounds; together they are the displayed
    two-sided 95% interval. ``p_below`` tests H0: value >= 0, ``p_above`` H0: value <= 0."""

    estimate: float
    se: float
    lower: float
    upper: float
    p_below: float
    p_above: float


def contrast(fit: EraFit, weights: dict[str, float]) -> Directional:
    """Normal-approximation inference on sum_k w_k * param_k using the HAC covariance."""
    w = pd.Series(weights).reindex(fit.params.index, fill_value=0.0).to_numpy()
    est = float(w @ fit.params.to_numpy())
    var = float(w @ fit.cov.to_numpy() @ w)
    if not var > 0 or not math.isfinite(var):
        raise ValueError(f"contrast variance is not positive and finite: {var}")
    se = math.sqrt(var)
    z = est / se
    # Phi(z) = erfc(-z/sqrt2)/2 via erfc keeps precision in both tails; NormalDist.cdf is
    # erf-based and rounds tail probabilities below ~1e-17 to exactly 0.
    p_below, p_above = 0.5 * math.erfc(-z / math.sqrt(2)), 0.5 * math.erfc(z / math.sqrt(2))
    return Directional(est, se, est - C * se, est + C * se, p_below, p_above)


def rejects_below(d: Directional) -> bool:
    """Reject H0: value >= 0 at one-sided 0.025: U < 0 (⇔ p_below < 0.025). U = 0 → no."""
    return d.upper < 0


def rejects_above(d: Directional) -> bool:
    """Reject H0: value <= 0 at one-sided 0.025: L > 0 (⇔ p_above < 0.025). L = 0 → no."""
    return d.lower > 0


def delta(fit: EraFit, decline: float = MATERIAL) -> Directional:
    """delta = beta_new - (1 - decline) * beta_ref; delta < 0 means a decline of >= ``decline``."""
    return contrast(fit, {f"beta:{NEW}": 1.0, f"beta:{REF}": -(1 - decline)})


def fieller(fit: EraFit) -> list[tuple[float, float]]:
    """Fieller 95% confidence set for beta_new / beta_ref, as a list of closed intervals.

    The set is {r : (b_new - r b_ref)^2 <= C^2 (V_nn - 2 r V_nr + r^2 V_rr)}, a quadratic
    inequality a r^2 + b r + k <= 0. It is one bounded interval when beta_ref is
    significantly different from zero (a > 0), otherwise two unbounded rays or the whole
    line. Unbounded ends are +/-inf; the set is never truncated (ADR 0006 §5.2)."""
    bn, br = fit.beta(NEW), fit.beta(REF)
    n, r = f"beta:{NEW}", f"beta:{REF}"
    vnn, vrr, vnr = fit.covariance(n, n), fit.covariance(r, r), fit.covariance(n, r)
    a = br**2 - C**2 * vrr
    b = -2 * (bn * br - C**2 * vnr)
    k = bn**2 - C**2 * vnn
    disc = b**2 - 4 * a * k
    if a == 0:  # boundary case: a half-line (or everything / nothing)
        if b == 0:
            return [(-math.inf, math.inf)] if k <= 0 else []
        root = -k / b
        return [(-math.inf, root)] if b > 0 else [(root, math.inf)]
    if disc < 0:
        if a < 0:
            return [(-math.inf, math.inf)]
        # With a > 0 the point estimate always satisfies the inequality, so disc >= 0 in
        # exact arithmetic; a tiny negative value is rounding. Treat it as a double root.
        disc = 0.0
    # Numerically stable roots (no cancellation when a is near zero).
    q = -0.5 * (b + math.copysign(math.sqrt(disc), b))
    roots = (q / a, k / q) if q != 0 else (0.0, 0.0)
    r1, r2 = sorted(roots)
    return [(r1, r2)] if a > 0 else [(-math.inf, r1), (r2, math.inf)]


@dataclass(frozen=True)
class H1aResult:
    """Gate, S, R, outcome category and the descriptive report of ADR 0006 §5."""

    beta_ref: Directional  # gate: H0 beta_ref <= 0 uses p_above / lower
    beta_new: Directional
    delta: Directional  # material-decline contrast (decline = 1/3)
    absolute_change: Directional  # beta_new - beta_ref
    relative_change: float  # beta_new / beta_ref - 1 (point estimate; nan if beta_ref == 0)
    relative_change_set: list[tuple[float, float]]  # Fieller set for the ratio, minus 1
    sensitivity: dict[float, Directional]  # delta at the 1/4 and 1/2 declines
    implied_100bp_narrowing: dict[str, float]  # % FX association for a -1 pp change
    r2: dict[str, float]
    n: dict[str, int]
    lag: int
    spec: Spec = "primary"  # only "primary" is confirmatory H1a evidence (§5, §9.1)

    @property
    def gate(self) -> bool:
        """Reference association exists: p < 0.025 for H0 beta_ref <= 0 (⇔ lower > 0)."""
        return rejects_above(self.beta_ref)

    @property
    def s_rejects(self) -> bool:
        """S: reject H0 delta >= 0 (material decline) if p_S < 0.025 (⇔ U < 0)."""
        return rejects_below(self.delta)

    @property
    def r_rejects(self) -> bool:
        """R: reject H0 delta <= 0 (material decline ruled out) if p_R < 0.025 (⇔ L > 0)."""
        return rejects_above(self.delta)

    @property
    def outcome(self) -> Outcome:
        if not self.gate:
            return "not assessable"
        if self.s_rejects:
            return "supported"
        if self.r_rejects:
            return "ruled out"
        return "inconclusive"


def h1a_test(fit: EraFit, spec: Spec = "primary") -> H1aResult:
    """Apply ADR 0006 §5 to an era fit that contains both the reference and the new era.

    ``spec`` records which specification the fit came from. Pass "R1", "R2" or "R3" for the
    robustness variants: their outcomes only feed ``robustness_label`` (§9.1)."""
    missing = {REF, NEW} - set(fit.n.index)
    if missing:
        raise ValueError(f"era fit lacks {sorted(missing)}")
    bn, br = fit.beta(NEW), fit.beta(REF)
    return H1aResult(
        beta_ref=contrast(fit, {f"beta:{REF}": 1.0}),
        beta_new=contrast(fit, {f"beta:{NEW}": 1.0}),
        delta=delta(fit),
        absolute_change=contrast(fit, {f"beta:{NEW}": 1.0, f"beta:{REF}": -1.0}),
        relative_change=bn / br - 1 if br != 0 else math.nan,
        relative_change_set=[(lo - 1, hi - 1) for lo, hi in fieller(fit)],
        sensitivity={d: delta(fit, d) for d in SENSITIVITY},
        implied_100bp_narrowing={REF: -br, NEW: -bn},
        r2={e: float(fit.r2[e]) for e in (REF, NEW)},
        n={e: int(fit.n[e]) for e in (REF, NEW)},
        lag=fit.lag,
        spec=spec,
    )


def robustness_label(primary: H1aResult, variants: list[H1aResult]) -> str:
    """§9.1 labelling rule. "robust" if R1-R3 all share the primary outcome, otherwise
    "sensitive to R#" with their outcomes. The primary outcome is never changed here."""
    if primary.spec != "primary":
        raise ValueError("the first argument must be the primary specification")
    if sorted(v.spec for v in variants) != ["R1", "R2", "R3"]:
        raise ValueError("robustness needs exactly one result each for R1, R2 and R3")
    differ = [f"{v.spec} ({v.outcome})" for v in variants if v.outcome != primary.outcome]
    return "robust" if not differ else "sensitive to " + ", ".join(differ)


# --- secondary: Wald tests (§6.1, §6.3) -------------------------------------------------------
# Secondary analyses: unadjusted, reported in full, never decide H1a (ADR 0006 §6, §8).


def chi2_sf(w: float, df: int) -> float:
    """Upper tail P(chi2_df > w), exact closed form for integer df (no SciPy needed).

    Even df: exp(-w/2) * sum_{i<df/2} (w/2)^i / i!. Odd df: erfc(sqrt(w/2)) plus
    2 phi(sqrt w) * sum_{i=1}^{(df-1)/2} w^((2i-1)/2) / (1*3*...*(2i-1))."""
    if df < 1:
        raise ValueError("df must be a positive integer")
    if w <= 0:
        return 1.0
    if df % 2 == 0:
        term = total = 1.0
        for i in range(1, df // 2):
            term *= (w / 2) / i
            total += term
        return math.exp(-w / 2) * total
    term, total = math.sqrt(w), 0.0
    for i in range(1, (df - 1) // 2 + 1):
        total += term
        term *= w / (2 * i + 1)
    return math.erfc(math.sqrt(w / 2)) + 2 * math.exp(-w / 2) / math.sqrt(2 * math.pi) * total


@dataclass(frozen=True)
class Wald:
    """HAC Wald test of H0: R params = 0. ``stat`` ~ chi2(``df``) under H0."""

    stat: float
    df: int
    p: float

    @property
    def rejects(self) -> bool:
        """Reject at the unadjusted secondary level 0.05 (§6.1)."""
        return self.p < WALD_ALPHA


def wald(fit: EraFit, rows: list[dict[str, float]]) -> Wald:
    """Wald test of the linear restrictions sum_k w_k * param_k = 0, one per entry of ``rows``,
    using the fit's HAC covariance."""
    r = np.array([pd.Series(w).reindex(fit.params.index, fill_value=0.0) for w in rows])
    rb = r @ fit.params.to_numpy()
    rvr = r @ fit.cov.to_numpy() @ r.T
    try:
        stat = float(rb @ np.linalg.solve(rvr, rb))
    except np.linalg.LinAlgError as err:
        raise ValueError("restriction covariance R V R' is singular") from err
    return Wald(stat, len(rows), chi2_sf(stat, len(rows)))


def era_equality(fit: EraFit) -> Wald:
    """§6.1: H0 beta equal in all five ADR 0004 eras, chi2(4), secondary and unadjusted.

    Restrictions are the four consecutive differences beta_e - beta_(e+1) = 0; the Wald
    statistic is invariant to which full-rank set of differences is used."""
    eras = list(fit.n.index)
    if eras != list(ERAS):
        raise ValueError(f"era equality needs all five eras; fit has {eras}")
    rows = [{f"beta:{a}": 1.0, f"beta:{b}": -1.0} for a, b in zip(eras, eras[1:], strict=False)]
    return wald(fit, rows)


# --- descriptive: two-leg decomposition (§6.3) ------------------------------------------------


def leg_changes(daily: pd.DataFrame, maturity: str) -> pd.DataFrame:
    """Same-day changes of USD/JPY and of each leg of the differential, from SAMPLE_START.

    Uses exactly the primary (same-day) exclusion of ADR 0004: a row is dropped when
    ``diff_<m>_change_carried`` is true, i.e. either leg is carried. So ``dus - djgb``
    equals ``explore.changes(daily, maturity, "same-day")["ddiff"]`` row for row."""
    us, jgb = daily[f"us_{maturity}"], daily[f"jgb_{maturity}"]
    out = pd.DataFrame(
        {
            "date": daily["date"],
            "dfx": 100 * np.log(daily["usdjpy"]).diff(),
            "dus": us.diff(),
            "djgb": jgb.diff(),
        }
    )
    drop = daily[f"diff_{maturity}_change_carried"].astype(bool)
    out.loc[drop | out["dus"].isna() | out["djgb"].isna(), ["dfx", "dus", "djgb"]] = np.nan
    return out[out["date"] >= SAMPLE_START].reset_index(drop=True)


LEGS = {"beta_us": "dus", "beta_jp": "djgb"}


def _unidentified_legs(legs: pd.DataFrame) -> frozenset[str]:
    """Slopes "<label>:<era>" that cannot be estimated in an era: a leg that is numerically
    constant there (rank of [1, leg] < 2), or, if neither is, both slopes when the two legs
    are collinear (rank of [1, dus, djgb] < 3). Uses NumPy's default SVD rank tolerance."""
    d, era, eras = _usable(legs, list(LEGS.values()))
    omit = set()
    for e in eras:
        block = d.loc[era == e, list(LEGS.values())].to_numpy()
        ones = np.ones((len(block), 1))
        for j, label in enumerate(LEGS):
            if np.linalg.matrix_rank(np.hstack([ones, block[:, [j]]])) < 2:
                omit.add(f"{label}:{e}")
        if not omit & {f"{label}:{e}" for label in LEGS}:
            if np.linalg.matrix_rank(np.hstack([ones, block])) < 3:
                omit |= {f"{label}:{e}" for label in LEGS}
    return frozenset(omit)


def two_leg_regression(legs: pd.DataFrame) -> EraFit:
    """§6.3: dfx = sum_e 1[e] * (alpha_e + beta_us_e * dus + beta_jp_e * djgb) + e, HAC.

    A slope that is not identified in an era (see ``_unidentified_legs``) is left out of the
    fit instead of failing the whole regression or being estimated from rounding noise;
    ``opposite_legs`` then reports that era as not identified."""
    omit = _unidentified_legs(legs)
    d, era, eras, params, cov, lag = _era_ols(legs, LEGS, omit)
    n = d.groupby(era).size().reindex(eras)
    return EraFit(params, cov, n, pd.Series(np.nan, index=eras), lag)


@dataclass(frozen=True)
class LegTest:
    """§6.3 per-era test of H0 beta_us + beta_jp = 0 (equal magnitude, opposite sign).

    ``identified`` is False when either slope could not be estimated in the era; then no
    estimate or test exists, by design, so a missing test cannot be read as "no difference".
    When identified, ``total`` carries beta_us + beta_jp with its 95% interval: a wide
    interval means non-rejection reflects imprecision (e.g. a nearly pinned JGB leg), not
    evidence that the legs offset. ``wald`` is chi2(1) = (total / se)^2. Descriptive."""

    identified: bool
    total: Directional | None
    wald: Wald | None


def opposite_legs(fit: EraFit) -> dict[str, LegTest]:
    """Run the §6.3 test in every era of a two-leg fit, reporting unidentified eras as such."""
    out = {}
    for e in fit.n.index:
        names = {f"beta_us:{e}": 1.0, f"beta_jp:{e}": 1.0}
        if not set(names) <= set(fit.params.index):
            out[e] = LegTest(False, None, None)
            continue
        out[e] = LegTest(True, contrast(fit, names), wald(fit, [names]))
    return out


def leg_spread(legs: pd.DataFrame) -> pd.DataFrame:
    """Diagnostic: rows used and standard deviation of each leg's changes, per era."""
    d, era, eras = _usable(legs, list(LEGS.values()))
    g = d.groupby(era)
    return pd.DataFrame(
        {"n": g.size(), "sd_dus": g["dus"].std(), "sd_djgb": g["djgb"].std()}
    ).reindex(eras)


# --- descriptive: rolling beta and R² (§6.3) --------------------------------------------------


def rolling_beta(ch: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing OLS slope and R² of dfx on ddiff over ``window`` rows of the USD/JPY calendar.

    Uses rows where both changes are present; reported only when at least MIN_SHARE of the
    window survives (ADR 0004 80% rule). Descriptive: no inference (ADR 0006 §6.3)."""
    ch = ch[ch["date"] <= DAILY_END].reset_index(drop=True)
    x, y = ch["ddiff"], ch["dfx"]
    ok = x.notna() & y.notna()
    x, y = x.where(ok), y.where(ok)
    minp = int(MIN_SHARE * window)
    n = ok.astype(float).rolling(window, min_periods=1).sum()  # usable rows in the window
    var = x.rolling(window, min_periods=minp).var()
    beta = x.rolling(window, min_periods=minp).cov(y) / var.where(var > 0)
    r = x.rolling(window, min_periods=minp).corr(y)
    # n is reported for every window, so an unreported beta shows why (n < MIN_SHARE * window).
    return pd.DataFrame({"date": ch["date"], "beta": beta, "r2": r**2, "n": n})


def plot_rolling_beta(ch: pd.DataFrame) -> Figure:
    """Rolling beta (top) and R² (bottom) for the ADR 0004 windows. Descriptive only."""
    fig, axes = _figure(2, sharex=True, height=2.8)
    for (label, window), color in zip(WINDOWS.items(), COLORS, strict=False):
        rb = rolling_beta(ch, window)  # NaN kept: lines break where a window is unreported
        axes[0].plot(rb["date"], rb["beta"], color=color, label=f"{label} window")
        axes[1].plot(rb["date"], rb["r2"], color=color)
    axes[0].axhline(0, color=MUTED, lw=0.8)
    axes[0].set_title("Rolling beta: % USD/JPY per 1 pp differential change", loc="left")
    axes[1].set_title("Rolling R²", loc="left")
    axes[0].legend(frameon=False, loc="upper left")
    for ax in axes:
        _events(ax)
    return fig


# --- robustness R2: monthly changes (§9.1) ----------------------------------------------------


def monthly_changes(monthly: pd.DataFrame, maturity: str) -> pd.DataFrame:
    """R2 changes table from ``monthly.csv``: consecutive month-end rows, stored values.

    Carried flags are deliberately not applied (§9.1). A missing level makes both adjacent
    changes missing (no bridging over gaps). Kept: month-ends from SAMPLE_START (the
    January 1981 change uses December 1980) to MONTHLY_END. Era = month-end date."""
    m = monthly.sort_values("date").reset_index(drop=True)
    months = m["date"].dt.to_period("M")
    if months.duplicated().any() or (months.diff().dropna().map(lambda o: o.n) != 1).any():
        raise ValueError("monthly rows must be one per calendar month, with no missing months")
    out = pd.DataFrame(
        {
            "date": m["date"],
            "dfx": 100 * np.log(m["usdjpy"]).diff(),
            "ddiff": m[f"diff_{maturity}"].diff(),
        }
    )
    keep = (out["date"] >= SAMPLE_START) & (out["date"] <= MONTHLY_END)
    return out[keep].reset_index(drop=True)
