# ADR 0006 — H1 Formal Econometric Testing Protocol

Date: 2026-10-09. **Status: Frozen.**

This ADR was frozen by committing it on its own and pushing it to the public repository,
before any model in it was estimated on real data. Implementation is developed and tested
on synthetic data only until the real-data run in §11.

**Scope.**
- **H1a (short-run comovement):** fully specified here (§3–§9).
- **H1b (long-run levels relationship):** a planned follow-up. This ADR does not freeze its
  testing procedure; a separate ADR will (§10).

## 1. Context

ADR 0004 froze an exploratory view of H1, and `notebooks/01_exploration.ipynb` reported
it. The exploration separated two meanings of "decoupling":

- the comovement of daily **changes**, tested here as H1a;
- the relationship between **levels**, to be tested later as H1b.

### 1.1 Status: pre-specified, not blind

Already inspected, in the notebook and README:

- era means of 1y and 3y rolling correlations of daily FX and differential changes (all
  eight ADR 0004 variants);
- era standard deviations of daily FX and 2Y differential changes;
- the month-end levels scatter by era;
- ADF/KPSS results for log USD/JPY and both differentials.

Not yet computed: any regression coefficient, R², Wald test, sup-Wald test, bounds test,
long-run coefficient, or end-of-sample test.

**Disclosure: the exploratory results already reveal approximate H1a coefficients.** A
regression slope equals a correlation times a ratio of standard deviations,
`β = ρ · sd(Δs) / sd(Δd)`. From numbers already published (era-mean 1y same-day 2Y
correlation, era standard deviations):

| Era | ρ | sd(Δs), % | sd(Δd), pp | β (approx.), % per pp |
|---|---|---|---|---|
| 2013–2021 | 0.37 | 0.549 | 0.032 | ≈ 6.3 |
| 2022– | 0.44 | 0.666 | 0.073 | ≈ 4.0 |

That gives an approximate ratio of ≈ 0.63, close to the 2/3 threshold in §5. The
approximation is crude: an era mean of rolling correlations is not the era correlation,
and sd(Δs) uses all rows rather than rows after exclusion.

- The ⅓ threshold was proposed before this arithmetic was done, and it is kept unchanged.
  Moving it now would be tuning with the approximate answer in view.
- What the formal test adds is exact estimation, valid uncertainty, and a decision rule
  committed in advance. It does not add surprise.
- An "inconclusive" outcome is a likely, legitimate result.

## 2. What was decided before and after the exploration

| Decided **before** exploration (source) | Refined **after** exploration (this ADR) |
|---|---|
| H1 claim and "evidence against" (`HYPOTHESES.md`) | Split of H1 into H1a / H1b; H1a tests the *decline* direction |
| Candidate methods incl. rolling regression, Chow/Bai–Perron, HAC errors (`RESEARCH_SPEC.md` §5, §10) | Slope β is the primary quantity; R² and correlation are descriptive |
| Sample from 1981 (ADR 0001) | Reference era 2013–2021 |
| Sources and vintage (ADR 0002) | Material-decline threshold ⅓, tested as a linear restriction |
| Alignment, availability lags, lagged-timing requirement (ADR 0003) | Monthly frequency as a robustness check |
| Change definitions, timing variants, exclusion rule, 2Y primary / 10Y robustness, eras with the 2022-01 boundary, event list (ADR 0004) | 2022-01 era boundary used as the H1a candidate regime boundary |
| | Two-leg decomposition (motivated by the JGB leg being pinned in 1999–2022) |
| | Unknown-break-date inference deferred to the structural-break ADR (§6.2) |
| | Bonferroni split of α across H1a and H1b |

`HYPOTHESES.md` says "weakened **or changed** materially". H1a tests the decoupling
direction. A material *increase* in β is reported (§5, "ruled out" outcome, plus the
absolute change) but does not count as support for H1. `HYPOTHESES.md` is not edited;
this table is the record of the refinement.

## 3. What H1a estimates, and what it does not

