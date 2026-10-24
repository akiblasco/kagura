import numpy as np
from concurrent.futures import ProcessPoolExecutor
from wwlib import fmols
def run(a):
    T, rho_u, rho_v, endog, R, seed = a; rng = np.random.default_rng(seed); tf = []
    for _ in range(R):
        e = rng.standard_normal((T + 1, 3)); v = np.zeros((T + 1, 2)); uu = np.zeros(T + 1)
        for t in range(1, T + 1):
            v[t] = rho_v * v[t-1] + e[t, 1:]; uu[t] = rho_u * uu[t-1] + e[t, 0] + endog * e[t, 1]
        X = v.cumsum(0)[1:]; y = X @ [1., 2.] + uu[1:]
        th, corr, w2, Zs, _ = fmols(y, X, np.ones((T, 1)))
        tf.append((th[1:] - [1, 2]) / np.sqrt(w2 * np.diag(np.linalg.inv(Zs.T @ Zs)))[1:])
    return a[:4], (np.abs(np.array(tf)) > 1.96).mean(0)
if __name__ == "__main__":
  jobs = [(500, 0, 0, 0, 2000, 1), (500, 0, 0, .8, 2000, 2), (500, .6, .5, .8, 2000, 3), (2000, .6, .5, .8, 1000, 4), (5000, .6, .5, .8, 500, 5)]
  with ProcessPoolExecutor(5) as ex:
    for k, r in ex.map(run, jobs):
        print(f"T={k[0]:<5} rho_u={k[1]} rho_v={k[2]} endog={k[3]}: FM t 5% rejection {r.round(3)}")
