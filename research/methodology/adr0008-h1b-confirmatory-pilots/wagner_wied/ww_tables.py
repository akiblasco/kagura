"""Summary tables from ww_pilot.npy (written by `ww_pilot.py 2000 1000`).

Reconstructs ww_null_ci.out and ww_power_table.out, which were first produced by inline commands.
"""
import numpy as np
from scipy import stats
from ww_pilot import CV

res = np.load("ww_pilot.npy", allow_pickle=True).item()
cv = CV["pkg"]


def cp(k, n, a):
    return (stats.beta.ppf(a / 2, k, n - k + 1) if k else 0.0,
            stats.beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0)


def screen(k, n):                              # 99 % Clopper–Pearson against Bradley-type 1.5α = .0375
    lo, hi = cp(k, n, .01)
    return "FAIL" if lo > .0375 else "PASS" if hi <= .0375 else "AMBIG"


with open("ww_null_ci.out", "w") as f:
    print("cell | FM-andrews rate [95% CP] screen | D-OLS rate [95% CP] screen   "
          "(screen: FAIL if 99% CP lower > .0375; PASS if 99% CP upper <= .0375; else AMBIG)", file=f)
    for k, o in res.items():
        if k[4] is not None:
            continue
        line = f"rho={k[0]:<5}{k[1]:<7}d={k[2]} drift={k[3]}"
        for j in (0, 4):
            c, n = int((o[:, j] > cv).sum()), len(o); lo, hi = cp(c, n, .05)
            line += f" | {c / n:.3f} [{lo:.3f},{hi:.3f}] {screen(c, n)}"
        print(line, file=f)

with open("ww_power_table.out", "w") as f:
    print("power raw / size-corrected (null cell 97.5% quantile), R=1000", file=f)
    for k, o in res.items():
        if k[4] is None:
            continue
        n0 = res[(k[0], "normal", "I1", 0.0, None)]
        line = f"rho={k[0]} {str(k[4]):<16}"
        for nm, j in zip(("FMand", "FMnw", "FMlarge", "Dand"), (0, 1, 2, 4)):
            line += f" {nm} {np.mean(o[:, j] > cv):.3f}/{np.mean(o[:, j] > np.quantile(n0[:, j], .975)):.3f}"
        print(line, file=f)