| Kind of claim | Status in H1a |
|---|---|
| **Contemporaneous association**: how much USD/JPY and the differential move together over (approximately) the same window | **This is what H1a estimates**, and whether it changed between eras. |
| **Forecasting**: whether today's information predicts future USD/JPY | **Not estimated.** There is no out-of-sample evaluation. The lagged-timing variant uses only information known at the fix, but it is an in-sample regression, not a forecast test. Forecasting is v0.3. |
| **Causal effect**: what a rate change *does* to the yen | **Not identified.** Common shocks (US macro news moves US yields and the dollar together) and reverse causality (yen weakness moving BOJ expectations) both enter β. Causal work is v0.4. |
| **Mechanism**: why β changed | **Not addressed.** That is H2/H3. |

Sentences in the write-up must use association language: "is associated with",
"comoves with". They must not say "drives", "causes", "predicts" or "responds to".

## 4. Specification

### 4.1 Variables

From `kagura.explore.changes` (ADR 0004), unchanged:

- `Δs_t = 100 · (log usdjpy_t − log usdjpy_{t−1})`, in %.
- `Δd_t = diff_t − diff_{t−1}`, in pp. Primary: the **2Y** differential.
- ADR 0004 exclusion rule: a row is used only if both changes are between consecutive live
  observations.
- No trimming, winsorizing or outlier removal.

### 4.2 Eras

The ADR 0004 eras, unchanged:

| Era | From | To |
|---|---|---|
| 1981–1989 | 1981-01-01 | 1989-12-31 |
| 1990–1998 | 1990-01-01 | 1998-12-31 |
| 1999–2012 | 1999-01-01 | 2012-12-31 |
| **ref**: 2013–2021 | 2013-01-01 | 2021-12-31 |
| **new**: 2022– | 2022-01-01 | end of sample (§9) |

**2022-01-01 is a pre-specified *candidate* regime boundary, not an assumed true break.**
If the true change occurred elsewhere (for example mid-2023), the "new" era mixes regimes
and the contrast is biased toward no change. Unknown-break-date inference is deferred to
the structural-break ADR (§6.2).

### 4.3 Regression

Fully era-interacted OLS on the pooled sample:

```
Δs_t = Σ_e 1[t ∈ e] · (α_e + β_e · Δd_t) + ε_t
```

- **β_e:** the % change in USD/JPY associated with a 1 pp change in the 2Y differential,
  within era e. So β/10 is the association per 10 bp, and β the association for a 100 bp
  narrowing (with the sign reversed).
- **α_e:** the era drift. It is not interpreted.
- **R²_e = β_e² · Var_e(Δd) / Var_e(Δs):** the share of era-e FX variance associated with
  the differential. It is descriptive only. It falls whenever the differential is quiet,
  even if the link is unchanged.

### 4.4 Standard errors

Newey–West HAC, Bartlett kernel, lag `L = floor(4 · (T/100)^(2/9))` with T the number of
rows used (L = 11 for the daily primary, about 5 monthly), with no small-sample correction.

- Excluded rows are dropped and the remaining rows are treated as consecutive.
- HAC on the pooled interacted model allows each era its own error variance, along with
  conditional heteroskedasticity, volatility clustering and weak serial correlation.

### 4.5 Timing: what the primary specification estimates

Times are New York (ADR 0003; the JGB snapshot time is approximate and still to be checked
against MOF methodology):

| Series | Observed at | Window of its daily change |
|---|---|---|
| USD/JPY | 12:00 noon fix | (12:00 on t−1, 12:00 on t] |
| US Treasury yields | ≈ 15:30 | (15:30 on t−1, 15:30 on t] |
| JGB yields | ≈ 01:00–02:00 on t (Tokyo ≈ 15:00 JST) | (≈ 01:00 on t−1, ≈ 01:00 on t] |

Every variant estimates a population linear-projection coefficient:

```
β = Cov(Δs_t, Δd_t) / Var(Δd_t)
```

Split each change into sub-intervals of the day. The numerator then contains:

