"""ADR 0007 historical structural-break run, Phase A of ADR 0011: descriptive only.

Phase A computes least-squares partitions, BIC/LWZ selections, regime coefficients and Bai
intervals. It does not compute sup F(k), UDmax, WDmax, sequential sup F(l + 1 | l) or WF
bootstrap statistics (ADR 0011 §3, §7): Phase B is withheld, so those code paths are absent
here, and `guard` refuses any row that looks like a test result.

The policy-event comparison (ADR 0009 §7) is Phase C and is not done here.

Gate (ADR 0011 §7): the R cross-check reports no FAIL, and every original §9 validation
output is byte-identical to the hash recorded in ADR 0011 §5, so the failed critical-value
check is carried forward unchanged.

Writes to research/adr0007/out/phase_a/:
  partitions.csv   every cell, m = 0..5: SSR, BIC, LWZ, break dates     (descriptive)
  selection.csv    every cell: T, h, candidates, m chosen by BIC, LWZ  (model selection)
  break_table.csv  every cell and m = 1..5: dates, Bai intervals with widths in rows,
                   calendar days and share of the eligible range       (descriptive)
  regime_table.csv every cell and m = 0..5: regime coefficients, HAC SE (descriptive)
  daily_sensitivity.csv  primary spec, m = 1 date on the daily grid beside the month-start
  README.txt       the disclosures below
Run: uv run python research/adr0007/run_breaks.py
"""

from __future__ import annotations

import csv
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from data import Cell, cell
from kagura import breaks
from kagura.vintage import sha256

HERE = Path(__file__).parent
OUT = HERE / "out" / "phase_a"
VALIDATION = HERE.parents[0] / "methodology/adr0007-break-grid"
M = 5
EPS = (0.15, 0.10, 0.05)
CELLS = [
    *(
        (s, smp, e, 0)
        for s in ("primary", "V1", "V2", "V3")
        for smp in ("full", "recent")
        for e in EPS
    ),
    *(("lag", smp, e, 1) for smp in ("full", "recent") for e in EPS),
]
LABEL = "exploratory (ADR 0007), Phase A (ADR 0011)"
TIERS = {"descriptive estimate", "model selection"}
CI_NOTE = (
    "nominal level only, coverage not established; simulated coverage at nominal 95 % ranged "
    "from 76.5 % (ADR 0011 §6: T = 1,000, shift 0.15) to 97.2 % (ADR 0012 §3.2: full grid, "
    "shift 0.60, eta = 4); not a bound for these estimates"
)
# ADR 0011 §5: the original validation outputs, kept byte for byte.
ORIGINALS = {
    "critical_values_tables.txt": (
        "5c932795783f2021be6e2cf12ac9c6018cf02e18a92a29c04d9d6f71bc34ff50"
    ),
    "critical_values_tables_1000.txt": (
        "b1db57ef3bc497a9e7ba5809c3ea1b8ab8af4a58cee6a986f9f665e9d60b92fe"
    ),
    "validation_sims.txt": ("7eba72d84579f3b3bb6c8fc3a206e0debd921729f5ae4f92527dcbc66da973c9"),
    "r-crosscheck/comparison.txt": (
        "b690585c4e03c18250b8899ee04c1662f7aebe3c258c74db7e65f449d42e3f1b"
    ),
    "r-crosscheck/r_results.json": (
        "c6e43db91cfb4264d63526a122553a397e9069dcef3ec1aa3ddfa28a7f51d6d0"
    ),
}
# ADR 0012 §4, §7: the R comparison rerun with exact bounds and the phi2s correction.
COMPARISON = "r-crosscheck/comparison_adr0012.txt"
COMPARISON_SHA256 = "93fb041358a85a01a08430c3722e209ccde7858ea07da2abd2501199ea9af38f"
# ADR 0012 §5: an allow-list. Any other column, e.g. a test statistic, is refused.
ALLOWED = frozenset(
    {
        *("spec", "sample", "eps", "p", "label", "tier"),
        *("T", "h", "q", "hac_lag", "n_candidates", "first_eligible", "last_eligible"),
        *("m_BIC", "m_LWZ", "m", "selected_by", "ssr", "bic", "lwz", "dates", "break", "date"),
        *(
            f"ci{lev}_{part}"
            for lev in ("95", "90")
            for part in (
                "nominal",
                "truncated",
                "width_rows",
                "width_days",
                "width_share_eligible",
            )
        ),
        *("ci_note", "regime", "start", "end", "rows", "coef", "estimate", "hac_se"),
        *("daily_date", "daily_ssr", "month_date", "month_ssr"),
    }
)
WITHHELD_LABEL = re.compile(r"tested|bootstrap|significan|confirm", re.I)
README = f"""ADR 0007 break estimation, Phase A (ADR 0011). {LABEL}.

Everything here is descriptive or model selection. Nothing is a tested claim.
- Break dates: least-squares partitions for a given m. They locate changes in a linear fit,
  not economic regimes (ADR 0007 L1).
- BIC and LWZ: model-selection results under the model's assumptions; both are shown and
  neither is "the number of breaks". Sequential-rule counts are withheld (ADR 0011 §4).
- Bai intervals: {CI_NOTE}. The 90 %/95 % labels are nominal, not validated coverage.
  Coverage on real data, where m and the error process are unknown, may be lower.
- Not computed: sup F(k), UDmax, WDmax, sequential tests, WF bootstrap (Phase B, withheld).
- The ADR 0007 §9.1 critical-value check FAILED as frozen (11/72; 9/66 in the frozen scope)
  and remains failed (ADR 0011 §1).
"""


