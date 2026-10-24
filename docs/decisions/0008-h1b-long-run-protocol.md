# ADR 0008 — H1b Long-Run Levels Relationship: Confirmatory Claim Not Assessable; Exploratory Plan

Date: 2026-10-23.

**Status: FROZEN 2026-10-24 (revision 5 final: reviewer decisions E1–E4 plus the §9.3
I(2) correction).**

- **Freezing** means committing this file and its two companion folders (§12), then
  pushing. This must happen before any historical H1b regression or test is run, as for
  ADR 0006 (§11).
- **After freezing,** any change needs a new ADR.
- **History.** Superseded drafts (revisions 2–4, the Wagner–Wied pilot report and the first
  revision-5 draft) are in `docs/decisions/superseded/0008/`. They are history, not
  authority.

## 0. Decision summary

Approved by the reviewer on 2026-10-23:

| # | Decision |
|---|---|
| 1 | H1b's confirmatory claim (§2) is **NOT ASSESSABLE** with the methods evaluated. |
| 2 | H1b's α = 0.025 (ADR 0006 §8) is **unused**. It is not reallocated to H1a or to anything else. |
| 3 | The Andrews–Kim and Wagner–Wied results (§4–§5) are **methodological findings from synthetic data**. They are not empirical evidence about USD/JPY. |
| 4 | H1b continues as **explicitly exploratory** research (§9). |
| 5 | No exploratory result may be presented as confirming or rejecting the claim in §2. |
| 6 | The search for a confirmatory method has ended. No further candidate will be investigated (§6). |

H1 family error. H1a was run at 0.025 and was inconclusive. H1b spends nothing. The
family-wise false-support probability for H1 is therefore at most 0.025, within the 0.05
budget of ADR 0006 §8.

## 1. Disclosure: what had been seen before this ADR

| Seen | Source | Bearing on H1b |
|---|---|---|
| Month-end USD/JPY ≈ 108 (2019-06) vs ≈ 160 (2026-08), at a similar 2Y differential | README, levels scatter | Anticipates a post-2022 gap |
| The 1980s levels cloud shifts around the Plaza Accord | Levels scatter | Pre-period stability is doubtful (A4) |
| ADF/KPSS on s and d, in levels and changes | `01_exploration` §6 | Integration order of s and d partly known |
| H1a: β 6.44 → 4.05 (inconclusive); rolling β declined before 2022 | `02_h1a_formal` | Any change may predate 2022-01 (A5) |
| CPI-only facts (revision 2): calendar-month effects in Japanese CPI; tax months 1989-04, 1997-04, 2014-04 and 2019-10; x fell 88.7 log-points over 1981–2021 | Review session | Seasonal and tax handling (§9.2) |
| Japan CPI file structure and provenance (§8.2) | Read-only check | Resolves A9 |

**Not computed on historical data:**
- no levels regression;
- no bounds, ARDL, FM-OLS or D-OLS statistic;
- no unit-root test on x;
- no Andrews–Kim or Wagner–Wied statistic;
- no residual.

Every model simulation in §4–§5 used synthetic data only.

## 2. The original hypothesis

**Intended confirmatory claim** (Bonferroni H1 family, α = 0.025). The long-run levels
relation among the three series below held over 1981-01…2021-12 (T = 492). It did not hold
over 2022-01…2026-07 (m = 55; the US CPI for 2025-10 is missing).

| Symbol | Definition |
|---|---|
| s | 100·ln(USD/JPY), month-end |
| x | 100·ln(CPI_JP/CPI_US), by reference month |
| d | US 2Y − JGB 2Y, percentage points |

**Planned procedure:**
1. A validity gate: an ARDL/PSS bounds test for a pre-period levels relation (Case III,
   k = 2), after ruling out I(2) variables.
2. A single end-of-sample breakdown test at 0.025.

**Scope of the claim.** It concerned the **joint** relation. Reading it as "decoupling from
the differential" required γ > 0 as a wording qualifier. A "supported" outcome would have
meant a breakdown through any of:
- a coefficient shift;
- a loss of cointegration;
- a change in the residual distribution.

It would not have dated the change or attributed it to d.

## 3. Eligibility requirements for a confirmatory method

Fixed in revisions 2–3. A candidate had to meet all four:

1. **Theory.** Its theory covers this design:
   - a drifting stochastic-trend regressor x;
   - d of uncertain integration order, possibly stationary.
