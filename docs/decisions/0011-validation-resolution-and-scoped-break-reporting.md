# ADR 0011 — ADR 0007 Validation Resolution and Scoped Break Reporting

Date: 2026-11-17.

**Status: FROZEN 2026-11-17** (reviewer approval of the Phase A direction, with six
adjustments, all incorporated).

- ADR 0011 changes how ADR 0007's results may be computed and labelled.
- ADR 0007 itself, its §9.1 thresholds and every original validation output stay unchanged.
- After freezing, any change needs a new ADR.

## 0. Decision summary

| # | Decision |
|---|---|
| 1 | The ADR 0007 §9.1 critical-value check **failed** as frozen. It stays recorded as failed and is **not resolved** (§1). |
| 2 | The grid-resolution explanation and the 1,000-point table comparison are **supporting diagnostics only**. No revised pass criterion is adopted (§2). |
| 3 | Three tiers, never merged: **descriptive estimate**, **model selection**, **tested claim**. Phase A produces only the first two (§3). |
| 4 | **Sequential-rule break counts are withheld.** The q = 2 discrepancy is plausibly explained but unresolved (§4). |
| 5 | **Phase B** (sup F(k), UDmax, WDmax, WF bootstrap) is **withheld** until its validation requirements are separately approved. Supplementary designs S1–S3 are proposed, not adopted (§5). |
| 6 | Bai intervals appear only as **nominal** intervals, beside their simulated undercoverage (76.5–92.7 % at nominal 95 %). Widths are reported in rows, calendar days and share of the eligible range. No width-based classification is used (§6). |
| 7 | **Phase A** (descriptive estimation) is authorised once this ADR is frozen. It is run by `research/adr0007/run_breaks.py`, which does not compute the withheld statistics (§7). |

## 1. The failed check

ADR 0007 §9.1 requires simulated sup F(k), UDmax and sup F(l + 1 | l), for q = 2 and q = 10
at ε = 5, 10, 15 %, to lie within 0.35 of the published tables at a 4,000-point grid.

- **Result** (`research/methodology/adr0007-break-grid/critical_values_tables.txt`):
  - 11 of 72 rows lie outside 0.35, between +0.37 and +0.53, and all are positive;
  - **within the frozen scope**, which excludes WDmax (WDmax was added by the script, not by
    §9.1), **9 of 66 rows lie outside**;
  - in every failing row the table value lies below the simulation's 95 % order-statistic
    interval.
- **Status: FAILED. Not resolved.**
- The 1,000-point diagnostic below does not change this result. That diagnostic was chosen
  after the failure was seen.

**Supporting diagnostic** (`critical_values_tables_1000.txt`):
- At the tables' own 1,000-step design, 72 of 72 rows lie within 0.35 (maximum 0.33).
- 10 of the 11 failures fall to |difference| ≤ 0.15.
- The mean 4,000 − 1,000 difference is +0.32 to +0.37 for q = 10 and +0.11 to +0.19 for
  q = 2.

This is consistent with grid resolution: a supremum over more points is larger, and the
effect grows with q. Two caveats:
- the two runs used different seeds, so per-row grid effects include Monte Carlo noise (five
  q = 2 UDmax/WDmax rows even show negative effects);
- even at 1,000 points, 26 of 72 table values lie outside our Monte Carlo interval.

## 2. Two questions, kept apart

| Question | Appropriate comparison | Reason |
|---|---|---|
| A. Does our limit simulator reproduce the published tables (definition, q scaling, DP, sequential construction)? | The tables' own design: a 1,000-step grid | A table value is a quantile of one particular discretised limit. Comparing it with a finer grid adds a known, one-sided resolution bias, so the comparison tests resolution, not correctness. |
| B. Which reference values suit KAGURA's data? | Neither. Values simulated on each cell's **actual candidate fractions** (ADR 0007 §6.1, unchanged) | Month-start grids have 164–550 candidates; their values lie 0.3–0.8 below the tables. |

- **Question A.** The 1,000-point comparison is a diagnostic for A, not a pass criterion.
  A tolerance derived from both Monte Carlo errors (about 0.40 for q = 2 and 0.54 for
  q = 10) was considered and **not adopted**: it would pass every observed row, and it
  cannot detect simulator errors below that size.
- **Question B** needs its own validation (S3, §5) before any Phase B use. Phase B
  validation requirements are to be approved separately.

## 3. Evidence tiers

