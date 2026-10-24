# ADR 0008 — Revision 3: Statistical Validation Design (delta to revision 2)

Date: 2026-10-23. **Status: PROPOSED (revision 3). Not frozen.** This document records what
revision 2 changes and why. Anything not mentioned stands as in
`docs/decisions/0008-h1b-long-run-protocol.PROPOSED-r2.md`.

All evidence below comes from **synthetic-data pilots only**. No historical H1b regression,
bounds statistic or Andrews–Kim (AK) statistic was computed. The only real-data work was
on CPI files, as disclosed in §6 (the CPI-only descriptives). The pilot code is in the
review scratchpad under `sim/`. It is not in the repository.

## 0. Summary

| Status | Item |
|---|---|
| **Settled** | D1 (m = 55, sample ends 2026-07); D2 (the joint s/x/d breakdown is the claim, with γ as a wording qualifier); 1981–2021 pre-period; PSS reference values verified; statsmodels `bounds_test` not used; matched-gap handling (validated, §3.3); CPI definitions and frozen bytes (§6) |
| **Proposed, needs approval** | Calibrating the bounds gate by full-procedure simulation (§2); Monte Carlo decision rule (§3.5); pre-period stability assessment (§4); tax-dummy form (§6.3); compute plan (§7) |
| **Blocker** | **B1. The AK P test cannot deliver a 2.5 % test at T = 492, m = 55 (§3).** This is not an implementation error: the implementation reproduces AK Table 1. It is a structural limit of subsampling critical values when T/m ≈ 9. The primary H1b test must be re-decided before anything else can be frozen. |

## 1. Verified references (new this revision)

- **PSS (2001), *JAE* 16(3), published PDF (DOI 10.1002/jae.616), Case III, k = 2,
  α = 2.5 %:**

  | | I(0) | I(1) | Source |
  |---|---|---|---|
  | F | 4.41 | 5.52 | Table CI(iii), p. 300 |
  | t | −3.13 | −3.80 | Table CII(iii) |

  PSS state the tables use T = 1,000 and 40,000 replications. (Revision 2's "from memory"
  F values were correct.)
- **AK (2006), Table 1.** The P test at nominal .05, T = 250, m = 10. The paper reports
  eight-model averages of .057, .051 and .048 at ρ = 0, .4 and .8.

## 2. Bounds test calibration

### 2.1 Pilot results (synthetic data, n = 480, design dummies, homoskedastic F and t)

| Check | Result |
|---|---|
| PSS asymptotic replication (n = 1,000, 200k replications) | F: 4.389 / 5.482 vs 4.41 / 5.52. t: −3.118 / −3.783 vs −3.13 / −3.80. **Pass** (all within ±0.04) |
| Fixed lag order, i.i.d. null, upper bound, (1,1,1)…(12,12,12) | F 5.33–5.39, t −3.70 to −3.75: nearly invariant to lag order |
| Fixed (1,1,1), nuisance DGPs | GARCH: F 5.52, t −3.79. Drift in x: F 5.63, t −3.87. t₅: unchanged. Under-fitted dynamics: F 6.24 |
| Joint gate (F **and** t beyond their own 2.5 % I(1) values), fixed lag order | Null pass rate 0.017–0.018 (upper DGP) and ≈ 0.013 (lower). It is conservative because F and t are imperfectly correlated. |
| **Full BG-filtered AIC selection** (800 reps per DGP, 0.07 s per rep) | Critical values conditional on the selected order (fixed-order simulation) give marginal null rejection of **F 0.029–0.045 and t 0.030–0.039**, and a joint rate of 0.022–0.028. The full-procedure 97.5 % quantiles are **F 5.49–6.04 and t −3.80 to −3.95** (iid, dyn, GARCH, drift). |

**Conclusion:** a fixed-lag simulation does **not** represent the BG-filtered AIC
procedure. Lag selection is a pretest that inflates F, so calibrating at the realized lag
order makes the gate too liberal.

### 2.2 Proposed calibration (replaces revision 2 §6.3)

**What is simulated.** The entire procedure:
- data generation;
- all 1,728 lag orders;
- the BG(12) filter;
- the AIC choice;
- F and t at the selected order;
- the same constant, 11 centred seasonal dummies and tax dummies as the real design.

**Null DGPs.** Each is run under both bounds. Upper: x and d I(1). Lower: x and d I(0).