2. **Size.** Its simulated **full-procedure** null rejection rate at nominal 0.025, at
   T = 492 and m = 55 with the gap, is acceptably close to 0.025.
3. **Tuning.** All tuning is fixed in advance, never chosen from the H1b outcome.
4. **Verifiability.** Its published equations and critical values were read and reproduced.

**Tolerance.** Requirement 2 was screened against 1.5α = 0.0375, using Clopper–Pearson bounds
so that Monte Carlo noise alone neither passes nor fails a cell.
- This tolerance is a **project convention, used diagnostically.**
- It is commonly attributed to Bradley (1978). That attribution is **not** relied on as
  support (§12).
- **Neither rejection depended on it:**
  - Andrews–Kim fails because 2.5 % is unattainable at any critical value (§4).
  - Wagner–Wied fails on theoretical applicability and lack of power (§5). Its size results
    are corroborating, not decisive.

## 4. Why Andrews–Kim (2006) was rejected

**Verified.**
- The P test was transcribed from *JBES* 24(4), eqs. (3)–(15).
- The implementation reproduces AK Table 1 (T = 250, m = 10, nominal 5 %, eight models,
  5,000 replications each). All differences are under 2 MC s.e.:

  | ρ | Ours | AK |
  |---|---|---|
  | 0 | .0554 | .057 |
  | .4 | .0515 | .051 |
  | .8 | .0497 | .048 |

- The fast implementation equals a direct loop to 1e-14.

**Finite-sample failure.** At nominal 0.025, with T = 492, m = 55 and 4,000 replications:
- Null rejection was **.047–.107** in every main cell (ρ_u ∈ {0, .8, .95, .98, .99};
  normal and GARCH; with and without the gap).
- The only cell below .047 was the deliberate pre-period variance-break violation, at .029.
- An oracle using the true β distorts just as much (.065 at m = 55, ρ = 0).

The cause is the subsampling quantile: 438 overlapping window sums carry only about
T/m ≈ 9 independent pieces of information. AK's fixed-m theory (Theorem 1) and their
evidence (m ≤ 10, ρ ≤ .8) do not cover m/T = 0.11.

**Structural infeasibility.**
- The smallest attainable p-value is 1/438.
- P(p ≤ 1/438) under the null was **.035–.087** in every cell.
- So no critical value, nominal or size-corrected, gives a 2.5 % test.
- The R statistic shares the same limitation.

**Joint gate + AK procedure.**
- Where the gate had power (ρ_u ≤ .95), false "supported" rates were 1.7–2.9 × 0.025.
- It stayed within budget only where H1b was almost never assessable.

## 5. Why Wagner–Wied (2017) was rejected

### 5.1 Source verification

- **Two detector forms.** Published eq. (12) has no calibration-period subtraction. The
  2014 working paper (eq. 37) and the authors' `cointmonitoR` 0.1.0 subtract it and take
  `abs`.
- **Only the subtracting form reproduces the critical values** (k = 2, 97.5 %):

  | Form | m = 0.5 | m = 0.9 | IM-OLS m = 0.5 |
  |---|---|---|---|
  | Package / working paper | 6.99 | 0.317 | 15.62 |
  | Own simulation, subtracting form | 7.12 | 0.311 | 15.60 |
  | Own simulation, published eq. (12) | 7.14 | 0.033 | 15.60 |

- **Unresolved.** The published Supplementary Appendix C was unavailable, so the discrepancy
  is documented, not adjudicated.
- The interpolated critical value at m = 492/547 is 0.3174.
- **Correction:** revision 4's "Table 10" values are from Table 11 (IM-OLS).

### 5.2 Theoretical applicability (decisive regardless of simulation)

Eq. (2), X_t = X_{t−1} + v_t with Ω_vv > 0 (Assumption 2), makes every regressor a
**driftless** random walk with a non-singular long-run covariance.

- A **stationary d** violates this. Whether d is I(0) or I(1) was to stay unexamined before
  the freeze.
- A **drifting x** is outside the theory.

Simulation measures the consequences of these violations. It cannot restore coverage.

### 5.3 Finite-sample pilot

Synthetic data, R = 2,000 null and 1,000 power replications per cell, 95 % CP intervals.

