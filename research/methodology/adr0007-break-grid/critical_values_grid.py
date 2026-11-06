"""ADR 0007 §6.1, second (and last) comparison: sup F(1) quantiles by evaluation grid, with
Monte Carlo error. Synthetic only; critical_values_check.py and its output are kept as run.

One set of draws (4,000-step random walks) is evaluated on four grids, so differences between
grids are not draw-to-draw noise:
- "4000": every step (closest to the continuous limit);
- "1000": every 4th step, exactly a 1,000-step walk (the resolution of the first check);
- "548" / "164": equally spaced points standing in for the month-start grids of the full
  daily sample (about 548 months) and the 2013+ sample (about 164 months).
The statistic is the Wald-scale limit sup |W(l) - l W(1)|^2 / (l (1 - l)) over grid points with
eps <= l <= 1 - eps, as in critical_values_check.py. The 95 % interval for each quantile uses
binomial order statistics, so it needs no extra assumption about the distribution.

Run from the repository root:
    uv run python research/methodology/adr0007-break-grid/critical_values_grid.py > \
        research/methodology/adr0007-break-grid/critical_values_grid.txt
"""

from __future__ import annotations

import numpy as np

N = 4000
DRAWS = 100_000
CHUNK = 500
SEED = 20261107
GRIDS = {"4000": 4000, "1000": 1000, "548": 548, "164": 164}
EPS = (0.15, 0.10, 0.05)
TABLE = {  # mbreaks 1.0.1 R/supF/cv_{1,2,3}.csv, m = 1, rows q = 1, 2: (10 %, 5 %)
    (1, 0.15): (7.04, 8.58),
    (2, 0.15): (9.81, 11.47),
    (1, 0.10): (7.42, 9.10),
    (2, 0.10): (10.37, 12.25),
    (1, 0.05): (8.02, 9.63),
    (2, 0.05): (11.02, 12.89),
}


def grid_index(points: int, eps: float) -> np.ndarray:
    """0-based step indices of grid points l = j / points with eps <= l <= 1 - eps."""
    j = np.arange(1, points)
    lam = j / points
    j = j[(lam >= eps - 1e-12) & (lam <= 1 - eps + 1e-12)]
    return np.rint(j * N / points).astype(int) - 1


def quantile_ci(s: np.ndarray, p: float) -> tuple[float, float, float]:
    s = np.sort(s)
    n = len(s)
    half = 1.96 * np.sqrt(n * p * (1 - p))
    lo, hi = int(np.floor(n * p - half)), int(np.ceil(n * p + half))
    return float(np.quantile(s, p)), float(s[lo]), float(s[hi])


def main() -> None:
    rng = np.random.default_rng(SEED)
    lam = np.arange(1, N + 1) / N
    idx = {(g, e): grid_index(pts, e) for g, pts in GRIDS.items() for e in EPS}
    print(f"steps={N} draws={DRAWS} seed={SEED}")
    print("q eps  grid  q90 [95% CI]          q95 [95% CI]          table90 table95")
    for q in (1, 2):
        out: dict[tuple[str, float], list[np.ndarray]] = {k: [] for k in idx}
        for _ in range(DRAWS // CHUNK):
            w = np.cumsum(rng.standard_normal((CHUNK, q, N)), axis=2) / np.sqrt(N)
            stat = ((w - lam * w[:, :, -1:]) ** 2).sum(axis=1)
            for k, ix in idx.items():
                out[k].append((stat[:, ix] / (lam[ix] * (1 - lam[ix]))).max(axis=1))
        for e in EPS:
            for g in GRIDS:
                s = np.concatenate(out[(g, e)])
                a, b = quantile_ci(s, 0.90), quantile_ci(s, 0.95)
                t = TABLE[(q, e)]
                print(
                    f"{q} {e:.2f} {g:>5}  {a[0]:5.2f} [{a[1]:5.2f},{a[2]:5.2f}]  "
                    f"{b[0]:5.2f} [{b[1]:5.2f},{b[2]:5.2f}]  {t[0]:6.2f} {t[1]:6.2f}"
                )


if __name__ == "__main__":
    main()
