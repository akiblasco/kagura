"""Compare kagura.breaks with the committed R reference results (ADR 0007 §9.2).

Reads the fixtures and r_results.json in this directory; writes comparison.txt.
Pass rules (§9.2): strucchange dates identical and SSR to 1e-8 for m = 0..5; mbreaks sup F to
1e-6, sequential m identical, interval bounds to one row. Rows reported as "convention" are
differences explained by a documented difference between the two codes, not by a defect.
Run: uv run python <this file>
"""

import json
import math
from pathlib import Path

import numpy as np

from kagura import breaks

HERE = Path(__file__).parent
CONFIGS = {
    "homo": breaks.Cov(robust=False, hetvar=False, kernel="qs"),
    "homo_het": breaks.Cov(robust=False, hetvar=True, kernel="qs"),
    "hac": breaks.Cov(kernel="qs"),
    "hac_pw": breaks.Cov(kernel="qs", prewhit=True),
}


def psigmq_variant(y: np.ndarray, xm: np.ndarray, bk: tuple[int, ...]) -> tuple[float, np.ndarray]:
    """F(k) and SEs as mbreaks computes them with robust = 0, hetvar = 1: `psigmq` uses rows
    b[j-1]..b[j] (1-based, inclusive) for a middle regime, one row more than the regime, over
    b[j] - b[j-1]. Used only to confirm that this explains the difference."""
    n_obs, q = xm.shape
    zm = breaks.diag_partition(xm, bk)
    delta, *_ = np.linalg.lstsq(zm, y, rcond=None)
    res = y - zm @ delta
    e = [0, *bk, n_obs]
    sig = []
    for j in range(len(e) - 1):
        lo = e[j] - 1 if 0 < j < len(e) - 2 else e[j]
        sig.append(float(res[lo : e[j + 1]] @ res[lo : e[j + 1]]) / (e[j + 1] - e[j]))
    vdel = np.kron(np.diag(sig), np.eye(q)) @ np.linalg.inv(zm.T @ zm)
    k = len(bk)
    rmat = np.kron(np.eye(k, k + 1, 1) - np.eye(k, k + 1), np.eye(q))
    rd = rmat @ delta
    wald = float(rd @ np.linalg.solve(rmat @ vdel @ rmat.T, rd))
    return (n_obs - (k + 1) * q) / (n_obs * k) * wald, np.sqrt(np.diag(vdel))


def load(name: str) -> tuple[np.ndarray, np.ndarray]:
    a = np.loadtxt(HERE / f"{name}.csv", delimiter=",", skiprows=1, ndmin=2)
    y = a[:, 0]
    xm = np.ones((len(y), 1)) if a.shape[1] == 1 else np.column_stack([np.ones(len(y)), a[:, 1]])
    return y, xm