**Validation:**
- The detector matches a direct loop to 4e-17.
- D-OLS matches statsmodels to 2.5e-15.
- The FM-OLS t-size tends to .05 as T grows (.111 → .077 → .050).
- The Andrews bandwidth matches `cointReg`. Removing a ρ cap changed sizes only within MC
  noise.

**Null rejection at nominal .025:**

| Variant | d I(1) | d I(0) | x drifting |
|---|---|---|---|
| FM-OLS, Andrews bandwidth | .018–.028 | .043–.077 | ≈ 0 |
| FM-OLS, fixed NW bandwidth | .02–.90 | .04–.94 | — |
| FM-OLS, large fixed bandwidth | .01–.38 | .03–.55 | — |
| D-OLS | .02–.23 | .04–.35 | — |

- With the Andrews bandwidth and d I(0), 7 of 8 cells exceed the screen and 1 is ambiguous.
- Size depends decisively on the bandwidth rule, which the theory does not pin down.
- The missing month had no effect.

**Power.** FM-OLS, Andrews bandwidth, size-corrected:

| Alternative | ρ_u | Power |
|---|---|---|
| 1–2 σ_u level shift, slope shift, random-walk loss of cointegration, variance × 2 | .95–.98 | .02–.08 |
| 4 σ_u shift | .95–.98 | .38–.45 |
| 6 σ_u shift | .95–.98 | .75–.88 |
| 4 σ_u shift | .8 | .92 |

**Verdict: NO-GO.**

## 6. Why the search for a confirmatory method ends here

**Candidates.** Revision 4 screened them, and only WW was verifiable:
- Kejriwal–Perron (2010) and sieve-bootstrap procedures were not verifiable to §3(4).
- Nothing else met §3.

**The binding constraints come from the design:**
- a 55-month end window against 492 months;
- plausibly very persistent equilibrium errors;
- an uncertain integration order for d;
- a drifting x;
- a 0.025 budget.

Further searching would amount to a specification search over tests. The project rules
exclude that (CLAUDE.md principle 8; the standing instruction not to add methods to rescue
a desired conclusion).

## 7. Methodological infeasibility ≠ empirical rejection

| Statement | Allowed? |
|---|---|
| "H1b's confirmatory claim is not assessable with the evaluated methods" | **Yes** |
| "The relation did not break down" / "no evidence of decoupling" | **No.** No test was run on real data. |
| "The relation broke down" / "evidence of decoupling" | **No.** No confirmatory test exists. |
| "The simulations show USD/JPY residuals are too persistent to test" | **No.** The persistence values were design points, not estimates. |
| "H1 is unsupported" or "H1 is rejected" | **No.** H1a was inconclusive and H1b was not assessed, so H1 has no confirmatory result either way. |

### 7.1 Exploratory significance levels do not inherit α

The unused 0.025 is **not** carried into the exploratory work, in whole or in part.

- **No family-wise meaning.** The 5 % reference level in §9.4 is a conventional descriptive
  benchmark. It has no family-wise or confirmatory interpretation and gives no error-rate
  guarantee for any claim about §2.
- **No confirmatory language.** Exploratory p-values are reported as numbers, never as
  "significant evidence for H1/H1b".
- **No accumulation.** Nothing exploratory can be "promoted" to confirmatory by meeting a
  stricter level. A future confirmatory claim needs a new hypothesis, a new ADR frozen
  before data contact, and a new error budget; ADR 0006 §8's H1 family is closed.

### 7.2 Model-implied benchmark ≠ fundamental fair value

**Allowed terms.** If §9.4 classifies a relation as credible or fragile, its fitted long-run
combination ŝ*_t = ĉ + θ̂x_t + γ̂d_t is a **model-implied benchmark**, and s_t − ŝ*_t is the
**deviation from the model-implied benchmark**. Both are conditional on the following
(and the conditioning must be stated alongside any value):
- the specification;
- the estimator;
- the 1981–2021 estimation sample;
- the frozen vintage.

**Banned terms, in any table, figure, caption or summary:**
- "fair value";
- "fundamental value", "equilibrium exchange rate";
- "over-" or "undervalued", "misalignment".

**Why.** These terms imply that the model has identified a structural equilibrium. A
two-variable reduced-form relation estimated on one sample cannot establish that.

**If the classification is "not defensible",** no benchmark is computed at all.

## 8. Retained facts

### 8.1 Data design