- covariances within the overlapping sub-intervals (contemporaneous comovement);
- cross-covariances between non-overlapping sub-intervals (lead–lag effects).

The denominator includes the variance from the non-overlapping parts. **So the direction
of any bias, relative to an instantaneous response, depends on the data-generating
process (DGP).**

- **Attenuation (pulled toward zero)** happens only if news arrives as independent
  increments, both markets absorb it instantly, and the loading is the same at every time
  of day.
- **Delayed or anticipatory adjustment** (positive cross terms) can offset or reverse the
  attenuation.
- **Intraday reversal** (negative cross terms) can deepen it.
- **A changing mix of news across the day** makes β a variance-weighted mix of
  time-of-day loadings. For example, FOMC statements have been released after the noon fix
  since 1994: around 14:15 New York time, and at 14:00 since 2013.

What each variant estimates:

- **Same-day (primary).**
  - The US leg overlaps the FX window for ≈ 20.5 h; the JGB leg for ≈ 13–14 h, and its
    change ends about 11 h before the fix.
  - Mostly contemporaneous association.
  - It includes US information from after the fix, so it is not real-time feasible and
    not a forecasting relationship.
- **Lagged US leg** (`us[t−1] − jgb[t]`).
  - The US leg overlaps the FX window for ≈ 3.5 h. Its other ≈ 20.5 h comes before the
    window, so that part is a lead–lag relationship. The JGB leg is as in same-day.
  - Every input was known at the fix, but this is a different estimand, not "same-day
    without the look-ahead".
- **Monthly.**
  - The misaligned share is about 0.5–1.5% of the window, so timing distortion is
    negligible.
  - But it is a different horizon: it also captures delayed adjustment and slower common
    drivers. A gap between daily and monthly β is therefore not, by itself, evidence of a
    timing artefact.

**For the era comparison.** The comparison measures a change in the *same-day projection
coefficient*. Reading it as a change in the underlying contemporaneous link requires the
timing distortion to be stable between ref and new (assumption A5, §7). Two mechanisms
could violate this:

- JGB yields move again since 2024, so the JGB-leg misalignment weighs more in the new era;
- the time-of-day mix of US news may have shifted.

The relative threshold (§5) is immune to a distortion that scales β by the same factor in
both eras. It is not immune to any other kind.

## 5. Primary test and decision rule

**Claim tested: material decline.** β_new is less than two-thirds of β_ref, i.e. a decline
of at least one-third.

**The ⅓ threshold is a preselected operational definition of materiality**, fixed before
estimation (§1.1). It is not an established economic constant, and no literature value is
claimed for it. Two interpretation aids, not derivations:

- Someone applying the 2013–2021 pass-through to the new era would overstate the FX
  movement associated with a given change in the differential by at least 50%
  (1 / (2/3) = 1.5).
- A relative threshold is unaffected by a timing attenuation that is common and
  proportional to both eras (§4.5). An absolute threshold would not be.

Other thresholds (¼, ½) are reported as sensitivity and never enter the decision.

**Test quantity.** Linear in the coefficients, so there is no ratio and no division by
β_ref:

```
δ = β_new − (2/3) · β_ref
z = δ̂ / se(δ̂)
```

- δ̂ comes from the §4.3 regression.
- se(δ̂) uses the HAC covariance of (β_new, β_ref).
- Normal approximation. Expected sample sizes are about 2,000 ref and 1,000 new daily rows.
  **These counts are provisional**, taken from the exploration's exclusion tables; the
  exact counts are reported at estimation.
- Notation: c = Φ⁻¹(0.975) = 1.959964.

### 5.1 Inference rules (α = 0.025, one-sided)

Every decision uses a **one-sided** p-value, or equivalently a **one-sided 97.5% confidence
bound**, at the H1a level α = 0.025 (§8).