def gate(validation: Path = VALIDATION) -> None:
    """ADR 0011 §7 Phase A gate, as amended by ADR 0012 §5: the rerun R comparison passes;
    original outputs unchanged."""
    rerun = validation / COMPARISON
    if not rerun.exists():
        raise SystemExit(f"Phase A gate: {COMPARISON} missing; run r-crosscheck/compare.py")
    if sha256(rerun) != COMPARISON_SHA256:
        raise SystemExit(f"Phase A gate: {COMPARISON} differs from ADR 0012 §7; run refused")
    last = rerun.read_text().strip().splitlines()[-1]
    if "'FAIL': 0}" not in last:
        raise SystemExit("Phase A gate: R cross-check does not pass; run refused")
    for rel, want in ORIGINALS.items():
        if sha256(validation / rel) != want:
            raise SystemExit(f"Phase A gate: {rel} differs from ADR 0011 §5; run refused")


def guard(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Refuse rows carrying a withheld statistic or a label stronger than Phase A allows."""
    for r in rows:
        bad = sorted(set(r) - ALLOWED)
        if bad:
            raise ValueError(f"column not allowed in Phase A output: {bad}")
        if r.get("tier") not in TIERS:
            raise ValueError(f"tier must be one of {sorted(TIERS)}: {r.get('tier')!r}")
        if WITHHELD_LABEL.search(str(r.get("label", ""))):
            raise ValueError(f"label too strong for Phase A: {r['label']!r}")
    return rows


def date(c: Cell, i: int) -> str:
    return str(c.dates.iloc[int(np.clip(i, 0, c.n_obs - 1))].date())


def analyse_cell(c: Cell) -> dict[str, list[dict[str, Any]]]:
    cand = c.eligible()
    q = c.xm.shape[1]
    cov = breaks.Cov(lags=c.lags)
    parts = breaks.global_partitions(c.y, c.xm, c.h, M, cand)
    sel = breaks.select(parts, c.n_obs, q)
    chosen = {m: [r.upper() for r in ("bic", "lwz") if sel[r] == m] for m in parts}
    base = {"spec": c.spec, "sample": c.sample, "eps": c.eps, "p": c.p, "label": LABEL}
    eligible_rows = cand[-1] - cand[0]

    selection = [
        {
            **base,
            "tier": "model selection",
            "T": c.n_obs,
            "h": c.h,
            "q": q,
            "hac_lag": c.lags,
            "n_candidates": len(cand),
            "first_eligible": date(c, cand[0]),
            "last_eligible": date(c, cand[-1]),
            "m_BIC": sel["bic"],
            "m_LWZ": sel["lwz"],
        }
    ]
    partitions, break_rows, regime_rows = [], [], []
    for m, pt in parts.items():
        partitions.append(
            {
                **base,
                "tier": "descriptive estimate",
                "m": m,
                "selected_by": "+".join(chosen[m]),
                "ssr": pt.ssr,
                "bic": breaks.bic(pt.ssr, c.n_obs, m, q),
                "lwz": breaks.lwz(pt.ssr, c.n_obs, m, q),
                "dates": " ".join(date(c, b) for b in pt.breaks),
            }
        )
        ivs = breaks.break_intervals(c.y, c.xm, pt.breaks, cov) if m else []
        for i, (b, iv) in enumerate(zip(pt.breaks, ivs, strict=True)):
            row = {
                **base,
                "tier": "descriptive estimate",
                "m": m,
                "selected_by": "+".join(chosen[m]),
                "break": i + 1,
                "date": date(c, b),
            }
            for lev, lo, hi in (("95", iv.lo95, iv.hi95), ("90", iv.lo90, iv.hi90)):
                clo, chi = max(lo, cand[0]), min(hi, cand[-1])
                row[f"ci{lev}_nominal"] = f"{date(c, clo)} .. {date(c, chi)}"
                row[f"ci{lev}_truncated"] = (clo != lo) or (chi != hi)
                row[f"ci{lev}_width_rows"] = hi - lo
                row[f"ci{lev}_width_days"] = (c.dates.iloc[chi] - c.dates.iloc[clo]).days
                row[f"ci{lev}_width_share_eligible"] = round((hi - lo) / eligible_rows, 4)
            row["ci_note"] = CI_NOTE
            break_rows.append(row)
        coef, se = breaks.regime_table(c.y, c.xm, pt.breaks, cov)
        for j, (a, b) in enumerate(breaks.regime_bounds(pt.breaks, c.n_obs)):
            for k, nm in enumerate(c.names):
                regime_rows.append(
                    {
                        **base,
                        "tier": "descriptive estimate",
                        "m": m,
                        "selected_by": "+".join(chosen[m]),
                        "regime": j + 1,
                        "start": date(c, a),
                        "end": date(c, b - 1),
                        "rows": b - a,
                        "coef": nm,
                        "estimate": coef[j, k],
                        "hac_se": se[j, k],
                    }
                )
    out = {
        "selection": selection,
        "partitions": partitions,
        "breaks": break_rows,
        "regimes": regime_rows,
    }
    if c.spec == "primary":
        allrows = list(range(c.h, c.n_obs - c.h + 1))
        daily = breaks.global_partitions(c.y, c.xm, c.h, 1, allrows)[1]
        out["daily"] = [
            {
                **base,
                "tier": "descriptive estimate",
                "daily_date": date(c, daily.breaks[0]),
                "daily_ssr": daily.ssr,
                "month_date": date(c, parts[1].breaks[0]),
                "month_ssr": parts[1].ssr,
            }
        ]
    return {k: guard(v) for k, v in out.items()}


def analyse(key: tuple[str, str, float, int]) -> dict[str, list[dict[str, Any]]]:
    return analyse_cell(cell(*key))


def write(path: Path, rows: list[dict[str, Any]]) -> None:
    guard(rows)
    cols: list[str] = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    gate()
    OUT.mkdir(parents=True, exist_ok=True)
    # ADR 0012 §5: a daily-grid cell peaks at ~2.3 GB (measured), so 4 workers stay under ~10 GB.
    with ProcessPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(analyse, CELLS))
    for part, name in (
        ("selection", "selection.csv"),
        ("partitions", "partitions.csv"),
        ("breaks", "break_table.csv"),
        ("regimes", "regime_table.csv"),
        ("daily", "daily_sensitivity.csv"),
    ):
        write(OUT / name, [r for x in res for r in x.get(part, [])])
    (OUT / "README.txt").write_text(README)
    print("written:", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
