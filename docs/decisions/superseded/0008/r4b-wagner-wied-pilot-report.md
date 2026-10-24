# ADR 0008 — Wagner–Wied Replacement Pilot: Results and GO/NO-GO

Date: 2026-10-23. **Status: for independent review.**

**Recommendation: NO-GO.** Further confirmatory development of Wagner–Wied (WW) for H1b
should stop. The fixed fallback (option D) applies: H1b's confirmatory test is
**NOT ASSESSABLE**, and its 0.025 stays unused.

**What was and was not done:**
- All model simulations used synthetic data only.
- The only real-data contact was a **read-only** inspection of `raw/jp_cpi.csv` for CPI
  provenance (§5). Its checksum is unchanged.
- No historical H1b regression, test or integration-order test was run.
- No repository file was modified; nothing was committed; ADR 0008 was not frozen.

Scripts are in the scratchpad: `sim2/` (WW pilot) and `cran/` (inspected R package
sources, not executed).

## 1. The published paper vs the 2014 working paper

**Sources read in full:**

| Source | What it is |
|---|---|
| Published JTSA 38(6), 960–980 | Author-hosted PDF, wisostat.uni-koeln.de |
| SFB 823 DP 23/2014 | The working paper |
| `cointmonitoR` 0.1.0 R source (CRAN, 2016) | The package the published paper says it used for "both our finite sample simulations as well as the empirical application" |
| `cointReg` 0.2.0 R source (bandwidth code) | Its estimation dependency |

| Item | 2014 DP | Published 2017 | Authors' package |
|---|---|---|---|
| Model | y on D_t and I(1) X_t | Same: eq. (1) and **eq. (2) X_t = X_{t−1} + v_t, "a k-dimensional vector random walk regressor"** | — |
| Assumptions | Assumption 1 (deterministics); Assumption 3 FCLT for η = (u, v′)′; Ω_vv > 0 | Assumption 1; Assumption 2(a)–(c): FCLT, the ∫B dB′ + Δ limit, joint convergence; Ω_vv > 0 | — |
| H0 / H1 | H1 stated as I(0)→I(1); deterministic breaks also analysed | H0 (3): θ constant and u I(0). **H1 (4): a parameter change θ₁ ≠ θ, or I(0)→I(1), at r ≥ m** | — |
| Detector | eq. (37): ω̂⁻²[T⁻¹Σ_{i=[mT]+1}^{[sT]}(Ŝ⁺_i/√T)² **−** T⁻¹Σ_{i≤[mT]}(Ŝ⁺_i/√T)²] | **eq. (12): ω̂⁻²·T⁻¹Σ_{i=[mT]+1}^{[sT]}(Ŝ⁺_i/√T)², with no calibration term.** Footnote 4 attributes the subtracting form to the WP | **Subtracting form**: `erg <- (cumsum.ms - sum.1m) / omega` |
| Rejection rule | eq. (10): \|H/g\| > c | eq. (20): F/g > c (no absolute value) | `abs(erg / w)` > c |
| g(s) | s³ (intercept) | s³ (intercept) | `s^3` |
| Estimators | FM-OLS, D-OLS, IM-OLS | Same | Same; ω̂_{u·v} always taken from the FM fit on the calibration sample |
| Critical values | Appendix B Tables 4–13 (k ≤ 2) | "Supplementary Appendix C", k = 0…4. **Not in the author PDF; not verified** | `sysdata.rda` `cv.coint`, k = 1…4 |

**Critical-value reproduction** (k = 2, intercept, 97.5 %; my simulation of the limits in
eqs. (13), (18), (38); random walks of length 1,000; 100,000 replications):

