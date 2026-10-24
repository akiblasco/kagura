"""Reproduce AK (2006) Table 1, P test, T=250, m=10: eight-model average null rejection at nominal .05."""
import sys, numpy as np
from simlib import ak_p
G = {"N": lambda r, n: r.standard_normal(n),
     "chi2": lambda r, n: (r.chisquare(2, n) - 2) / 2,
     "t3": lambda r, n: r.standard_t(3, n) / np.sqrt(3),
     "U": lambda r, n: r.uniform(-np.sqrt(12) / 2, np.sqrt(12) / 2, n)}
MODELS = {1: ("N", 0, 2, 2, True), 2: ("chi2", 0, 2, 2, True), 3: ("t3", 0, 2, 2, True), 4: ("U", 0, 2, 2, True),
          5: ("N", .4, 2, 2, True), 6: ("N", .8, 2, 2, True), 7: ("N", 0, 4, 0, True), 8: ("N", 0, 2, 2, False)}

def ar(r, g, n, rho, burn=200):
    e = g(r, n + burn); a = np.empty_like(e); a[0] = e[0]
    for t in range(1, len(e)): a[t] = rho * a[t - 1] + e[t]
    return a[burn:]

def draw(r, model, rho, N):
    law, rdu, d1, d2, trend = MODELS[model]; g = G[law]
    psi, eta = ar(r, g, N, rho), ar(r, g, N, rho)
    xi = np.column_stack([ar(r, g, N, rho) for _ in range(d1)])
    x2 = [ar(r, g, N, rho) for _ in range(d2)]
    u = np.sqrt(1 - rdu) * psi + np.sqrt(rdu) * eta                       # eq. (34)
    x1 = (np.sqrt(1 - rdu) * xi + np.sqrt(rdu) * eta[:, None]).cumsum(0)
    cols = [np.ones(N)] + ([np.arange(1, N + 1.)] if trend else []) + [x1] + ([np.column_stack(x2)] if d2 else [])
    return u, np.column_stack(cols)

T, m, R = 250, 10, int(sys.argv[1])
pub = {0: .057, .4: .051, .8: .048}
for rho in (0, .4, .8):
    rates = []
    for model in MODELS:
        r = np.random.default_rng([2006, model, int(rho * 10)])
        rates.append(np.mean([ak_p(*draw(r, model, rho, T + m), T, m, alpha=.05)[2] for _ in range(R)]))
    avg = np.mean(rates); se = np.sqrt(np.mean(rates) * (1 - np.mean(rates)) / R / 8)
    print(f"rho={rho}: avg {avg:.4f} (MC se {se:.4f}) published {pub[rho]}  range [{min(rates):.3f},{max(rates):.3f}]  diff {avg - pub[rho]:+.4f}")
