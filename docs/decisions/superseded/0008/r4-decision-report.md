# ADR 0008 — Revision 4 Decision Report: Confirmatory-Test Blocker

Date: 2026-10-23. **Status: for review. Not frozen, not implemented.**

No historical H1b regression or test was run. No data, ADR or repository file was
changed, and nothing was committed. No simulation was executed for this report: the
pilot in §5 is a proposal only.

## 1. What revision 3's "option D" was

Revision 3 §3.6 option D:
- declares H1b's confirmatory test **infeasible at T = 492, m = 55**;
- reports AK P, AK R and the post-2022 residual path as **pre-specified exploratory**
  statistics, each next to its simulated null rejection rate;
- leaves H1b's 0.025 unused, with no reallocation.

**Option D is not a test.** It is a classification: H1b becomes NOT ASSESSABLE
(confirmatory) plus exploratory reporting. This is exactly your decision 6 fallback. So D
is **adopted as the pre-committed fallback**, not as the method. Revision 3's option E (a
bootstrap of AK P) is superseded by the comparison below. The candidate set changed
because I read the literature, not because of any data.

## 2. Alternatives considered (at most three)

**Ground rule.** Candidates were screened for (a) a hypothesis matching H1b, (b) asymptotics
that fit a fixed post-period fraction rather than a fixed m, and (c) a primary source I
could read. No H1b statistic has been computed, so no candidate was chosen with knowledge
of an outcome.

### A. Wagner–Wied cointegration monitoring, applied retrospectively

**Reference.** Wagner, M., and Wied, D. (2017), "Consistent monitoring of cointegrating
relationships: The US housing market and the subprime crisis", *Journal of Time Series
Analysis* 38(6), 960–980.
- **Read in full:** the discussion-paper version, "Monitoring stationarity and
  cointegration", SFB 823 DP 23/2014 (TU Dortmund Eldorado).
- **Not read:** the published JTSA version (paywalled). Differences between the two are
  unverified.

