# ADR 0008 — H1b Long-Run Levels Relationship: Confirmatory Test Not Assessable; Exploratory Plan

Date: 2026-10-23. **Status: PROPOSED (revision 5) — for independent review. Not frozen.**

Supersedes revisions 2–4 and the Wagner–Wied pilot report. Those remain as the record of how
the decision was reached.

Freezing means committing this file alone and pushing, before any historical H1b regression
or test is run (ADR 0006 §11). The exploratory plan in §9 can be revised before freezing.
After freezing, any change needs a new ADR.

## 0. Decision summary

| # | Decision (approved by the reviewer, 2026-10-23) |
|---|---|
| 1 | H1b's confirmatory claim (§2) is **NOT ASSESSABLE** with the methods evaluated. |
| 2 | H1b's α = 0.025 (ADR 0006 §8) is **unused**. It is not reallocated to H1a or any other claim. |
| 3 | The Andrews–Kim and Wagner–Wied results in §4–§5 are **methodological findings from synthetic data**. They are not empirical evidence about USD/JPY. |
| 4 | H1b continues as **explicitly exploratory** research (§9). |
| 5 | No exploratory result may be presented as confirming or rejecting the frozen hypothesis in §2. |
| 6 | The search for a confirmatory method has ended. No fourth candidate will be investigated (§6). |

Under ADR 0006 §8 the H1 family keeps its error bound. H1a was run at 0.025 and was
inconclusive. H1b spends nothing. So the family-wise false-support probability is at most
0.025, below the 0.05 budget.

## 1. Disclosure: what had been seen before this ADR

Unchanged from revision 2 §1:
- the levels scatter and README (USD/JPY near 108 in 2019-06 against near 160 in 2026-08,
  at a similar 2Y differential);
- the Plaza-era shift;
- ADF and KPSS on s and d (`01_exploration` §6);
- the H1a results;
- the CPI calendar and tax-month facts.

Added since revision 2:
- Japan CPI provenance (§8.2).
- **No historical H1b statistic has been computed.** That means no levels regression, bounds
  statistic, unit-root test on x, Andrews–Kim or Wagner–Wied statistic, or residual. Every
  model simulation in §4–§5 used synthetic data only.

## 2. The original hypothesis (as intended for confirmation)

**Confirmatory claim (Bonferroni H1 family, α = 0.025):** the long-run levels relation among

- s = 100·ln(USD/JPY), month-end;
- x = 100·ln(CPI_JP/CPI_US), by reference month;
- d = US 2Y − JGB 2Y, in percentage points;

that held over 1981-01…2021-12 (T = 492) did not hold over 2022-01…2026-07 (m = 55, with US
CPI for 2025-10 missing).

It was planned in two steps:
1. **Validity gate.** Establish a pre-period levels relation with an ARDL/PSS bounds test
   (Case III, k = 2), after ruling out I(2) variables.
2. **Confirmatory test.** Test for its breakdown with a single end-of-sample stability test
   at 0.025.

The claim was about the **joint** relation. Reading it as "decoupling from the differential"
needed γ > 0 as a wording qualifier (revision 2 §7.2, §9).

**What "supported" would have meant:** the joint relation broke down in the window, through
a coefficient shift, a loss of cointegration or a change in the residual distribution. It
would not have dated the break or attributed it to d.

## 3. Requirement every confirmatory candidate had to meet

A candidate test was eligible only if it met all of the following, as fixed in revisions 2–3:
1. Its theory covers this data design. That means one stochastic-trend regressor x, which
   drifts; and d, whose integration order is uncertain and which may be stationary.
2. Its null rejection rate at nominal 0.025, simulated for the **full procedure** at
   T = 492, m = 55 with the gap, stays within Bradley's liberal bound of 0.0375. The decision
   uses Clopper–Pearson bounds, so Monte Carlo noise alone neither passes nor fails a cell.
3. Its tuning is fixed in advance and is not chosen from the H1b outcome.
4. Its source is verifiable: the published equations and critical values have been read and
   reproduced.

Tolerances were diagnostic only (reviewer decision after revision 3). A failure ends the
candidate. It is never rescued by retuning.

## 4. Why Andrews–Kim (2006) was rejected

