"""ADR 0012 §3: coverage of Bai intervals, corrected phi2s against the original (`mbreaks`).

DGP, one slope break at k0 (fixed here, not calibrated to fitted values):
  y_t = 0.5 x_t + shift * 1[t >= k0] * x_t + e_t,  e_t ~ N(0, 1),
  x_t ~ N(0, 1), multiplied by sqrt(eta) from k0 on, so Δ'Q2Δ / Δ'Q1Δ ≈ eta.
Shifts 0.15 / 0.30 / 0.60 as in ADR 0011 §6; eta = 0.25, 1, 4.

Grid and sizes are Phase A's: the primary-specification month-start eligible candidates and
T of each sample at ε = 15 % (`research/adr0007/data.py`; only frozen dates are used, nothing
is fitted to USD/JPY). k0 is the eligible candidate nearest T / 2.
Estimation as in Phase A: m = 1 least-squares break on that grid, Cov(lags = ADR 0006 lag),
rounded bounds. Coverage: lo <= k0 <= hi. Clopper-Pearson 95 % intervals.
Run: uv run python research/methodology/adr0012-bai-interval/coverage.py
"""

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

from kagura import breaks

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "adr0007"))
sys.path.insert(0, str(HERE.parent / "adr0007-break-grid/r-crosscheck"))
from compare import mbreaks_interval  # noqa: E402  (original phi2s, for comparison)

SEED = 20261118
REPS = 1000
SHIFTS = (0.15, 0.30, 0.60)
ETAS = (0.25, 1.0, 4.0)


def grid(sample: str) -> tuple[int, int, list[int], int]:
    from data import cell  # frozen dates only, for T, h and month-start positions

    c = cell("primary", sample, 0.15)
    return c.n_obs, c.h, c.eligible(), c.lags


def cp(k: int, n: int) -> tuple[float, float]:
    lo = stats.beta.ppf(0.025, k, n - k + 1) if k else 0.0
    hi = stats.beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def job(args: tuple[str, float, float]) -> list[str]:
    sample, shift, eta = args
    n_obs, h, cand, lags = grid(sample)
    k0 = min(cand, key=lambda b: abs(b - n_obs / 2))
    cov = breaks.Cov(lags=lags)
    rng = np.random.default_rng([SEED, n_obs, int(shift * 100), int(eta * 100)])
    t = np.arange(n_obs)
    res: dict[str, list[tuple[int, int, int, int]]] = {"corrected": [], "original": []}
    for _ in range(REPS):
        x = rng.standard_normal(n_obs) * np.where(t < k0, 1.0, np.sqrt(eta))
        y = 0.5 * x + np.where(t >= k0, shift, 0.0) * x + rng.standard_normal(n_obs)
        xm = np.column_stack([np.ones(n_obs), x])
        bk = breaks.global_partitions(y, xm, h, 1, cand)[1].breaks
        for name, iv in (
            ("corrected", breaks.break_intervals(y, xm, bk, cov)[0]),
            ("original", mbreaks_interval(y, xm, bk, cov)[0]),
        ):
            res[name].append((iv.lo95, iv.hi95, iv.lo90, iv.hi90))
    out = []
    for name, r in res.items():
        a = np.array(r)
        c95 = int(np.sum((a[:, 0] <= k0) & (k0 <= a[:, 1])))
        c90 = int(np.sum((a[:, 2] <= k0) & (k0 <= a[:, 3])))
        left, right = np.mean(k0 < a[:, 0]), np.mean(k0 > a[:, 1])
        lo, hi = cp(c95, REPS)
        out.append(
            f"{sample:6} T={n_obs:5} shift={shift:.2f} eta={eta:<4} {name:9} "
            f"cover95={c95 / REPS:.3f} [{lo:.3f}, {hi:.3f}] cover90={c90 / REPS:.3f} "
            f"true<lo={left:.3f} true>hi={right:.3f} "
            f"median width95={int(np.median(a[:, 1] - a[:, 0]))} rows"
        )
    return out


def main() -> None:
    designs = [(s, sh, e) for s in ("recent", "full") for sh in SHIFTS for e in ETAS]
    with ProcessPoolExecutor(max_workers=9) as ex:
        lines = [ln for block in ex.map(job, designs) for ln in block]
    header = f"ADR 0012 coverage study, seed {SEED}, {REPS} reps per design, nominal 95 % / 90 %"
    (HERE / "coverage.txt").write_text("\n".join([header, *lines]) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