| Form, m | DP table | Package | Mine |
|---|---|---|---|
| FM/D, subtracting form, m = 0.50 | 6.99 (Table 10) | 6.9939 | 7.1207 |
| FM/D, subtracting form, m = 0.90 | 0.32 | 0.3171 | 0.3112 |
| IM, subtracting form, m = 0.50 | 15.62 (Table 11) | 15.619 | 15.596 |
| IM, subtracting form, m = 0.90 | 0.10 | 0.0957 | 0.0952 |
| FM/D, **published eq. (12) form**, m = 0.90 | — | — | **0.0331** |

**Verified finding.** The detector printed in the published eq. (12) is **not** the one the
DP tables or the authors' software use. Their critical values match only the subtracting
form; the printed form implies values about 10× smaller at m = 0.9. I could not see
Supplementary Appendix C, so I cannot verify which form it tabulates. The pilot uses the
software/DP form, the only one with verified critical values. **This discrepancy is
unresolved.**

**Correction to my revision-4 report.** The values I cited there as "DP Table 10"
(15.62 at m = 0.50; 0.10 at m = 0.90) are actually Table 11 (IM-OLS). In the extracted text
each table caption follows its own body, and I read the numbers after the wrong caption.
The FM/D-OLS, k = 2 values are 6.99 and 0.32.

## 2. Theoretical eligibility (verified from the published text)

**Applicability problem 1: a stationary d.**
- Eq. (2) makes **every** stochastic regressor a random walk.
- Assumption 2 requires Ω_vv > 0, where v_t = ΔX_t. If d_t is I(0), Δd_t is
  over-differenced, its long-run variance is 0, and Ω_vv is singular.
- The limit theory (J(s) = [D(s)′, W_v(s)′]′) then does not apply.
- The theory does **not** permit a stationary regressor alongside integrated ones. Earlier
  KAGURA exploration left the 2Y differential between I(0) and I(1) (ADF p ≈ 0.05, KPSS
  ≈ 0.01–0.02), so this is a direct applicability problem. Simulation cannot resolve it.

**Applicability problem 2: drift in x.**
- Assumption 2's FCLT for η_t = (u_t, v_t′)′ implies mean-zero v_t, so the regressors are
  driftless random walks.
- Relative CPI has a strong deterministic drift. That was disclosed in revision 2 and is
  known from the CPI-only descriptives; no new data analysis was done here.
- A drifting regressor is outside the stated theory.
- WW's intercept-plus-trend case (g = s⁵) might absorb the drift, but that changes H1b's
  long-run specification. It was **not** investigated (no new variants, per your
  restriction).

## 3. Implementation and validation

| Check | Result |
|---|---|
| Detector vs a direct double loop | max \|diff\| 4e-17 |
| D-OLS (leads = lags = 2) vs an independent pandas-shift design plus statsmodels OLS | max \|coef diff\| 2.5e-15 |
| FM-OLS, iid errors (T = 500, 2,000 reps): t-test size at 5 % | .064 / .058 |
| FM-OLS, endogeneity only | .050 / .052 |
| FM-OLS, endogeneity + serial correlation (ρ_u .6, ρ_v .5) | .111 (T = 500) → .077 (T = 2,000) → .050 (T = 5,000), with bias reduced vs OLS (.0064 → .0016) |
| Critical values | Reproduced (§1) |

The FM-OLS pattern is the known finite-sample oversizing that vanishes with T. It is
consistent with a correct implementation. There is no independent FM-OLS reference in
Python, and R is not installed here, so `cointReg` itself could not be run.

**Settings used:**
- Bartlett kernel, with three bandwidth rules:

  | Rule | Bandwidth |
  |---|---|
  | **Andrews (1991) AR(1) plug-in** (the `cointReg` default formula, confirmed from source) | data-dependent |
  | Fixed Newey–West | ⌊4(T/100)^{2/9}⌋ |
  | "Large" | ⌊12(T/100)^{1/4}⌋ |

- My first run capped the plug-in ρ at 0.97, which was my own choice. `cointReg` has **no**
  cap. Re-running without it changed the FM-OLS sizes only within MC error (.019–.022 in
  I(1) cells, .045–.060 in I(0) cells).