**Verified.** The P test was transcribed from JBES 24(4), eqs. (3)–(15) (revision 2 §8.1).
The implementation reproduces AK Table 1 (T = 250, m = 10, nominal 5 %, eight models, 5,000
replications each):

| ρ | Ours | AK |
|---|---|---|
| 0 | .0554 | .057 |
| .4 | .0515 | .051 |
| .8 | .0497 | .048 |

All three are within 2 MC standard errors.

**Finite-sample failure at this design.** At nominal 0.025, with T = 492, m = 55 and 4,000
replications, null rejection was **.047–.107** in every cell, across ρ_u ∈ {0, .8, .95, .98,
.99}, normal and GARCH innovations, with and without the gap. The variance-break cell at
ρ = .95 was the only one below .05 (.029).

- An oracle version using the true β distorted just as much (.065).
- So the cause is the subsampling quantile, not estimation of β.
- 438 overlapping window sums carry only about T/m ≈ 9 independent pieces of information.
- AK's fixed-m asymptotics (Theorem 1) fail at m/T = 0.11. Their own evidence stops at
  m ≤ 10, m/T ≤ 0.1 and ρ ≤ .8.

**Structural infeasibility, not just distortion.** The smallest attainable p-value is
1/438. Its null probability P(P > every P_j) was **.035–.087** in every cell. So no AK critical
value, nominal or size-corrected, can deliver a 2.5 % test here. The R statistic uses the
same quantile and inherits the same limit.

**Joint procedure.** The ARDL gate followed by AK P gave false "supported" rates of
1.7–2.9 × 0.025 wherever the gate had power (ρ_u ≤ .95). It was within budget only where H1b
was almost never assessable (ρ_u ≥ .98).

The reviewer withdrew approval of AK after revision 3.

## 5. Why Wagner–Wied (2017) was rejected

### 5.1 Source verification

- **The published and working-paper detectors differ.** Published eq. (12) (JTSA 38(6),
  author PDF) has no calibration-period subtraction. The working paper (SFB 823 DP 23/2014,
  eq. 37) and the authors' `cointmonitoR` 0.1.0 code subtract the calibration term and take
  `abs`.
- **Only the subtracting form reproduces the critical values** (k = 2, 97.5 %):

  | Detector | m = 0.5 | m = 0.9 | IM-OLS |
  |---|---|---|---|
  | Package / DP | 6.99 | 0.317 | 15.62 |
  | Own simulation, subtracting form | 7.12 | 0.311 | 15.60 |
  | Own simulation, published eq. (12) form | — | 0.033 | — |

- The published critical-value appendix (Supplementary Appendix C) was not available. So
  the discrepancy is unresolved and was documented, not adjudicated.
- At m = 492/547 the interpolated critical value is 0.3174.
- **Correction to revision 4:** the values cited there as "Table 10" (15.62 / 0.10) are from
  Table 11 (IM-OLS).

### 5.2 Theoretical applicability (decisive regardless of the simulations)

- **Eq. (2): X_t = X_{t−1} + v_t, with Ω_vv > 0 (Assumption 2).** Every regressor must be a
  driftless I(1) process with a non-singular long-run covariance. This has two consequences:
  - **A stationary d violates the assumption.** Whether d is I(0) or I(1) over 1981–2021 is
    not settled, and the confirmatory test was to be fixed before looking.
  - **The drifting x is outside the theory.** x fell 88.7 log-points over 1981–2021.
- These are applicability failures. Simulation shows how bad the consequences are. It cannot
  restore the theory's coverage.

### 5.3 Finite-sample pilot (synthetic data, R = 2,000 per cell, 95 % CP intervals)

**Validation:**
- The detector matches a direct loop to 4e-17.
- D-OLS matches statsmodels to 2.5e-15.
- FM-OLS t-size tends to .05 as T grows (.111 → .077 → .050).
- The Andrews AR(1) bandwidth matches `cointReg`. Removing my ρ cap changed sizes only within
  MC noise.

**Null rejection at nominal .025:**

| Estimator / bandwidth | d I(1) | d I(0) | x drifting |
|---|---|---|---|
| FM-OLS, Andrews | .018–.028 (pass/ambiguous) | .043–.077 (**fail** 7 of 8 cells, 1 ambiguous) | ≈ 0 |
| FM-OLS, fixed NW | .14–.94 | | |
| FM-OLS, large fixed | .03–.55 | | |
| D-OLS | up to .35 (.15–.35 at ρ ≥ .95) | | |

