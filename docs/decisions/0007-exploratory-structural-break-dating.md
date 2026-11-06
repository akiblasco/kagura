# ADR 0007 — Exploratory Structural-Break Dating of the H1a Short-Run Relation

Date: 2026-11-04. Revision 3 final: 2026-11-06.

**Status: FROZEN 2026-11-06 (revision 3 final: reviewer approval with conditions on L11,
the mandatory R cross-check and grid-specific simulated thresholds).**

- **Freezing** means committing this file, ADR 0009 and `research/methodology/adr0007-break-grid/`
  in one commit, then pushing, before any break statistic is computed on historical data.
- Nothing in §4–§8 has been run on real data. The only real-data computation is the row
  and candidate-date count in §3.3, which fits no model.
- **After freezing,** any change needs a new ADR.

## 0. Decision summary

| # | Decision | Approved |
|---|---|---|
| 1 | **Trimming, option (iii).** The full 1981–2026 sample and a 2013+ subsample, each at 15 %, 10 % and 5 %. Long-regime and shorter-regime analyses are kept apart (§3). | 2026-11-04 |
| 2 | **Lag-augmented model** as a sensitivity analysis with its own estimand and its own reference distributions (§4.2, §6.3). It never replaces H1a's regression. | 2026-11-04 |
| 3 | **Policy events** come from ADR 0009, frozen with this ADR and collected before any break estimation. | 2026-11-04 |
| 4 | Recent sample starts **2013-01-01** (Q-A). | 2026-11-06 |
| 5 | **Pure structural change:** intercept and all slopes may break (Q-B). | 2026-11-06 |
| 6 | **M = 5** at every trimming (Q-C). | 2026-11-06 |
| 7 | **R `strucchange` cross-check** on synthetic fixtures, outside the core environment and CI (Q-D, §9.2). | 2026-11-06 |
| 8 | **Elliott–Müller intervals deferred** (Q-E). | 2026-11-06 |
| 9 | **Primary search grid: month-start candidates.** Daily-grid single-break search as a sensitivity (§3.2). | 2026-11-06 |
| 10 | Everything is **exploratory**. Nothing confirms or rejects H1, H1a or H1b, and nothing is gated at α. | — |

## 1. Context

- **ADR 0006 §6.2** deferred unknown-break-date inference from H1a to this ADR, recording
  Boldea, Cornea-Madeira and Hall's (2019) wild fixed-regressor (WF) bootstrap as the
  candidate. That bootstrap needs martingale-difference (MDS) errors. The same-day H1a
  regression violates that by construction (ADR 0006 §4.5).
- **ADR 0006 A6.** If the true change is not at 2022-01, H1a's era contrast is biased toward
  no change. Break dating is the direct check.
- **H1a result:** β 6.44 (2013–2021) → 4.05 (2022–), inconclusive. The rolling β declined
  before 2022.
- **H1b:** no defensible long-run baseline (ADR 0008 §9.4 and Stage 1). This ADR **does not
  date breaks in a levels or cointegrating relation.**
- **ADR 0004 and ADR 0008 §9.6** forbid choosing era boundaries from the data. Estimated
  break dates are **never turned into eras** for any other analysis.

### 1.1 Disclosure: what has been seen

| Seen | Bearing |
|---|---|
| H1a era β for all five ADR 0004 eras, rolling β and R², two-leg decomposition, era-equality Wald | Approximate timing of changes in β is known. |
| ADR 0004 rolling correlations and era standard deviations | Volatility differs strongly by era (§5.3). |
| Usable rows and eligible candidate dates (§3.3) | Counted for this ADR, with no model fitted. |

**Not computed:** any sup-Wald, sup-F, Bai–Perron statistic, information criterion, break
date or interval, or any lag-augmented regression on real data.

## 2. Questions, and what the answers can be called

| Question | Answer type |
|---|---|
| Q1. Is one constant β a poor description of 1981–2026, and of 2013–2026? | sup-type statistics (§6) |
| Q2. Where do least-squares estimates place changes, and how uncertain are they? | Break dates and intervals (§5, §7) |
| Q3. Do the dates sit near official policy events? | Descriptive coincidence comparison (ADR 0009 §7) |
| Causation | **Not addressed** (ADR 0009 §7.4) |
| A confirmatory test of H1 or H1a | **Not possible.** ADR 0006 §8's H1 family is closed (ADR 0008 §7.1). |

### 2.1 Three labels for a break, never merged

