"""ADR 0007 §9.1 critical-value check: simulated limits on a 4,000-point grid vs the tables.

For q = 2 and q = 10 at ε = 5, 10, 15 %, compares the simulated 5 % values of sup F(k)
(k = 1..5), sup F(l + 1 | l) (l = 0..4), UDmax and WDmax with the Bai-Perron tables as
distributed in mbreaks 1.0.1 (`tables_mbreaks.json`, exported by `export_tables.R`).
Pass (§6.1): within 0.35, where the table has the entry.

Settings, fixed before the run:
- k = 1 and sup F(l + 1 | l): 100,000 draws (the one-break limit is O(n) per draw).
  sup F(l + 1 | l) uses the tables' construction, l + 1 independent one-break limits with
  trimming ε in each regime, so its 5 % value is the 0.95^(1/(l+1)) quantile of sup F(1).
- k = 2..5, UDmax, WDmax: 10,000 draws, because each draw needs a dynamic programme over
  4,000 points (about 0.2 s). The order-statistic interval shows the Monte Carlo error.
Run: uv run python research/methodology/adr0007-break-grid/critical_values_tables.py
"""

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from kagura import breaksim as bs

HERE = Path(__file__).parent
# 4,000 is the frozen check (§9.1). "1000" as argument is a diagnostic at the tables' own
# grid (Bai and Perron 2003b: 1,000 steps), written to a separate file.
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
TOL = 0.35
SEED = 20261117


def cell(key: str) -> list[str]:
    t = json.loads((HERE / "tables_mbreaks.json").read_text())[key]
    eps, q = t["eps"], t["q"]
    h = round(eps * N)
    rng = np.random.default_rng([SEED, q, h])
    f1 = bs.supf1_limit(np.arange(h, N - h + 1) / N, q, 100_000, rng)
    dp = bs.supf_limit(list(range(1, N)), N, h, q, 5, 10_000, SEED + 7 * q + h, chunk=1)
    rows = []

    def row(name: str, qt: bs.Quantile, table: float) -> None:
        d = qt.value - table
        status = "pass" if abs(d) <= TOL else "FAIL"
        rows.append(
            f"{status:4} eps={eps:.2f} q={q:2d} {name:10} sim={qt.value:6.2f} "
            f"[{qt.lo:6.2f}, {qt.hi:6.2f}] n={qt.draws:6d} table={table:6.2f} diff={d:+.2f}"
        )

    row("supF(1)", bs.quantile(f1), t["supF"][0])
    for k in range(2, 6):
        row(f"supF({k})", bs.quantile(dp[:, k - 1]), t["supF"][k - 1])
    for ell in range(5):
        row(f"seq({ell + 1}|{ell})", bs.quantile(f1, 0.95 ** (1 / (ell + 1))), t["seq"][ell])
    cv = np.array([bs.quantile(dp[:, k]).value for k in range(5)])
    row("UDmax", bs.quantile(dp.max(axis=1)), t["dmax"][0])
    row("WDmax", bs.quantile((dp * bs.wd_weights(cv)).max(axis=1)), t["dmax"][1])
    return rows


def main() -> None:
    keys = list(json.loads((HERE / "tables_mbreaks.json").read_text()))
    with ProcessPoolExecutor(max_workers=6) as ex:
        out = [r for rows in ex.map(cell, keys) for r in rows]
    fails = sum(r.startswith("FAIL") for r in out)
    out.append(f"summary: {len(out)} comparisons, {fails} outside {TOL}")
    (
        HERE / ("critical_values_tables.txt" if N == 4000 else f"critical_values_tables_{N}.txt")
    ).write_text("\n".join(out) + "\n")
    print(out[-1])


if __name__ == "__main__":
    main()