Size depends decisively on the bandwidth rule, which is a tuning choice that the theory does
not pin down. The gap made no difference (identical to three decimals).

**Power.** FM-OLS with the Andrews bandwidth, size-corrected, at ρ_u = .95–.98:

| Alternative | Power |
|---|---|
| 1–2 σ_u level shift, slope shift, random-walk loss of cointegration, variance × 2 | .02–.08 |
| 4 σ_u shift | .38–.45 |
| 6 σ_u shift | .75–.88 |

At ρ_u = .8, a 4 σ_u shift gives .92. **Where size was controlled, there was essentially no
power against the alternatives H1b was about.**

**Verdict: NO-GO** (reviewer approved, 2026-10-23).

## 6. Why the search for a confirmatory method ends here

- Revision 4 screened all candidates. WW was the only one that was verifiable:
  - Kejriwal–Perron (2010) and Chang–Park–Song-type sieve bootstraps were ineligible, because
    their exact procedures and critical values were not verified;
  - nothing else met §3.
- The binding constraints come from the **design**, not from any one test:
  - an end-of-sample window of m = 55 against T = 492, with highly persistent equilibrium
    errors (plausible ρ_u ≈ .95–.99), leaves about 9 effective pre-period windows;
  - d's integration order is uncertain;
  - x has a drift;
  - the 0.025 budget is small.
- Under these constraints, the two well-founded methods either cannot attain the level (AK)
  or attain it only where they have no power (WW).
- Searching further until some method "works" would be a specification search over tests,
  which the project's principles rule out (CLAUDE.md principle 8; standing instruction "do
  not introduce additional methods simply to rescue a desired conclusion").

## 7. Methodological infeasibility ≠ empirical rejection

| Statement | Correct? |
|---|---|
| "H1b is not assessable with the evaluated confirmatory methods" | **Yes** |
| "The relation did not break down in 2022" / "no evidence of decoupling" | **No.** No test was run on real data. |
| "The relation broke down" / "evidence of decoupling" | **No.** No confirmatory test exists. |
| "AK/WW show the USD/JPY relation is too persistent to test" | **No.** The persistence values were simulation design points, not estimates. Whether the actual residuals are that persistent is an exploratory question (§9). |
| "H1 is unsupported" | **No.** H1a was inconclusive and H1b was not assessed. H1 has no confirmatory support either way. |

Exploratory findings (§9) may describe, estimate and quantify uncertainty. They carry no
error-rate guarantee for the §2 claim, and must be labelled **exploratory (ADR 0008 §9)** in
every table, figure and summary.

## 8. Retained facts

### 8.1 Data design (unchanged from revision 2 §3)

- Samples: pre-period 1981-01…2021-12 (T = 492); window 2022-01…2026-07 (m = 55).
- The window ends at 2026-07 because the frozen Japan CPI ends there.
- US CPI 2025-10 is missing (BLS shutdown). Matched-gap handling; no imputation in the primary.
- Checksums: `raw/jp_cpi.csv` `a40f9238981868e66ca40498ff7ee2d54b3e2d2a226d6d8bc1ed30034c3fe1d0`;
  `raw/us_cpi.csv` `f8ecddf53a9a9a74dda92c2c4204e6039466fcb744bc74171b73b5f6aac48119`
  (re-verified 2026-10-23). Plus the ADR 0006 §9.2 files.
- Japan CPI has strong calendar and consumption-tax effects (revision 2 §1, §4). The tax
  adjustment (R9) and seasonal handling are carried into §9.

### 8.2 Japan CPI file: counts and provenance (read-only, 2026-10-23; resolves A9)

**File facts:**
- **960 data rows, 1946-08…2026-07.** That is exactly the 960 calendar months in the span.
- Missingness: no missing months, no duplicate months, no empty or non-numeric values.
- Metadata: FREQ = M, REF_AREA = JP, UNIT_MEASURE = 628 (index), OBS_STATUS = A and
  OBS_CONF = F on every row; BREAKS is empty.
