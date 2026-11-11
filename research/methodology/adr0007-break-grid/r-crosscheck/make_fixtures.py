"""Write the ADR 0007 §9.2 synthetic fixtures and the Python results to compare with R.

Designs are fixed in advance and not calibrated to real data (§9.1). Every row is a candidate,
because `strucchange` has no grid option. Run: uv run python <this file>
"""

import json
import math
from pathlib import Path

import numpy as np
import statsmodels.api as sm

from kagura import breaks

OUT = Path(__file__).parent
EPS = 0.15
M = 5


def design(name: str, n_obs: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n_obs)
    t = np.arange(n_obs)
    if name == "two_break_slope":
        e = rng.normal(size=n_obs)
        slope = np.select([t < n_obs * 0.35, t < n_obs * 0.7], [1.0, 0.2], 1.2)
    elif name == "hetero_regimes":  # one slope break, error s.d. 1 then 3
        e = rng.normal(size=n_obs) * np.where(t < n_obs * 0.5, 1.0, 3.0)
        slope = np.where(t < n_obs * 0.5, 1.0, 0.4)
    elif name == "ar1_errors":  # one slope break, AR(1) errors with rho = 0.6
        u = rng.normal(size=n_obs)
        e = np.zeros(n_obs)
        for i in range(1, n_obs):
            e[i] = 0.6 * e[i - 1] + u[i]
        slope = np.where(t < n_obs * 0.6, 1.0, 0.3)
    else:
        raise ValueError(name)
    return 0.1 + slope * x + e, x


def main() -> None:
    fixtures: dict[str, tuple[np.ndarray, np.ndarray | None]] = {
        "nile": (sm.datasets.nile.load_pandas().data["volume"].to_numpy(float), None)
    }
    for i, name in enumerate(("two_break_slope", "hetero_regimes", "ar1_errors")):
        fixtures[name] = design(name, 400, 20261111 + i)
    result = {}
    for name, (y, x) in fixtures.items():
        n_obs = len(y)
        xm = np.ones((n_obs, 1)) if x is None else np.column_stack([np.ones(n_obs), x])
        h = math.floor(EPS * n_obs)
        cols = "y" if x is None else "y,x"
        rows = [
            f"{v!r}" if x is None else f"{v!r},{w!r}"
            for v, w in zip(y, x if x is not None else y, strict=True)
        ]
        (OUT / f"{name}.csv").write_text(cols + "\n" + "\n".join(rows) + "\n")
        parts = breaks.global_partitions(y, xm, h, M)
        result[name] = {
            "T": n_obs,
            "h": h,
            "q": xm.shape[1],
            "selected": breaks.select(parts, n_obs, xm.shape[1]),
            "partitions": {
                str(m): {
                    # 1-based last row of the old regime = strucchange's breakpoint
                    "strucchange_breaks": list(p.breaks),
                    "ssr": p.ssr,
                    "supF": breaks.sup_f(y, xm, p) if m else None,
                }
                for m, p in parts.items()
            },
        }
    (OUT / "python_results.json").write_text(json.dumps(result, indent=1) + "\n")


if __name__ == "__main__":
    main()
