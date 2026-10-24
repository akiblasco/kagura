import numpy as np
from concurrent.futures import ProcessPoolExecutor
from simlib import ak_dgp, ak_p
T = 492

def oracle(u, T, m, alpha):          # true beta = 0: P and P_j are raw window sums of u^2
    c = np.r_[0, np.cumsum(u**2)]
    P = c[T + m] - c[T]; j = np.arange(T - m + 1); Pj = c[j + m] - c[j]
    return (P > Pj).sum() >= (1 - alpha) * len(Pj)

def cell(a):
    m, rho, law, R = a
    rng = np.random.default_rng([7, m, int(rho * 100), len(law)])
    r = np.zeros(4)
    for _ in range(R):
        y, X = ak_dgp(rng, T + m, rho, law, 0, .5, "I1")
        r += [ak_p(y, X, T, m, alpha=.025)[2], ak_p(y, X, T, m, alpha=.05)[2], oracle(y, T, m, .025), oracle(y, T, m, .05)]
    return a[:3], r / R

if __name__ == "__main__":
    grid = [(m, rho, law, 4000) for m in (10, 25, 55) for rho, law in ((0, "normal"), (.95, "normal"), (0, "garch"))]
    with ProcessPoolExecutor(9) as ex:
        for k, r in ex.map(cell, grid):
            print(f"m={k[0]:<3} rho={k[1]:<5} {k[2]:<6} AK@.025={r[0]:.4f} AK@.05={r[1]:.4f} | oracle-beta@.025={r[2]:.4f} @.05={r[3]:.4f}  (T/m={T/k[0]:.0f})", flush=True)