- Pre-period 1981-01…2021-12 (T = 492). Window 2022-01…2026-07 (m = 55).
- The window ends where the frozen Japan CPI ends.
- US CPI 2025-10 is missing (BLS shutdown). It is handled as a matched gap and is not imputed
  in any primary display.
- 2022-01 is a reference marker, not an assumed break.

### 8.2 CPI files: counts, missingness and provenance

Read-only check, 2026-10-23.

| | `raw/jp_cpi.csv` (BIS) | `raw/us_cpi.csv` (FRED CPIAUCSL) |
|---|---|---|
| Data rows | **960** | 956 |
| Span | 1946-08…2026-07 (960 months) | 1947-01…2026-08 (956 months) |
| Missing months / duplicates | 0 / 0 | 0 / 0 |
| Non-numeric values | 0 | **1 (2025-10)** |
| Usable rows 1981-01…2021-12 | 492 | 492 |
| Usable rows 2022-01…2026-07 | 55 | 54 |
| Other | FREQ M, REF_AREA JP, UNIT 628, OBS_STATUS A and OBS_CONF F on all rows; BREAKS empty | — |

**Correction.** The pilot report's "559 months" for 1970-01…2026-07 was an arithmetic error.
The correct figure is **679**. The provenance check covered all 679.

**Japan CPI provenance.**
- From 1970-01 to 2026-07, every value equals c·L_t, with c = 1.18052 and L_t on a
  one-decimal 2025 = 100 grid. The maximum deviation is 4.2e-7, i.e. exact at stored
  precision.
- Examples: L(1981-01) = 67.4, L(2024-12) = 98.9, L(2025-01) = 99.3, L(2026-07) = 102.0.
- The 2025 mean of L is 100.008.
- The 2025 annual change is 3.19 %, against the official 3.2 %.
- Values before 1970 are off the grid. That doesn't matter for H1b, which starts in 1981.
- **A9 is resolved:** one consistently linked official 2025-base index, with no in-window
  splice.
- **Limitation:** no official month-by-month table was obtained. Pre-2025 rounding is at
  most about 0.07 % in levels.

**Checksum inventory** (SHA-256, all re-verified 2026-10-23 against the files in `data/`):

| File | SHA-256 | In `vintage.FROZEN_SHA256` |
|---|---|---|
| processed/daily.csv | `edfc95cf676d3647b6af3667b3b34fc74b4b6e692d750bf6ab8008de9105cd99` | yes |
| processed/monthly.csv | `3f19c005d8db1ab1963488b2af748dcb6f956fe3a6a6cf6f4acdafda92a56215` | yes |
| raw/manifest.json | `c0f5676e888751690cf8a5ad86df63c8727b5a02f63302b33fb535e315bee51c` | yes |
| raw/usdjpy.csv | `0ea1de1993e69827ccfdddc390af8f8f5abf15c566f4c4cd5a6072495b773965` | yes |
| raw/us_2y.csv | `1289774410381729569844068b657a7cc11a56a699669509bf6ed26a0db572a4` | yes |
| raw/us_10y.csv | `94c1e5b98460d7de645be32f3211853c3d749724ecb12cac33bc84623ea759b4` | yes |
| raw/jgb.csv | `997a8f95dc20c884d506c627ac075b1e93a357410094058ac19f3effead2e353` | yes |
| raw/jgb_current.csv | `8da8cc83668bf280f1849ce2e6fab752881fc771b87d4691887bdb85e2f9f519` | yes |
| raw/jp_cpi.csv | `a40f9238981868e66ca40498ff7ee2d54b3e2d2a226d6d8bc1ed30034c3fe1d0` | **no — added in Stage 1 (§9.7)** |
| raw/us_cpi.csv | `f8ecddf53a9a9a74dda92c2c4204e6039466fcb744bc74171b73b5f6aac48119` | **no — added in Stage 1 (§9.7)** |

### 8.3 Verified critical values

PSS (2001) Case III, transcribed from Tables CI(iii) and CII(iii):

| k | Level | F I(0) / I(1) | t I(0) / I(1) |
|---|---|---|---|
| 2 (s on x, d) | 5 % | 3.79 / 4.85 | −2.86 / −3.53 |
| 2 | 2.5 % | 4.41 / 5.52 | −3.13 / −3.80 |
| 1 (q on d) | 5 % | 4.94 / 5.73 | −2.86 / −3.22 |

