"""Reference distributions, robust BG test and wild fixed-regressor bootstrap (ADR 0007 §6).

- Limit draws (§6.1): the Brownian-motion limits of sup F_T(k) and sup F(l + 1 | l), evaluated
  exactly at the candidate fractions of a cell. W is sampled at the candidates, so the only
  approximation is the limit itself.
- `robust_bg` (§6.3 step 1): residual on regressors and its own lags, HC0 joint test.
- `wf_sup_wald` (§6.3 step 2): Boldea, Cornea-Madeira and Hall (2019) §2.3, eqs. (15)-(21)
  and (23), specialised to OLS (no endogenous regressors, so v_t = 0 and x-hat = x).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from kagura import breaks

Arr = NDArray[np.float64]


def _nodes(candidates: list[int], n_obs: int, h: int) -> tuple[Arr, NDArray[np.int64]]:
    rows = np.array([0, *sorted(c for c in candidates if h <= c <= n_obs - h), n_obs])
    return rows / n_obs, rows


def supf_limit(
    candidates: list[int],
    n_obs: int,
    h: int,
    q: int,
    m_max: int,
    draws: int,
    seed: int,
    chunk: int = 32,
) -> Arr:
    """Draws of the sup F_T(k) limit for k = 1..m_max, shape (draws, m_max).

    F(k) = (1/k) [max over partitions of sum_j |W(l_j) - W(l_{j-1})|^2 / (l_j - l_{j-1})
    - |W(1)|^2], partitions on the candidates with every regime at least h rows. This is the
    Wald/k scale of Bai and Perron (2003b) ("multiplied by q", ADR 0007 §6.1). The maximum is
    found by dynamic programming for every draw."""
    lam, rows = _nodes(candidates, n_obs, h)
    valid = rows[None, :] - rows[:, None] >= h
    sd = np.sqrt(np.diff(lam))
    rng = np.random.default_rng(seed)
    out = np.empty((draws, m_max))
    for s in range(0, draws, chunk):
        r = min(chunk, draws - s)
        dw = rng.standard_normal((r, len(lam) - 1, q)) * sd[None, :, None]
        p = np.concatenate([np.zeros((r, 1, q)), np.cumsum(dw, axis=1)], axis=1)
        out[s : s + r] = supf_from_paths(p, lam, valid, m_max)
    return out


def supf_from_paths(p: Arr, lam: Arr, valid: NDArray[np.bool_], m_max: int) -> Arr:
    """sup F(k) limits, k = 1..m_max, for paths p (draws, nodes, q) of W at fractions lam
    (first 0, last 1); valid[a, b] marks admissible segments between nodes a < b."""
    span = np.where(valid, lam[None, :] - lam[:, None], 1.0)
    sq = np.einsum("rnq,rnq->rn", p, p)
    seg = sq[:, None, :] + sq[:, :, None] - 2 * (p @ p.transpose(0, 2, 1))
    seg /= span
    seg[:, ~valid] = -np.inf
    best = seg[:, 0, :]
    out = np.empty((len(p), m_max))
    for k in range(1, m_max + 1):
        best = np.max(best[:, :, None] + seg, axis=1)
        out[:, k - 1] = (best[:, -1] - sq[:, -1]) / k
    return out


def supf1_limit(
    fractions: Arr, q: int, draws: int, rng: np.random.Generator, chunk: int = 2048
) -> Arr:
    """Draws of sup over `fractions` (in (0, 1)) of the one-break F limit, shape (draws,)."""
    lam = np.concatenate([[0.0], np.sort(fractions), [1.0]])
    sd = np.sqrt(np.diff(lam))
    mu = lam[1:-1]
    out = np.empty(draws)
    for s in range(0, draws, chunk):
        r = min(chunk, draws - s)
        p = np.cumsum(rng.standard_normal((r, len(sd), q)) * sd[None, :, None], axis=1)
        pt = p[:, -1, :]
        pm = p[:, :-1, :]
        f = (
            np.einsum("rnq,rnq->rn", pm, pm) / mu
            + np.einsum("rnq,rnq->rn", pt[:, None] - pm, pt[:, None] - pm) / (1 - mu)
            - np.einsum("rq,rq->r", pt, pt)[:, None]
        )
        out[s : s + r] = f.max(axis=1)
    return out


def seq_limit(
    regimes: list[tuple[int, int]],
    candidates: list[int],
    h: int,
    q: int,
    draws: int,
    seed: int,
) -> Arr:
    """Draws of the sup F(l + 1 | l) limit for the given l-break regimes (ADR 0007 §6.1):
    the maximum over regimes of independent one-break limits, each on that regime's own
    candidates (h rows from either end). Regimes shorter than 2h contribute nothing, as in
    `breaks.sequential`."""
    rng = np.random.default_rng(seed)
    out = np.zeros(draws)
    for a, b in regimes:
        inner = np.array([c for c in candidates if a + h <= c <= b - h], dtype=float)
        if b - a < 2 * h or not len(inner):
            continue
        out = np.maximum(out, supf1_limit((inner - a) / (b - a), q, draws, rng))
    return out


@dataclass(frozen=True)
class Quantile:
    value: float
    lo: float  # binomial order-statistic 95 % interval
    hi: float
    draws: int


def quantile(x: Arr, p: float = 0.95) -> Quantile:
    """Empirical p-quantile with a binomial order-statistic 95 % interval."""
    s = np.sort(x)
    n = len(s)
    half = 1.96 * math.sqrt(n * p * (1 - p))
    k = math.ceil(n * p) - 1
    lo, hi = max(0, math.floor(n * p - half) - 1), min(n - 1, math.ceil(n * p + half) - 1)
    return Quantile(float(s[k]), float(s[lo]), float(s[hi]), n)


def tail_prob(x: Arr, stat: float) -> float:
    """Share of draws at or above stat: a simulated p-value."""
    return float(np.mean(x >= stat))


def wd_weights(cv: Arr) -> Arr:
    """WDmax weights c(1) / c(k) from 5 % critical values (Bai and Perron 1998, `mbreaks`)."""
    return np.asarray(cv[0] / cv, dtype=np.float64)


def robust_bg(resid: Arr, xm: Arr, lags: int = 10) -> tuple[float, float]:
    """ADR 0007 §6.3 step 1: regress the residual on the regressors and its own `lags` lags
    (zero-filled before the first row, as in Breusch-Godfrey), and test the lag coefficients
    jointly with an Eicker-White (HC0) covariance. Returns (Wald, chi2(lags) p-value)."""
    n_obs = len(resid)
    lagm = np.column_stack(
        [np.concatenate([np.zeros(i), resid[: n_obs - i]]) for i in range(1, lags + 1)]
    )
    xa = np.column_stack([xm, lagm])
    xx_inv = np.linalg.inv(xa.T @ xa)
    coef = xx_inv @ xa.T @ resid
    e = resid - xa @ coef
    meat = (xa * (e * e)[:, None]).T @ xa
    v = xx_inv @ meat @ xx_inv
    g = coef[-lags:]
    w = float(g @ np.linalg.solve(v[-lags:, -lags:], g))
    return w, float(stats.chi2.sf(w, lags))


def _node_sums(z: Arr, w: Arr, edges: NDArray[np.int64]) -> Arr:
    """Cumulative sums over rows of w, evaluated at `edges` (first entry 0)."""
    c = np.concatenate([np.zeros((1, *w.shape[1:])), np.cumsum(w, axis=0)])
    return np.asarray(c[edges], dtype=np.float64)


def _ew_wald_h1(y: Arr, xm: Arr, a: int, b: int, cand: list[int]) -> Arr:
    """Wald(c) for one break at each c in cand inside rows [a, b), each sub-regime with its
    own OLS fit and an Eicker-White meat from its own (H1) residuals (Boldea et al. §2.2):
    W = d'(V1 + V2)^-1 d, V_j = Q_j^-1 M_j Q_j^-1 (the T scalings cancel)."""
    z, yy = xm[a:b], y[a:b]
    edges = np.array([0, *[c - a for c in cand], b - a])
    zz = _node_sums(z, z[:, :, None] * z[:, None, :], edges)
    zy = _node_sums(z, z * yy[:, None], edges)
    a2 = _node_sums(z, (z[:, :, None] * z[:, None, :]) * (yy * yy)[:, None, None], edges)
    z2 = z[:, :, None] * z[:, None, :]
    a3 = _node_sums(z, z2[:, :, :, None] * (z * yy[:, None])[:, None, None, :], edges)
    a4 = _node_sums(z, z2[:, :, :, None, None] * z2[:, None, None, :, :], edges)
    out = np.empty(len(cand))
    for i in range(1, len(edges) - 1):
        parts = []
        for lo, hi in ((0, i), (i, len(edges) - 1)):
            q_ = zz[hi] - zz[lo]
            beta = np.linalg.solve(q_, zy[hi] - zy[lo])
            m = (
                (a2[hi] - a2[lo])
                - 2 * np.einsum("abc,c->ab", a3[hi] - a3[lo], beta)
                + np.einsum("abcd,c,d->ab", a4[hi] - a4[lo], beta, beta)
            )
            qi = np.linalg.inv(q_)
            parts.append((beta, qi @ m @ qi))
        d = parts[0][0] - parts[1][0]
        out[i - 1] = float(d @ np.linalg.solve(parts[0][1] + parts[1][1], d))
    return out