| | Hypotheses | p-value | Equivalent bound | Rule |
|---|---|---|---|---|
| **G. Gate**: a reference association exists | H0: β_ref ≤ 0 vs H1: β_ref > 0 | 1 − Φ(β̂_ref / se) | L_ref = β̂_ref − c·se(β̂_ref) | Passes if p < 0.025 ⇔ L_ref > 0 |
| **S. Material decline** (H1a's confirmatory claim) | H0_S: δ ≥ 0 vs H1_S: δ < 0 | p_S = Φ(z) | U = δ̂ + c·se(δ̂), one-sided 97.5% **upper** bound | Reject H0_S if p_S < 0.025 ⇔ U < 0 |
| **R. Material decline ruled out** | H0_R: δ ≤ 0 vs H1_R: δ > 0 | p_R = 1 − Φ(z) | L = δ̂ − c·se(δ̂), one-sided 97.5% **lower** bound | Reject H0_R if p_R < 0.025 ⇔ L > 0 |

**Outcome categories:**

| Outcome | Condition | Meaning |
|---|---|---|
| **Not assessable** | G fails | No reference association has been established, so a relative decline is undefined. Only absolute quantities are reported. |
| **H1a supported** | G passes, S rejects | Evidence that β_new is below two-thirds of β_ref: a decline of at least ⅓. |
| **Material decline ruled out** | G passes, R rejects | Evidence that β_new exceeds two-thirds of β_ref. This is a one-sided, non-inferiority-type claim. It does **not** show that β is unchanged, and it is consistent with a smaller decline or with an increase. No equivalence ("no change") claim is made or tested; that would need a second, upper margin, which is not specified. |
| **Inconclusive** | G passes, neither S nor R rejects | The data cannot distinguish a decline of at least ⅓ from a smaller decline or an increase. **This is not evidence of stability, and not evidence of decline.** Failure to reject H0_S is never reported as support for "no material decline". |

**How these fit together:**

- S and R cannot both reject: U < 0 and L > 0 are incompatible.
- If the true δ < 0, only R can make a false claim, with probability ≤ 0.025. If δ > 0,
  only S can, with probability ≤ 0.025. At the boundary point δ = 0 exactly, both claims
  are false and the probability of making one of them is ≤ 0.05.
- The gate is a precondition, not a claim, and it uses the same α.
- p-values and bounds are equivalent: p_S < 0.025 ⇔ z < −c ⇔ U < 0; p_R < 0.025 ⇔ z > c ⇔
  L > 0. The equality case has probability zero and is resolved as "not rejected".

**Limitations of the gate G:**

- **It establishes only that β_ref is positive.** It does not show that β_ref is precise or
  economically large. If β_ref is barely positive, its uncertainty dominates se(δ̂): S and
  R are then likely to be inconclusive, and the Fieller set wide or unbounded.
- **It is a pretest.** A false "supported" or "ruled out" outcome needs both G to pass and
  S or R to reject, so gating cannot raise their unconditional error rates above 0.025.
  The error rate *conditional on G having passed* is not controlled, and can exceed 0.025
  when G passes only narrowly.
- **A failed gate is neither for nor against H1.** H1a is then "not assessable". Its
  0.025 is not transferred to H1b (§8).
- **The gate's outcome has partly been seen.** The exploration implies β_ref ≈ 6.3
  (§1.1), so a gate failure is not expected. This expectation itself comes from inspected
  data.
- **It conditions on β_ref only.** A negative β_new is allowed, and S rejects whenever
  δ is significantly below zero.

### 5.2 Always reported (descriptive, not decision inputs)

- β_ref and β_new; the implied % FX association for a 100 bp narrowing.
- **Absolute change** β_new − β_ref, in % per pp.
- **Relative change** β_new / β_ref − 1:
  - point estimate;
  - **Fieller** confidence set at the same level, from the HAC covariance. When β_ref is
    imprecise this set may be unbounded or a union of two intervals; it is reported as
    such, never truncated or replaced by the delta method.
- δ, U and L at the sensitivity thresholds ¼ and ½.
- R²_ref and R²_new.

All intervals are shown as two-sided 95% intervals. Each endpoint is the one-sided 97.5%
bound above, so the displayed intervals and the decision rules are numerically
consistent.

## 6. Secondary analyses (reported in full, never decide H1a)

### 6.1 Era equality

HAC Wald test of H0: β equal in all five eras, χ²(4), α = 0.05, unadjusted. This answers
`HYPOTHESES.md`'s "evidence against": does one β describe the whole sample?

### 6.2 Unknown break date: deferred

**Decision.** H1a contains **no unknown-break-date test and no bootstrap.** Inference on
an unknown break date moves to the structural-break ADR (roadmap: stability work), and is
frozen there before it is run. Within H1a, the timing of changes is shown only by the
rolling β in §6.3, which is descriptive.

**Why it is deferred:**

1. **Lee (2021) cannot be verified.** Its sieve-wild algorithm and conditions could not be
   read (paywalled), so it is not used.
2. **The verifiable alternative needs an assumption the same-day specification breaks.**
   Boldea, Cornea-Madeira and Hall (2019) verified this session from the arXiv full text,
   1811.04125. Their wild fixed-regressor (WF) bootstrap:
   - draws `u*_t = û_t·ν_t`, with û_t the null-imposed residuals and ν_t i.i.d. (0, 1)
     with a finite 4+δ moment (Assumption 10; Rademacher in their simulations);
   - holds the regressors fixed;
   - recomputes sup-Wald with a heteroskedasticity-robust (Eicker–White) variance in each
     regime (§2.3, eqs. 15–21);
   - is shown valid in Theorems 1–2, which cover OLS as a special case (Remark 10).
   Their error assumption (Assumption 9) allows unconditional variance shifts, conditional
   heteroskedasticity, leverage and asymmetric volatility clustering. But it requires the
   errors to be a **martingale difference sequence**, with all dynamics carried by the
   included regressors (Remark 4).
   
   In the same-day H1a regression this is doubtful *by construction*. The US yield move
   after the fix on day t−1 sits in Δd_{t−1} but in the FX window of day t (§4.5), which
   induces short-lag dependence. The exploration's positive lagged-timing correlations (2Y
   era means ≈ 0.06–0.15 since 1999) are consistent with this.
