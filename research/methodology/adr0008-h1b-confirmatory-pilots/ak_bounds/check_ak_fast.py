"""Fixture: fast AK P (Gram down-dating) equals the direct leave-ceil(m/2)-out loop, with and without the gap."""
import numpy as np
from simlib import ak_dgp, ak_p, ak_p_direct

T, m = 492, 55
rng = np.random.default_rng([20261023, 999])
for gap in (None, 45):
    for rho in (0, .95):
        y, X = ak_dgp(rng, T + m, rho, "normal", .5, .5, "I1")
        P, _, _, Pj = ak_p(y, X, T, m, gap)
        P0, Pj0 = ak_p_direct(y, X, T, m, gap)
        diff = max(abs(P - P0), np.abs(Pj - Pj0).max()) / max(P0, Pj0.max())
        assert diff < 1e-9, diff
        print(f"gap={gap} rho={rho}: max relative diff {diff:.1e}  OK")
