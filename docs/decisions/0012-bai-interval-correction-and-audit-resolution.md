# ADR 0012 — Bai Interval Correction and Independent-Audit Resolution

Date: 2026-11-18.

**Status: FROZEN 2026-11-18** (reviewer acceptance of the correction; the §7 evidence was
generated and checked before freezing). Any change needs a new ADR.

- ADR 0012 resolves the independent audit of 2026-11-17 (CONDITIONAL PASS).
- ADR 0007, ADR 0011, every original validation output (ADR 0011 §5) and the frozen data are
  unchanged.
- No break statistic has been computed on historical data.

## 0. Decision summary

| # | Decision |
|---|---|
| 1 | The robust Bai interval's `phi2s` is **corrected** to Δ'Ω₂Δ / Δ'Q₂Δ. This departs deliberately from `mbreaks` 1.0.1, which divides by Δ'Q₁Δ (§1–§2). |
| 2 | The correction is validated by an **independent limit simulation** and a **coverage study on the Phase A month-start grids** (§3). Intervals stay **nominal**: coverage is not calibrated. |
| 3 | The R comparison is rerun with **exact** interval bounds. Every difference is reproduced by a named convention. R agreement is described as **implementation fidelity** only (§4). |
| 4 | Phase A: an **allow-list** output guard; an **amended gate** using the rerun comparison; **4 workers** (§5). |
| 5 | Remaining limitations are recorded (§6). None blocks Phase A. |

## 1. The defect

`kagura.breaks.break_intervals`, robust branch (the ADR 0007 protocol):