3. **Making the assumption plausible needs a new specification.** Adding Δd_{t−1} and Δs_{t−1}
   as regressors would change the model and its β. That is a decision for the structural-
   break ADR, not a patch to H1a.

**Recorded for that ADR, not binding:** the candidate method is Boldea et al.'s WF
bootstrap with sup-Wald (Eicker–White variance, null-imposed residuals, 15% trimming) on a
dynamic specification that includes lags.

**Note on the bootstrap's mechanics.** The i.i.d. multipliers in a wild bootstrap do not
reproduce volatility clustering as a dynamic. The bootstrap errors û_t·ν_t have no
conditional-variance dependence across t. What the fixed-design wild bootstrap preserves
is each residual's magnitude at its own date, and Boldea et al. prove this is sufficient
for the sup-Wald limit under their Assumption 9, which permits clustering in the true
errors.

**Why H1a's primary inference is unaffected.** §5 uses Newey–West HAC (§4.4), which
accommodates short-lag dependence and heteroskedasticity in the scores. It does not
require martingale-difference errors.

### 6.3 Descriptive

- **Rolling β and rolling R²:** ADR 0004 windows (250 and 750 rows) with the 80% rule.
  No inference.
- **Two-leg decomposition:** `Δs = α + β_US·Δus + β_JP·Δjgb + ε`, by era, with HAC Wald
  tests of β_US = −β_JP. This shows whether the "differential" behaves as one variable.
  In 1999–2022 the JGB leg is nearly constant, so β_JP is imprecise there by
  construction.

## 7. Assumptions

