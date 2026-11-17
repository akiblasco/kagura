"""Multiple structural-break estimation for ADR 0007 (pure structural change).

Conventions (ADR 0007 §3.2): a break is the 0-based index of the **first row of the new
regime**. `strucchange` reports the last row of the old regime, i.e. our index (1-based)
minus one: our b (0-based) equals strucchange's breakpoint (1-based).

Every regime has at least h rows; break positions are restricted to `candidates`.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Arr = NDArray[np.float64]


def segment_ssr(y: Arr, xm: Arr, i: int, j: int) -> float:
    """OLS SSR of y[i:j] on X[i:j]."""
    beta, *_ = np.linalg.lstsq(xm[i:j], y[i:j], rcond=None)
    r = y[i:j] - xm[i:j] @ beta
    return float(r @ r)


@dataclass(frozen=True)
class Partition:
    breaks: tuple[int, ...]
    ssr: float


def global_partitions(
    y: Arr, xm: Arr, h: int, m_max: int, candidates: list[int] | None = None
) -> dict[int, Partition]:
    """Global minimum-SSR partition for m = 0..m_max (Bai and Perron 2003a, ADR 0007 §5.1).

    Dynamic programming over admissible break positions: the candidates b with
    h <= b <= T - h. Segment SSRs come from cumulative cross-product sums between nodes
    (§5.1); the SSR reported for each chosen partition is recomputed by OLS."""
    n_obs = len(y)
    cand = sorted(range(h, n_obs - h + 1) if candidates is None else candidates)
    cand = [b for b in cand if h <= b <= n_obs - h]
    nodes = np.array([0, *cand, n_obs])
    n = len(nodes)
    cxx = np.concatenate(
        [np.zeros((1, *xm.shape[1:] * 2)), np.cumsum(xm[:, :, None] * xm[:, None, :], 0)]
    )
    cxy = np.concatenate([np.zeros((1, xm.shape[1])), np.cumsum(xm * y[:, None], 0)])
    cyy = np.concatenate([[0.0], np.cumsum(y * y)])
    a_idx, b_idx = np.nonzero(nodes[None, :] - nodes[:, None] >= h)
    if m_max == 1:  # only segments that start at 0 or end at T are needed
        keep = (a_idx == 0) | (b_idx == n - 1)
        a_idx, b_idx = a_idx[keep], b_idx[keep]
    na, nb = nodes[a_idx], nodes[b_idx]
    sxx, sxy = cxx[nb] - cxx[na], cxy[nb] - cxy[na]
    fit = np.einsum("ij,ij->i", sxy, np.linalg.solve(sxx, sxy[:, :, None])[:, :, 0])
    ssr = np.full((n, n), np.inf)
    ssr[a_idx, b_idx] = cyy[nb] - cyy[na] - fit
    # best[k][b]: min SSR of rows 0..nodes[b] split into k + 1 segments; arg for backtracking.
    best = [ssr[0].copy()]
    arg: list[NDArray[np.int64]] = [np.zeros(n, dtype=np.int64)]
    for _ in range(m_max):
        tot = best[-1][:, None] + ssr  # tot[a, b] = best split ending at a, then segment a..b
        a_star = np.argmin(tot, axis=0)
        best.append(tot[a_star, np.arange(n)])
        arg.append(a_star)
    out: dict[int, Partition] = {}
    for m in range(m_max + 1):
        if not np.isfinite(best[m][n - 1]):
            break
        idx, k, bs = n - 1, m, []
        while k > 0:
            idx = int(arg[k][idx])
            bs.append(int(nodes[idx]))
            k -= 1
        breaks_ = tuple(sorted(bs))
        exact = sum(segment_ssr(y, xm, a, b) for a, b in regime_bounds(breaks_, n_obs))
        out[m] = Partition(breaks_, exact)
    return out


def n_params(m: int, q: int, p: int = 0) -> int:
    """p* = (m + 1) q + m + p (ADR 0007 §5.2): coefficients, break dates, fixed coefficients."""
    return (m + 1) * q + m + p


def bic(ssr: float, n: int, m: int, q: int, p: int = 0) -> float:
    """ln[S/n] + p* ln(n) / n (ADR 0007 §5.2)."""
    return math.log(ssr / n) + n_params(m, q, p) * math.log(n) / n


def lwz(ssr: float, n: int, m: int, q: int, p: int = 0) -> float:
    """ln[S/(n - p*)] + p* c0 (ln n)^(2 + d0) / n, c0 = 0.299, d0 = 0.1 (Liu, Wu, Zidek 1997)."""
    k = n_params(m, q, p)
    return math.log(ssr / (n - k)) + k * 0.299 * float(math.log(n) ** 2.1) / n


def select(parts: dict[int, Partition], n: int, q: int, p: int = 0) -> dict[str, int]:
    """Number of breaks chosen by BIC and by LWZ (descriptive, ADR 0007 §2.1)."""
    crit = {"bic": bic, "lwz": lwz}
    return {name: min(parts, key=lambda m: f(parts[m].ssr, n, m, q, p)) for name, f in crit.items()}


def regime_bounds(breaks: tuple[int, ...], n_obs: int) -> list[tuple[int, int]]:
    edges = [0, *breaks, n_obs]
    return list(zip(edges[:-1], edges[1:], strict=True))


@dataclass(frozen=True)
class Cov:
    """Covariance options, named as in `mbreaks` 1.0.1 (`pvdel`, `correct`, `interval`).

    ADR 0007 protocol (§5.3, §6.2, §7): robust, hetdat, hetvar, hetq, hetomega all on,
    Bartlett kernel with the ADR 0006 §4.4 lag of the whole sample, no prewhitening.
    `kernel="qs"` is `mbreaks`' quadratic-spectral kernel with Andrews' AR(1) bandwidth; it
    exists so the port can be checked against `mbreaks` (ADR 0007 §9.2)."""

    robust: bool = True
    hetdat: bool = True
    hetvar: bool = True
    hetq: bool = True
    hetomega: bool = True
    prewhit: bool = False
    kernel: str = "bartlett"
    lags: int | None = None  # Bartlett truncation lag; required when kernel == "bartlett"


def _qs(x: Arr) -> Arr:
    d = 6 * np.pi * x / 5
    return np.asarray(3 * (np.sin(d) / d - np.cos(d)) / (d * d), dtype=np.float64)


def _andrews_bandwidth(v: Arr) -> float:
    """`mbreaks::bandw`: AR(1) plug-in bandwidth for the QS kernel."""
    nt, d = v.shape
    a2n = a2d = 0.0
    for i in range(d):
        yv, dy = v[1:, i], v[:-1, i]
        b = float(dy @ yv / (dy @ dy))
        sig = float(np.sum((yv - b * dy) ** 2)) / (nt - 1)
        a2n += 4 * b * b * sig * sig / (1 - b) ** 8
        a2d += sig * sig / (1 - b) ** 4
    return float(1.3221 * (a2n / a2d * nt) ** 0.2)


def _autocov(v: Arr, max_lag: int) -> Arr:
    """G[j] = sum_t v[t + j] v[t]' for j = 0..max_lag, by FFT."""
    nt = len(v)
    f = np.fft.rfft(v, 2 * nt, axis=0)
    g = np.fft.irfft(f[:, :, None] * np.conj(f[:, None, :]), 2 * nt, axis=0)
    return np.asarray(g[: max_lag + 1], dtype=np.float64)