| Aspect | Content |
|---|---|
| Hypothesis | **H0:** the regression errors are I(0) over the whole sample, with the cointegrating parameters estimated on the calibration period 1,…,[mT] only. **H1:** from some point after [mT], the errors become I(1) (cointegration breaks down). The DP also derives consistency against breaks in the deterministic components (intercept) after [mT], and simulates power against slope breaks. |
| Statistic (DP eqs. (36)–(38), (10)) | Ĥ(s) = ω̂⁻²_{u·v}·[T⁻¹ Σ_{i=[mT]+1}^{[sT]} (T^{−½} Ŝ⁺_i)² − T⁻¹ Σ_{i=1}^{[mT]} (T^{−½} Ŝ⁺_i)²], where Ŝ⁺ are partial sums of FM-OLS or D-OLS modified residuals, with the parameters and ω̂²_{u·v} from the calibration period only. Reject if sup_{s∈(m,1]} \|Ĥ(s)/g(s)\| > c, with g(s) = s³ (intercept case). The limit is a functional of Brownian motions depending on k and m (eq. 38). |
| Critical values | DP Appendix B, Table 10 (FM-OLS/D-OLS, two regressors, intercept). 97.5 %: 0.11 at m = 0.89, 0.10 at m = 0.90, 15.62 at m = 0.50. The stationarity tables are stated to use random walks of length 1,000 and 1,000,000 replications; the cointegration tables are simulated "analogously". **IM-OLS needs different values** (Remark 7; Table 11). All values verified from the DP text. |
| Verified assumptions | Assumption 1 (deterministics); Assumption 3: η_t = (u_t, v_t')' satisfies an FCLT, with v_t = ΔX_t; Ω_vv > 0, which excludes cointegration among the regressors. Serial correlation and endogeneity are handled by the modified OLS plus long-run variance estimation. **Remark 9:** nonstationary volatility (time-varying unconditional variance) causes asymptotic size distortion. |
| I(1) / I(0) regressors | Requires **I(1), non-cointegrated regressors**. A stationary d violates Ω_vv > 0. |
| Persistence and heteroskedasticity | DP simulations, T = 200 and 500, 10,000 replications, nominal 5 %: "larger values of ρ₁, ρ₂ lead to increasing size distortions", reduced by a larger m and larger T; IM-OLS distorts least. The **largest ρ studied is 0.9**, while the PPP-type residual persistence relevant here is ≈ .98. Conditional heteroskedasticity is allowed only if the FCLT holds; unconditional variance shifts distort (Remark 9). |
| Fit to T = 492, m = 55 | The calibration fraction is 492/547 = 0.8995, inside the tabulated range 0.10–0.90 but at its edge, where the critical values are tiny (two decimals) and must be re-simulated. The monitoring period is a **fixed fraction** asymptotically, the regime AK's fixed-m theory lacked. |
| Variance-only rejection | **Yes, possible but not consistent.** A window variance increase inflates the window partial sums relative to the calibration long-run variance (Remark 9 logic). Its rejection rate must be simulated. |
| Validation | Feasible: re-simulate the critical values and reproduce Table 10 entries; null size on the revision-3 grid; the matched gap enters as an omitted increment in the partial sums. |
| Meaning of H1b | **Preserved.** The test asks whether the 1981–2021 relation, estimated **without** post-2022 data, still holds after 2022: errors stay I(0) and the intercept and slopes are unchanged. This is closer to H1b than AK P, whose β̂ uses the window data. |

### B. Known-date coefficient-change Wald test at 2022-01 in a cointegrating regression

**Reference.** Kejriwal, M., and Perron, P. (2010), *JBES* 28(4), 503–522, with the
companion paper (2008), *J. Econometrics* 146(1), 59–73.
- **Not verified.** Both PDF downloads were blocked (they returned HTML), so the
  assumptions and the known-date limit theory were **not read**.

| Aspect | Content (unverified unless noted) |
|---|---|
| Hypothesis | Constant cointegrating vector (intercept and slopes) vs a shift at the pre-specified boundary 2022-01 |
| Regressors | I(1), optionally with I(0) regressors (stated in the RePEc abstract); D-OLS-based |
| Persistence | Requires long-run variance estimation; at ρ ≈ .98 severe distortion is expected |
| T, m | Post-break slopes are estimated from 55 observations with leads and lags, so identification is weak. The unknown-date sup-Wald versions use trimming that excludes the last 10 %. |
| Variance-only | Asymptotically not, if the long-run variance is regime-robust |
| Meaning | Partly preserved: it detects a coefficient change, not a loss of cointegration |
| **Status** | **Not eligible to be preferred:** the primary source is unverified |

### C. Model-based (sieve) bootstrap null distribution for AK P

**Reference.** Chang, Y., Park, J. Y., and Song, K. (2006), "Bootstrapping cointegrating
regressions", *J. Econometrics* 133(2), 703–739. **Not read.** The title and venue come
from RePEc.

| Aspect | Content |
|---|---|
| Hypothesis | As AK (2006) H0 and H1, including variance-only changes |
| Basis | Their bootstrap targets cointegrating-regression statistics. Applying it to an end-of-sample sum of squares is an **unpublished extension** |
| Persistence | Sieve/AR bootstraps are known to be fragile near a unit root (general knowledge; not verified here) |
| Variance-only | **Yes**: P is a sum of squared residuals |
| **Status** | **Not eligible:** no verified theory for this statistic. Adopting it would come close to introducing a method to rescue a conclusion. |

## 3. Preferred candidate

**A (Wagner–Wied) is the only candidate eligible for piloting. It is not yet preferred for
adoption.**

Basis, independent of any H1b result:
1. its null and alternatives match H1b (stable cointegration vs breakdown or coefficient
   change after a calibration period);
2. its asymptotics treat the post-period as a fixed fraction, unlike AK's fixed m;
3. the parameters come from the calibration period only;
4. the primary source (DP version) was read, and the critical values are published and
   reproducible.

**Expected-failure disclosure.** The authors' own evidence stops at ρ = 0.9 and already
shows distortions rising with persistence. At ρ ≈ .98 the pilot may well fail. If it
fails, the result is option D (NOT ASSESSABLE). **No fourth candidate will be sought.**

**Open choice: modified-OLS estimator.**

| Estimator | For | Against |
|---|---|---|
| **IM-OLS** (recommended for the pilot) | Least distortion per WW | Needs Vogelsang–Wagner (2014), not read, and its own critical values |
| FM-OLS | Standard | Kernel and bandwidth choices |
| D-OLS | Simplest | Worst size per WW |

Recommendation: **pilot FM-OLS and D-OLS** (critical values verified, Table 10). Pilot
IM-OLS only after verifying Vogelsang–Wagner (2014) and the IM-OLS table.

## 4. What does not change

- The bounds gate V2 still precedes the breakdown test, with the full-procedure
  calibration you approved (decision 2).
- The tax-impulse lag propagation (decision 3) and the pre-period stability assessment
  (decision 4) carry over from revision 3.
- WW also **maintains** I(0) errors in 1981–2021, so revision 3 §4's interpretation rule
  for an unstable pre-period applies unchanged.
- Simulation tolerances are diagnostics (decision 5).

## 5. Proposed synthetic pilot for A (not executed)

**Step 0: critical values.**
1. Simulate the eq. (38) limit for k = 2, intercept, g(s) = s³, using random walks of
   length 1,000 and 200,000 replications.
2. **Check:** reproduce Table 10 at m = 0.50, 0.75 and 0.90 (97.5 %: 15.62, 0.98, 0.10)
   within MC error. Because the table has two decimals, the m = 0.90 check is coarse.
3. Then simulate c at m = 492/547 with 1,000,000 replications. Report its MC se by
   batching.

**Step 1: implementation.**
- D-OLS with leads = lags = 2 (fixed). FM-OLS with a Bartlett kernel and
  bandwidth ⌊4(T_cal/100)^{2/9}⌋ (fixed rule, as ADR 0006).
- ω̂²_{u·v} from calibration OLS residuals stacked with ΔX.
- Unit tests: the detector equals a direct loop, and recovers the coefficients on
  noiseless data.

**Step 2: null size.**
- T_cal = 492, window = 55, with and without the gap at window position 46.
- Cells: ρ_u ∈ {0, .8, .95, .98} × {normal, GARCH(.10, .85)} × d ∈ {I(1), I(0) AR(.97)}.
  That is 16 cells, each run with and without the gap.
- R = 2,000 per cell; the MC se at .025 is ≈ .0035.

**Step 3: power (diagnostic).**
- Cells: ρ_u ∈ {.95, .98}, normal.
- Alternatives: intercept shift of 1 and 2 σ_u; ramp to 2 σ_u; u becomes a random walk;
  **variance ×2 only**.
- R = 1,000; raw and size-corrected.

**Seeds and tooling.**
- `SeedSequence([20261024, *cell_key])`, NumPy PCG64.
- Standard-library process pool; no new dependency.

**Cost.** Steps 0–3 should take minutes on this machine. This is estimated from revision 3
timings, not measured.

**Pre-registered reading (diagnostic, decision 5).** If in any I(1)-d cell with
ρ_u ≥ .95 the size is clearly above the Bradley 1.5α bound (lower 99 % Clopper–Pearson
bound > .0375), A is rejected and **H1b is NOT ASSESSABLE**. A pass licenses only the full
grid, not adoption.

## 6. 2025-base Japanese CPI and the frozen file

**Verified facts:**

| Fact | Source |
|---|---|
| The 2025-base CPI was first released in August 2026 | Statistics Bureau "Main points of the 2025-base revision" |
| The 2025-base index runs from **January 2025 retroactively**; indices before December 2024 are converted and linked; published rates of change for earlier bases are used unmodified | Same page |
| The 2020-base CPI continues to be published until December 2026 | Same page |
| BIS documentation lists Japan from January 1970 as "Consumer Price Index (2025=100)" | BIS long CPI documentation (its own revision date not established) |
| The frozen `jp_cpi.csv` was downloaded 2026-09-15, ends at 2026-07, is BIS-rebased to 2010 = 100, has empty `BREAKS`/`OBS_PRE_BREAK`, and its bytes are unchanged | Manifest; checksum re-verified |

**Unverified (from a secondary search summary only):** the exact first-release date
(national July 2026 data on 2026-08-21).

**Unresolved provenance:**
- whether BIS had applied the 2025 base to Japan before 2026-09-15;
- if so, how BIS linked the series (ratio splice at 2024-12 is the likely method,
  unverified);
- whether the frozen 2025-01…2026-07 values therefore carry 2025-weight inflation rates.

**Implications:**
- Linking preserves pre-2025 rates of change, so a rebasing alone changes the level of x
  by a constant. The regression constant absorbs that.
- The only substantive risk is **different monthly rates for 2025-01…2026-07**: window
  positions 37–55, entirely inside the test window and outside the pre-period.
- Effect: a small level discrepancy in x at the end of the window. Its size is unknown;
  it equals the cumulative difference between 2020-base and 2025-base inflation over 19
  months.
- It cannot affect the bounds gate or the pre-period estimates. It could only slightly
  move the window residuals.

**Proposed resolution (read-only, frozen bytes untouched):**
- compare the frozen file's 2025 annual-average change and its 2026 monthly changes with
  the Statistics Bureau's published figures on each base;
- record which base the frozen vintage reflects, as a provenance note in the ADR;
- if neither matches, keep assumption A9 with that finding.

## 7. Decisions requested

1. Approve A (Wagner–Wied, FM-OLS/D-OLS) as the **only** candidate to pilot, with option D
   as the pre-committed fallback.
2. Approve the §5 pilot design and its stop rule.
3. Approve verifying the published JTSA 2017 version (library access needed) before any
   adoption, and checking for differences from the 2014 DP.
4. Approve the §6 read-only provenance check.
