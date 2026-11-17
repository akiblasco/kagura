"""ADR 0007 §6.3 step 1: fix the lag order p before any break statistic.

On each sample, fit the no-break lag-augmented model for p = 1..5, regress its residual on
the regressors and 10 own lags, and test the lag coefficients jointly with HC0. p is the
smallest order with p-value >= 0.05; if none passes, no bootstrap on that sample.
No break statistic is computed here. Run: uv run python research/adr0007/step1_lags.py
"""

import csv
from pathlib import Path

import numpy as np

from data import cell
from kagura import breaksim

OUT = Path(__file__).parent / "out"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rows = []
    for sample in ("full", "recent"):
        chosen = None
        for p in range(1, 6):
            c = cell("lag", sample, 0.15, p)
            coef, *_ = np.linalg.lstsq(c.xm, c.y, rcond=None)
            w, pv = breaksim.robust_bg(c.y - c.xm @ coef, c.xm, lags=10)
            if chosen is None and pv >= 0.05:
                chosen = p
            rows.append(
                {
                    "sample": sample,
                    "p": p,
                    "T": c.n_obs,
                    "q": c.xm.shape[1],
                    "bg_wald": round(w, 4),
                    "bg_p": round(pv, 6),
                }
            )
        rows.append(
            {"sample": sample, "p": f"chosen={chosen}", "T": "", "q": "", "bg_wald": "", "bg_p": ""}
        )
    with (OUT / "step1_lags.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