**Full-procedure 97.5 % quantiles** (BG-filtered AIC lag selection, synthetic): F 5.49–6.04
and t −3.80 to −3.95. These show that lag selection pushes the effective bounds outward.

## 9. Exploratory H1b plan

### 9.0 Rules for every step

- **Labelling.** Every table, figure and summary is labelled **"exploratory (ADR 0008 §9)"**.
  Nothing is gated at 0.025, and no result is presented as a test of §2 (§7).
- **Data.** The frozen vintage only. Steps needing new series are listed in §9.6 and need a
  separate data ADR.
- **Uncertainty.** Every estimate has an interval:
  - HAC (Bartlett kernel, Andrews bandwidth) unless stated otherwise;
  - bootstrap where stated.
- **Order.** Stage 1 (§9.1–§9.4) uses the **pre-period only**, except the descriptive
  nominal/real displays in §9.1. Window data enter model-based work only in Stage 2 (§9.5).

### 9.1 Nominal vs real USD/JPY (Stage 1, descriptive, no models)

**Series:**
- s;
- the CPI-based real rate q = s − x (rising q = real yen depreciation);
- x, raw and tax-adjusted;
- d;
- the 10Y differential;
- the real-differential proxy r = d − (12-month π_US − π_JP).

r uses realised, backward-looking inflation. It is a proxy, because there are no expectations
data in the vintage.

**Displays:**
- Levels over the full sample, with the ADR 0004 event markers and the 2022-01 reference
  line.
- Summary statistics of q, d and r by ADR 0004 era (§9.6).
- An arithmetic split of the 2022-01→2026-07 change in s into the change in q and the change
  in x.

**Question:** how much of the post-2022 nominal move is a real-rate move? This is arithmetic
on frozen data, with no estimation.

### 9.2 Integration diagnostics (Stage 1, pre-period)

**Tests.** For s, q, x (raw and tax-adjusted), d, the 10Y differential and r, in levels and
first differences:
- ADF: constant (plus trend for x and q in levels), AIC lags up to 12, MacKinnon p-values.
- KPSS: level, plus trend where relevant.
- Δx also gets centred seasonal dummies and tax-month impulse dummies.
- The largest AR root of Δx is reported as a near-I(2) indicator.

**Classification:**

| Class | Rule |
|---|---|
| I(0) | ADF rejects and KPSS does not |
| I(1) | Levels: ADF does not reject and KPSS rejects. Differences: classified I(0) |
| I(2) risk | The Δ-series is not classified I(0) |
| Ambiguous | Anything else |

The 5 % reference is descriptive. Low power near a unit root and the confounding of breaks
with unit roots (ADR 0004) are stated next to the results.

**Sensitivity:**
- a pre-period starting 1990-01;
- the full sample through 2026-07, labelled as including window data. It is reported but
  never feeds §9.3.

### 9.3 Estimator applicability (Stage 1; decided from §9.2 before any levels estimate)

| §9.2 outcome | ARDL / bounds | FM-OLS, D-OLS |
|---|---|---|
| s, x, d all I(1) | Applicable | Applicable to s on (x, d) |
| d I(0); s, x I(1) | Applicable (PSS allow I(0)/I(1) mixes) | **Only for the I(1) block:** s on x (θ). d is not used as an I(1) regressor. γ comes from the ARDL only. A D-OLS with d as an added stationary level regressor is shown only as a sensitivity, with no γ interval claimed. |
| d ambiguous | Applicable | Run under both treatments above. If θ or γ depends on the treatment, the result can be at most "fragile" (§9.4). |
| x has I(2) risk | Not applicable to (a), (c) or (d) | Not applicable to (a), (c) or (d). PPP-imposed (b) is assessed **only if q's own §9.2 classification is I(0) or I(1)**, and d's is too. Imposing θ = 1 does not remove I(2) behaviour: if x is I(2) and s is I(1), q = s − x is I(2). |
| q or s classified I(0) | The levels-relation question changes. Report descriptively and stop §9.4 for that specification. | — |

**Transformed series are assessed on their own.**
- Every series that enters a specification needs its own §9.2 classification. That
  includes q, tax-adjusted x and the 10Y differential. No series inherits a classification
  from its components or from a restriction such as θ = 1.
- ARDL bounds tests need every variable to be I(0) or I(1).
- FM-OLS and D-OLS need I(1) regressors that are cointegrated with the dependent variable.
- No estimator is applied outside these conditions.
- A series classified "I(2) risk" or "ambiguous between I(1) and I(2)" excludes every
  specification it enters.