| DGP | Content |
|---|---|
| iid | Gaussian |
| dyn | AR(1) 0.3 in Δs, AR(1) in Δx with a deterministic seasonal, AR(1) in Δd |
| garch | GARCH(1,1), (0.10, 0.85) |
| drift | x has drift/sd = 0.5 |
| t5 | t₅ errors |
| varbreak | error variance ×2 over the first 108 months |

**Critical values.** For each bound, the gate uses the **most conservative** quantile
across the six DGPs: the largest F₀.₉₇₅ and the most negative t₀.₀₂₅. This is fixed before
any real data are touched, and requires no knowledge of the true nuisance process.

**Replications.** 20,000 per DGP and bound. The MC standard error of a 97.5 % quantile is
reported (sectioning into 20 batches).

**Gate.** Unchanged: F > F_{I(1)} **and** t < t_{I(1)}.

**Heteroskedasticity check.**
- Report the joint null pass rate for each DGP at the chosen critical values.
- Acceptance follows the §3.5 rule (true rate ≤ 0.0375).
- No HAC statistics are used.

**Known limit.** The gate's **power** is low at PPP-like persistence (§3.4). An outcome of
"not assessable" is the most likely one, and it must be disclosed as an expectation.

## 3. Andrews–Kim validation

### 3.1 Implementation is correct

- **Fast vs direct.** The fast version (Gram-matrix down-dating) matches a direct loop to
  2e-12, with and without the gap.
- **AK Table 1 reproduction.** 5,000 replications per model, eight models:

  | ρ | This run (MC se) | Published | Difference |
  |---|---|---|---|
  | 0 | .0554 (.0011) | .057 | −.0016 |
  | .4 | .0515 (.0011) | .051 | +.0005 |
  | .8 | .0497 (.0011) | .048 | +.0017 |

  Every difference is under 2 MC standard errors. **Pass.**

### 3.2 Size at our design (T = 492, m = 55, nominal 2.5 %, 4,000 replications, MC se ≈ .003–.005)

| ρ_u | normal, no gap | normal, gap | GARCH, no gap | GARCH, gap |
|---|---|---|---|---|
| 0 | .055 | .058 | .092 | .092 |
| .80 | .049 | .047 | .069 | .071 |
| .95 | .056 | .053 | .063 | .066 |
| .98 | .071 | .074 | .073 | .080 |
| .99 | .099 | .107 | .099 | .098 |

Other cells at ρ = .95 with the gap:

| Cell | Size |
|---|---|
| endogeneity .5 | .058 |
| t₅ | .048 |
| no drift | .062 |
| d stationary | .052 |
| pre-period variance break | .029 (.053 at ρ = .98) |

These are **real distortions, not MC noise.** Every cell except the pre-period
variance-break cell is 5–20 MC standard errors above .025.

**Why it happens.** Diagnostic with 4,000 replications:

| m | ρ = 0, normal | ρ = .95, normal | ρ = 0, GARCH |
|---|---|---|---|
| 10 | .032 | .042 | .037 |
| 25 | .034 | .042 | .052 |
| 55 | .059 | .050 | .085 |

An oracle version that uses the **true** β distorts just as much (.065 at m = 55, ρ = 0).
So the problem is not estimation of β. It is the empirical 97.5 % quantile of 438
overlapping window sums, which carry only about T/m ≈ 9 independent pieces of information.
This is AK's fixed-m asymptotics failing at m/T = 0.11, well outside their evidence
(m ≤ 10, m/T ≤ 0.1, ρ ≤ .8).

### 3.3 Matched gap: validated

Across the ten cells, gap minus no-gap differences lie in [−.003, +.008]. That is under
about 1.3 MC standard errors of the difference, with no consistent sign. The singular-Ω
extension does not materially change size. **Settled**, subject to B1.

### 3.4 Combined ARDL gate + AK (3,000 replications per cell; gate at the true lag order (1,1,1))

| Pre-period | ρ_u | Gate passes | AK rejects | False "supported" |
|---|---|---|---|---|
| Cointegrated throughout (AK H0) | .80 | 1.00 | .053 / .072 | **.053 / .072** |
| | .95 | .45 / .46 | .060 / .063 | **.043 / .046** |
| | .98 | .084 / .087 | .069 / .065 | .014 / .013 |
| | .99 | .036 / .044 | .100 / .101 | .007 / .010 |
| No cointegration (u a random walk) | 1 | .023 / **.038** | .136 / .138 | .006 / .010 |