| Label | Meaning | When it may be used |
|---|---|---|
| **Descriptive** | The least-squares partition for a given m, or the m picked by an information criterion | Always. Every estimated date starts here. |
| **Approximately tested** | An asymptotic sup-type statistic beyond its 5 % reference value, with conditions known to hold only approximately | Static specification (§6.2) |
| **Bootstrap-supported** | A WF-bootstrap sequential statistic beyond its 5 % reference value, **with** the §6.3 diagnostics passed before and after breaks | Lag-augmented specification only |

- None of these labels means a break is **statistically established**. No procedure here
  is known to have correct size under the data's dependence and volatility (§6.1).
- The strongest wording allowed is "bootstrap-supported, conditional on the assumptions in
  §6.3". Association language only (ADR 0006 §3). Nothing is "significant evidence" for H1.

## 3. Samples, search grid and trimming

### 3.1 Samples

| Sample | Dates | Role |
|---|---|---|
| **Full** | 1981-01-01 to 2026-09-11 (daily), 1981-01 to 2026-08 (monthly) | Long-regime analysis |
| **Recent** | **2013-01-01** to the same ends | Shorter-regime analysis |

Both end at the ADR 0006 §9.2 sample ends. Nothing is downloaded.

**Why 2013-01-01.** It is the start of ADR 0006's reference era and of ADR 0004's
2013–2021 era. ADR 0004 bounded that era by BOJ policy history (QQE, 2013-04-04) before any
result was seen. It was **not** chosen from a fitted break; none exists. The rolling-β path
had been seen (§1.1).

### 3.2 Search grid and break-date convention

**Convention.** A break date is the **first row of the new regime**. (`strucchange` reports
the last row of the old regime instead. §9 translates between the two.)

| Grid | Candidates | Used for |
|---|---|---|
| **Month-start (primary)** | The first usable daily row of each calendar month | All multi-break estimation, m = 0…5, every sample, ε and specification |
| **Daily (sensitivity)** | Every usable daily row | Single-break (m = 1) sup-Wald and date only, static primary specification |
| **Monthly data (V3)** | Every month-end row | Both grids coincide |

- **Why month-start.** A daily-resolution date is not interpretable at the precision it
  implies, because the date intervals (§7) span months. A coarser grid also makes dynamic
  programming over five breaks cheap and makes the supremum less sensitive to single
  volatile days.
- **What it costs.** A true break mid-month is placed at a month start, at most about 11
  business days away. The supremum over a restricted grid is smaller than over all rows, so
  reference values must be simulated **on the grid used** (§6.1).
- **Regimes are still measured in rows.** Each regime must have at least h = ⌊εT⌋ usable
  daily rows. Rows inside a month stay in the regression.

### 3.3 Eligible candidate ranges

Computed 2026-11-06 by `research/methodology/adr0007-break-grid/eligible_ranges.py`. The script
checks the frozen checksums first and fits nothing. Full output, including every variant and
every lag order, is in `eligible_ranges.csv` beside it.

**Primary: daily, same-day 2Y, static.** Month-start grid; the daily grid's first and last
dates are within one to four weeks of these.

| Sample | T | ε | h rows | h (years) | Candidates | First eligible | Last eligible |
|---|---|---|---|---|---|---|---|
| Full | 10,279 | 15 % | 1,541 | 6.85 | 384 | 1987-11-02 | **2019-10-01** |
| Full | 10,279 | 10 % | 1,027 | 4.56 | 439 | 1985-08-01 | **2022-02-01** |
| Full | 10,279 | 5 % | 513 | 2.28 | 493 | 1983-05-09 | 2024-05-01 |
| Recent | 3,052 | 15 % | 457 | 2.05 | 115 | 2015-02-02 | 2024-08-01 |
| Recent | 3,052 | 10 % | 305 | 1.37 | 132 | 2014-06-02 | 2025-05-01 |
| Recent | 3,052 | 5 % | 152 | 0.68 | 148 | 2013-10-01 | 2026-01-06 |

With M = 5 and these h, five breaks are feasible in every cell.

**Variants (from the CSV):**
- Lagged US leg (V1): T = 10,276 full; ranges identical at month resolution.
- 10Y (V2): T = 9,035 full from 1986-07-08; 15 % range 1992-07-01 to 2020-08-03, 10 %
  1990-07-02 to 2022-08-01, 5 % 1988-08-01 to 2024-08-01. Recent as for 2Y.
- Monthly 2Y (V3): T = 548 full (15 % 1987-11 to 2019-11; 10 % to 2022-03), 164 recent
  (15 % 2015-01 to 2024-09).