| Tier | Meaning | Phase A |
|---|---|---|
| **Descriptive estimate** | The least-squares partition for a given m, its dates and regime coefficients. Regime HAC standard errors are reported as descriptive scale measures, conditional on the estimated dates. | **Reported** for m = 0…5 in every cell |
| **Model selection** | The m picked by BIC or by LWZ under the model's assumptions | **Reported**: both rules, never "the number of breaks" |
| **Tested claim** | Any statement that a statistic exceeds a reference value, including ADR 0007's "approximately tested" and "bootstrap-supported" | **None.** sup F(k), UDmax, WDmax, sequential and WF statistics are not computed. |

- **R agreement is not coverage.** The §9.2 cross-check (359 pass, 40 documented
  conventions, 0 FAIL) shows that our formulas compute what `strucchange` and `mbreaks`
  compute. It shows nothing about size or coverage on these data.
- **Assumptions for any future tested claim.** Each must state its assumptions: the HAC lag
  rule, regime-specific variances, the Brownian-motion limit on the actual candidate set,
  the order-statistic interval of the reference value, and the unsimulated finite-sample
  size of HAC sup-type tests (ADR 0007 §6.2).
- **"Bootstrap-supported" is unavailable.** It needs at least S1 and S2 reviewed, plus a
  separate approval.

## 4. The q = 2, ε = 15 % sup F(2 | 1) discrepancy: plausibly explained, unresolved

This was one focused investigation using existing sources only:
- our `breaksim.seq_limit`;
- `mbreaks`' `sequa`, `getcv1` and `getcv2`;
- the two table runs.

| Candidate cause | Evidence | Verdict |
|---|---|---|
| Statistic scaling | seq(1 \| 0) equals sup F(1) in tables and simulation; every q = 10 sequential row agrees within 0.12 at 1,000 points | Ruled out |
| Null/alternative partitions | In the limit, only the per-regime trimming fractions matter; the table design uses ε in each regime | Not applicable |
| Trimming within segments | A different rule would shift every (l + 1 \| l) row and every q in the same direction. Observed: q = 2, ε = 15 %: +0.29, +0.13, −0.08, +0.03 for l = 1…4; q = 10: +0.02, +0.05, −0.09, −0.03 | Not supported |
| Monte Carlo error in the reference table | The published increments seq(l + 1 \| l) − seq(l \| l − 1) should shrink with l and rise smoothly with q. They break this pattern in six places (e.g. ε = 10 %, q = 1: 0.81, then 0.99). The q = 2, ε = 15 % first increment (1.48) dips below q = 1 (1.55) and q = 3 (1.74); our 1,000-point value is 1.66 | **Plausible; not confirmed** |

- Bai and Perron (1998) and their simulation draws were not read (ADR 0007 L11).
- **Sequential-rule break-count inference stays withheld.** Phase A does not compute it.

## 5. Supplementary validation designs (proposed, not run, not adopted)

These correct design defects in ADR 0007 §9.1. They are supplementary and do not replace
the original results. Running them, and any pass rule for Phase B, need separate approval.

| # | Corrects | Proposed design |
|---|---|---|
| S1 | BG power (D1). The AR(1) alternative was largely absorbed by the y₍t−1₎ regressor: power at ρ = .05 equalled size. | Lag-augmented layout (q = 4, both T). Alternatives the regressors cannot span: e_t = u_t + θu₍t−5₎ with θ = .05 and .10, and e_t = u_t + θu₍t−2₎ with θ = .10. GARCH(1,1) u_t, 1,000 reps. Report the residual autocorrelation the regressors leave. |
| S2 | Non-MDS alternative (D2). The 0.3·x₍t+1₎ term showed no distortion. | Lead–lag with γ = 0.3 and 1.0; nonlinear mean dependence δ(x₍t−1₎² − 1) with δ = .3 and .6. WF size at B = 999, 500 reps, both T, plus the step-1 BG rejection rate in the same draws. |
| S3 | Grid comparisons on different seeds (D3) | One set of draws per (q, ε), evaluated on the 4,000-step grid, the 1,000-step grid and each cell's actual candidate fractions. 100,000 draws. Paired grid effects with intervals. |

**Original outputs, preserved byte for byte.** The Phase A gate checks these hashes:

| File (under `research/methodology/adr0007-break-grid/`) | SHA-256 |
|---|---|
| `critical_values_tables.txt` | `5c932795783f2021be6e2cf12ac9c6018cf02e18a92a29c04d9d6f71bc34ff50` |
| `critical_values_tables_1000.txt` | `b1db57ef3bc497a9e7ba5809c3ea1b8ab8af4a58cee6a986f9f665e9d60b92fe` |
| `validation_sims.txt` | `7eba72d84579f3b3bb6c8fc3a206e0debd921729f5ae4f92527dcbc66da973c9` |
| `r-crosscheck/comparison.txt` | `b690585c4e03c18250b8899ee04c1662f7aebe3c258c74db7e65f449d42e3f1b` |
| `r-crosscheck/r_results.json` | `c6e43db91cfb4264d63526a122553a397e9069dcef3ec1aa3ddfa28a7f51d6d0` |

