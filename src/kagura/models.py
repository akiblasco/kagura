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

from kagura.explore import ERAS, era_of

# --- frozen specification (ADR 0006) ---------------------------------------------------------

ALPHA = 0.025  # one-sided level for the gate, S and R (§5.1, §8)
C = NormalDist().inv_cdf(1 - ALPHA)  # 1.959964
MATERIAL = 1 / 3  # preselected operational definition of a material decline (§5)
SENSITIVITY = (1 / 4, 1 / 2)  # reported thresholds; never enter the decision (§5.2)
REF, NEW = "2013–2021", "2022–"  # era labels from ADR 0004 / kagura.explore.ERAS
DAILY_END = "2026-09-11"  # fixed sample end, daily (§9.2)

Outcome = Literal["not assessable", "supported", "ruled out", "inconclusive"]


def hac_lag(n: int) -> int:
    """Newey–West lag rule frozen in ADR 0006 §4.4: floor(4 * (n/100)^(2/9))."""
    return int(math.floor(4 * (n / 100) ** (2 / 9)))


# --- era-interacted regression (§4.3) ---------------------------------------------------------


@dataclass(frozen=True)
class EraFit:
    """Fully era-interacted OLS: dfx = sum_e 1[e] * (alpha_e + beta_e * ddiff) + e.

    ``params`` and ``cov`` are indexed by "alpha:<era>" / "beta:<era>". ``cov`` is the
    Newey–West HAC covariance with ``lag`` lags and no small-sample correction."""

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


def era_regression(ch: pd.DataFrame) -> EraFit:
    """Estimate the §4.3 regression on every era with data.

    Rows with a missing ``dfx`` or ``ddiff``, after DAILY_END, or outside the ADR 0004 eras
    are dropped before estimation; the remaining rows keep their order and are treated as
    consecutive. Dates must be strictly increasing, since HAC lags follow row order."""
    if not ch["date"].is_monotonic_increasing or ch["date"].duplicated().any():
        raise ValueError("dates must be strictly increasing")
    d = ch.loc[ch["date"] <= DAILY_END, ["date", "dfx", "ddiff"]].dropna()
    era = era_of(d["date"])
    d, era = d[era.notna()], era[era.notna()]
    eras = [e for e in ERAS if (era == e).any()]
    if not eras:
        raise ValueError("no usable rows in any era")

    cols = {}
    for e in eras:
        on = (era == e).to_numpy(dtype=float)
        cols[f"alpha:{e}"] = on
        cols[f"beta:{e}"] = on * d["ddiff"].to_numpy()
    x = pd.DataFrame(cols, index=d.index)
    if np.linalg.matrix_rank(x.to_numpy()) < x.shape[1]:
        raise ValueError("design is rank deficient: an era has constant ddiff or < 2 rows")

    lag = hac_lag(len(d))
    res = sm.OLS(d["dfx"], x).fit(
        cov_type="HAC", cov_kwds={"maxlags": lag, "use_correction": False}, use_t=False
    )
    params = pd.Series(res.params, index=x.columns)
    cov = pd.DataFrame(res.cov_params(), index=x.columns, columns=x.columns)
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


def h1a_test(fit: EraFit) -> H1aResult:
    """Apply ADR 0006 §5 to an era fit that contains both the reference and the new era."""
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
    )