- Rows by span:
  - 1970-01…2026-07: 679;
  - 1981-01…2026-07: 547;
  - 1981-01…2021-12: 492.

**Correction.** The pilot report's "559 months" for 1970-01…2026-07 was an arithmetic error;
the correct figure is 679. The provenance check itself was run on all rows, and its result
is unchanged.

**Provenance.** For all 679 rows from 1970-01 to 2026-07:
- each value equals c × L_t, where L_t is an index on a one-decimal 2025 = 100 grid and
  c = 1.18052;
- the largest deviation is 4.2e-7, i.e. exact to the file's stored precision;
- examples: L(1981-01) = 67.4, L(2024-12) = 98.9, L(2025-01) = 99.3, L(2026-07) = 102.0;
- 2025 mean = 100.008;
- the 2025 annual change is 3.19 %, against the official 3.2 % (2020-base yearly result).

Before 1970 the values are **not** on that grid (maximum deviation .0499, i.e. uniform
rounding noise). That is irrelevant to H1b, which starts in 1981.

**Conclusion:** the series used by H1b is a single consistently linked official 2025-base
index, with no in-window splice. **A9 is resolved.**

**Limitation:** no official month-by-month table was obtained (e-Stat needs an API key or
renders client-side). Pre-2025 values are rounded to 0.1 index points, a level error of at
most about 0.07 %.

### 8.3 Verified critical values kept for exploratory use

- PSS Case III, k = 2, 2.5 %: F 4.41 / 5.52 and t −3.13 / −3.80 (Tables CI(iii), CII(iii)).
- Full-procedure (BG-filtered AIC) simulated 97.5 % quantiles: F 5.49–6.04 and t −3.80 to
  −3.95.

## 9. Exploratory H1b plan

**Rules for every step:**
- **Label.** Everything is exploratory and secondary. Nothing is gated at 0.025 or presented
  as a test of §2.
- **Data.** Frozen vintage only. Steps that need new series (§9.5) are marked and need a
  separate data ADR.
- **Uncertainty.** Every estimate carries an interval. Use HAC/Newey–West with an
  Andrews-selected bandwidth, or simulation and bootstrap where stated. Nominal p-values are
  reported as descriptive, with their simulated null rates where §4–§5 give them.
- **No fundamental value by default.** A "fundamental" or "fair value" level is reported
  **only** if §9.3 finds a defensible relation. Otherwise the output is "no defensible
  long-run anchor at this sample", and residual-based gap measures are not computed.
- **Order.** Steps 1–3 use the pre-period only. Window data enter at step 4.

### 9.1 Nominal vs real USD/JPY (descriptive)

Series:
- s;
- the CPI-based real rate q = s − x (rising q = real yen depreciation);
- d;
- the real-differential proxy r = d − (12-month π_US − π_JP), using backward-looking
  inflation (disclosed as a proxy; no expectations data in the vintage);
- tax-adjusted x (R9 definition).

Outputs:
- levels plots with the 2022-01 marker;
- q's distribution in the pre-period against the window;
- rolling 60-month mean and sd of q.

Question: is the post-2022 move in s mostly a move in q, i.e. not explained by relative
prices? This is arithmetic, with no model.

### 9.2 Integration diagnostics (pre-period; descriptive classification)

Series s, q, x (raw and tax-adjusted), d and r, in levels and first differences:
- ADF with AIC lags up to 12, and KPSS. Δx gets centred seasonal and tax dummies.
- The largest AR root of Δx (near-I(2) check).
- Each series is classified I(0), I(1) or **ambiguous** (ADF and KPSS disagree). There is no
  pre-test chain: the classification informs which estimators are meaningful, not a gate.
- The known low power of these tests at ρ near 1 is stated with the results.
- Sensitivity: the 1990-01 start; full sample through 2026-07 (labelled as including window
  data).

### 9.3 Can a meaningful long-run relation be estimated? (pre-period)

**Estimators, side by side:**
1. ARDL/UECM (Case III, BG-filtered AIC, max lag 12), with bounds F and t. Each statistic is
   reported against both the PSS asymptotic bounds and the full-procedure simulated
   quantiles (§8.3).
2. FM-OLS (Andrews bandwidth) for θ and γ.
3. D-OLS (leads and lags by BIC) for θ and γ.

