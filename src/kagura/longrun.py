"""H1b exploratory long-run helpers (ADR 0008 §9). Exploratory only: nothing here is a test
of the ADR 0008 §2 claim, and no 5 % reference level inherits H1b's unused α (ADR 0008 §7.1).

Contents: data assembly from the frozen vintage (§9.1), integration classification (§9.2),
the ARDL/UECM bounds statistics with BG-filtered AIC lag selection (§9.4), FM-OLS and D-OLS
(adapted from the archived ``wagner_wied/wwlib.py``), and the ARDL impulse-response
half-life with a recursive moving-block bootstrap.

Kept separate from ``kagura.models``, which implements the frozen H1a test (ADR 0006).
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

import numpy as np
import numpy.typing as npt
import pandas as pd
from statsmodels.tools.sm_exceptions import InterpolationWarning
from statsmodels.tsa.stattools import adfuller, kpss

from kagura import ROOT
from kagura.h1a import verify_checksums
from kagura.models import chi2_sf
from kagura.vintage import CPI_SHA256, FROZEN_SHA256

Array = npt.NDArray[np.float64]

H1B_SHA256 = {**FROZEN_SHA256, **CPI_SHA256}  # every file H1b reads (ADR 0006 §9.2, 0008 §8.2)
PRE_START, PRE_END = "1981-01", "2021-12"  # ADR 0008 §8.1
WINDOW_END = "2026-07"
TAX_MONTHS = ("1989-04", "1997-04", "2014-04", "2019-10")  # consumption-tax changes
LEVEL = 0.05  # descriptive reference level (ADR 0008 §9.2, §9.4)
MAX_LAG = 12  # ARDL p and q, and ADF lags (§9.2, §9.4)
DOLS_MAX = 6  # dum-OLS leads/lags (§9.4)
HALF_LIFE_CAP = 1200  # months searched before a half-life is called infinite

# PSS (2001) Case III, Tables CI(iii) and CII(iii), 5 %: k -> (F_I0, F_I1, t_I0, t_I1).
PSS_5PCT = {1: (4.94, 5.73, -2.86, -3.22), 2: (3.79, 4.85, -2.86, -3.53)}


# --- data (§9.1) -------------------------------------------------------------------------------


def load_monthly(root: Path = ROOT, expected: dict[str, str] = H1B_SHA256) -> pd.DataFrame:
    """Month-indexed frame (PeriodIndex) 1981-01…2026-07 after verifying every frozen checksum.

    s = 100 ln USD/JPY (month-end), x = 100 ln(CPI_JP/CPI_US) by reference month, q = s - x,
    d2/d10 = US-Japan 2Y/10Y differentials (month-end, pp), r = d2 minus the 12-month
    inflation gap (pi_US - pi_JP, by reference month), x_tax = x with excess tax-month
    changes removed (R9). The US CPI for 2025-10 is missing, so x, q, r and x_tax are NaN
    there; nothing is imputed."""
    verify_checksums(root, expected)
    data = root / "data"
    m = pd.read_csv(data / "processed" / "monthly.csv", parse_dates=["date"])
    m.index = m["date"].dt.to_period("M")
    jp = pd.read_csv(data / "raw" / "jp_cpi.csv", usecols=["TIME_PERIOD", "OBS_VALUE"])
    jp_cpi = pd.Series(jp["OBS_VALUE"].to_numpy(float), pd.PeriodIndex(jp["TIME_PERIOD"], freq="M"))
    us = pd.read_csv(data / "raw" / "us_cpi.csv", parse_dates=["observation_date"])
    us_cpi = pd.Series(
        pd.to_numeric(us["CPIAUCSL"], errors="coerce").to_numpy(float),
        us["observation_date"].dt.to_period("M"),
    )
    idx = pd.period_range(PRE_START, WINDOW_END, freq="M")
    out = pd.DataFrame(index=idx)
    out["s"] = 100 * np.log(m["usdjpy"].reindex(idx))
    out["d2"] = m["diff_2y"].reindex(idx)
    out["d10"] = m["diff_10y"].reindex(idx)
    ljp = pd.Series(100 * np.log(jp_cpi.to_numpy()), index=jp_cpi.index)
    lus = pd.Series(100 * np.log(us_cpi.to_numpy()), index=us_cpi.index)
    out["x"] = (ljp - lus).reindex(idx)
    out["q"] = out["s"] - out["x"]
    infl_gap = (lus - lus.shift(12, freq="M")) - (ljp - ljp.shift(12, freq="M"))
    out["r"] = out["d2"] - infl_gap.reindex(idx)
    out["x_tax"] = tax_adjusted(out["x"])
    if out[["s", "d2"]].isna().any().any():
        raise ValueError("s or d2 has missing months in 1981-01…2026-07")
    return out


def tax_adjusted(x: pd.Series) -> pd.Series:
    """R9: each tax-month change minus its 1981–2021 same-calendar-month median (tax months
    excluded) is removed permanently from x from that month on."""
    dx = x.diff()
    pre = dx.loc[PRE_START:PRE_END]
    taxes = pd.PeriodIndex(TAX_MONTHS, freq="M")
    shift = pd.Series(0.0, index=x.index)
    months = pd.PeriodIndex(pre.index).month
    for t in taxes:
        same = pre[(months == t.month) & ~pre.index.isin(taxes)]
        shift[shift.index >= t] += float(dx[dx.index == t].iloc[0]) - same.median()
    return x - shift


# --- integration classification (§9.2) ---------------------------------------------------------

IClass = Literal["I(0)", "I(1)", "I(2) risk", "ambiguous"]


@dataclass(frozen=True)
class Integration:
    name: str
    adf_level_p: float
    kpss_level_p: float
    adf_diff_p: float
    kpss_diff_p: float
    adf_lags: int
    max_root_diff: float  # largest AR root modulus of the (filtered) first difference
    klass: IClass


def _adf_kpss(y: Array, trend: bool) -> tuple[float, float, int]:
    reg = "ct" if trend else "c"
    adf = adfuller(y, maxlag=MAX_LAG, regression=reg, autolag="AIC", result_object=True)
    with warnings.catch_warnings():  # KPSS p-values are truncated to [0.01, 0.10]
        warnings.simplefilter("ignore", InterpolationWarning)
        kp = kpss(y, regression=reg, nlags="auto", result_object=True)
    return float(adf.pvalue), float(kp.pvalue), int(adf.lags)


def _max_root(y: Array, p: int = MAX_LAG) -> float:
    """Largest modulus of the roots of an AR(p) fitted by OLS (companion eigenvalues)."""
    z = y - y.mean()
    xs = np.column_stack([z[p - j - 1 : len(z) - j - 1] for j in range(p)])
    a = np.linalg.lstsq(xs, z[p:], rcond=None)[0]
    comp = np.zeros((p, p))
    comp[0], comp[1:, :-1] = a, np.eye(p - 1)
    return float(np.abs(np.linalg.eigvals(comp)).max())


def seasonal_filter(dy: pd.Series) -> pd.Series:
    """Remove centred calendar-month means and tax-month impulses from a monthly change
    series by OLS, keeping its overall mean (§9.2: Δx gets seasonal and tax dummies)."""
    dy = dy.dropna()
    idx = pd.PeriodIndex(dy.index)
    months = pd.get_dummies(idx.month).to_numpy(float)
    dum = months[:, 1:] - months[:, 1:].mean(0)
    taxes = np.column_stack([(idx == pd.Period(t, "M")).astype(float) for t in TAX_MONTHS])
    keep = taxes.any(0)
    zm = np.column_stack([np.ones(len(dy)), dum, taxes[:, keep]])
    b = np.linalg.lstsq(zm, dy.to_numpy(float), rcond=None)[0]
    return pd.Series(dy.to_numpy(float) - zm[:, 1:] @ b[1:], index=dy.index)


def classify(name: str, y: pd.Series, trend: bool = False, seasonal: bool = False) -> Integration:
    """ADF (AIC lags ≤ 12, MacKinnon p) and KPSS on the level and the first difference.

    I(2) risk: the difference is not I(0). Otherwise I(0): level ADF rejects and KPSS does not;
    I(1): level ADF does not reject and KPSS rejects. Anything else is ambiguous. With
    ``seasonal`` the difference is filtered by ``seasonal_filter`` first. Missing months are
    dropped (the 2025-10 gap only occurs outside the pre-period)."""
    lev = y.dropna()
    d = lev.diff().dropna()
    if seasonal:
        d = seasonal_filter(d)
    al, kl, lags = _adf_kpss(lev.to_numpy(float), trend)
    ad, kd, _ = _adf_kpss(d.to_numpy(float), False)

    def i0(adf_p: float, kpss_p: float) -> bool:
        return adf_p < LEVEL and kpss_p >= LEVEL

    if not i0(ad, kd):
        klass: IClass = "I(2) risk"
    elif i0(al, kl):
        klass = "I(0)"
    elif al >= LEVEL and kl < LEVEL:
        klass = "I(1)"
    else:
        klass = "ambiguous"
    return Integration(name, al, kl, ad, kd, lags, _max_root(d.to_numpy(float)), klass)


# --- ARDL / UECM bounds statistics (§9.4) ------------------------------------------------------


@dataclass(frozen=True)
class ARDL:
    p: int  # lags of y in levels
    q: int  # lags of each regressor in levels (common), q >= 1
    f_stat: float
    t: float
    phi: float  # loading on y_{t-1}
    long_run: Array  # -pi/phi for each regressor
    lr_se_hac: Array
    lr_se_ols: Array
    bg_p: float
    bg_passed: bool  # False if no order passed BG(12) and the AIC minimum was taken anyway
    resid: Array
    fitted_coef: Array
    nobs: int
    start: int  # first usable row of the input arrays


def _uecm_design(y: Array, xs: Array, p: int, q: int, start: int) -> tuple[Array, Array]:
    """Δy_t on [1, y_{t-1}, X_{t-1}, Δy_{t-1..t-p+1}, ΔX_{t..t-q+1}] for t = start..n-1."""
    n = len(y)
    dy = np.r_[np.nan, np.diff(y)]
    dxs = np.vstack([np.full((1, xs.shape[1]), np.nan), np.diff(xs, axis=0)])
    t = np.arange(start, n)
    cols = [np.ones(len(t)), y[t - 1], *xs[t - 1].T]
    cols += [dy[t - i] for i in range(1, p)]
    cols += [dxs[t - i, j] for j in range(xs.shape[1]) for i in range(q)]
    return dy[t], np.column_stack(cols)


def _ols(yv: Array, zm: Array) -> tuple[Array, Array, Array]:
    zinv = np.linalg.inv(zm.T @ zm)
    b = zinv @ zm.T @ yv
    e = yv - zm @ b
    return b, e, zinv


def _bartlett_lrv(u: Array, nlag: int) -> Array:
    """Bartlett long-run covariance of the rows of u (n × m), L lags."""
    u = u - u.mean(0)
    n = len(u)
    acc = u.T @ u / n
    for j in range(1, nlag + 1):
        gam = u[j:].T @ u[:-j] / n
        acc += (1 - j / (nlag + 1)) * (gam + gam.T)
    return acc


def _hac_cov(zm: Array, e: Array, zinv: Array, nlag: int) -> Array:
    n = len(e)
    return n * zinv @ _bartlett_lrv(zm * e[:, None], nlag) @ zinv


def bg_pvalue(e: Array, zm: Array, lags: int = 12) -> float:
    """Breusch–Godfrey LM (n R²) p-value, missing initial residual lags set to zero."""
    elag = np.column_stack([np.r_[np.zeros(j), e[:-j]] for j in range(1, lags + 1)])
    wmat = np.column_stack([zm, elag])
    _, u, _ = _ols(e, wmat)
    r2 = 1 - (u @ u) / ((e - e.mean()) @ (e - e.mean()))
    return chi2_sf(float(len(e) * r2), lags)


def fit_ardl(y: Array, xs: Array, p: int, q: int, start: int | None = None) -> ARDL:
    """UECM at fixed orders. F tests y_{t-1} and X_{t-1} jointly (PSS Case III); t is the
    t-ratio on y_{t-1}. Long-run coefficients -pi/phi with delta-method HAC and OLS s.e."""
    k = xs.shape[1]
    start = MAX_LAG + 1 if start is None else start
    yv, zm = _uecm_design(y, xs, p, q, start)
    b, e, zinv = _ols(yv, zm)
    n, kz = zm.shape
    s2 = e @ e / (n - kz)
    vcov = s2 * zinv
    lev = slice(1, 2 + k)
    wmat = b[lev] @ np.linalg.solve(vcov[lev, lev], b[lev])
    phi, pi = b[1], b[2 : 2 + k]
    vhac = _hac_cov(zm, e, zinv, int(math.floor(4 * (n / 100) ** (2 / 9))))
    lr = -pi / phi
    se = {}
    for name, vv in (("hac", vhac), ("ols", vcov)):
        out = np.empty(k)
        for j in range(k):  # gradient of -pi_j/phi wrt (phi, pi_j)
            g = np.array([pi[j] / phi**2, -1 / phi])
            ii = [1, 2 + j]
            out[j] = math.sqrt(g @ vv[np.ix_(ii, ii)] @ g)
        se[name] = out
    bgp = bg_pvalue(e, zm)
    return ARDL(
        p, q, float(wmat / (k + 1)), float(phi / math.sqrt(vcov[1, 1])), float(phi), lr,
        se["hac"], se["ols"], bgp, bgp > LEVEL, e, b, n, start,
    )  # fmt: skip


def select_ardl(y: Array, xs: Array, max_lag: int = MAX_LAG) -> ARDL:
    """BG-filtered AIC over p in 1..max_lag and a common q in 1..max_lag on one fixed
    estimation sample: the lowest-AIC order whose BG(12) p-value exceeds 5 %; if none passes,
    the overall AIC minimum (flagged by ``bg_passed=False``)."""
    start = max_lag + 1
    best: tuple[float, int, int] | None = None
    best_any: tuple[float, int, int] | None = None
    for p in range(1, max_lag + 1):
        for q in range(1, max_lag + 1):
            yv, zm = _uecm_design(y, xs, p, q, start)
            _, e, _ = _ols(yv, zm)
            aic = len(e) * math.log(e @ e / len(e)) + 2 * zm.shape[1]
            if best_any is None or aic < best_any[0]:
                best_any = (aic, p, q)
            if (best is None or aic < best[0]) and bg_pvalue(e, zm) > LEVEL:
                best = (aic, p, q)
    chosen = best or best_any
    assert chosen is not None
    fit = fit_ardl(y, xs, chosen[1], chosen[2], start)
    if best is None:
        fit = replace(fit, bg_passed=False)
    return fit


def ar_polynomial(fit: ARDL) -> Array:
    """Levels AR coefficients a_1..a_p of y implied by the UECM (phi and the Δy terms)."""
    k = len(fit.long_run)
    g = fit.fitted_coef[2 + k : 2 + k + fit.p - 1]  # Δy lags 1..p-1
    a = np.zeros(fit.p)
    a[0] = 1 + fit.phi + (g[0] if fit.p > 1 else 0.0)
    for i in range(1, fit.p):
        a[i] = (g[i] if i < fit.p - 1 else 0.0) - g[i - 1]
    return a


def half_life(a: Array) -> float:
    """First horizon (months) at which the impulse response of y_t = sum a_i y_{t-i} + e_t
    to a unit shock falls to 0.5 or below; inf if not within HALF_LIFE_CAP months or if the
    AR polynomial is not stable."""
    p = len(a)
    comp = np.zeros((p, p))
    comp[0], comp[1:, :-1] = a, np.eye(p - 1)
    if np.abs(np.linalg.eigvals(comp)).max() >= 1:
        return math.inf
    irf = np.zeros(HALF_LIFE_CAP + p)
    irf[p - 1] = 1.0
    for h in range(p, len(irf)):
        irf[h] = a @ irf[h - p : h][::-1]
        if irf[h] <= 0.5:
            return float(h - p + 1)
    return math.inf


def bootstrap_half_life(
    y: Array, xs: Array, fit: ARDL, draws: int = 999, block: int = 24, seed: int = 20261024
) -> Array:
    """Recursive moving-block residual bootstrap: rebuild y from the fitted UECM with
    block-resampled residuals and the observed X, refit at the same orders, return the
    half-lives. Initial values are the observed y."""
    rng = np.random.default_rng(seed)
    b, e = fit.fitted_coef, fit.resid - fit.resid.mean()
    n = len(e)
    out = np.empty(draws)
    for r in range(draws):
        starts = rng.integers(0, n - block + 1, size=math.ceil(n / block))
        eb = np.concatenate([e[s : s + block] for s in starts])[:n]
        yb = y.copy()
        for i, t in enumerate(range(fit.start, len(y))):
            _, zt = _uecm_design(yb[: t + 1], xs[: t + 1], fit.p, fit.q, t)
            yb[t] = yb[t - 1] + zt[0] @ b + eb[i]
        out[r] = half_life(ar_polynomial(fit_ardl(yb, xs, fit.p, fit.q, fit.start)))
    return out


def simulate_bounds_quantiles(
    n: int, k: int, reps: int, level: float = 0.95, seed: int = 20261024, max_lag: int = MAX_LAG
) -> tuple[float, float]:
    """Upper-bound PSS null (independent random walks of length n, no levels relation): F
    upper-``level`` and t lower-(1 - ``level``) quantiles of the full ``select_ardl`` procedure.
    Synthetic data only."""
    rng = np.random.default_rng(seed)
    fs, t = np.empty(reps), np.empty(reps)
    for r in range(reps):
        wmat = rng.standard_normal((n, k + 1)).cumsum(0)
        fit = select_ardl(wmat[:, 0], wmat[:, 1:], max_lag)
        fs[r], t[r] = fit.f_stat, fit.t
    return float(np.quantile(fs, level)), float(np.quantile(t, 1 - level))


def loading(dz: Array, ect: Array, controls: Array) -> tuple[float, float]:
    """Coefficient and HAC t-ratio of ect_{t-1} in a regression of Δz_t on a constant,
    ect_{t-1} and the given controls (long-run forcing check, §9.3)."""
    zm = np.column_stack([np.ones(len(dz)), ect, controls])
    b, e, zinv = _ols(dz, zm)
    vcov = _hac_cov(zm, e, zinv, int(math.floor(4 * (len(e) / 100) ** (2 / 9))))
    return float(b[1]), float(b[1] / math.sqrt(vcov[1, 1]))


# --- FM-OLS and dum-OLS (§9.4) -------------------------------------------------------------------


def andrews_bandwidth(u: Array) -> float:
    """Andrews (1991) AR(1) plug-in bandwidth for the Bartlett kernel (as ``cointReg``)."""
    num = den = 0.0
    for a in u.T:
        rho = float(a[1:] @ a[:-1] / (a[:-1] @ a[:-1]))
        s2 = float(np.mean((a[1:] - rho * a[:-1]) ** 2))
        num += 4 * rho**2 * s2**2 / ((1 - rho) ** 6 * (1 + rho) ** 2)
        den += s2**2 / (1 - rho) ** 4
    return float(min(1.1447 * (num / den * len(u)) ** (1 / 3), len(u) - 1))


def _bartlett_parts(e: Array, bw: float) -> tuple[Array, Array]:
    """Two-sided Omega and one-sided Delta = sum_{j>=0} w_j E[e_{t-j} e_t']."""
    n = len(e)
    delta = e.T @ e / n
    for j in range(1, int(math.floor(bw)) + 1):
        delta = delta + (1 - j / (bw + 1)) * (e[:-j].T @ e[j:] / n)
    return delta + delta.T - e.T @ e / n, delta


@dataclass(frozen=True)
class CointFit:
    coef: Array  # [constant, regressors...]
    se: Array
    bandwidth: float
    extra: int  # dum-OLS leads/lags (0 for FM-OLS)


def fmols(y: Array, xs: Array) -> CointFit:
    """Phillips–Hansen FM-OLS with a constant, Bartlett kernel, Andrews bandwidth.
    s.e. from omega^2_{u.v} (Z'Z)^{-1}."""
    v = np.diff(xs, axis=0)
    zm = np.column_stack([np.ones(len(y)), xs])
    u = (y - zm @ np.linalg.lstsq(zm, y, rcond=None)[0])[1:]
    eta = np.column_stack([u, v])
    bw = andrews_bandwidth(eta)
    om, de = _bartlett_parts(eta, bw)
    corr = np.linalg.solve(om[1:, 1:], om[1:, 0])
    yp = y[1:] - v @ corr
    zs = zm[1:]
    rhs = zs.T @ yp
    rhs[1:] -= len(yp) * (de[1:, 0] - de[1:, 1:] @ corr)
    zinv = np.linalg.inv(zs.T @ zs)
    w2 = float(om[0, 0] - om[1:, 0] @ corr)
    return CointFit(zinv @ rhs, np.sqrt(w2 * np.diag(zinv)), bw, 0)


def _dols_design(y: Array, xs: Array, extra: Array | None, k: int) -> tuple[Array, Array]:
    n = len(y)
    dxs = np.vstack([np.full((1, xs.shape[1]), np.nan), np.diff(xs, axis=0)])
    cols = [np.ones(n), xs] + ([extra] if extra is not None else [])
    for j in range(-k, k + 1):  # ΔX_{t-j}
        sh = np.full_like(dxs, np.nan)
        if j >= 0:
            sh[j:] = dxs[: n - j]
        else:
            sh[: n + j] = dxs[-j:]
        cols.append(sh)
    zm = np.column_stack(cols)
    ok = ~np.isnan(zm).any(1)
    trim = np.zeros(n, bool)
    trim[DOLS_MAX + 1 : n - DOLS_MAX] = True  # common sample for every k
    return y[ok & trim], zm[ok & trim]


def dols(y: Array, xs: Array, extra: Array | None = None) -> CointFit:
    """Stock–Watson D-OLS: y on a constant, X, optional stationary ``extra`` regressors and
    k leads and lags of ΔX, k ≤ DOLS_MAX by BIC on a common sample. s.e. from the Bartlett
    long-run variance of the residuals (Andrews bandwidth) times (Z'Z)^{-1}."""
    best: tuple[float, int] | None = None
    for k in range(DOLS_MAX + 1):
        yv, zm = _dols_design(y, xs, extra, k)
        e = yv - zm @ np.linalg.lstsq(zm, yv, rcond=None)[0]
        bic = len(e) * math.log(e @ e / len(e)) + zm.shape[1] * math.log(len(e))
        if best is None or bic < best[0]:
            best = (bic, k)
    assert best is not None
    yv, zm = _dols_design(y, xs, extra, best[1])
    b, e, zinv = _ols(yv, zm)
    bw = andrews_bandwidth(e[:, None])
    w2 = float(_bartlett_parts(e[:, None], bw)[0][0, 0])
    m = 1 + xs.shape[1] + (0 if extra is None else (extra.shape[1] if extra.ndim > 1 else 1))
    return CointFit(b[:m], np.sqrt(w2 * np.diag(zinv))[:m], bw, best[1])
