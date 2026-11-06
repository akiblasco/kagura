"""ADR 0007 §6.1: compare simulated sup F(1) quantiles with the Bai–Perron tables.

Synthetic only. The limit of sup F(1) with q breaking coefficients, on the Wald scale the
tables use, is sup over eps <= l <= 1 - eps of |W(l) - l W(1)|^2 / (l (1 - l)), W a
q-dimensional Brownian motion approximated by an n-step random walk.

Run from the repository root:
    uv run python research/methodology/adr0007-break-grid/critical_values_check.py [n] [draws]
"""

from __future__ import annotations

import sys

import numpy as np

# m = 1 column of mbreaks 1.0.1 R/supF/cv_{1,2,3}.csv, rows q = 1, 2: (10 %, 5 %).
TABLE = {
    (1, 0.15): (7.04, 8.58),
    (2, 0.15): (9.81, 11.47),
    (1, 0.10): (7.42, 9.10),
    (2, 0.10): (10.37, 12.25),
    (1, 0.05): (8.02, 9.63),
    (2, 0.05): (11.02, 12.89),
}
SEED = 20261106
CHUNK = 1000


def simulate(q: int, n: int, draws: int, rng: np.random.Generator) -> dict[float, np.ndarray]:
    lam = np.arange(1, n + 1) / n
    out: dict[float, list[np.ndarray]] = {e: [] for e in (0.15, 0.10, 0.05)}
    for _ in range(draws // CHUNK):
        w = np.cumsum(rng.standard_normal((CHUNK, q, n)), axis=2) / np.sqrt(n)
        bridge = w - lam * w[:, :, -1:]
        stat = (bridge**2).sum(axis=1)[:, :-1] / (lam[:-1] * (1 - lam[:-1]))
        for eps in out:
            keep = (lam[:-1] >= eps) & (lam[:-1] <= 1 - eps)
            out[eps].append(stat[:, keep].max(axis=1))
    return {eps: np.concatenate(v) for eps, v in out.items()}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    draws = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
    rng = np.random.default_rng(SEED)
    print(f"steps={n} draws={draws} seed={SEED}")
    for q in (1, 2):
        for eps, s in simulate(q, n, draws, rng).items():
            sim = np.quantile(s, [0.90, 0.95])
            tab = TABLE[(q, eps)]
            print(
                f"q={q} eps={eps:.2f}  sim 10%={sim[0]:.2f} 5%={sim[1]:.2f}  "
                f"table {tab[0]:.2f} {tab[1]:.2f}  "
                f"diff {sim[0] - tab[0]:+.2f} {sim[1] - tab[1]:+.2f}"
            )


if __name__ == "__main__":
    main()
