import sys, itertools, numpy as np
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, "../ak_bounds")
from ww_pilot import gen, T0
from wwlib import ww_stat
def cell(a):
    key, R, seed = a; rng = np.random.default_rng(seed); o = []; bws = []
    for _ in range(R):
        y, X = gen(rng, key[0], key[1], key[2], key[3], key[4])
        o.append([ww_stat(y, X, T0, "FM", "andrews_nocap"), ww_stat(y, X, T0, "D", "andrews_nocap")])
    return key, np.array(o)
if __name__ == "__main__":
    cells = [(r, "normal", d, 0.0, None) for r in (0, .8, .95, .98) for d in ("I1", "I0")] + [(.98, "garch", "I1", 0.0, None)]
    cells += [(r, "normal", "I1", 0.0, a) for r in (.95, .98) for a in (("shift", 1), ("shift", 2), ("slope", 1), ("rw", None))]
    with ProcessPoolExecutor(10) as ex:
        res = dict(ex.map(cell, [(k, 2000 if k[4] is None else 1000, [20261025, i]) for i, k in enumerate(cells)]))
    np.save("ww_nocap.npy", res, allow_pickle=True)
    for k, o in res.items():
        print(f"{str(k):<45} FM-nocap {np.mean(o[:,0] > 0.3174):.3f}   D-nocap {np.mean(o[:,1] > 0.3174):.3f}")