- If no specification remains applicable, the long-run baseline is classified **not
  defensible** (§9.4), and Stage 2 is limited to descriptives.

**Drift caveat.** x has a strong drift. The FM-OLS and D-OLS intercept-only limit theory
assumes driftless regressors, so their intervals are labelled **approximate** whenever x
enters. D-OLS with a linear trend is a sensitivity check.

**Long-run forcing.** The ARDL conditional model assumes x and d are long-run forcing
(PSS Assumption 3). The loadings of Δx and Δd on the lagged equilibrium error are reported.
If either loading is clearly non-zero, the ARDL estimates of θ and γ carry a stated
warning.

### 9.4 Long-run model assessment (Stage 1, pre-period)

**Specifications:**
- (a) s on x and d;
- (b) PPP imposed, q on d;
- (c) as (a) with the 10Y differential, from 1986-07;
- (d) as (a) with tax-adjusted x.

Each runs only where §9.3 makes it applicable.

**Estimators:**
- ARDL/UECM: Case III, BG-filtered AIC lags, maximum 12.
- FM-OLS: Andrews bandwidth.
- D-OLS: leads and lags by BIC, maximum 6.

All are reported side by side with HAC intervals.

**Assessment layers.** Each layer is reported separately, with reasons. These are
**screening benchmarks, not validity conditions or hypothesis tests.**

| Layer | What is examined | Benchmark (descriptive) |
|---|---|---|
| A. Applicability | The §9.3 outcome | — |
| B. Statistical diagnostics | Bounds F and t; residual BG(12), ARCH-LM(12) and Jarque–Bera; impulse-response half-life with a 90 % moving-block bootstrap interval (block 24, 999 draws) | F and t beyond the PSS 5 % I(1) bound (§8.3), and beyond the simulated 95 % full-procedure quantile (§9.7). Half-life interval finite, with its upper end under 10 years. |
| C. Economic plausibility | θ (PPP predicts 1); the sign and size of γ (uncovered-interest-parity / real-interest-differential reasoning predicts γ > 0) | θ̂ and its 95 % interval inside or overlapping (0, 2). γ̂ positive, of the same sign across applicable estimators. |
| D. Stability | Recursive estimates; 120-month rolling estimates; separate estimates in the four pre-period ADR 0004 eras (1981–89, 1990–98, 1999–2012, 2013–21) | θ and γ keep their sign in at least 3 of 4 eras, and the era intervals overlap the full-sample interval |

**Classification of each specification, with written reasoning:**

| Class | Meaning |
|---|---|
| **Credible baseline** | Applicable, and all of B–D within their benchmarks. Applicable estimators agree on θ (and γ where estimable) to within their intervals. |
| **Fragile baseline** | Applicable, with some support, but at least one of the following: a statistic between the PSS bound and the simulated quantile, or in the inconclusive band; a half-life interval that is unbounded or extends beyond 10 years; estimator disagreement; a sign change across eras; dependence on the treatment of d; support only under PPP-imposed (b). |
| **Not defensible** | Not applicable, **or** no mean-reversion support (statistics below the I(0) bound, or a non-finite half-life interval), **or** θ or γ implausible with intervals excluding the plausible range. |

**Consequences:**
- **Credible:** Stage 2 computes the model-implied benchmark (§7.2).
- **Fragile:** Stage 2 may show the benchmark only as a labelled sensitivity display, with
  wide bands. It never appears in a headline or summary sentence.
- **Not defensible:** no benchmark and no gap measure. Stage 2 is limited to the q, d and r
  descriptives.

The benchmarks are judgment aids. A credible classification is **not** evidence for or
against §2.

**Stage 1 ends here.** The §9.4 classification is reported for review before Stage 2.

### 9.5 Stage 2: pre-2022 fit and post-2022 deviations

Stage 2 runs only for credible or fragile specifications, and only after review of Stage 1.

**In-sample residuals:**
- path, ACF, AR(1) ρ̂_u with a bias-corrected interval;
- historical extremes: 1985, 1998, 2007 and 2011.

**Out-of-sample path:**
- pre-period coefficients applied to window x and d;
- the 2025-10 row is shown as missing;
- the deviation from the model-implied benchmark, never "misvaluation" (§7.2).