- **Lag-augmented (§4.2) loses rows.** Each lag must also pass the ADR 0004 exclusion rule:

  | p | 1 | 2 | 3 | 4 | 5 |
  |---|---|---|---|---|---|
  | T, full | 9,767 | 9,279 | 8,818 | 8,391 | 7,996 |
  | T, recent | 2,891 | 2,738 | 2,594 | 2,458 | 2,332 |

  At p = 5 the full sample loses 22 % of the static rows. The lag-augmented sample is
  therefore a different, holiday-thinned sample, which is a second reason (with §4.2) why its
  dates are not directly comparable with the static ones.

**Consequences, stated before any estimate:**
- **Full sample at 15 %: a break at or after 2022-01 is ineligible.** The last candidate is
  2019-10-01, and no regime shorter than 6.85 years can be found. This is a **long-regime**
  analysis only and cannot speak to the 2022-01 candidate.
- Full sample at 10 %: the 2022-01 month start is eligible, with one month to spare. A break
  there would leave a final segment of 4.7 years, the minimum the trimming allows.
- **Recent sample:** a break at the 2022-01 month start (first row 2022-01-03) would split
  the sample into about **9.0 years before and 4.7 years after.** At 15 % it lies inside the
  eligible range (2015-02-02 to 2024-08-01), 2.6 years before its upper end.
- The 2022– era can be its own regime only at full-sample 5 % or in the recent sample.

### 3.4 Trimming roles

| ε | Role |
|---|---|
| 15 % | Conventional when errors may be heteroskedastic or serially correlated (Bai and Perron 2003a). |
| 10 % | Sensitivity. |
| 5 % | Sensitivity. Short regimes make variance estimates noisy and sup statistics oversized. A date found only here is reported as such and never promoted. |

## 4. Specifications

### 4.1 Static (the H1a estimand)

```
Δs_t = α_j + β_j · Δd_t + ε_t,     t in regime j = 1, …, m + 1
```

- Variables, exclusion rule and row order exactly as H1a (ADR 0006 §4.1, §4.4, A9).
- Pure structural change: **q = 2** coefficients break.
- β_j has H1a's interpretation: a same-day linear-projection coefficient, % per pp.

### 4.2 Lag-augmented (sensitivity; a different estimand)

```
Δs_t = α_j + β0_j · Δd_t + Σ_{i=1..p} (β_i,j · Δd_{t−i} + φ_i,j · Δs_{t−i}) + ε_t
```

- **Why:** to make MDS errors more plausible, so the WF bootstrap may apply (§6.3).
- **p is chosen by the §6.3 rule** before any break statistic. One lag is not assumed to be
  enough.
- Lags are previous rows of the USD/JPY calendar. A row is used only if it and all p lagged
  rows pass the ADR 0004 exclusion rule (§3.3 gives T).
- Pure structural change: **q = 2 + 2p** coefficients break (4 to 12).
- **Estimand.** β0_j is the same-day coefficient holding the lagged changes fixed. It is not
  H1a's β and is never compared numerically with 6.44 or 4.05. The cumulative
  (β0 + Σβ_i)/(1 − Σφ_i) is a further estimand, reported descriptively. Dates from §4.1 and
  §4.2 date changes in different quantities, on different rows, and may legitimately differ.

### 4.3 Robustness variants (static only, all samples and trimmings)

| Variant | Change |
|---|---|
| V1 | Lagged US leg (ADR 0004 timing) |
| V2 | 10Y differential (full sample from 1986-07) |
| V3 | Monthly, month-end rows of `monthly.csv`, as ADR 0006 R2 |

## 5. Estimation

### 5.1 Break dates for a given m

Global minimisation of the sum of squared residuals over all partitions whose break dates are
grid candidates (§3.2) and whose regimes each have at least h rows. Dynamic programming as in
Bai and Perron (2003a), with segment SSRs from cumulative cross-product sums between
candidates.

### 5.2 Number of breaks: estimates, not established counts

| Rule | Label (§2.1) |
|---|---|
| BIC | Descriptive |
| LWZ (Liu, Wu and Zidek 1997) | Descriptive |
| Sequential sup F(l + 1 \| l), static, asymptotic (§6.2) | Approximately tested |
| Sequential sup F(l + 1 \| l), lag-augmented, WF bootstrap (§6.3) | Bootstrap-supported, if its conditions hold |

