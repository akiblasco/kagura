import sys, time, numpy as np
from concurrent.futures import ProcessPoolExecutor
from simlib import bounds_null_data, full_design, idx_for, f_t, select
N = 492
GRID = [(1, 1, 1), (2, 2, 2), (3, 3, 3), (4, 4, 4), (6, 6, 6), (8, 8, 8), (12, 12, 12)]

def pss_asym(a):                       # PSS-table replication: levels only + const, large n
    bound, R, seed = a; rng = np.random.default_rng(seed); n = 1000; F = []; t = []
    for _ in range(R):
        e = rng.standard_normal((n + 1, 3)); y = e[:, 0].cumsum()
        xs = e[:, 1:].cumsum(0) if bound == "upper" else e[:, 1:]
        dy = np.diff(y); Z = np.column_stack([np.ones(n), y[:-1], xs[:-1]])
        b, rss = np.linalg.lstsq(Z, dy, rcond=None)[:2]; rss = rss[0]
        rr = ((dy - dy.mean()) ** 2).sum(); s2 = rss / (n - 4)
        F.append((rr - rss) / 3 / s2); t.append(b[1] / np.sqrt(s2 * np.linalg.inv(Z.T @ Z)[1, 1]))
    return bound, np.quantile(F, .975), np.quantile(t, .025)

def fixed(a):
    order, bound, dgp, R, seed = a; rng = np.random.default_rng(seed); F = []; t = []
    for _ in range(R):
        y, X, nm = full_design(*bounds_null_data(rng, N, bound, dgp))
        f, tt, _, _ = f_t(y, X, nm, idx_for(nm, *order)); F.append(f); t.append(tt)
    return a[:3], np.array(F), np.array(t)

def selected(a):
    dgp, R, seed = a; rng = np.random.default_rng(seed); out = []; t0 = time.time()
    for _ in range(R):
        y, X, nm = full_design(*bounds_null_data(rng, N, "upper", dgp))
        o, f, tt = select(y, X, nm); out.append((o, f, tt))
    return dgp, out, (time.time() - t0) / R

if __name__ == "__main__":
    Rf, Rs = int(sys.argv[1]), int(sys.argv[2])
    with ProcessPoolExecutor(10) as ex:
        print("PSS asymptotic replication (n=1000, 200k reps split):")
        for b in ("lower", "upper"):
            parts = list(ex.map(pss_asym, [(b, 20000, [1, k, b == "upper"]) for k in range(10)]))
            print(f"  {b}: F97.5 ~ {np.mean([p[1] for p in parts]):.3f}  t2.5 ~ {np.mean([p[2] for p in parts]):.3f}   (PSS: F {'4.41' if b=='lower' else '5.52'}, t {'-3.13' if b=='lower' else '-3.80'})")
        jobs = [(o, b, "iid", Rf, [2, i, j]) for i, o in enumerate(GRID) for j, b in enumerate(("upper", "lower"))]
        jobs += [((1, 1, 1), "upper", g, Rf, [3, k]) for k, g in enumerate(("dyn", "garch", "drift", "t5"))]
        jobs += [((4, 4, 4), "upper", g, Rf, [4, k]) for k, g in enumerate(("dyn", "garch", "drift", "t5"))]
        fx = {k: (F, t) for k, F, t in ex.map(fixed, jobs)}
        sel = {g: (out, sec) for g, out, sec in ex.map(selected, [(g, Rs, [5, k]) for k, g in enumerate(("iid", "dyn", "garch", "drift"))])}
    np.save("bounds_pilot.npy", {"fx": fx, "sel": sel}, allow_pickle=True)
    print("\nFixed-order CVs (n=480, design dummies): order bound dgp: F97.5 t2.5 | joint pass rate under null using own CVs")
    cv = {}
    for k, (F, t) in fx.items():
        cf, ct = np.quantile(F, .975), np.quantile(t, .025); cv[k] = (cf, ct)
        print(f"  {k}: F={cf:.3f} t={ct:.3f}  joint(F>cF & t<ct)={np.mean((F > cf) & (t < ct)):.4f}")
    Ks = np.array([(o[0] - 1) + o[1] + o[2] for o in GRID])
    cF = np.array([cv[(o, 'upper', 'iid')][0] for o in GRID]); cT = np.array([cv[(o, 'upper', 'iid')][1] for o in GRID])
    print("\nFull BG-filtered AIC selection under upper-bound null:")
    for g, (out, sec) in sel.items():
        ok = [o for o in out if o[0] is not None]
        K = np.array([(o[0][0] - 1) + o[0][1] + o[0][2] for o in ok]); F = np.array([o[1] for o in ok]); t = np.array([o[2] for o in ok])
        cf_c, ct_c = np.interp(K, Ks, cF), np.interp(K, Ks, cT)          # CVs conditional on the selected order (iid design)
        pF, pT = np.quantile(F, .975), np.quantile(t, .025)               # unconditional full-procedure CVs
        print(f"  {g:<6} {sec:.2f}s/rep  none-pass-BG={1-len(ok)/len(out):.3f}  median K_sr={np.median(K):.0f} (IQR {np.percentile(K,25):.0f}-{np.percentile(K,75):.0f})"
              f"\n         conditional-CV rejection: F {np.mean(F>cf_c):.4f}  t {np.mean(t<ct_c):.4f}  joint {np.mean((F>cf_c)&(t<ct_c)):.4f}"
              f"\n         full-procedure CVs: F97.5={pF:.3f} t2.5={pT:.3f}  (iid fixed (1,1,1): F={cF[0]:.3f} t={cT[0]:.3f})")