def _jhat(v: Arr, cov: Cov) -> Arr:
    """`mbreaks::jhatpr` with the kernel in `cov`: (G0 + sum_j k_j (G_j + G_j')) / (n - d)."""
    nt, d = v.shape
    if cov.kernel == "qs":
        g = _autocov(v, nt - 1)
        w = _qs(np.arange(1, nt) / _andrews_bandwidth(v))
    elif cov.kernel == "bartlett":
        if cov.lags is None:
            raise ValueError("Bartlett kernel needs cov.lags (ADR 0006 §4.4)")
        lag = min(cov.lags, nt - 1)
        g = _autocov(v, lag)
        w = 1 - np.arange(1, lag + 1) / (lag + 1)
    else:
        raise ValueError(cov.kernel)
    s = np.einsum("j,jab->ab", w, g[1:])
    return np.asarray((g[0] + s + s.T) / (nt - d), dtype=np.float64)


def lrv(reg: Arr, res: Arr, cov: Cov) -> Arr:
    """`mbreaks::correct`: long-run variance of reg_t * res_t, optionally VAR(1)-prewhitened."""
    v = reg * res[:, None]
    if not cov.prewhit:
        return _jhat(v, cov)
    d = v.shape[1]
    bmat, *_ = np.linalg.lstsq(v[:-1], v[1:], rcond=None)
    vstar = v[1:] - v[:-1] @ bmat
    inv = np.linalg.inv(np.eye(d) - bmat.T)
    return np.asarray(inv @ _jhat(vstar, cov) @ inv.T, dtype=np.float64)