All with HAC intervals.

**Specifications:**
- (a) s on x and d;
- (b) PPP imposed: q on d;
- (c) the 10Y differential (from 1986-07);
- (d) tax-adjusted x.

**Defensibility criteria, fixed before estimation.** A relation is "defensible" only if all
of these hold:
1. **Mean reversion.** Bounds F and t both exceed the I(1) bound at 5 % by the simulated
   quantiles. In addition, the bootstrap 90 % interval for the half-life of the ARDL impulse
   response is finite and below 10 years.
2. **Economic coherence.** The 95 % HAC interval for θ includes 1 or lies in (0, 2), and γ̂
   has the same sign under all three estimators.
3. **Estimator agreement.** The θ and γ point estimates agree across ARDL, FM-OLS and D-OLS
   to within their HAC intervals.
4. **Stability.** Recursive and rolling (120-month) estimates of θ and γ stay inside the
   full pre-period 95 % interval for most of 1990–2021. This is judged by plot, and stated
   as a judgment.

**Outcomes:**
- All four hold: proceed to §9.4 with that specification.
- Only (b), PPP with d, holds: proceed with (b) only.
- Nothing holds: report that, skip the gap measures in §9.4, and take only the descriptive
  q and d analysis into §9.5.

The criteria are a quality bar for exploratory interpretation. They are not a test.

### 9.4 Pre-2022 fit and post-2022 deviations (only for a defensible relation)

- **In-sample residuals.** Path, ACF, AR(1) ρ̂_u with a bias-corrected interval, and
  historical extremes: Plaza 1985, 1998, 2007, 2011.
- **Out-of-sample path.** Use the pre-period coefficients and the window x and d. The
  2025-10 row is shown as missing; nothing is imputed.
- **Uncertainty bands combine two parts:**
  - parameter uncertainty, by a moving-block bootstrap over the pre-period with block length
    24, re-estimating the coefficients;
  - residual uncertainty, from the pre-period residual distribution at the same horizon.
  - Bands are 80 % and 95 %.
- **Deviation scale.** The window gap in σ_u units, and its percentile against all 55-month
  pre-period windows. The percentile is descriptive: §4 shows such ranks are not valid
  p-values here.
- **Decomposition.** Split the window gap into the parts from movements in x, d and the
  residual.
- **AK P and R** may be shown with their simulated null rates from §4 (.047–.107 at
  nominal .025), labelled as not a test.

### 9.5 Regimes and omitted fundamentals (descriptive)

**Policy-regime context, using frozen data only.** Residual or q means and sds by
pre-registered policy eras:

| Era | Months |
|---|---|
| Pre-QQE | to 2013-03 |
| QQE | 2013-04 to 2016-08 |
| YCC | 2016-09 to 2022-11 |
| YCC band widening to NIRP exit | 2022-12 to 2024-02 |
| Post-NIRP | 2024-03 onward |

Fed hiking starts 2022-03. Era boundaries are documented dates, not estimated breaks. **No
break-date estimation**: formal structural-break work belongs to the separate
structural-break milestone and ADR.

**Omitted fundamentals. Each needs new data and a data ADR first; none is run now.**
- Terms of trade or energy import prices.
- Net international investment position or current account.
- Survey-based inflation expectations (to replace the r proxy).
- BoJ and Fed balance sheets.

Each is to be added **one at a time** to the defensible specification. Report:
- the change in the pre-period fit;
- the stability of θ and γ;
- the change in the window gap.

Every candidate tried is listed, including the ones that do nothing, so the results are not
a forking-paths search.

**Interpretation limits.** Results are association language only. A smaller gap after adding
a variable means "statistically associated with", not "explains" or "caused".

### 9.6 Deliverables and checks

- One notebook, `notebooks/03_h1b_exploratory.ipynb`. Small helpers go into the existing
  `src/kagura/models.py`. A new module is added only if steps 9.3–9.4 need more than a few
  functions.
- One `pytest` check per new non-trivial helper, on synthetic data. For example, the half-life
  bootstrap on a known AR(1), and the decomposition summing to the total gap.
- The ADR 0006 checksum guard is extended with the two CPI checksums.
- `make` target `h1b-explore`.
- Figures go in `reports/figures/h1b_*.png`.