## 6. Break-date intervals

**Simulated coverage at nominal 95 %** (`validation_sims.txt`; T = 1,000, one slope break at
row 500, Bartlett HAC with 6 lags, 1,000 reps):

| Slope shift | 95 % coverage [CP95] | 90 % coverage | Median 95 % width |
|---|---|---|---|
| 0.15 | **76.5 %** [73.7, 79.1] | 66.5 % | 448 rows |
| 0.30 | 87.7 % [85.5, 89.7] | 80.5 % | 199 rows |
| 0.60 | 92.7 % [90.9, 94.2] | 87.5 % | 59 rows |
| 0.30, error sd 1 → 2 | 81.4 % [78.8, 83.8] | 72.0 % | 375 rows |

**Reporting rules:**
- Interval columns are named `ci95_nominal` and `ci90_nominal`. Every row carries the note:
  "nominal level only; simulated coverage at nominal 95 % was 76.5–92.7 %". The
  90 %/95 % labels are **not** validated coverage.
- Coverage on real data may be lower: these designs assume one true break, a correctly
  chosen m and simple errors.
- Widths are reported three ways:
  - **rows**, untruncated;
  - **calendar days**, between the truncated endpoints;
  - **share of the eligible range**: rows ÷ (last − first eligible candidate).
  
  A truncation flag marks intervals cut at the eligible range.
- **No width threshold classifies an interval.** The 20 % heuristic proposed in the draft is
  withdrawn.
- **What an interval can still convey, descriptively:** the relative precision of dates
  within the same run, and asymmetry about the estimate. It cannot convey a probability that
  the true date lies inside it.

## 7. Phase A

| Phase | Content | Gate |
|---|---|---|
| **A** | Every ADR 0007 cell: partitions for m = 0…5 (SSR, BIC, LWZ, dates); BIC and LWZ selections; dates and nominal Bai intervals for m = 1…5; regime coefficients and HAC SEs for m = 0…5; daily-grid m = 1 date for the primary specification. Cells: primary, V1, V2, V3 × full/recent × ε = 15/10/5 %, and lag-augmented (p = 1) × full/recent × ε. | This ADR frozen; R cross-check 0 FAIL; §5 hashes unchanged |
| B | Tested claims (Phase B statistics) | Withheld; separate approval |
| C | ADR 0009 §7 event comparison | After Phase A is reported and reviewed |

**Implementation** (`research/adr0007/run_breaks.py`):
- `gate()` enforces the Phase A gate.
- The withheld statistics are not computed.
- `guard()` rejects any output row with:
  - a column name suggesting a test statistic, critical value, p-value, sequential or
    bootstrap result;
  - a tier other than "descriptive estimate" or "model selection";
  - a label containing "tested", "bootstrap", "significan…" or "confirm…".
- `write()` applies `guard()` before anything is written.
- `tests/test_phase_a.py` tests all of this.

**Command:** `uv run python research/adr0007/run_breaks.py`, writing to
`research/adr0007/out/phase_a/`.

**Reporting order:**
1. Dates, nominal intervals and widths.
2. Coefficients.
3. BIC/LWZ disagreements across m, ε, sample, grid and specification.
4. Limitations.

The event comparison waits for Phase C.

## 8. Limitations added

| # | Item |
|---|---|
| L13 | The §9.1 critical-value check failed as frozen and is unresolved. Grid resolution is supported only by a post-hoc diagnostic. |
| L14 | Sequential break counts are withheld. The q = 2, ε = 15 % gap is plausibly table Monte Carlo error, not confirmed. |
| L15 | Bai intervals undercover in every simulated design (76.5–92.7 % at nominal 95 %). |
| L16 | Finite-sample size of HAC sup-type tests on the real dependence structure is unsimulated. |
| L17 | The WF bootstrap has no independent implementation to check against. |
| L18 | BG power and non-MDS bootstrap behaviour are not validated (design defects D1, D2). |

## 9. Not changed

- ADR 0007, including its thresholds, labels and §9.1;
- ADR 0009 and ADR 0010;
- historical data and checksums;
- H1a/H1b results;
- every original validation output (§5).