def diag_partition(xm: Arr, breaks_: tuple[int, ...]) -> Arr:
    """`mbreaks::diag_par`: block-diagonal regressors, one block of columns per regime."""
    n_obs, q = xm.shape
    zm = np.zeros((n_obs, (len(breaks_) + 1) * q))
    for j, (a, b) in enumerate(regime_bounds(breaks_, n_obs)):
        zm[a:b, j * q : (j + 1) * q] = xm[a:b]
    return zm


def coef_cov(y: Arr, xm: Arr, breaks_: tuple[int, ...], cov: Cov) -> tuple[Arr, Arr]:
    """Regime coefficients and their covariance (`mbreaks::pvdel`, p = 0).

    One deliberate difference: with robust = 0 and hetvar = 1, `mbreaks::psigmq` includes
    the previous regime's last row in each middle regime's variance. Here each regime uses
    its own rows only."""
    n_obs, q = xm.shape
    zm = diag_partition(xm, breaks_)
    delta, *_ = np.linalg.lstsq(zm, y, rcond=None)
    res = y - zm @ delta
    bounds = regime_bounds(breaks_, n_obs)
    zz_inv = np.linalg.inv(zm.T @ zm)
    lam = np.diag([(b - a) / n_obs for a, b in bounds])
    if not cov.robust:
        if cov.hetvar:
            sig = np.diag([float(res[a:b] @ res[a:b]) / (b - a) for a, b in bounds])
        else:
            sig = float(res @ res) / n_obs * np.eye(len(bounds))
        base = zz_inv if cov.hetdat else np.linalg.inv(np.kron(lam, xm.T @ xm))
        return delta, np.kron(sig, np.eye(q)) @ base
    if not cov.hetdat:
        raise ValueError("robust errors need hetdat (mbreaks returns zeros)")
    if cov.hetvar:
        hac = np.zeros_like(zz_inv)
        for j, (a, b) in enumerate(bounds):
            sl = slice(j * q, (j + 1) * q)
            hac[sl, sl] = (b - a) * lrv(xm[a:b], res[a:b], cov)
        return delta, zz_inv @ hac @ zz_inv
    pooled = np.kron(lam, lrv(xm, res, cov))
    return delta, n_obs * zz_inv @ pooled @ zz_inv


def f_test(y: Arr, xm: Arr, breaks_: tuple[int, ...], cov: Cov, p: int = 0) -> float:
    """F_T(k) at the given dates (`mbreaks::pftest`): (T - (k + 1) q - p) / (T k) * Wald.

    sup F_T(k) is this statistic at the global minimum-SSR partition (Bai and Perron 2003a
    practice, as in `mbreaks`); the sup over dates is taken through the SSR, not the Wald."""
    n_obs, q = xm.shape
    k = len(breaks_)
    delta, vdel = coef_cov(y, xm, breaks_, cov)
    rmat = np.kron(np.eye(k, k + 1, 1) - np.eye(k, k + 1), np.eye(q))
    rd = rmat @ delta
    wald = float(rd @ np.linalg.solve(rmat @ vdel @ rmat.T, rd))
    return float((n_obs - (k + 1) * q - p) / (n_obs * k) * wald)


def one_break(y: Arr, xm: Arr, h: int, candidates: list[int] | None) -> int:
    """SSR-minimising single break in y (positions relative to the segment start)."""
    return global_partitions(y, xm, h, 1, candidates)[1].breaks[0]


