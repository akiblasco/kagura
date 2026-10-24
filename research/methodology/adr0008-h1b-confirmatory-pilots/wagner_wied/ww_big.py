import sys, numpy as np
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, "../ak_bounds")
from ww_pilot import gen, T0
from wwlib import ww_stat
def cell(a):
    key, R, seed = a; rng = np.random.default_rng(seed)
    return key, np.array([[ww_stat(*gen(rng, *key), T0, e, "andrews") for e in ("FM", "D")] for _ in range(R)])
if __name__ == "__main__":
    cells = [(r, "normal", "I1", 0.0, a) for r in (.8, .95, .98) for a in (None, ("shift", 4), ("shift", 6))]
    with ProcessPoolExecutor(9) as ex:
        res = dict(ex.map(cell, [(k, 1000, [20261026, i]) for i, k in enumerate(cells)]))
    for k, o in res.items():
        n0 = res[(k[0], "normal", "I1", 0.0, None)]
        print(f"rho={k[0]} {str(k[4]):<14} FM raw {np.mean(o[:,0]>.3174):.3f} sc {np.mean(o[:,0]>np.quantile(n0[:,0],.975)):.3f} | D raw {np.mean(o[:,1]>.3174):.3f} sc {np.mean(o[:,1]>np.quantile(n0[:,1],.975)):.3f}")