@dataclass(frozen=True)
class Bootstrap:
    stat: float
    regime: int  # index of the regime giving the maximum
    date: int  # sup-Wald date in that regime (row index, first row of the new regime)
    boot: Arr  # B bootstrap statistics
    p_value: float  # share of bootstrap statistics at or above stat
    cv95: float


def wf_sup_wald(
    y: Arr,
    xm: Arr,
    breaks_: tuple[int, ...],
    candidates: list[int],
    h: int,
    reps: int = 999,
    seed: int = 0,
) -> Bootstrap:
    """WF bootstrap of sup-Wald(l + 1 | l), with l = len(breaks_) held at its estimate
    (Boldea et al. 2019, case (ii); l = 0 is case (i) with one break).

    Null fit: OLS in each of the l + 1 regimes; u-hat its (non-centred) residuals.
    Bootstrap: y* = fit + u-hat * nu, nu Rademacher, regressors fixed (eq. 15-16).
    Statistic: max over regimes of at least 2h rows of the sup over its candidates of the
    one-break Wald (eq. 23). Original sample: Eicker-White meat from H1 residuals. Bootstrap:
    meat EW[z u*] (eq. 21 with v = 0), which with nu^2 = 1 equals EW[z u-hat]."""
    n_obs, q = xm.shape
    zm = breaks.diag_partition(xm, breaks_)
    coef, *_ = np.linalg.lstsq(zm, y, rcond=None)
    uhat = y - zm @ coef
    rng = np.random.default_rng(seed)
    nu = rng.choice(np.array([-1.0, 1.0]), size=(n_obs, reps))
    stat, best_reg, best_date = -np.inf, -1, -1
    boot = np.full(reps, -np.inf)
    for j, (a, b) in enumerate(breaks.regime_bounds(breaks_, n_obs)):
        cand = [c for c in candidates if a + h <= c <= b - h]
        if b - a < 2 * h or not cand:
            continue
        w = _ew_wald_h1(y, xm, a, b, cand)
        if w.max() > stat:
            stat, best_reg, best_date = float(w.max()), j, cand[int(w.argmax())]
        z, u = xm[a:b], uhat[a:b]
        edges = np.array([0, *[c - a for c in cand], b - a])
        zz = _node_sums(z, z[:, :, None] * z[:, None, :], edges)
        zzu = _node_sums(z, z[:, :, None] * z[:, None, :] * (u * u)[:, None, None], edges)
        blocks = np.stack(
            [
                (z[lo:hi] * u[lo:hi, None]).T @ nu[a + lo : a + hi]
                for lo, hi in zip(edges[:-1], edges[1:], strict=True)
            ]
        )
        g = np.concatenate([np.zeros((1, q, reps)), np.cumsum(blocks, axis=0)])
        for i in range(1, len(edges) - 1):
            q1, q2 = zz[i], zz[-1] - zz[i]
            q1i, q2i = np.linalg.inv(q1), np.linalg.inv(q2)
            v = q1i @ zzu[i] @ q1i + q2i @ (zzu[-1] - zzu[i]) @ q2i
            d = q1i @ g[i] - q2i @ (g[-1] - g[i])
            wb = np.einsum("qr,qr->r", d, np.linalg.solve(v, d))
            boot = np.maximum(boot, wb)
    return Bootstrap(
        stat, best_reg, best_date, boot, float(np.mean(boot >= stat)), quantile(boot).value
    )