| # | Assumption | Needed for | If violated |
|---|---|---|---|
| A1 | β_e is constant within each era | Reading β_e as "the" era coefficient | β_e is a variance-weighted average over the era. Rolling β (§6.3) shows within-era drift. |
| A2 | Weak dependence and finite fourth moments of Δd_t·ε_t | HAC consistency, normal approximation | CIs too narrow. Heavy tails are partly mitigated by large era samples; not otherwise addressed. |
| A3 | E[Δd_t·ε_t] = 0 by definition of a linear projection | Interpreting β as a projection coefficient | None for association. It is **not** an assumption of exogeneity (§3). |
| A4 | Data, exclusion rule and eras as in ADR 0003/0004 | Everything | — |
| A5 | Timing distortion stable between ref and new | Reading δ as a change in the underlying contemporaneous link (not its validity as a test) | δ partly reflects timing. The monthly robustness check is the guard (§9); intraday data could settle it but is out of scope. |
| A6 | 2022-01 boundary | Era contrast | If mis-dated, the contrast is biased toward no change. Rolling β (§6.3) shows timing descriptively; break-date inference is deferred (§6.2). |
| A7 | Normal approximation for z | §5 p-values and bounds | Inaccurate one-sided error rates. Mitigated by large era samples; not otherwise addressed. |
| A8 | Observation times in §4.5: US yields ≈ 15:30 and the JGB snapshot ≈ 15:00 JST, taken from ADR 0003 and not verified against the source methodologies | Interpreting the timing variants (§4.5) | Overlap hours change. The specifications and tests are unaffected; only their interpretation is. |
| A9 | HAC treats retained rows as consecutive across excluded rows (§4.4) | se(δ̂) | Minor misstatement of autocovariances around holidays. About 10% of rows are excluded (ADR 0004 counts). |

## 8. Multiple testing

**H1 family = {H1a, H1b}, family-wise error rate 0.05, Bonferroni split fixed now: 0.025
each.**

- Bonferroni, not Holm, so H1a can be finalised and reported before H1b is specified or
  run. Holm's step-down would make H1a's final status depend on H1b's p-value.
- Bonferroni is valid under any dependence between the two.
- The H1b ADR **must** use α = 0.025 for its primary test and may not reallocate.
- The Bonferroni family covers the claims **supporting H1**: S here, and H1b's primary
  claim later. Their joint false-support probability is ≤ 0.05.
- R (material decline ruled out) is a claim *against* H1, tested at 0.025 one-sided,
  outside this family. S and R cannot both reject (§5.1).
- The gate G is a precondition, not a claim. If G fails, H1a's 0.025 is not reallocated
  to H1b.
- Everything in §6 and §9 is unadjusted and labelled secondary or robustness. It can
  qualify the primary conclusion. It can never replace it.

## 9. Robustness, fixed sample and data vintage

### 9.1 Robustness variants

Each variant re-runs §5.1 (gate, S, R, category) exactly, with only the stated change:

| Variant | Change |
|---|---|
| R1 | Lagged US leg (§4.5) |
| R2 | Monthly: changes between consecutive month-end rows of `monthly.csv`, using the stored values. Carried flags are not applied; a month-end value at most 5 business days old is a small misalignment over a month. Era is assigned by month-end date. HAC lag ≈ 5. Provisionally about 108 ref and 56 new months: low power. |
| R3 | 10Y differential. It starts 1986-07, so the ref and new eras are fully covered. |

**Labelling rule.**
- "Robust" if R1–R3 fall in the same category as the primary result.
- Otherwise "sensitive to R#", with the categories listed.
- The primary category is never changed by robustness results.

### 9.2 Fixed sample and vintage

- **Samples:** daily 1981-01-01 to **2026-09-11**; monthly 1981-01 to **2026-08**. Fixed
  here. Later downloads do not extend them.
- **Vintage:** raw data downloaded 2026-09-15 (`data/raw/manifest.json`), processed
  2026-09-22.
- The analysis checks these SHA-256 checksums before running and stops on a mismatch.
  Raw data are not committed (ADR 0005).