## 10. Remaining assumptions and limitations

| # | Item |
|---|---|
| A1 | Simulated critical values (§8.3) assume the simulated DGP class. They are used only descriptively. |
| A3 | Long-run forcing of x and d, needed for the PSS conditional model. Checked descriptively through ECM loadings. |
| A4 | Pre-period stability 1981–2021 is doubtful (Plaza era). §9.3 criterion 4 and the 1990-01 sensitivity address it descriptively. |
| A5 | Any change may predate 2022 (rolling H1a β fell before 2022). The 2022-01 marker is a reference date, not an assumed break. |
| A8 | 2023 energy subsidies distort window x; not adjusted. |
| A9 | **Resolved** (§8.2). |
| A10 | US rent/OER understatement 2025-11…2026-03. Sensitivity: window ending 2025-09. |
| A11 | Current-vintage CPI, not real-time. |
| New | The real-differential proxy uses realised, not expected, inflation. |
| New | WW published-vs-DP discrepancy unresolved (Supplementary Appendix C unseen). Irrelevant after NO-GO, recorded for the literature. |

## 11. Order of operations

1. Reviewer approves this revision. Freeze by committing this file alone and pushing; the
   revision-2 copy is kept or removed as the reviewer decides.
2. Implement the §9.6 helpers and tests on synthetic data.
3. Run §9.1 → §9.2 → §9.3. **Stop and report** the §9.3 outcome before running §9.4.
4. Run §9.4 and the frozen-data part of §9.5. Report.
5. Omitted-fundamentals work comes later, under its own data ADR.

## 12. References

**Verified in sessions on 2026-10-23:**
- Andrews, D. W. K., and Kim, J.-Y. (2006). Tests for cointegration breakdown over a short
  time period. *JBES* 24(4), 379–394. DOI 10.1198/073500106000000297. Read in full.
- Pesaran, M. H., Shin, Y., and Smith, R. J. (2001). Bounds testing approaches to the
  analysis of level relationships. *JAE* 16(3), 289–326. Tables CI(iii) and CII(iii).
- Wagner, M., and Wied, D. (2017). Consistent monitoring of cointegrating relationships: The
  US housing market and the subprime crisis. *JTSA* 38(6), 960–980. Author PDF:
  https://wisostat.uni-koeln.de/sites/statistik/Dominik_Wied/Wagner_Wied_2017_JTSA.pdf
- Wagner, M., and Wied, D. (2014). SFB 823 Discussion Paper 23/2014.
  https://doi.org/10.17877/DE290R-14599
- R packages `cointmonitoR` 0.1.0 and `cointReg` (CRAN source, read but not run).
- Statistics Bureau of Japan: 2025-base revision
  (https://www.stat.go.jp/english/data/cpi/2025plan.html); 2025 yearly average
  (https://www.stat.go.jp/english/data/cpi/158c.html).
- BLS, 2025 federal government shutdown CPI FAQ. BIS long CPI series documentation.
- statsmodels 0.15.0 `tsa/ardl` source.

**Cited, not re-read:**
- Bradley (1978), *Br. J. Math. Stat. Psychol.* — to verify before freezing.
- Kejriwal and Perron (2010).
- Pesaran and Shin (1999).
- Phillips and Hansen (1990).
- Stock and Watson (1993).
- Andrews (1991).
- Dornbusch (1976).
- Frankel (1979).

**Session artifacts (scratchpad, not in the repo):**
- revision 3;
- the revision-4 decision report;
- the WW pilot report;
- `sim/` and `sim2/` scripts and outputs.

Committing the pilot code for reproducibility is an open decision (§13).

## 13. Open decisions for the reviewer

- **E1.** The §9.3 defensibility criteria and thresholds: 5 % using simulated quantiles; a
  half-life below 10 years; θ in (0, 2).
- **E2.** The policy-era dates in §9.5.
- **E3.** Whether to commit the synthetic AK and WW pilot code (for example as
  `research/sim/`) alongside the frozen ADR, so §4–§5 are reproducible from the repo.
- **E4.** Whether to keep or delete the untracked `0008-…PROPOSED-r2.md` in
  `docs/decisions/`.