Each pair is normal / GARCH. The gate's power depends on the DGP's signal-to-noise ratio,
so these pass rates are illustrative.

**Reading:**
- Where the gate has power (ρ ≤ .95), the procedure's false-support rate is **1.7–2.9× the
  2.5 % budget**.
- Where it is within budget (ρ ≥ .98), that is only because H1b is almost never
  assessable.
- With homoskedastic, iid-calibrated critical values, the gate itself exceeds 2.5 % under
  GARCH when there is no cointegration (.038). §2.2 addresses this.

### 3.5 Monte Carlo uncertainty vs distortion (applies to every simulated acceptance check)

- **Tolerance on the true rate.** Use Bradley's (1978) liberal criterion, 1.5α = 0.0375,
  instead of revision 2's ad hoc 0.035. It is a standard, citable tolerance. The paper was
  not re-read this session, so the citation is to be verified.
- **Decision on simulated rates.** Use a sequential rule:
  - R = 10,000 per cell;
  - **pass** if the upper 99 % Clopper–Pearson bound ≤ 0.0375;
  - **fail** if the lower bound > 0.0375;
  - otherwise raise R to 40,000 and decide by the point estimate.
  
  So MC noise alone neither passes nor fails a cell.
- **The ρ rounding rule (revision 2 §8.4) is withdrawn.**
  - The AR(1) coefficient of LS residuals is biased downward, so rounding up does not
    guarantee coverage.
  - Any persistence-dependent acceptance should take the **worst case over a pre-registered
    set of ρ values**, or over a set derived from a bias-corrected upper confidence bound.
  - This is moot until B1 is resolved, because size fails at every ρ.

### 3.6 B1: the AK P test is infeasible at α = 0.025 here

- The smallest attainable AK p-value is 1/438. Its null probability is
  P(P > every P_j), which in the pilot is **.035–.087 in every cell**: .037 (ρ = 0, normal)
  up to .087 (ρ = .99, GARCH).
- So **no** AK critical value, nominal or size-corrected, achieves 2.5 % at T = 492, m = 55.
- The R statistic uses the same subsample quantile and inherits the same limit.

Options for the reviewer (my recommendation is marked):

| Option | Keeps α = .025 | Cost / risk |
|---|---|---|
| A. Keep AK P as primary at its attainable size | No (≈ 5–10 %) | Violates ADR 0006 §8. **Not admissible.** |
| B. Shorten the window to restore T/m | Not clearly (the floor ≈ 1/(T/m)) | Changes the approved question (D1). Even m = 10 gives ≈ .03–.04. Not admissible. |
| C. Model-based null for P (for example a sieve or AR-GARCH bootstrap of the pre-period residuals) | Possibly | A new method that needs literature verification and its own validation on this grid. It is known to be fragile near a unit root (ρ ≈ .98–.99). |
| **D. Recommended:** declare H1b's confirmatory test **infeasible at these dimensions**. Report AK P, R and the window residual path as **pre-specified exploratory** statistics, alongside their simulated null rejection rates. | n/a | H1b's 0.025 goes unused, and cannot be reallocated (ADR 0006 §8). This is honest, and consistent with research principle 8. |
| E. Investigate C first, and fall back to D if its pre-registered validation fails | Possibly | Adds one verification round. A reasonable choice if a confirmatory H1b matters. |

Revision 3 recommends **D, or E with D as the pre-committed fallback**. Either choice
changes revision 2 §8–§9 and requires a revision 4 before any freeze.

## 4. Pre-period stability

**What the AK result requires (Assumption S and H0):**
1. u_t stationary and strong-mixing over 1…T;
2. β constant over 1…T;
3. any stationary regressors exogenous.

(1) and (2) are the maintained hypothesis. If they fail, the subsample statistics describe
an unstable history rather than the null distribution.

**Interpreting a rejection when the pre-period was already unstable.**
- Under pre-period instability, a rejection means only this: the 2022–26 residuals, from a
  fit to all 1981–2026 data, were larger than about 97.5 % of historical 55-month windows.
- It does **not** show that a stable relationship broke down. There was none to break.
- Pre-period variance breaks make the test **conservative** (pilot: .029 vs .053 at
  ρ = .95).