| | Before | After |
|---|---|---|
| `phi1s` | Δ'Ω₁Δ / Δ'Q₁Δ | unchanged |
| `phi2s` | Δ'Ω₂Δ / **Δ'Q₁Δ** | Δ'Ω₂Δ / **Δ'Q₂Δ** |
| `eta`, `a` | Δ'Q₂Δ / Δ'Q₁Δ, (Δ'Q₁Δ)² / Δ'Ω₁Δ | unchanged |

- **Before** was a faithful port of `mbreaks::interval`. Its source was inspected on 2026-11-17:
  `phi2s = t(delv) %*% omega1 %*% delv / (t(delv) %*% qmat %*% delv)`.
- The two agree only when η = 1.
- Every ADR 0007 validation design, R fixture and unit test had η ≈ 1, so the defect was
  invisible to all of them.

## 2. Derivation

Let the estimated break be r rows away from the true break k₀.

**Late estimate (r > 0).** Rows k₀+1 … k₀+r, which belong to regime 2, are fitted with δ₁.
The SSR rises by r·Δ'Q₂Δ plus a noise term. The noise has long-run variance 4r·Δ'Ω₂Δ.

**Early estimate (r < 0).** The same holds with Q₁ and Ω₁.

**Rescaling.** Put r = s / a with a = (Δ'Q₁Δ)² / Δ'Ω₁Δ, and divide the objective by
2Δ'Ω₁Δ / Δ'Q₁Δ. Then a(k̂ − k₀) converges to the argmax of Z(s):

- Z(s) = W₁(−s) − |s|/2 for s ≤ 0;
- Z(s) = √φ·W₂(s) − ξs/2 for s > 0;
- ξ = Δ'Q₂Δ / Δ'Q₁Δ and φ = Δ'Ω₂Δ / Δ'Ω₁Δ.

**What `cvg` expects.** `cvg(η, p₁, p₂)` (`bai_quantiles`) gives the quantiles of this Z with
ξ = η and φ = η·p₂/p₁. Two checks support this:

- It is consistent with the non-robust branch. There p_j = σ_j², and under Ω_j = σ_j²Q_j,
  φ = ησ₂²/σ₁².
- It is confirmed numerically by an independent simulation of Z
  (`tests/test_breaks.py::test_bai_quantiles_match_independent_limit_simulation`, within 8 %).
  Example: `cvg(2, 1, 1.5)` = [−10.42, −7.09, 6.06, 8.58]; the simulation of Z with ξ = 2 and
  φ = 3 gives [−10.36, −7.14, 6.02, 8.60].

**Consequence.** Getting φ right requires p₂ / p₁ = φ / ξ, that is, p₂ = Δ'Ω₂Δ / Δ'Q₂Δ.

- The old code implied φ·ξ in place of φ: η was counted twice.
- Under homoskedastic errors with Var(x) multiplied by η after the break, the correct 95 %
  quantiles are:
  - η = 4: [−11.03, 2.76];
  - η = 0.25: [−11.03, 44.13].
- The old code used:
  - η = 4: [−11.84, 7.91];
  - η = 0.25: [−7.91, 11.84].

**Caveat.** Bai (1997) itself was not read (ADR 0007 L11). The derivation above and the
simulations, not the paper, are the evidence. Whether the original Bai–Perron GAUSS code
shares the defect is unknown.

**Real-data relevance**, computed for the audit with no break estimated: the variance of the
daily 2Y Δdiff in the five ADR 0004 eras is

| Era | Variance |
|---|---|
| 1981–1989 | 0.0152 |
| 1990–1998 | 0.0048 |
| 1999–2012 | 0.0035 |
| 2013–2021 | 0.00099 |
| 2022– | 0.0053 |

So η of roughly 0.3–5.4 is plausible at the boundaries of interest.

## 3. Validation

### 3.1 Regression tests (`tests/test_breaks.py`)

- **Limit quantiles.** `bai_quantiles` against an independent Monte Carlo of Z for
  (ξ, φ) = (0.25, 0.25), (1, 1), (4, 4) and (2, 3).
- **Interval mapping**, at η = 0.25, 1 and 4.
  - **Design:** T = 40,000, true break at 20,000, shift 0.6, Bartlett lag 0.
  - **Check:** at the true break, the half-widths times the population a must match the
    population quantiles. The left/right width ratio, which does not depend on a, must agree
    within 5 %.
  - **Result:** the original code fails at η = 0.25 and 4, and passes at η = 1. This was
    checked by running the same test against `breaks.py` at commit `8e4b8bd`.

### 3.2 Coverage study (`research/methodology/adr0012-bai-interval/coverage.py`)

**Design:**
- Phase A's primary month-start eligible grids at ε = 15 %: recent T = 3,052 and
  full T = 10,279.
- The true break is the eligible candidate nearest T/2.
- m = 1 is estimated on the grid, with the Bartlett lag of ADR 0006 §4.4.
- Slope shifts 0.15, 0.30 and 0.60 (ADR 0011 §6). Unit error variance; Var(x) multiplied by η
  after the break.
- 1,000 repetitions per design; seed 20261118.
- Only frozen dates are read. Nothing is fitted to USD/JPY.

**Coverage at nominal 95 %**, corrected → original. Brackets are Clopper–Pearson 95 %
intervals for the corrected method. "Left" is the share of runs where the true date lay left
of the interval (target about 2.5 %).

| Sample | Shift | η | Coverage, corrected [CP95] | Coverage, original | Left, corrected / original | Right, corrected / original | Median width, corrected / original (rows) |
|---|---|---|---|---|---|---|---|
| recent | 0.15 | 0.25 | 0.800 [0.774, 0.824] | 0.638 | 0.117 / 0.282 | 0.083 / 0.080 | 1298 / 627 |
| recent | 0.15 | 1 | 0.869 [0.846, 0.889] | 0.868 | 0.062 / 0.063 | 0.069 / 0.069 | 756 / 758 |
| recent | 0.15 | 4 | 0.895 [0.874, 0.913] | 0.903 | 0.037 / 0.007 | 0.068 / 0.090 | 523 / 752 |
| recent | 0.30 | 0.25 | 0.886 [0.865, 0.905] | 0.719 | 0.064 / 0.240 | 0.050 / 0.041 | 520 / 205 |
| recent | 0.30 | 1 | 0.931 [0.913, 0.946] | 0.933 | 0.034 / 0.033 | 0.035 / 0.034 | 232 / 231 |
| recent | 0.30 | 4 | 0.943 [0.927, 0.957] | 0.939 | 0.021 / 0.000 | 0.036 / 0.061 | 149 / 212 |
| recent | 0.60 | 0.25 | 0.938 [0.921, 0.952] | 0.763 | 0.042 / 0.221 | 0.020 / 0.016 | 147 / 55 |
| recent | 0.60 | 1 | 0.960 [0.946, 0.971] | 0.959 | 0.013 / 0.014 | 0.027 / 0.027 | 61 / 61 |
| recent | 0.60 | 4 | 0.951 [0.936, 0.964] | 0.944 | 0.017 / 0.001 | 0.032 / 0.055 | 39 / 55 |
| full | 0.15 | 0.25 | 0.900 [0.880, 0.918] | 0.719 | 0.063 / 0.247 | 0.037 / 0.034 | 2026 / 799 |
| full | 0.15 | 1 | 0.937 [0.920, 0.951] | 0.937 | 0.032 / 0.032 | 0.031 / 0.031 | 891 / 888 |
| full | 0.15 | 4 | 0.934 [0.917, 0.949] | 0.942 | 0.032 / 0.001 | 0.034 / 0.057 | 593 / 849 |
| full | 0.30 | 0.25 | 0.948 [0.932, 0.961] | 0.750 | 0.030 / 0.229 | 0.022 / 0.021 | 588 / 218 |
| full | 0.30 | 1 | 0.955 [0.940, 0.967] | 0.954 | 0.019 / 0.020 | 0.026 / 0.026 | 245 / 244 |
| full | 0.30 | 4 | 0.937 [0.920, 0.951] | 0.945 | 0.036 / 0.000 | 0.027 / 0.055 | 152 / 218 |
| full | 0.60 | 0.25 | 0.948 [0.932, 0.961] | 0.702 | 0.031 / 0.279 | 0.021 / 0.019 | 152 / 56 |
| full | 0.60 | 1 | 0.954 [0.939, 0.966] | 0.954 | 0.025 / 0.025 | 0.021 / 0.021 | 62 / 62 |
| full | 0.60 | 4 | 0.972 [0.960, 0.981] | 0.976 | 0.005 / 0.000 | 0.023 / 0.024 | 39 / 56 |

**Reading the results:**
- **η = 1:** the two methods are identical up to Monte Carlo noise, as the derivation implies.
- **η = 0.25:** the original undercovers badly, at 63.8–76.3 %. In 22–28 % of runs the true
  date lies left of the interval. The corrected method gives 80.0–94.8 %, with the misses
  balanced much better.
- **η = 4:** the original's coverage looks acceptable, but its shape is wrong. The left miss is
  about 0 % and the right miss up to 9 %, and intervals are about 40 % too wide. The corrected
  method is balanced and narrower.
- **Calibration is not shown.**
  - Coverage still depends on the shift size: 80.0 % at shift 0.15, η = 0.25 (recent).
  - Some designs over-cover. At full, shift 0.60, η = 4, 90 % coverage equals 95 % coverage
    (0.971 vs 0.972). With intervals about two months wide, the month-start grid makes
    coverage lumpy.
  - These designs assume one true break, the correct m, and i.i.d. errors.

**Two sets of experiments, kept apart:**

| Set | Designs | Coverage at nominal 95 % | Status |
|---|---|---|---|
| ADR 0011 §6, the original `validation_sims.txt` | T = 1,000, daily grid, η = 1, shifts 0.15/0.30/0.60 and an error-sd 1 → 2 design | 76.5–92.7 % | Unchanged. With η = 1 the correction has no effect, so these numbers also describe the corrected method. |
| ADR 0012 §3.2, this study | Phase A month-start grids, η = 0.25/1/4 | Corrected method 80.0–97.2 %; original 63.8–97.6 % | New |

**Phase A note** (`CI_NOTE`): "nominal level only, coverage not established; simulated
coverage at nominal 95 % ranged from 76.5 % (ADR 0011 §6: T = 1,000, shift 0.15) to 97.2 %
(ADR 0012 §3.2: full grid, shift 0.60, eta = 4); not a bound for these estimates".
- The low endpoint is ADR 0011's small-shift design; the high endpoint is this study's
  full-sample, shift 0.60, η = 4 design.
- **The range is not a coverage bound for historical USD/JPY estimates.** Those have unknown
  m, unknown break sizes, several breaks per partition, and GARCH-type, non-MDS errors (ADR
  0006 §4.5). None of these is simulated here, and coverage could lie outside the range.
- **Nominal 95 % coverage is not established** for any design class.
- The ADR 0007 §9.1 critical-value check stays **FAILED** (ADR 0011 §1) and is untouched by
  this ADR.

**Not regenerated:** `validation_sims.txt` (ADR 0011 §5 original) is kept byte for byte. Its
CI rows have η = 1, so the correction does not change their expected values.

## 4. R comparison: exact bounds, implementation fidelity

- `compare.py` now:
  - requires identical interval bounds (previously within one row);
  - reproduces `mbreaks`' robust `phi2s` with `mbreaks_interval`;
  - writes `comparison_adr0012.txt`. The frozen `comparison.txt` is not rewritten.
- **In-memory run on 2026-11-18:** 309 pass, 90 convention, **0 FAIL** (399 rows, as before).
  Of the 96 interval rows:
  - 30 match exactly;
  - 34 differ by the `phi2s` correction, 16 of them together with the `mbreaks` rounding
    quirk;
  - 32 differ by the rounding quirk alone.
  - In the ADR 0011 run, 32 one-row differences had been labelled "pass" under the one-row
    tolerance.
- Every convention row is reproduced exactly by its named `mbreaks` behaviour before it gets
  that label.
- **Meaning.** Agreement shows that the port computes what `strucchange`/`mbreaks` compute
  (implementation fidelity). It is not evidence that either is correct: this defect was shared
  and could not be detected this way.

## 5. Phase A changes (`research/adr0007/run_breaks.py`)

| Item | Change |
|---|---|
| Guard | `ALLOWED`, an explicit set of output columns, replaces the name blocklist. Any other column is refused. Tier and label checks are unchanged. A test asserts that the allow-list contains no withheld-statistic name. |
| Gate | ADR 0011 §7 is amended: the R condition reads `comparison_adr0012.txt`, which must exist, match the §7 hash and report 'FAIL': 0. The five ADR 0011 §5 hashes are still checked, including the original `comparison.txt`. |
| Workers | 10 → 4. One daily-grid cell peaked at 2.26 GB (measured on synthetic data, T = 10,279, ε = 5 %), so the peak is about 10 GB at most. |
| CI note | As in §3.2. |

Unchanged: the dynamic program, grids, BIC/LWZ, coefficient tables and cell list. The audit
verified the dynamic program and grids against brute force and found no defect in them.

## 6. Limitations recorded (none blocks Phase A)

| # | Item |
|---|---|
| L19 | **FX/yield timing.** USD/JPY is the 12:00 New York fix; US yields are about 15:30; FOMC statements come at 14:00–14:15. Post-noon news moves the same-day Δdiff but the next day's ΔFX. Its share varies by era, so estimated dates may partly reflect intraday news timing. V1 (lagged) is the check. State this beside every break date. |
| L20 | **Phase C multiplicity.** 30 cells × m = 1…5 × breaks × event classes make many comparisons. Before Phase C, freeze which cell and m are headline, or report the comparisons as one family. The ADR 0009 §7.2 chance baselines are per comparison. |
| L21 | **Intervention alignment.** MOF records trade dates. New York-afternoon operations (e.g. 2022-10-21, probably 2024-05-01) follow the noon fix, so `fx_row_decision` is one row early. They are flagged `fx_row_uncertain`. This is immaterial on a month grid, but not for daily-row statistics. |
| L22 | **Incomplete audit coverage.** The 2026-11-17 audit did not re-run H1b, did not inspect the restricted BOJ data (ADR 0010 §3a's second coding pass is still required before BOJ C1 is used), did not review the critical-value simulator beyond its summary counts, and did not re-run R itself. |
| L23 | **Interval calibration** (§3.2). The corrected intervals are better shaped but not calibrated; coverage depends on the break size, and the month grid makes it lumpy. |

## 7. Validation artifacts (generated 2026-11-18)

**Environment:**
- Python 3.12.8, NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.5, uv 0.7.2.
- R was not re-run. `compare.py` reads the committed `r_results.json` (ADR 0011 §5 hash
  unchanged; R 4.5.3, strucchange 1.6-0, mbreaks 1.0.1, per `r-crosscheck/sessionInfo.txt`).

| Artifact (under `research/methodology/`) | Command | Seed | SHA-256 |
|---|---|---|---|
| `adr0007-break-grid/r-crosscheck/comparison_adr0012.txt` | `uv run python research/methodology/adr0007-break-grid/r-crosscheck/compare.py` | none (deterministic) | `93fb041358a85a01a08430c3722e209ccde7858ea07da2abd2501199ea9af38f` |
| `adr0012-bai-interval/coverage.txt` | `uv run python research/methodology/adr0012-bai-interval/coverage.py` | 20261118 | `115fb816b5f670f755bdf768bc732100a8760e4b3bdb99d87f65eb40ba34f280` |

**Checks made 2026-11-18:**
- Every value of every §3.2 row (18 designs × 2 methods) equals `coverage.txt`. That file is
  identical to an earlier in-memory run of the same code.
- `comparison_adr0012.txt` reports 309 pass, 90 convention, 0 FAIL. The 90 conventions break
  down as:
  - 24 `psigmq` (non-robust SEs and F, from before);
  - 32 rounding quirk;
  - 18 `phi2s`;
  - 16 `phi2s` with the rounding quirk.
  
  None is unlabelled.
- The five ADR 0011 §5 originals are byte-identical.
- The Phase A gate now also pins the `comparison_adr0012.txt` hash above.
