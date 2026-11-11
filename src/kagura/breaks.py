"""Multiple structural-break estimation for ADR 0007 (pure structural change).

Conventions (ADR 0007 §3.2): a break is the 0-based index of the **first row of the new
regime**. `strucchange` reports the last row of the old regime, i.e. our index (1-based)
minus one: our b (0-based) equals strucchange's breakpoint (1-based).

Every regime has at least h rows; break positions are restricted to `candidates`.
"""

from __future__ import annotations

import math
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
    h <= b <= T - h. Segment SSRs are computed once for every pair of nodes."""
    n_obs = len(y)
    cand = sorted(range(h, n_obs - h + 1) if candidates is None else candidates)
    cand = [b for b in cand if h <= b <= n_obs - h]
    nodes = [0, *cand, n_obs]
    n = len(nodes)
    ssr = np.full((n, n), np.inf)
    for a in range(n):
        for b in range(a + 1, n):
            if nodes[b] - nodes[a] >= h:
                ssr[a, b] = segment_ssr(y, xm, nodes[a], nodes[b])
    # best[k][b]: min SSR of rows 0..nodes[b] split into k + 1 segments; arg for backtracking.
    best = [ssr[0].copy()]
    arg: list[NDArray[np.int64]] = [np.zeros(n, dtype=np.int64)]
    for _ in range(m_max):
        prev = best[-1]
        tot = prev[:, None] + ssr  # tot[a, b] = best split ending at a, then segment a..b
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
            bs.append(nodes[idx])
            k -= 1
        out[m] = Partition(tuple(sorted(bs)), float(best[m][n - 1]))
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


def sup_f(y: Arr, xm: Arr, part: Partition, p: int = 0) -> float:
    """F_T(k) of Bai and Perron (1998) for the break dates in `part`, homoskedastic
    covariance, scaled as tabulated ("multiplied by q", ADR 0007 §6.1):
    (n_obs - (k + 1) q - p) / (n_obs k) * Wald. Evaluated at the global SSR partition, which is
    the sup F under the homoskedastic covariance used by `strucchange`/`mbreaks`
    (`prewhit = 0, robust = 0`)."""
    n_obs, q = xm.shape
    k = len(part.breaks)
    zm = np.zeros((n_obs, (k + 1) * q))
    for j, (a, b) in enumerate(regime_bounds(part.breaks, n_obs)):
        zm[a:b, j * q : (j + 1) * q] = xm[a:b]
    delta, *_ = np.linalg.lstsq(zm, y, rcond=None)
    r = y - zm @ delta
    s2 = float(r @ r) / (n_obs - (k + 1) * q - p)
    rmat = np.zeros((k * q, (k + 1) * q))
    for j in range(k):
        rmat[j * q : (j + 1) * q, j * q : (j + 1) * q] = -np.eye(q)
        rmat[j * q : (j + 1) * q, (j + 1) * q : (j + 2) * q] = np.eye(q)
    rd = rmat @ delta
    vmat = s2 * rmat @ np.linalg.inv(zm.T @ zm) @ rmat.T
    wald = float(rd @ np.linalg.solve(vmat, rd))
    return float((n_obs - (k + 1) * q - p) / (n_obs * k) * wald)


def month_starts(dates: list[np.datetime64] | NDArray[np.datetime64]) -> list[int]:
    """Indices of the first usable row of each calendar month (ADR 0007 §3.2 primary grid).
    Row 0 is excluded: the sample's first row cannot start a new regime."""
    months = np.asarray(dates, dtype="datetime64[M]")
    return [int(i) for i in np.flatnonzero(months[1:] != months[:-1]) + 1]
