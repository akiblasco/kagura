"""ADR 0007 §9.1 simulation checks: robust BG, WF bootstrap size, Bai-interval coverage.

Designs are fixed here, before any break statistic is computed on real data, and are not
calibrated to fitted values (§9.1). The only real-data inputs are structural: T and the
month-start candidate positions of each sample, and q = 4 from §6.3 step 1 (p = 1 in both
samples, `research/adr0007/out/step1_lags.csv`).

DGP for BG and bootstrap (lag-augmented layout, q = 2 + 2p = 4):
  x_t = 0.1 x_{t-1} + eta_t,  y_t = 0.02 + 0.5 x_t + 0.1 x_{t-1} + 0.05 y_{t-1} + e_t
  GARCH(1,1) MDS errors: e_t = s_t u_t, s_t^2 = 0.05 + 0.08 e_{t-1}^2 + 0.90 s_{t-1}^2
  AR(1) errors (BG power): e_t = rho e_{t-1} + u_t, rho = 0.05 and 0.10
  Lead-lag errors (non-MDS, ADR 0006 §4.5 type): e_t = 0.3 x_{t+1} + GARCH term
Fitted model: regressors (1, x_t, x_{t-1}, y_{t-1}), no breaks under the null.

Rejection rates at the 5 % level with Clopper-Pearson 95 % intervals. Pass for size: the
interval contains 0.05. Interval coverage is reported, not tuned (§7, §9.1).
Run: uv run python research/methodology/adr0007-break-grid/validation_sims.py
"""

import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

from kagura import breaks, breaksim

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "adr0007"))
SEED = 20261117
SAMPLES = {"full": 9767, "recent": 2891}  # T of the p = 1 lag-augmented samples


def grid(sample: str) -> tuple[int, list[int]]:
    from data import cell  # real dates only, for the month-start positions

    c = cell("lag", sample, 0.15, 1)
    return c.h, c.eligible()


def simulate(n_obs: int, rng: np.random.Generator, err: str) -> tuple[np.ndarray, np.ndarray]:
    burn = 200
    n = n_obs + burn + 1
    eta, u = rng.standard_normal(n), rng.standard_normal(n)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = 0.1 * x[t - 1] + eta[t]
    e = np.zeros(n)
    s2 = 0.05 / (1 - 0.98)
    for t in range(1, n):
        if err.startswith("ar1"):
            e[t] = float(err[3:]) * e[t - 1] + u[t]
        else:
            s2 = 0.05 + 0.08 * e[t - 1] ** 2 + 0.90 * s2
            e[t] = math.sqrt(s2) * u[t]
    if err == "leadlag":
        e[:-1] += 0.3 * x[1:]
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = 0.02 + 0.5 * x[t] + 0.1 * x[t - 1] + 0.05 * y[t - 1] + e[t]
    sl = slice(burn + 1, n)
    xm = np.column_stack([np.ones(n_obs), x[sl], x[burn:-1], y[burn:-1]])
    return y[sl], xm


def cp(k: int, n: int) -> tuple[float, float]:
    lo = stats.beta.ppf(0.025, k, n - k + 1) if k else 0.0
    hi = stats.beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def bg_job(args: tuple[str, str, int]) -> str:
    sample, err, reps = args
    n_obs = SAMPLES[sample]
    rng = np.random.default_rng([SEED, n_obs, len(err)])
    rej = 0
    for _ in range(reps):
        y, xm = simulate(n_obs, rng, err)
        coef, *_ = np.linalg.lstsq(xm, y, rcond=None)
        rej += breaksim.robust_bg(y - xm @ coef, xm)[1] < 0.05
    lo, hi = cp(rej, reps)
    kind = "size" if err == "garch" else "power"
    ok = "pass" if kind == "power" or lo <= 0.05 <= hi else "FAIL"
    return (
        f"{ok:4} BG {kind:5} {sample:6} T={n_obs:5} errors={err:8} "
        f"reject={rej / reps:.3f} CP95=[{lo:.3f}, {hi:.3f}] reps={reps}"
    )


def boot_job(args: tuple[str, str, int]) -> str:
    sample, err, reps = args
    n_obs = SAMPLES[sample]
    h, cand = grid(sample)
    rng = np.random.default_rng([SEED, n_obs, 7, len(err)])
    rej = 0
    for r in range(reps):
        y, xm = simulate(n_obs, rng, err)
        b = breaksim.wf_sup_wald(y, xm, (), cand, h, reps=999, seed=SEED + r)
        rej += b.p_value < 0.05
    lo, hi = cp(rej, reps)
    if err == "garch":
        ok = "pass" if lo <= 0.05 <= hi else "FAIL"
    else:
        ok = "info"
    return (
        f"{ok:4} WF size  {sample:6} T={n_obs:5} q=4 errors={err:8} "
        f"reject={rej / reps:.3f} CP95=[{lo:.3f}, {hi:.3f}] reps={reps} B=999"
    )


def ci_job(args: tuple[str, float, float, int]) -> str:
    name, shift, sd2, reps = args
    n_obs, b0 = 1000, 500
    rng = np.random.default_rng([SEED, int(shift * 100), int(sd2 * 10)])
    cov = breaks.Cov(lags=6)  # ADR 0006 §4.4 lag for T = 1000
    cover95 = cover90 = 0
    widths = []
    for _ in range(reps):
        x = rng.standard_normal(n_obs)
        t = np.arange(n_obs)
        e = rng.standard_normal(n_obs) * np.where(t < b0, 1.0, sd2)
        y = 0.1 + np.where(t < b0, 1.0, 1.0 + shift) * x + e
        xm = np.column_stack([np.ones(n_obs), x])
        bk = breaks.global_partitions(y, xm, 150, 1)[1].breaks
        iv = breaks.break_intervals(y, xm, bk, cov)[0]
        cover95 += iv.lo95 <= b0 <= iv.hi95
        cover90 += iv.lo90 <= b0 <= iv.hi90
        widths.append(iv.hi95 - iv.lo95)
    l95, h95 = cp(cover95, reps)
    return (
        f"info CI {name:22} slope shift={shift:.2f} sd after={sd2:.1f} T={n_obs} "
        f"cover95={cover95 / reps:.3f} [{l95:.3f}, {h95:.3f}] cover90={cover90 / reps:.3f} "
        f"median width95={int(np.median(widths))} rows reps={reps}"
    )


def main() -> None:
    bg = [(s, e, 1000) for s in SAMPLES for e in ("garch", "ar10.05", "ar10.10")]
    boot = [(s, e, 500) for s in SAMPLES for e in ("garch", "leadlag")]
    ci = [
        ("small", 0.15, 1.0, 1000),
        ("medium", 0.30, 1.0, 1000),
        ("large", 0.60, 1.0, 1000),
        ("medium, sd 1 -> 2", 0.30, 2.0, 1000),
    ]
    with ProcessPoolExecutor(max_workers=10) as ex:
        out = list(ex.map(bg_job, bg)) + list(ex.map(boot_job, boot)) + list(ex.map(ci_job, ci))
    fails = sum(r.startswith("FAIL") for r in out)
    out.append(f"summary: {len(out)} rows, {fails} FAIL")
    (HERE / "validation_sims.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