**Formulas** (n usable rows, l breaks, q breaking coefficients, p non-breaking coefficients,
S(l) the minimised SSR, p\* = (l + 1)q + l + p):
- **LWZ:** ln[S(l)/(n − p\*)] + p\* · c₀ (ln n)^(2 + δ₀) / n, with c₀ = 0.299 and δ₀ = 0.1.
  Read 2026-11-06 in Liu, Wu and Zidek (1997), eq. (2.3) and §3.3. Their p\* = (l + 1)p + l
  counts all regression coefficients as breaking. Here p\* also adds the non-breaking ones.
- **BIC:** ln[S(l)/n] + p\* ln(n)/n. This is the usual Schwarz form. Its exact printed form in
  Bai and Perron (2003a) was not read.
- **Sequential:** start from the global m = 1 fit. At step l, re-estimate one break inside
  each of the l + 1 regimes, and take the largest of the l + 1 one-break sup F statistics. If
  it exceeds the sup F(l + 1 | l) reference value for its q, add that break and continue;
  stop otherwise, or at M. This matches `mbreaks::sequa`. Bai and Perron (1998) was not read.

- **All rules are reported for every cell. None is treated as valid in general.**
  Information criteria tend to over-select under serial correlation and heteroskedasticity,
  both present here. Sequential tests inherit their reference distribution's size problems.
- **If the rules disagree,** every m they pick is reported with its dates. No m is called
  "the" number of breaks.
- If no rule's conditions hold (§6), the record says so, and m = 1…5 partitions are shown
  only as descriptions.

### 5.3 Heteroskedasticity across regimes

- Every Wald statistic and interval allows different error variances, and different
  regressor moment matrices, across regimes (Bai and Perron 2003a heterogeneous option).
- Variance breaks are not dated separately (L4).

## 6. Inference

Every p-value is a number at a 5 % descriptive reference level, with no family-wise meaning
(ADR 0008 §7.1).

### 6.1 Reference distributions must match q, ε, M and the grid

