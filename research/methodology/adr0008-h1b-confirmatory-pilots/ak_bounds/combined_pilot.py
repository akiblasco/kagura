import numpy as np
from concurrent.futures import ProcessPoolExecutor
from simlib import innov, ar1, full_design, idx_for, f_t, ak_p
T, m = 492, 55
CF, CT = 5.355, -3.724            # pilot upper-bound CVs, fixed (1,1,1), n=480, iid (bounds_pilot.out)

def cell(a):
    rho, law, R, seed = a; rng = np.random.default_rng(seed); g = sup = ak = 0
    for _ in range(R):
        N = T + m
        x = (0.5 + rng.standard_normal(N)).cumsum(); d = rng.standard_normal(N).cumsum()
        u = ar1(rng, innov(rng, N, law), rho) * 3          # u sd ~ 3x innovation; theta=1, gamma=2
        s = x + 2 * d + u
        y, X, nm = full_design(s[:T], x[:T], d[:T])          # gate on pre-period only
        F, t, _, _ = f_t(y, X, nm, idx_for(nm, 1, 1, 1))
        gate = (F > CF) and (t < CT)
        rej = ak_p(s, np.column_stack([np.ones(N), x, d]), T, m, 45)[2]
        g += gate; ak += rej; sup += gate and rej
    return a[:2], g / R, ak / R, sup / R

if __name__ == "__main__":
    grid = [(rho, law, 3000, [21, k, j]) for k, rho in enumerate((.8, .95, .98, .99, 1.0)) for j, law in enumerate(("normal", "garch"))]
    with ProcessPoolExecutor(10) as ex:
        for k, g, ak, sup in ex.map(cell, grid):
            lab = "NO cointegration (u random walk)" if k[0] == 1 else "cointegrated throughout (AK H0)"
            print(f"rho={k[0]:<5}{k[1]:<7} gate pass={g:.3f}  AK reject={ak:.3f}  'supported' (false)={sup:.4f}   [{lab}]", flush=True)