- Critical value: 0.3174, the package table interpolated at m = 492/547.

## 4. Pilot results

Design: T_cal = 492, window = 55, endogeneity 0.5, R = 2,000 for null cells, 1,000 for
power cells. Seeds come from `SeedSequence([20261024, i])`. Total wall time ≈ 1 minute.

### 4.1 Null rejection at nominal 2.5 % [95 % Clopper–Pearson interval]

Screening rule (a diagnostic, not proof): **FAIL** if the 99 % CP lower bound > .0375;
**PASS** if the 99 % CP upper bound ≤ .0375; otherwise **AMBIG**.

| ρ_u, errors | d | FM-OLS (Andrews) | D-OLS |
|---|---|---|---|
| 0, normal | I(1) | .021 [.015, .028] PASS | .021 PASS |
| 0, normal | I(0) | .050 [.041, .060] **FAIL** | .045 AMBIG |
| 0, GARCH | I(1) | .020 PASS | .018 PASS |
| 0, GARCH | I(0) | .043 AMBIG | .043 AMBIG |
| .8, normal | I(1) | .021 PASS | .049 AMBIG |
| .8, normal | I(0) | .058 **FAIL** | .090 **FAIL** |
| .8, GARCH | I(1) | .022 PASS | .050 **FAIL** |
| .8, GARCH | I(0) | .057 **FAIL** | .099 **FAIL** |
| .95, normal | I(1) | .027 [.020, .035] AMBIG | .159 **FAIL** |
| .95, normal | I(0) | .061 **FAIL** | .244 **FAIL** |
| .95, GARCH | I(1) | .018 PASS | .152 **FAIL** |
| .95, GARCH | I(0) | .059 **FAIL** | .239 **FAIL** |
| .98, normal | I(1) | .023 PASS | .225 **FAIL** |
| .98, normal | I(0) | .072 **FAIL** | .340 **FAIL** |
| .98, GARCH | I(1) | .028 [.021, .036] AMBIG | .230 **FAIL** |
| .98, GARCH | I(0) | .077 **FAIL** | .353 **FAIL** |
| Drift 0.5 in x, ρ = 0 … .98, I(1) d | | .000–.001 (degenerate) | .000–.011 |

**Matched gap vs complete data.** Identical rejection rates to three decimals for both
estimators. The gap changes the statistic by less than 0.01.

**Sensitivity to the long-run variance estimator** (FM-OLS, I(1) d):

| Bandwidth | ρ = .8 | ρ = .95 | ρ = .98 |
|---|---|---|---|
| Andrews plug-in | .021 | .027 | .023 |
| Fixed Newey–West | .14 | .70 | .89 |
| Large fixed | .03 | .18 | .38 |

**The test's size is determined by the bandwidth rule.**

### 4.2 Power (ρ_u ∈ {.95, .98}, normal errors, I(1) d, no drift)

Each pair is raw / size-corrected. σ_u is the stationary sd of u.

| Alternative | FM-OLS (Andrews), ρ = .95 | ρ = .98 | D-OLS, ρ = .95 (size-corrected) | ρ = .98 (size-corrected) |
|---|---|---|---|---|
| Intercept shift 1σ_u | .022 / .020 | .031 / .034 | .021 | .015 |
| Intercept shift 2σ_u | .040 / .039 | .077 / .081 | .025 | .025 |
| Intercept shift 4σ_u | .40 / .45 | .39 / .38 | .10 | .07 |
| Intercept shift 6σ_u | .84 / .88 | .75 / .75 | .47 | .25 |
| Slope shift (γ change, ≈ 1σ_u at mid-window) | .020 / .017 | .024 / .026 | .018 | .027 |
| Loss of cointegration (u becomes a random walk) | .062 / .058 | .039 / .043 | .031 | .027 |
| Variance ×2 only | .017 / .017 | .015 / .018 | .015 | .018 |

For comparison, at ρ = .8 FM-OLS power is .92 against a 4σ_u shift.

