import sys, time, itertools, numpy as np
from concurrent.futures import ProcessPoolExecutor
from simlib import ak_dgp, ak_p
T, m = 492, 55

def cell(args):
    rho, law, endog, drift, dtype, gap, R, seed, extra = args
    rng = np.random.default_rng(seed); rej = 0; t0 = time.time()
    for _ in range(R):
        y, X = ak_dgp(rng, T + m, rho, law, endog, drift, dtype, **extra)
        rej += ak_p(y, X, T, m, gap)[2]
    return args[:6], rej / R, (time.time() - t0) / R

if __name__ == "__main__":
    R = int(sys.argv[1])
    grid = [(rho, law, 0.0, 0.5, "I1", gap, R, [20261023, k], {})
            for k, (rho, law, gap) in enumerate(itertools.product((0, .8, .95, .98, .99), ("normal", "garch"), (None, 45)))]
    grid += [(.95, "normal", .5, .5, "I1", 45, R, [20261023, 100], {}), (.95, "t5", 0, .5, "I1", 45, R, [20261023, 101], {}),
             (.95, "normal", 0, 0, "I1", 45, R, [20261023, 102], {}), (.95, "normal", 0, .5, "I0", 45, R, [20261023, 103], {}),
             (.95, "normal", 0, .5, "I1", 45, R, [20261023, 104], {"pre_var_break": 108}),
             (.98, "normal", 0, .5, "I1", 45, R, [20261023, 105], {"pre_var_break": 108})]
    with ProcessPoolExecutor(10) as ex:
        for key, rate, sec in ex.map(cell, grid):
            se = np.sqrt(rate * (1 - rate) / R)
            print(f"rho={key[0]:<5} law={key[1]:<6} endog={key[2]} drift={key[3]} d={key[4]} gap={str(key[5]):<4}  size={rate:.4f} (se {se:.4f})  {sec*1e3:.1f} ms/rep", flush=True)