def sequential(
    y: Arr,
    xm: Arr,
    h: int,
    m_max: int,
    crit: Callable[[int, list[tuple[int, int]]], float],
    cov: Cov,
    candidates: list[int] | None = None,
) -> tuple[tuple[int, ...], list[float]]:
    """Sequential sup F(l + 1 | l) (ADR 0007 §5.2, `mbreaks::sequa` with p = 0).

    Step 0 tests the global one-break fit. At step l, each regime of at least 2h rows gets
    its SSR-minimising break on the candidates inside it, and F(1) is computed on that
    regime alone. The largest is compared with crit(l, regimes); the break is added if it
    is not smaller, otherwise the procedure stops. Returns the breaks and the statistics."""
    n_obs = len(y)
    cand = list(range(n_obs)) if candidates is None else candidates
    b1 = one_break(y, xm, h, cand)
    stats = [f_test(y, xm, (b1,), cov)]
    if stats[0] < crit(0, [(0, n_obs)]):
        return (), stats
    found: tuple[int, ...] = (b1,)
    while len(found) < m_max:
        regimes = regime_bounds(found, n_obs)
        best, best_b = 0.0, -1
        for a, b in regimes:
            if b - a < 2 * h:
                continue
            inner = [c - a for c in cand if a + h <= c <= b - h]
            if not inner:
                continue
            c = one_break(y[a:b], xm[a:b], h, inner)
            f = f_test(y[a:b], xm[a:b], (c,), cov)
            if f > best:
                best, best_b = f, a + c
        stats.append(best)
        if best_b < 0 or best < crit(len(found), regimes):
            break
        found = tuple(sorted((*found, best_b)))
    return found, stats


def _funcg(x: float, bet: float, alph: float, b: float, deld: float, gam: float) -> float:
    """`mbreaks::funcg`: cdf of Bai's (1997) asymmetric limiting distribution."""
    phi = _norm_cdf
    if x <= 0:
        xb = bet * math.sqrt(abs(x))
        tail = (
            (bet / alph) * math.exp(-alph * x) * phi(-bet * math.sqrt(abs(x)))
            if abs(xb) <= 30
            else math.exp(
                math.log(bet / alph)
                - alph * x
                - xb**2 / 2
                - math.log(math.sqrt(2 * math.pi))
                - math.log(xb)
            )
            * phi(-math.sqrt(abs(x)) / 2)
        )
        return (
            -math.sqrt(-x / (2 * math.pi)) * math.exp(x / 8)
            - tail
            + ((2 * bet * bet / alph) - 2 - x / 2) * phi(-math.sqrt(abs(x)) / 2)
        )
    xb = deld * math.sqrt(x)
    tail = (
        (b * deld / gam) * math.exp(gam * x) * phi(-deld * math.sqrt(x))
        if abs(xb) <= 30
        else math.exp(
            math.log(b * deld / gam)
            + gam * x
            - xb**2 / 2
            - math.log(math.sqrt(2 * math.pi))
            - math.log(xb)
        )
    )
    return (
        1
        + (b / math.sqrt(2 * math.pi)) * math.sqrt(x) * math.exp(-b * b * x / 8)
        + tail
        + (2 - b * b * x / 2 - 2 * deld * deld / gam) * phi(-b * math.sqrt(x) / 2)
    )


def _norm_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2))


def bai_quantiles(eta: float, phi1s: float, phi2s: float) -> tuple[float, ...]:
    """`mbreaks::cvg`: 2.5, 5, 95 and 97.5 % quantiles by bisection on [-2000, 2000].

    Kept as in `mbreaks`, including its iteration cap (99 halvings, tolerance 1e-6 on the
    cdf)."""
    a = phi1s / phi2s
    gam = ((phi2s / phi1s) + 1) * eta / 2
    b = math.sqrt(phi1s * eta / phi2s)
    deld = math.sqrt(phi2s * eta / phi1s) + b / 2
    alph = a * (1 + a) / 2
    bet = (1 + 2 * a) / 2
    out = []
    for sig in (0.025, 0.05, 0.95, 0.975):
        upb, lwb, crit, cct, xx = 2000.0, -2000.0, 999999.0, 1, 0.0
        while abs(crit) >= 1e-6:
            cct += 1
            if cct > 100:
                break
            xx = lwb + (upb - lwb) / 2
            crit = _funcg(xx, bet, alph, b, deld, gam) - sig
            if crit <= 0:
                lwb = xx
            else:
                upb = xx
        out.append(xx)
    return tuple(out)