**Uncertainty bands, 80 % and 95 %:**
- parameter uncertainty, by a moving-block bootstrap with re-estimation;
- residual uncertainty, from pre-period residuals at the same horizon.

**Deviation scale:**
- the window gap in σ_u units;
- its percentile against all 55-month pre-period windows. This is descriptive: §4 shows such
  ranks are not valid p-values here.

**Decomposition:** the gap split into its x, d and residual contributions.

### 9.6 Stage 2: regimes and omitted fundamentals (descriptive)

**Regimes.** Use only the eras and event markers fixed in ADR 0004:
- eras 1981–1989, 1990–1998, 1999–2012, 2013–2021 and 2022–end;
- the 13 dated event markers, from the Plaza Accord (1985-09-22) to the BoJ ending
  negative rates and YCC (2024-03-19).

**No new boundaries** are chosen, and no break dates are estimated. Formal break work belongs
to the separate structural-break milestone.

**Omitted fundamentals. Each needs a data ADR first; none is part of Stage 1 or 2:**
- terms of trade or energy prices;
- net international investment position or current account;
- survey inflation expectations;
- central-bank balance sheets.

**Rules for adding them:**
- They are added one at a time.
- Every attempt is listed, including null results.
- Results use association language only.

### 9.7 Stage 1 deliverables and checks

| Deliverable | Detail |
|---|---|
| `notebooks/03_h1b_exploratory.ipynb` | §9.1–§9.4, ending at the classification table |
| Helpers in `src/kagura/models.py` | Unit-root classification; ARDL bounds wrapper (case, k, BG-filtered AIC); FM-OLS and D-OLS (adapted from the archived `wwlib.py`); impulse-response half-life with block bootstrap |
| Tests in `tests/test_models.py` | One per helper, on synthetic data. Classification recovers a known I(0)/I(1) pair. Bounds wrapper F and t equal a hand-built UECM. FM-OLS and D-OLS recover a known θ. The half-life of a known AR(1) lies inside the bootstrap interval. |
| Simulated 95 % bounds quantiles | The archived bounds pilot code, reused on **synthetic** data at the 95 % level, with seeds fixed in the notebook |
| `vintage.FROZEN_SHA256` | The two CPI checksums from §8.2 added |
| `make h1b-explore` | Checksum check, then notebook execution, writing `reports/figures/h1b_*.png` |
| Verification | `make lint`, `make test`, `make h1b-explore` |

## 10. Reconciliation with ADR 0006 (frozen; not modified)

| ADR 0006 commitment | ADR 0008 position |
|---|---|
| §8: H1b primary test at α = 0.025, no reallocation | No primary test is run. The 0.025 is unused and not reallocated (§0). This follows the same principle as ADR 0006 for a failed precondition: when the gate fails, H1a's 0.025 is not reallocated. |
| §8: family-wise bound 0.05 over H1-supporting claims | Holds, and is at most 0.025 in practice (§0). |
| §10: candidate regime boundary 2022-01, not an assumed break | Kept, as a reference marker (§8.1, §9.1). |
| §10 and §9.2: fixed samples and vintage; no extension | Kept. The window ends at 2026-07, inside the 2026-08 monthly sample, because the frozen Japan CPI ends there. Nothing was downloaded. |
| §10: monthly CPI checksums added in the H1b ADR | §8.2. Added to the code guard in Stage 1. |
| §10: 2Y differential primary | Kept (specification (a)); 10Y is (c). |
| §10: H1b's procedure frozen before any levels model is estimated | Kept. No levels model has been estimated. Freezing precedes Stage 1. |
| §10: disclosure of what H1a revealed | §1. |
| §10 (non-binding): AK-type breakdown test; break interactions are descriptive | AK evaluated and rejected (§4). Break interactions are not used. |
| §3: association language only | §7.2 and §9.6. |

**One substantive departure, recorded here:** ADR 0006 assumed that H1b *would* have a
primary test. ADR 0008 concludes that none is feasible. ADR 0006 is not amended. Its
commitments are honoured by leaving H1b's α unspent.

## 11. Remaining assumptions and limitations