**Reading:**
- FM-OLS with the Andrews bandwidth holds size within the theory's domain. The plug-in
  bandwidth grows with persistence, which inflates ω̂ and shrinks the detector.
- At PPP-like persistence it then has **essentially no power** against a coefficient
  shift, a loss of cointegration, or level shifts below about 4σ_u.
- Every bandwidth rule that gives power is grossly oversized.
- Variance-only changes are not detected. Under this design that is a property, not a
  defect.

## 5. Japanese CPI provenance (read-only)

**Verified:**
- `raw/jp_cpi.csv` checksum is unchanged (`a40f9238981868e6…`).
- **Every observation from 1970-01 to 2026-07 (559 months) equals one constant times a
  one-decimal index on the 2025 = 100 scale.** The maximum distance from the 0.1 grid is
  below 1e-4 in every sub-period. The implied source levels:

  | Date | Level |
  |---|---|
  | 1981-01 | 67.4 |
  | 2024-12 | 98.9 |
  | 2025-01 | 99.3 |
  | 2026-07 | 102.0 |
  | 2025 annual mean | 100.008 |

- The file's 2025 annual-average change (3.19 %) matches the official 2020-base figure:
  111.9 (2020 = 100), "up 3.2 %" (Statistics Bureau, released 2026-01-23).
- This matches the Statistics Bureau's stated method: the 2025-base index from January
  2025, and earlier indices "converted into the 2025-base and linked".

**Conclusion on linking.** The frozen vintage is BIS's constant rescaling (to 2010 = 100) of
the **official 2025-base linked series**, with the converted pre-2025 indices rounded to
one decimal. There is **no splice inside the H1b window**: one scale throughout.
Revision 3/4 assumption A9 (a possible in-window base splice) is **resolved**.

**Residual limitations:**
- The conversion rounds pre-2025 levels to 0.1 on an index of about 67–99. That is level
  quantization of at most ≈ 0.07 %, so monthly rates can differ slightly from originally
  published rates. This is negligible for x.
- I could not obtain the official month-by-month 2025-base table: e-Stat listings render
  client-side and its API needs a registered key. The identification therefore rests on the
  exact one-decimal-grid structure plus one annual cross-check, not on a month-by-month
  match.
- Pre-2025 months now carry converted-and-rounded values rather than the originally
  published ones. Any earlier vintage of this file would differ slightly; none is
  frozen, so this only matters for documentation.

## 6. GO/NO-GO

**NO-GO**, for three independent reasons. Any one would suffice.
1. **Theory.** Published WW requires driftless I(1) regressors with Ω_vv > 0. KAGURA's x
   drifts, and d may be I(0). Both lie outside the theory (§2). Simulation confirms the
   consequences: I(0)-d cells are oversized (FM .043–.077, failing the screen in 7 of 8
   cells, with one ambiguous), and the drift cells are degenerate (rejection ≈ 0).
2. **Size vs power.** Where size is controlled (FM-OLS, Andrews bandwidth, I(1) d, no
   drift), it comes with near-zero power at ρ ≥ .95 against every H1b-relevant
   alternative short of a ≥ 4σ_u level shift. Every rule with power is oversized
   (.14–.94).
3. **Method ambiguity.** The published detector (eq. 12) disagrees with the authors' own
   tables and software, and the published critical-value appendix could not be verified.

Per decisions 2–3: H1b confirmatory = **NOT ASSESSABLE**, the 0.025 stays unused, and no
fourth candidate is pursued.

**What can still be reported (exploratory, labelled as such, unchanged from revision 3):**
the ARDL long-run estimates, AK P and R with their simulated null rejection rates, and the
post-2022 residual path.

## 7. Items for the reviewer

- Confirm NO-GO and the option-D classification for revision 5 (the final ADR 0008 text).
- Note A9 as resolved (§5).
- Note the correction to the revision-4 Table 10 citation (§1).