@dataclass(frozen=True)
class Interval:
    """Bai (1997) interval for one break, in row indices (first row of the new regime).

    raw_*: b - c / a before rounding. lo/hi: `mbreaks` rounding, round(b - c_hi / a) and
    round(b - c_lo / a) + 1, applied once (see `break_intervals`)."""

    raw95: tuple[float, float]
    raw90: tuple[float, float]
    lo95: int
    hi95: int
    lo90: int
    hi90: int


def break_intervals(y: Arr, xm: Arr, breaks_: tuple[int, ...], cov: Cov) -> list[Interval]:
    """`mbreaks::interval` (p = 0), heterogeneous options from `cov` (ADR 0007 §7).

    `mbreaks` 1.0.1 applies its rounding and "+ 1" inside the loop over breaks, so the upper
    bound of break i is raised by one row m - i + 1 times. Here it is applied once; for m = 1
    the two agree. The difference is reported by the R cross-check."""
    n_obs, q = xm.shape
    zm = diag_partition(xm, breaks_)
    delta, *_ = np.linalg.lstsq(zm, y, rcond=None)
    res = y - zm @ delta
    edges = [0, *breaks_, n_obs]
    out = []
    for i in range(len(breaks_)):
        dv = delta[(i + 1) * q : (i + 2) * q] - delta[i * q : (i + 1) * q]
        r0, r1, r2 = edges[i], edges[i + 1], edges[i + 2]
        if cov.hetq:
            qm = xm[r0:r1].T @ xm[r0:r1] / (r1 - r0)
            qm1 = xm[r1:r2].T @ xm[r1:r2] / (r2 - r1)
        else:
            qm = qm1 = xm.T @ xm / n_obs
        dq = float(dv @ qm @ dv)
        eta = float(dv @ qm1 @ dv) / dq
        if not cov.robust:
            if cov.hetomega:
                phi1s = float(res[r0:r1] @ res[r0:r1]) / (r1 - r0)
                phi2s = float(res[r1:r2] @ res[r1:r2]) / (r2 - r1)
            else:
                phi1s = phi2s = float(res @ res) / n_obs
            a = dq / phi1s
        else:
            if cov.hetomega:
                om = lrv(xm[r0:r1], res[r0:r1], cov)
                om1 = lrv(xm[r1:r2], res[r1:r2], cov)
            else:
                om = om1 = lrv(xm, res, cov)
            phi1s = float(dv @ om @ dv) / dq
            phi2s = float(dv @ om1 @ dv) / dq
            a = dq**2 / float(dv @ om @ dv)
        c = bai_quantiles(eta, phi1s, phi2s)
        b = breaks_[i]
        raw95 = (b - c[3] / a, b - c[0] / a)
        raw90 = (b - c[2] / a, b - c[1] / a)
        out.append(
            Interval(
                raw95,
                raw90,
                _rround(raw95[0]),
                _rround(raw95[1]) + 1,
                _rround(raw90[0]),
                _rround(raw90[1]) + 1,
            )
        )
    return out


def _rround(x: float) -> int:
    """R's round(): half to even, as Python's round()."""
    return int(round(x))


def regime_table(y: Arr, xm: Arr, breaks_: tuple[int, ...], cov: Cov) -> tuple[Arr, Arr]:
    """Regime coefficients and HAC standard errors (`mbreaks::estim`, p = 0)."""
    delta, vdel = coef_cov(y, xm, breaks_, cov)
    q = xm.shape[1]
    return delta.reshape(-1, q), np.sqrt(np.diag(vdel)).reshape(-1, q)


def month_starts(dates: list[np.datetime64] | NDArray[np.datetime64]) -> list[int]:
    """Indices of the first usable row of each calendar month (ADR 0007 §3.2 primary grid).
    Row 0 is excluded: the sample's first row cannot start a new regime."""
    months = np.asarray(dates, dtype="datetime64[M]")
    return [int(i) for i in np.flatnonzero(months[1:] != months[:-1]) + 1]
