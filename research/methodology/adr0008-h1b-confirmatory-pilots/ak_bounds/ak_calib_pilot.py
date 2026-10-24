import numpy as np
from concurrent.futures import ProcessPoolExecutor
from simlib import ak_dgp, ak_p
T, m, J = 492, 55, 438
ALTS = [None, ("shift", 1.0), ("shift", 2.0), ("ramp", 2.0), ("rw", None), ("var", 2.0), ("early_shift", 1.0)]

def cell(a):
    rho, law, R = a
    out = {}
    for ai, alt in enumerate(ALTS):
        rng = np.random.default_rng([11, int(rho * 100), len(law), ai])
        out[alt] = np.array([ak_p(*ak_dgp(rng, T + m, rho, law, 0, .5, "I1", T=T, alt=alt), T, m, 45)[1] for _ in range(R)])
    return a[:2], out

if __name__ == "__main__":
    grid = [(rho, law, 3000) for rho in (0, .8, .95, .98, .99) for law in ("normal", "garch")]
    res = {}
    with ProcessPoolExecutor(10) as ex:
        for k, out in ex.map(cell, grid): res[k] = out
    np.save("ak_calib_pilot.npy", res, allow_pickle=True)
    ks = np.arange(1, J + 1) / J                      # attainable p-values k/438
    # alpha*: largest attainable level with null rejection <= .025 in EVERY cell (worst case)
    worst = np.max([[np.mean(res[k][None] <= a) for a in ks] for k in res], axis=0)
    astar = ks[worst <= .025].max() if (worst <= .025).any() else None
    print("worst-case null rej at nominal .025:", worst[ks <= .025].max().round(4), "| alpha* (worst case over all 10 cells) =", astar, f"= {round(astar*J) if astar else None}/438")
    for k in res:
        n0 = res[k][None]
        ok = ks[np.array([np.mean(n0 <= a) for a in ks]) <= .025]
        # archive fix: the original crashed here when no attainable level achieves .025 in a cell
        a_cell = f"{ok.max():.4f} ({round(ok.max()*J)}/438)" if ok.size else "none attainable"
        line = (f"rho={k[0]:<5}{k[1]:<7} size@.025={np.mean(n0 <= .025):.4f}  "
                f"P(p<=1/438)={np.mean(n0 <= 1 / J):.4f}  cell-alpha*={a_cell} | power@alpha*(worst):")
        for alt in ALTS[1:]:
            line += f" {alt[0]}{'' if alt[1] is None else alt[1]}={np.mean(res[k][alt] <= astar) if astar else float('nan'):.2f}"
        print(line, flush=True)