- Pre-period coefficient breaks contaminate β̂ in an undetermined direction.
- Wording in that case: "the post-2022 deviation is unusually large relative to
  1981–2021", never "breakdown".

**Proposed pre-registered assessment.** Secondary and descriptive. A finding of
instability triggers this wording only.
1. ARDL long-run (θ, γ) estimated separately on equal halves, 1981-01…2001-06 and
   2001-07…2021-12. The split is mechanical, not data-chosen. Report a Wald test of
   equality (HAC), and label it descriptive.
2. The time profile of the 438 subsample statistics P_j (AK's own objects). Report the
   share of the largest 5 % that falls in 1981–1989.
3. Hansen (1992) Lc parameter-instability test for cointegrating regressions, **only if**
   its statistic and critical values are verified from the paper before freezing (not done
   this session).
4. A placebo AK on a pseudo-window inside the pre-period is **not** proposed: it inherits
   B1.

## 5. Gap: settled

Matched-gap complete case as in revision 2 §5, validated in §3.3.

## 6. CPI verification

### 6.1 Seasonal adjustment

| Source | What it shows |
|---|---|
| BIS SDMX DSD `BIS_LONG_CPI` (fetched 2026-10-23) | Dimensions FREQ, REF_AREA, UNIT_MEASURE. Attributes TIME_FORMAT, BREAKS, COVERAGE, DECIMALS, OBS_CONF, OBS_PRE_BREAK, OBS_STATUS, UNIT_MULT, TITLE_TS. **There is no seasonal-adjustment dimension or attribute.** |
| BIS series page | Title "Japan Consumer price indicators, Index, 2010 = 100" |
| BIS documentation | Japan from Jan 1970 = Statistics Bureau "Consumer Price Index (2025=100)" |

- **NSA status rests on the data:** calendar-month effects, HAC Wald p ≈ 6e-34. It is not
  stated by the source. (The Statistics Bureau page mentions X-13ARIMA-SEATS for its own
  seasonally adjusted series, but not which series BIS takes.)
- **US:** FRED `CPIAUCSL` is SA.

### 6.2 Base-year change (Statistics Bureau, "Main points of the 2025-base revision")

- The 2025-base CPI was released from **August 2026**. The national monthly report has
  been on the 2025 base since 2026-08-21 (July 2026 data).
- The 2025-base index runs **from January 2025 retroactively**. Indices before December
  2024 are converted and linked.
- Published rates of change for earlier bases are kept unmodified.
- The frozen file was downloaded on **2026-09-15, after the switch**. Whether BIS had
  already applied the new base is **unverified**. If it had, window months 37–55
  (2025-01…2026-07) use 2025 weights and earlier months older weights. That is an
  in-window splice of unquantified size; the usual magnitude is tenths of a percentage
  point per year. It stays as assumption A9. The files are **not** re-downloaded.

### 6.3 Consistency of controls with the conditional ARDL

**Seasonal dummies.**
- If x_t = x_t^{sa} + S_t, with S deterministic and 12-periodic, then π_x x_{t−1} and
  ω_j Δx_{t−j} add only 12-periodic terms. The 11 centred dummies plus the constant absorb
  those **exactly**.
- This is consistent with Case III: an unrestricted intercept, extended to unrestricted
  seasonal intercepts.
- **But** Japan's seasonal pattern is not stable. The amplitude roughly halved after 2000:
  HAC Wald test of equal patterns, p = 2e-8. This is a CPI-only finding, disclosed here.
- So the dummies leave a stationary residual seasonal component in x. That affects
  efficiency, not validity, because the bounds test allows I(0) components.
- **Add sensitivity R10:** seasonal dummies interacted with a linear trend. This is a
  pre-specified, data-independent form.

**Tax dummies: revision 2 was incoherent.**
- A tax step τ·Step_e in x enters the UECM as:
  - π_x·τ·Step_{e,t−1} through the level term (a step, not an impulse);
  - ω_j·τ·I_{e+j,t} through Δx_{t−j}, for j = 0…q_x−1.
- An impulse at e alone removes only the j = 0 spike.

Two coherent options:

| Option | What it does | Consequence |
|---|---|---|
| **(i) Recommended** | Keep x tax-inclusive (CPI as published). Use impulses I_{e+j}, j = 0…q_x−1, varying with the candidate q_x in the selection. | The long-run level effect of tax stays in x by definition. Up to 4·q_x rows are neutralized (≤ 48 of 480). |
| (ii) | Tax-adjusted x (revision 2's R9) as primary, with no dummies | Uses a generated regressor based on the data's own excess jumps |

Either way, the bounds simulation (§2.2) must use the same dummy structure.

### 6.4 Frozen bytes

SHA-256 was re-computed 2026-10-23 for the ten frozen files: the eight in ADR 0006 §9.2
plus `us_cpi.csv` and `jp_cpi.csv` from revision 2. All match. (Comparison was by
12-character prefix; full hashes were computed.) Other raw files, such as `brent.csv`, are
not part of any freeze. Nothing was re-downloaded or written.

## 7. Computational feasibility (measured on this machine: Apple M2 Max, 12 cores)

| Component | Unit cost | Full grid | CPU time | Wall time, 10 workers |
|---|---|---|---|---|
| AK null grid (revision 2 §8.3: 120 cells + violation cells) | 0.7 ms per rep (normal); 2.7 ms (GARCH; Python recursion) | 130 cells × 10k | ≈ 1.2 h | ≈ 8 min |
| AK power (5 alternatives × 120 cells × 5k) | as above | 3M reps | ≈ 1.5 h | ≈ 10 min |
| Bounds full-procedure calibration (6 DGPs × 2 bounds × 20k) | 0.07–0.08 s per rep | 240k | ≈ 5 h | ≈ 30 min |
| Combined gate + AK (≈ 40 cells × 5k) | ≈ 0.08 s per rep | 200k | ≈ 4.5 h | ≈ 30 min |
| **Total** | | | ≈ 12 h | **≈ 1.5 h** |

**Coverage.** No reduction is needed. Revision 2's replication counts are affordable. The
bounds calibration can be raised to 100k per DGP and bound (≈ 2.5 h wall) if the quantile
standard errors call for it.

**Approach.**
- NumPy PCG64, with seeds from `SeedSequence([20261023, *cell_key])`. Each result is then
  independent of worker scheduling.
- `concurrent.futures.ProcessPoolExecutor` from the standard library: no new dependency.
- Per-replication outputs saved (`.npz`), with summary CSVs and NumPy/SciPy versions
  recorded.
- The `uv.lock` environment is used.

**Validation gates before any grid run:**
1. Fast AK vs direct (done);
2. AK Table 1 reproduction (done);
3. PSS asymptotic reproduction (done);
4. the F/t/BG functions vs statsmodels OLS (done; exact match);
5. unit tests committed with the implementation.

## 8. What makes H1b not assessable (revision-3 list)

1. V1–V4 and V6 as in revision 2, with V2 at the §2.2 critical values.
2. The bounds gate fails the §3.5 size check under any null DGP in §2.2.
3. **The confirmatory breakdown test fails its pre-registered size check (§3.5) at the
   design dimensions. Under the current AK P test this holds already (B1), so H1b is not
   confirmatorily assessable unless option C or E succeeds.**

## 9. Blockers before revision 4 can be frozen

| # | Blocker | Needed from the reviewer |
|---|---|---|
| **B1** | AK P cannot attain 2.5 % at T = 492, m = 55 | Choose D or E (§3.6) |
| B2 | Bounds calibration method | Approve §2.2 (full procedure, max over the six DGPs) |
| B3 | Tax-dummy form | Choose (i) or (ii) (§6.3) |
| B4 | Stability assessment | Approve §4. If item 3 is wanted, the Hansen (1992) Lc test must be verified from the paper first. |
| B5 | Bradley criterion and the sequential MC rule | Approve §3.5. The Bradley (1978) reference must be verified. |

**Not blockers:**
- A9 (the 2025-base splice) stays an assumption.
- The gate's low power at high persistence is disclosed, not fixed.

## 10. Reproduce the pilots

Scratchpad `sim/`, using the project's virtual environment:

| Script | Pilot |
|---|---|
| `ak_table1.py 5000` | AK Table 1 reproduction |
| `ak_size_pilot.py 4000` | AK size grid (§3.2) |
| `ak_diag.py` | Size by window length and oracle β (§3.2) |
| `ak_calib_pilot.py` | Attainable AK levels (§3.6) |
| `bounds_pilot.py 20000 800` | Bounds critical values and selection (§2.1) |
| `combined_pilot.py` | Combined gate + AK (§3.4) |