- **Published tables.** Bai and Perron (1998, 2003b) tabulate sup F(k), UDmax, WDmax and
  sup F(l + 1 | l) for q = 1…10 and ε ∈ {5, 10, 15, 20, 25 %}. Verified 2026-11-06 from the
  tables as distributed in `mbreaks` 1.0.1 (§12):
  - they are on the **q × F (Wald) scale**, not F/q. Checked in the code: `pftest` returns
    (T − (k + 1)q − p)/(T k) times the Wald statistic. For k = 1 this is the Wald statistic up
    to a degrees-of-freedom factor that tends to 1. The package prints it as "scaled by q";
  - indexing, from `getcv1`: file `cv_x` is ε = 5/10/15/20/25 % for x = 1…5. Rows are blocks
    of 10 per significance level (10 %, 5 %, 2.5 %, 1 %), with q = 1…10 within each block.
    Columns are k = 1, 2, …;
  - sup F(1) for q = 2 at 5 % (`cv_3` row 12, `cv_2` row 12, `cv_1` row 12, column 1):
    11.47 (ε = 15 %), 12.25 (10 %), 12.89 (5 %);
  - an own Brownian-bridge simulation (20,000 draws, 1,000-step grid, fixed seed;
    `research/methodology/adr0007-break-grid/critical_values_check.py`, output in
    `critical_values_check.txt`) of the q = 1 and q = 2 sup F(1) entries gives:

    | | ε = 15 % | ε = 10 % | ε = 5 % |
    |---|---|---|---|
    | 10 %, q = 1 / q = 2: sim − table | −0.01 / +0.07 | +0.03 / +0.07 | −0.01 / −0.04 |
    | 5 %, q = 1 / q = 2: sim − table | −0.04 / +0.05 | −0.13 / −0.20 | −0.06 / −0.28 |

    That first run is kept as it was run. Its 5 % gaps at ε = 10 % and 5 % (up to −0.28) are
    resolved by the second comparison below;
  - **second and last comparison** (`critical_values_grid.py`, output
    `critical_values_grid.txt`): 100,000 draws of a 4,000-step walk, a new fixed seed, and
    binomial order-statistic 95 % intervals for each quantile. The same draws are evaluated
    on four grids, so grid differences are not draw noise. Settings were fixed before the
    run and not adjusted afterwards. q = 2, 5 % critical value:

    | Grid points | ε = 15 % | ε = 10 % | ε = 5 % |
    |---|---|---|---|
    | 4,000 | 11.75 [11.68, 11.82] | 12.25 [12.19, 12.32] | 12.86 [12.79, 12.92] |
    | 1,000 | 11.60 [11.54, 11.68] | 12.09 [12.03, 12.17] | 12.65 [12.60, 12.72] |
    | 548 (≈ full-sample month starts) | 11.49 [11.42, 11.57] | 11.98 [11.92, 12.04] | 12.54 [12.47, 12.59] |
    | 164 (≈ 2013+ month starts) | 11.19 [11.11, 11.25] | 11.61 [11.55, 11.68] | 12.10 [12.04, 12.16] |
    | Table | 11.47 | 12.25 | 12.89 |

    The q = 1 rows follow the same pattern: at 4,000 points, 8.78 / 9.24 / 9.78 against the
    table's 8.58 / 9.10 / 9.63.
  - **Primary source (Bai and Perron 2003b, read 2026-11-06 from the authors' PDF).**
    - eq. (3.6) defines F_T with the factor 1/(kq), and eq. (3.9) defines its limit the same
      way;
    - the paper's response-surface table is headed "all statistics multiplied by q". So the
      tabulated scale is kq·F/k, the Wald statistic divided by k. For k = 1 that is the scale
      `mbreaks` prints and this ADR simulates. The scale is **confirmed from the primary
      source**;
    - design: W_q approximated by partial sums with n = 1,000 steps, 10,000 replications,
      sup by dynamic programming. The ε = 5 % values are taken from Bai and Perron (1998),
      whose design was not read;
    - the 7-page PDF does not reproduce the full critical-value tables, so the numbers
      themselves are still checked only against the `mbreaks` copy.
  - **Reading.** The statistic's definition, q and the indexing all match. The quantile rises
    with grid resolution, as a supremum over more points must. The size of the gap is now
    measured: the 20,000-draw interval half-width is about 0.15, and at 100,000 draws it is
    about 0.07. At ε = 10 % and 5 % the table lies within, or 0.03 beyond, the 4,000-point
    interval. At ε = 15 % it is closer to the 548–1,000-point values. The tables were simulated at
    1,000 steps (above). Against our 1,000-point values, the q = 2, 5 % table differs by
    −0.13 / +0.16 / +0.24 at ε = 15 / 10 / 5 %. With only 10,000 replications, the
    95 %-quantile half-width of the tables themselves is about 0.2 (√10 × our 0.07). So the
    ε = 15 % and 10 % differences are within the tables' own Monte Carlo error. The ε = 5 %
    difference is slightly beyond it, and that entry comes from the separate 1998
    simulation. **Exact reproduction of the published tables is not claimed.** Nothing points
    to a scaling or indexing error;
  - **consequence for this ADR:** a month-start grid has far fewer points than the tables
    assume. With 164 points, the correct q = 2, 5 % value is about 0.3–0.8 below the table.
    Using the table would make the tests conservative, by an amount that varies across cells.
    Hence the rule below.
- **Rule.** Every reference value used is **simulated for the actual q, ε, M and the actual
  candidate fractions** of that cell. The simulation is the Brownian-motion limit evaluated
  at the candidate positions, at least 100,000 draws, fixed seed, with the order-statistic
  interval reported. The approximation is confined to the Brownian-motion limit, evaluated
  on exactly the candidate set used. The published tables are a check, not the reference.
  The check passes if the 4,000-point simulation is within 0.35 of the table: the largest
  difference observed above, plus Monte Carlo error. It is applied where the table has the
  entry (q ≤ 10).
- **Label.** Static-model test results stay "approximately tested" (§2.1). The reason is the
  HAC and finite-sample approximation of §6.2. Critical-value uncertainty is a smaller
  source, and the order-statistic interval quantifies it. No inference is excluded on
  critical-value grounds.
- **The static q = 2 distribution is never used for the lag-augmented model.** That model has
  q = 4…12. q = 12 (p = 5) is outside the published tables and relies on the simulation
  alone.

### 6.2 Static specification: asymptotic, approximately tested

- sup-Wald (Andrews 1993), UDmax, WDmax and sequential sup F(l + 1 | l) with HAC (Bartlett,
  ADR 0006 §4.4 lag rule per sample) and regime-specific variances, against the §6.1
  simulated values for q = 2.
- **Approximate.** The limit distributions assume a consistent long-run variance under the
  null; HAC sup statistics are known to be oversized in finite samples with persistent
  volatility, more so at small ε. No bootstrap is applied: the WF bootstrap's MDS condition
  fails by construction here (ADR 0006 §6.2).

### 6.3 Lag-augmented specification: WF bootstrap under explicit assumptions

**Assumptions the bootstrap needs** (Boldea et al. 2019, Assumptions 9–10, Remark 4):

| | Assumption | Status here |
|---|---|---|
| B1 | Errors are an MDS with respect to the regressors and the past | **Not testable in full.** Only short-lag linear dependence is examined (step 1). |
| B2 | Conditional and unconditional heteroskedasticity allowed, with the stated moment conditions | Plausible for daily FX; heavy tails are not checked against the moment condition. |
| B3 | Regressors, including lagged Δs, held fixed in resampling | By construction. The bootstrap does not regenerate the dynamics. |
| B4 | Multipliers i.i.d. (0, 1) with finite 4 + δ moment | Rademacher. |
| B5 | Lag order p known | **Violated in practice.** p is pretested (step 1) and the bootstrap does not account for that. |

**Step 1 — fix p, before any break statistic.** On each sample, fit the no-break model for
p = 1…5. For each p, regress the residual on the regressors and its own 10 lags, and test the
10 lag coefficients jointly with an Eicker–White (HC0) covariance. Choose the smallest p with
p-value ≥ 0.05.

- Ordinary BG and Ljung–Box tests assume conditional homoskedasticity and are oversized under
  volatility clustering, so they are not used.
- **A pass shows only that the test found no linear autocorrelation in the first 10 lags.**
  It does not show MDS: it does not examine nonlinear dependence in the mean, dependence beyond
  lag 10, or dependence that the no-break model hides.
- **If no p ≤ 5 passes:** no bootstrap on that sample. Lag-augmented results get §6.2-type
  statistics with the §6.1 values for their q, and the label "MDS not supported".

**Step 2 — bootstrap.** Boldea et al. (2019) §2.3, eqs. (15)–(21): null-imposed residuals,
Rademacher multipliers, fixed regressors, sup-Wald with regime-specific Eicker–White variances,
B = 999, fixed seed. Sequential sup F(l + 1 | l) uses the l-break fit as the null.

**Step 3 — re-check.** The step-1 test is re-run on the residuals of each selected break
model. If it fails, the result is downgraded from "bootstrap-supported" to "approximately
tested", and the reason is reported.

**Simulation limits (§9.1).** Size is checked only on the synthetic designs listed there.
Acceptable size on those designs does not show acceptable size on the real data's
dependence. The report states this next to every bootstrap result.

## 7. Break-date intervals

- **Bai (1997) / Bai and Perron (2003a) asymptotic intervals,** 90 % and 95 %, heterogeneous
  case, computed in rows and reported as dates.
- **Construction**, transcribed from `mbreaks::interval`, the maintained implementation by
  Perron's group. The journal derivations were not read. For break i, with
  Δ = δ_{i+1} − δ_i:
  - Q₁, Q₂: the regressor second-moment matrices of the regimes before and after the break;
  - φ₁², φ₂²: the regime residual variances;
  - ξ = Δ′Q₂Δ / Δ′Q₁Δ, and a = Δ′Q₁Δ / φ₁²;
  - quantiles c from Bai's (1997) asymmetric limiting distribution, `cvg`(ξ, φ₁², φ₂²);
  - bounds T̂_i − c / a, rounded to rows.

  What was read is the non-robust branch (`robust = 0`, heterogeneous Q and variances). The
  HAC branch, and the internals of `cvg`, have not been read yet. They are transcribed when
  the code is implemented. The Python implementation is checked against `mbreaks::interval`
  on a synthetic fixture in the §9.2 R cross-check, not against the paper. This is
  disclosed as limitation L11.
- **Assumptions stated next to every interval:**
  - the shift shrinks with T. For large breaks the interval is conservative; for small ones
    its coverage is known to be poor;
  - the break is genuine and m is correct. Otherwise the interval has no coverage meaning;
  - regime-wise HAC long-run variances are consistent. At ε = 5 % this is doubtful;
  - the grid restriction is ignored: the interval is computed as if the break could fall on
    any row, so it is not narrowed to month starts.
- Asymmetric where the heterogeneous formula makes it so. Truncated at the eligible range,
  with the truncation flagged.
- Coverage is checked on synthetic designs (§9.1). No interval is described as having its
  nominal coverage unless that check supports it.
- Elliott–Müller (2007) intervals: deferred.

## 8. Outputs

All labelled **"exploratory (ADR 0007)"**, each break also carrying its §2.1 label.

| Output | Content |
|---|---|
| Grid table | Sample × ε × specification × variant: T, h, grid, candidate count, eligible range, sup-Wald, UDmax, WDmax, m by each rule |
| Break table | Per selected m: dates, 90 %/95 % intervals, regime coefficients with HAC 95 % intervals, §2.1 label |
| Daily-grid sensitivity | m = 1 date and sup-Wald on the daily grid, static primary, beside its month-start counterpart |
| Figure | H1a rolling β (unchanged), estimated dates and intervals, ADR 0004 markers, 2022-01 reference line |
| Event comparison | ADR 0009 §7 |

**Reading rules:**
- A full-sample 15 % result is a long-regime result and never evidence about 2022 (§3.3).
- A date found only at ε = 5 %, or only on the daily grid, is reported as such.
- Agreement across ε, samples, grids and specifications is described, not tested.

## 9. Validation (before real data)

### 9.1 Python checks (in `tests/` and the notebook)

| Check | Pass condition |
|---|---|
| DP vs brute force | T ≤ 300, an arbitrary candidate subset, m = 1, 2: DP partition and SSR equal an exhaustive search to 1e-10 |
| Grid | The candidate builder reproduces `eligible_ranges.csv` exactly |
| Known breaks | Synthetic two-break slope DGP: dates recovered to the nearest month start in most replications; at least one rule picks m = 2 |
| **Nile fixture** | statsmodels' Nile series (verified identical: mean 919.35), mean-shift model, h = 15 %, every row a candidate: BIC picks m = 1; break at observation 28 in `strucchange`'s convention (1898; first new-regime row 1899 in ours); segment means 1097.75 and 849.9722 (Zeileis et al. 2003 §4.1) |
| Critical values | Simulated sup F(k), UDmax and sup F(l + 1 \| l) for q = 2 and q = 10 at each ε are within 0.35 of the published tables at a 4,000-point grid (§6.1 check rule). The grid-specific values used are reported with order-statistic intervals |
| WF bootstrap size | 5 % null rejection with GARCH(1,1) MDS errors at the samples' T and the chosen q; Clopper–Pearson intervals. Also a non-MDS DGP with an ADR 0006 §4.5 lead–lag term, to show the distortion B1 guards against |
| Robust BG | Size under GARCH MDS errors; power against AR(1) errors |
| Interval coverage | Bai intervals on one-break designs with small, medium and large shifts and heteroskedastic regimes; coverage reported, not tuned |

Synthetic designs are fixed in advance and **not calibrated to fitted values from the real
data.**

### 9.2 Independent cross-check in R (outside the core environment)

- Python writes the synthetic fixtures (CSV, fixed seeds). An R script under
  `research/methodology/adr0007-break-grid/r-crosscheck/` runs `strucchange::breakpoints`
  on them (same h, every row a candidate, since `strucchange` has no grid option). Its outputs
  and `sessionInfo()` are committed as reference files.
- Pass: identical break dates (after the convention shift) and SSR to 1e-8 for m = 0…5.
- `mbreaks` 1.0.1 runs on the same fixtures. Pass: the sup F, sequential m and 90 %/95 %
  interval bounds match to 1e-6, or to one row for the bounds.
- This cross-check must pass before any historical inference. It is not required to freeze
  the ADR.
- R is not a project dependency and does not run in `make test` or CI. The comparison test
  reads the committed reference files.

## 10. Limitations

| # | Item |
|---|---|
| L1 | Break dates locate changes in a least-squares fit, not in an economic regime. |
| L2 | No break count is statistically established (§2.1, §5.2). |
| L3 | Asymptotic intervals rely on small-break approximations and the correct m (§7). |
| L4 | Variance breaks are allowed for but not dated. |
| L5 | Same-day timing caveats (ADR 0006 §4.5, A5, A8) apply unchanged. |
| L6 | The 2013 start and the rolling-β path were both seen before this ADR (§1.1). |
| L7 | No levels or cointegration breaks (§1). |
| L8 | 5 % trimming results are fragile by construction. |
| L9 | Month-start grid: dates are accurate to a month at best (§3.2). |
| L10 | Bootstrap validity rests on B1 and B5, which cannot be verified (§6.3). |
| L11 | **Provenance of formulas.** Verified in a primary source: the sup F statistic and its q scaling, and the table simulation design (Bai and Perron 2003b); LWZ (Liu, Wu and Zidek 1997). Reproduced from `mbreaks` code only: the sequential procedure, the Bai interval construction (non-robust branch read; HAC branch and `cvg` to be transcribed), and the BIC form. Not read: Bai (1997), Bai–Perron (1998, 2003a) (§12). The R cross-check (§9.2) is mandatory before historical inference. **Any statistic, date or interval it cannot validate is withheld from inferential claims and reported only as descriptive.** |
| L12 | Published critical-value tables are reproduced only to about 0.3 (§6.1). The values used are this ADR's own simulations on the actual grid. |

## 11. Remaining blockers to freezing

Status 2026-11-06 (third pass):

| # | Item | Status |
|---|---|---|
| 1 | Critical-value convention and the 5 % gaps (§6.1) | **Resolved.** The scale, q and indexing match. The gap is explained by grid resolution, with Monte Carlo error measured. The values used are simulated on the actual grid. |
| 2 | LWZ penalty and citation | **Resolved.** Read in the original paper (§5.2, §12). |
| 3 | Sequential procedure, Bai intervals, BIC form | **Acceptable with disclosure** (L11). Taken from `mbreaks` code; the paywalled originals were not read. Verified numerically in §9.2 before historical inference. |
| 4 | R / `mbreaks` / `strucchange` cross-check (§9.2) | **Not a freeze prerequisite.** Required before historical inference. |

## 12. References

**Verified 2026-11-06:**
- Zeileis, A., Kleiber, C., Krämer, W., and Hornik, K. (2003). Testing and dating of
  structural changes in practice. *Computational Statistics & Data Analysis* 44(1–2),
  109–123. doi:10.1016/S0167-9473(03)00030-6. **§4.1 read** (Nile results, h = 0.15, BIC,
  breakpoint observation 28 = 1898, segment means).
- Bai–Perron critical values as distributed in `mbreaks` 1.0.1 (CRAN source, MIT;
  `R/supF/cv_*.csv`, `R/Dmax/`, `R/supF_next/`; maintainers include P. Perron). Read; the
  q = 1, 2 sup F(1) entries were compared with a simulation, with the open 5 % gaps in §6.1. The journal tables themselves were not
  read; `mbreaks` attributes them to Bai and Perron.
- Bibliographic details via Crossref:
  - Andrews, D. W. K. (1993). *Econometrica* 61(4), 821–856. doi:10.2307/2951764.
  - Bai, J. (1997). *Review of Economics and Statistics* 79(4), 551–563.
    doi:10.1162/003465397557132.
  - Bai, J., and Perron, P. (1998). *Econometrica* 66(1), 47–78. doi:10.2307/2998540.
  - Bai, J., and Perron, P. (2003a). Computation and analysis of multiple structural change
    models. *Journal of Applied Econometrics* 18(1), 1–22. doi:10.1002/jae.659.
  - Bai, J., and Perron, P. (2003b). Critical values for multiple structural change tests.
    *Econometrics Journal* 6(1), 72–78. doi:10.1111/1368-423X.00102.
  - Cobb, G. W. (1978). The problem of the Nile: conditional solution to a changepoint
    problem. *Biometrika* 65(2), 243–251. doi:10.1093/biomet/65.2.243.
  - Zeileis, A., Leisch, F., Hornik, K., and Kleiber, C. (2002). strucchange. *Journal of
    Statistical Software* 7(2). doi:10.18637/jss.v007.i02.
  - Boldea, O., Cornea-Madeira, A., and Hall, A. R. (2019). *Journal of Econometrics* 213(2),
    359–397. doi:10.1016/j.jeconom.2019.05.019. Full text (arXiv 1811.04125) read
    2026-10-09 (ADR 0006 §13).

- Liu, J., Wu, S., and Zidek, J. V. (1997). On segmented multivariate regression. *Statistica
  Sinica* 7(2), 497–525. Read 2026-11-06 from the journal's own PDF
  (www3.stat.sinica.edu.tw/statistica/oldpdf/a7n213.pdf): eq. (2.3) and §3.3 constants.
  Crossref had no record; the journal page is the source.
- `mbreaks` 1.0.1 code read: `pftest` (statistic), `getcv1`/`getcv2` (indexing), `sequa`
  (sequential), `interval` (non-robust branch).

- Bai and Perron (2003b), read 2026-11-06 from
  www.columbia.edu/~jb3064/papers/2003_Critical_values_of_multiple_structural_change_tests.pdf.
  Read: §3 (eqs. 3.6–3.9 and the simulation design) and the Table 1 heading.

**Not read (paywalled):** Bai (1997); Bai and Perron (1998, 2003a); Andrews (1993) beyond
the bibliographic record. See L11.

**Not verified:**
- Elliott, G., and Müller, U. K. (2007). *Journal of Econometrics* 141(2), 1196–1218.
  Deferred, not used.

## 13. Order of operations

1. Reviewer approval of this revision and ADR 0009.
2. Close the §11 blockers.
3. Freeze ADR 0007, ADR 0009 and `research/methodology/adr0007-break-grid/` in one commit;
   push.
4. Collect policy events (ADR 0009 §10); checksum; review.
5. Implement and validate (§9) on synthetic data.
6. Historical run. Stop and report before interpreting the event comparison.
