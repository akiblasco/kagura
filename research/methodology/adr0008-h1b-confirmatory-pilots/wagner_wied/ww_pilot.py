import sys, itertools, time, numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, "../ak_bounds")
from simlib import ak_dgp
from wwlib import ww_stat
T0, MW = 492, 55; N = T0 + MW; GAP = T0 + 45
CV = {"pkg": 0.3174, "own": 0.3111}                      # 97.5 %: cointmonitoR interp at m=492/547; own 100k-rep limit sim
VARIANTS = [("FM", "andrews", None), ("FM", "nw", None), ("FM", "large", None), ("FM", "andrews", GAP), ("D", "andrews", None), ("D", "andrews", GAP)]

def gen(rng, rho, law, dtype, drift, alt):
    u, X = ak_dgp(rng, N, rho, law, 0.5, drift, dtype)
    sig = 1 / np.sqrt(1 - rho**2) if rho < 1 else 1.0
    if alt:
        kind, size = alt; d = X[:, 2]
        if kind == "shift": u[T0:] += size * sig
        if kind == "slope": u[T0:] += size * sig / np.sqrt(MW / 2) * (d[T0:] - d[T0 - 1])
        if kind == "rw": u[T0:] += np.sqrt(2) * rng.standard_normal(MW).cumsum()
        if kind == "var": u[T0:] = u[T0 - 1] * rho ** np.arange(1, MW + 1) + (u[T0:] - u[T0 - 1] * rho ** np.arange(1, MW + 1)) * np.sqrt(size)
    return u, X[:, 1:]

def cell(a):
    key, R, seed = a; rho, law, dtype, drift, alt = key
    rng = np.random.default_rng(seed); out = np.empty((R, len(VARIANTS))); t0 = time.time()
    for r in range(R):
        y, X = gen(rng, rho, law, dtype, drift, alt)
        out[r] = [ww_stat(y, X, T0, est, bw, gap) for est, bw, gap in VARIANTS]
    return key, out, (time.time() - t0) / R

def cp(k, n, a=.05):
    return (stats.beta.ppf(a / 2, k, n - k + 1) if k else 0.0, stats.beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0)

if __name__ == "__main__":
    Rn, Rp = int(sys.argv[1]), int(sys.argv[2])
    null = [(rho, law, d, 0.0, None) for rho, law, d in itertools.product((0, .8, .95, .98), ("normal", "garch"), ("I1", "I0"))]
    drift = [(rho, "normal", "I1", 0.5, None) for rho in (0, .8, .95, .98)]
    power = [(rho, "normal", "I1", 0.0, alt) for rho in (.95, .98) for alt in (("shift", 1), ("shift", 2), ("slope", 1), ("rw", None), ("var", 2))]
    jobs = [(k, Rn, [20261024, i]) for i, k in enumerate(null + drift)] + [(k, Rp, [20261024, 100 + i]) for i, k in enumerate(power)]
    res = {}
    with ProcessPoolExecutor(10) as ex:
        for k, o, sec in ex.map(cell, jobs): res[k] = (o, sec)
    np.save("ww_pilot.npy", {k: v[0] for k, v in res.items()}, allow_pickle=True)
    names = ["FM-and", "FM-nw", "FM-large", "FM-and+gap", "D-and", "D-and+gap"]
    print("NULL rejection at 97.5% CV (pkg 0.3174) [95% Clopper-Pearson]; R =", Rn)
    for k in null + drift:
        o, sec = res[k]; n = len(o); line = f"rho={k[0]:<5}{k[1]:<7}d={k[2]} drift={k[3]}:"
        for j, nm in enumerate(names):
            c = int((o[:, j] > CV["pkg"]).sum()); lo, hi = cp(c, n); line += f" {nm} {c/n:.3f}[{lo:.3f},{hi:.3f}]"
        print(line + f"  ({sec*1e3:.0f} ms/rep)", flush=True)
    print("\nOwn-CV (0.3111) FM-and rates, base cells:", [round(float((res[k][0][:, 0] > CV['own']).mean()), 3) for k in null])
    print("\nPOWER (FM-andrews, no gap): raw at pkg CV | size-corrected at the null cell's own 97.5% quantile; R =", Rp)
    for k in power:
        o = res[k][0][:, 0]; n0 = res[(k[0], "normal", "I1", 0.0, None)][0][:, 0]; q = np.quantile(n0, .975)
        print(f"rho={k[0]} alt={k[4]}: raw {np.mean(o > CV['pkg']):.3f}  size-corrected {np.mean(o > q):.3f}  (null 97.5% quantile {q:.3f})")