def compare() -> list[dict[str, object]]:
    ref = json.loads((HERE / "r_results.json").read_text())
    rows: list[dict[str, object]] = []

    def add(fx: str, item: str, py: object, r: object, ok: bool, note: str = "") -> None:
        status = "pass" if ok else ("convention" if note else "FAIL")
        rows.append(
            {"fixture": fx, "item": item, "python": py, "r": r, "status": status, "note": note}
        )

    for name, rr in ref.items():
        if name == "cvg":
            continue
        y, xm = load(name)
        n_obs, h, q = rr["T"], rr["h"], rr["q"]
        assert (len(y), math.floor(0.15 * len(y)), xm.shape[1]) == (n_obs, h, q)
        parts = breaks.global_partitions(y, xm, h, 5)
        for m in range(6):
            sc = rr["strucchange"][str(m)]
            b_r = tuple(sc["breaks"]) if isinstance(sc["breaks"], list) else (sc["breaks"],)
            b_r = tuple(b for b in b_r if b is not None)
            add(name, f"strucchange m={m} dates", parts[m].breaks, b_r, parts[m].breaks == b_r)
            d = abs(parts[m].ssr - sc["ssr"])
            add(
                name,
                f"strucchange m={m} SSR",
                parts[m].ssr,
                sc["ssr"],
                d <= 1e-8 * max(1, sc["ssr"]),
            )
        for k in range(1, 6):
            g = rr["mbreaks_global"][k - 1]
            g = tuple(g) if isinstance(g, list) else (g,)
            add(name, f"mbreaks global k={k} dates", parts[k].breaks, g, parts[k].breaks == g)
        cv_seq = rr["cv_seq"]
        for cn, cov in CONFIGS.items():
            mr = rr["mbreaks"][cn]
            for k in range(1, 6):
                f = breaks.f_test(y, xm, parts[k].breaks, cov)
                fr = mr["ftest"][k - 1]
                ok = abs(f - fr) <= 1e-6 * max(1, abs(fr))
                note = ""
                if not ok and cn == "homo_het":
                    fv, _ = psigmq_variant(y, xm, parts[k].breaks)
                    if abs(fv - fr) <= 1e-6 * max(1, abs(fr)):
                        note = f"psigmq middle-regime row; with it Python gives {fv:.10g}"
                add(name, f"{cn} supF({k})", f, fr, ok, note)
            found, _ = breaks.sequential(y, xm, h, 5, lambda ell, _r, cv=cv_seq: cv[ell], cov)
            sb = mr["seq_breaks"]
            sb = tuple(sb) if isinstance(sb, list) else (sb,)
            add(name, f"{cn} sequential m", len(found), mr["seq_m"], len(found) == mr["seq_m"])
            add(name, f"{cn} sequential dates", found, sb, found == sb)
            for e in mr["estim"]:
                bk = tuple(e["breaks"]) if isinstance(e["breaks"], list) else (e["breaks"],)
                m = len(bk)
                ints = breaks.break_intervals(y, xm, bk, cov)
                ci = np.asarray(e["CI"], dtype=float).reshape(m, 4)
                for i, iv in enumerate(ints):
                    py = (iv.lo95, iv.hi95, iv.lo90, iv.hi90)
                    r = tuple(int(v) for v in ci[i])
                    extra = m - i - 1  # mbreaks adds "+1" to break i's upper bounds m - i times
                    note = ""
                    ok = max(abs(a - b) for a, b in zip(py, r, strict=True)) <= 1
                    if not ok and extra and (py[0], py[1] + extra, py[2], py[3] + extra) == r:
                        note = (
                            f"mbreaks upper bounds +{extra}: rounding inside its loop over breaks"
                        )
                    add(name, f"{cn} CI m={m} break {i + 1}", py, r, ok, note)
                coef, se = breaks.regime_table(y, xm, bk, cov)
                br, ser = np.asarray(e["beta"]), np.asarray(e["SE"])
                add(
                    name, f"{cn} coef m={m}", "", "", bool(np.allclose(coef.ravel(), br, atol=1e-8))
                )
                se_ok = bool(np.allclose(se.ravel(), ser, rtol=1e-6))
                note = ""
                if not se_ok and cn == "homo_het":
                    _, sev = psigmq_variant(y, xm, bk)
                    if np.allclose(sev, ser, rtol=1e-6):
                        note = "psigmq middle-regime row; reproduced to 1e-6 with it"
                add(name, f"{cn} SE m={m}", "", "", se_ok, note)
    for c in ref["cvg"]:
        got = breaks.bai_quantiles(c["eta"], c["phi1s"], c["phi2s"])
        d = max(abs(a - b) for a, b in zip(got, c["c"], strict=True))
        add("cvg", f"eta={c['eta']} phi1={c['phi1s']} phi2={c['phi2s']}", got, c["c"], d <= 1e-6)
    return rows


def main() -> None:
    rows = compare()
    lines = [
        f"{r['status']:10} {r['fixture']:16} {r['item']:40} py={r['python']} r={r['r']} {r['note']}"
        for r in rows
    ]
    counts = {s: sum(r["status"] == s for r in rows) for s in ("pass", "convention", "FAIL")}
    lines.append(f"summary: {counts}")
    (HERE / "comparison.txt").write_text("\n".join(lines) + "\n")
    print(lines[-1])


if __name__ == "__main__":
    main()