| # | Item |
|---|---|
| A1 | Simulated bounds quantiles assume the simulated DGP class. They are used descriptively only. |
| A3 | Long-run forcing of x and d. Checked descriptively (§9.3). |
| A4 | Pre-period stability over 1981–2021 is doubtful. Checked through layer D of §9.4 and the 1990-01 sensitivity. |
| A5 | Any change may predate 2022. 2022-01 is a marker, not a break. |
| A8 | 2023 energy subsidies distort window x. Not adjusted. |
| A9 | **Resolved** (§8.2). |
| A10 | US rent/OER understatement in 2025-11…2026-03. Stage 2 sensitivity: window ending 2025-09. |
| A11 | Current-vintage CPI, not real-time. |
| A12 | r uses realised, not expected, inflation. |
| A13 | The WW published-vs-working-paper discrepancy is unresolved. Recorded for the literature; irrelevant after NO-GO. |
| A14 | The §9.4 benchmarks are conventions. Changing them after Stage 1 results are seen requires a new ADR and disclosure. |

## 12. Companion material and references

**Companion material (committed with this ADR):**
- `research/methodology/adr0008-h1b-confirmatory-pilots/`: the AK and WW pilot code, fixed
  seeds, package versions, validation fixtures and reference outputs. `run_all.sh`
  reproduces every reference output exactly; this was verified on 2026-10-23. See its
  README.
- `docs/decisions/superseded/0008/`: the superseded drafts, with errata.

**Verified (read in sessions on 2026-10-23):**
- Andrews, D. W. K., and Kim, J.-Y. (2006). Tests for cointegration breakdown over a short
  time period. *JBES* 24(4), 379–394. DOI 10.1198/073500106000000297.
- Pesaran, M. H., Shin, Y., and Smith, R. J. (2001). Bounds testing approaches to the
  analysis of level relationships. *JAE* 16(3), 289–326. Tables CI(iii) and CII(iii).
- Wagner, M., and Wied, D. (2017). Consistent monitoring of cointegrating relationships: The
  US housing market and the subprime crisis. *JTSA* 38(6), 960–980. Author PDF:
  https://wisostat.uni-koeln.de/sites/statistik/Dominik_Wied/Wagner_Wied_2017_JTSA.pdf
- Wagner, M., and Wied, D. (2014). SFB 823 Discussion Paper 23/2014.
  https://doi.org/10.17877/DE290R-14599
- `cointmonitoR` 0.1.0 and `cointReg` (CRAN sources, read but not run).
- Statistics Bureau of Japan:
  - 2025-base revision: https://www.stat.go.jp/english/data/cpi/2025plan.html
  - 2025 yearly average: https://www.stat.go.jp/english/data/cpi/158c.html
- BLS, 2025 shutdown CPI FAQ. BIS long CPI series documentation.
- statsmodels 0.15.0, `tsa/ardl` source.

**Bradley (1978), status: bibliographic details verified; content not verified from the
primary source.**
- **Verified (Crossref, DOI 10.1111/j.2044-8317.1978.tb00581.x):** Bradley, J. V. (1978).
  Robustness? *British Journal of Mathematical and Statistical Psychology* 31(2), 144–152.
- **Not verified:** the article text was not read.
- **Secondary sources:** the 0.5α–1.5α "liberal criterion" (p. 146) is attributed to it by
  several later papers. Examples are the ERIC document ED298155 and Blanca et al. (2018),
  *Behavior Research Methods*. These were seen only as search results, not read in full.
- **Context:** the criterion comes from robustness studies of tests in psychology.
- **How this ADR cites it:** as the usual attribution of a convention, **not** as established
  support for the project's tolerance (§3). No conclusion depends on it.

**Cited, not re-read:**
- Kejriwal and Perron (2010);
- Pesaran and Shin (1999);
- Phillips and Hansen (1990);
- Stock and Watson (1993);
- Andrews (1991);
- Dornbusch (1976);
- Frankel (1979).

## 13. Order of operations

1. **Reviewer approval** of this draft.
2. **Freeze.** Commit, in a single commit, then push:
   - this file;
   - `docs/decisions/superseded/0008/`;
   - `research/methodology/adr0008-h1b-confirmatory-pilots/`;
   - the `pyproject.toml` ruff exclusion.
3. **Stage 1 code.** Implement the §9.7 helpers and tests on synthetic data, and add the CPI
   checksums to the guard.
4. **Stage 1 run.** Run `make h1b-explore` (§9.1–§9.4). **Stop and report the
   classification.**
5. **Stage 2,** only on approval (§9.5–§9.6). The omitted-fundamentals work comes later,
   under data ADRs.