| File | SHA-256 |
|---|---|
| processed/daily.csv | `edfc95cf676d3647b6af3667b3b34fc74b4b6e692d750bf6ab8008de9105cd99` |
| processed/monthly.csv | `3f19c005d8db1ab1963488b2af748dcb6f956fe3a6a6cf6f4acdafda92a56215` |
| raw/manifest.json | `c0f5676e888751690cf8a5ad86df63c8727b5a02f63302b33fb535e315bee51c` |
| raw/usdjpy.csv | `0ea1de1993e69827ccfdddc390af8f8f5abf15c566f4c4cd5a6072495b773965` |
| raw/us_2y.csv | `1289774410381729569844068b657a7cc11a56a699669509bf6ed26a0db572a4` |
| raw/us_10y.csv | `94c1e5b98460d7de645be32f3211853c3d749724ecb12cac33bc84623ea759b4` |
| raw/jgb.csv | `997a8f95dc20c884d506c627ac075b1e93a357410094058ac19f3effead2e353` |
| raw/jgb_current.csv | `8da8cc83668bf280f1849ce2e6fab752881fc771b87d4691887bdb85e2f9f519` |

## 10. H1b — planned follow-up (not frozen here)

H1b asks whether a long-run levels relationship between USD/JPY and the differential
existed and then broke down. Its testing procedure will be frozen in a **separate ADR**,
before any levels model is estimated.

**Fixed now, so the later ADR cannot change it:**

- Primary-test α = 0.025 (§8).
- Candidate regime boundary 2022-01, as a candidate rather than an assumed break.
- The samples and vintage of §9.2. The monthly CPI files' checksums are added in that ADR.
- 2Y as the primary differential.

**Intended approach, not binding:**

- A long run including relative CPI (purchasing-power parity).
- Establishing a relationship (ARDL bounds test on the pre-2022 sample, after ruling out
  I(2) variables) kept separate from testing its stability (an end-of-sample breakdown
  test such as Andrews and Kim 2006).
- Break interactions in the error-correction model treated as descriptive, because they
  invalidate standard bounds critical values.

**Disclosure the later ADR must carry.** By the time it is written, the H1a results will
have been seen. It must state this, and list which H1b-relevant quantities H1a revealed.

## 11. Order of operations

1. Commit this ADR on its own and push it. This is the freeze.
2. Implement `src/kagura/models.py` and `tests/test_models.py` on synthetic data only:
   - recover a known β;
   - coverage of the one-sided U and L bounds;
   - correct S/R/inconclusive/not-assessable categorisation on constructed cases;
   - Fieller set behaviour as β_ref → 0.
3. Run `notebooks/02_h1a_formal.ipynb` on real data. Primary result first, then §6 and §9.
4. Anything not listed here is **post-hoc**, labelled as such, and recorded in a new ADR.

## 12. Items to close before the freeze

None. The bootstrap verification item is removed because break-date inference is deferred
(§6.2).

## 13. References

Verified this session (title and venue at least; content where stated):

- Boldea, O., Cornea-Madeira, A., and Hall, A. R. (2019). Bootstrapping structural change
  tests. *Journal of Econometrics* 213(2), 359–397. **Full text read** (arXiv 1811.04125):
  - WF algorithm, §2.3 eqs. (15)–(21);
  - error assumptions, Assumptions 9–10 and Remark 4 (martingale difference sequence;
    conditional and unconditional heteroskedasticity);
  - validity, Theorems 1–2; OLS special case, Remark 10.
  The published version was not compared against the arXiv text.
- Lee, D. J. (2021). Bootstrap tests for structural breaks when the regressors and the
  serially correlated error term are unstable. *Bulletin of Economic Research* 73(2),
  212–229. Title and venue only; algorithm not verified, so not used (§6.2).
- Andrews, D. W. K., and Kim, J.-Y. (2006). Tests for cointegration breakdown over a short
  time period. *Journal of Business & Economic Statistics* 24(4). Cited for H1b only.
- Fieller, E. C. (1954). Some problems in interval estimation. *Journal of the Royal
  Statistical Society, Series B* 16, 175–185.
- Newey, W. K., and West, K. D. (1987). A simple, positive semi-definite,
  heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica*
  55(3), 703–708.
- Federal Reserve FOMC statement release times (§4.5): about 14:15 from 1994, and 14:00
  since 2013. Checked against secondary sources.
