# ADR 0008 — H1b Long-Run Levels Relationship: Testing Protocol

Date: 2026-10-23. **Status: PROPOSED (revision 2) — for independent review. Not frozen.**
Freezing = committing this file alone and pushing, before any levels regression, bounds
statistic, cointegration test or Andrews–Kim statistic is computed on real data
(as ADR 0006 §11).

Inherited from ADR 0006 §8, §10 and not changeable here:
- primary α = 0.025, with no reallocation;
- 2022-01 is a candidate boundary, not an assumed break;
- the §9.2 vintage, and no sample extension;
- the 2Y differential is primary.

## 1. Disclosure: what is already known

| Seen | Source | Bearing on H1b |
|---|---|---|
| Month-end USD/JPY ≈ 108 (2019-06) vs ≈ 160 (2026-08) at a similar 2Y differential | README, levels scatter | Anticipates a post-2022 breakdown |
| The 1980s levels cloud shifts around Plaza | Levels scatter | Pre-period stability is doubtful (§9, A4) |
| ADF/KPSS on s, d in levels and changes | `01_exploration` §6 | Integration order of s and d partly known |
| H1a: β 6.44 → 4.05 (inconclusive); rolling β declined before 2022 | `02_h1a_formal` | Any change may predate the boundary (§9, A5) |
| **Revision 2 (2026-10-23), CPI only, no H1b statistic:** Japan monthly log CPI changes have strong calendar-month effects (HAC Wald p ≈ 6e-34, 1981–2021) and US ones do not (p = 0.50); Japan tax-month changes 1.8–2.1 % (1989-04, 1997-04, 2014-04) and 0.34 % (2019-10); 2023-02 change −0.64 % vs a same-month median of −0.13 %; x fell 88.7 log-points over 1981–2021; excess tax-month jumps sum to 5.25 | Review session | Used for §4.3 only |

Not yet computed: any levels regression, ARDL or bounds statistic, long-run coefficient,
unit-root test on x or Δx, Andrews–Kim statistic.

## 2. Hypothesis

**Confirmatory claim (enters the H1 Bonferroni family at 0.025):** the long-run levels
relation among s, x and d that held over 1981-01…2021-12 did not hold over
2022-01…2026-07.

This is a claim about the **joint** relation. "Decoupling from the differential" is a
narrower reading. It may be used only under the γ qualifier (§7.2), and even then it is an
interpretation, not a tested claim.

Motivation: the real-interest-differential model (Dornbusch 1976; Frankel 1979). The only
language allowed is association language (ADR 0006 §3).

## 3. Variables, sample, data construction

| Symbol | Definition | Source (frozen) |
|---|---|---|
| s_t | 100·ln(USD/JPY), month-end, stored value (≤ 5 business days carried, as ADR 0006 R2) | `processed/monthly.csv` `usdjpy` |
| d_t | US 2Y − JGB 2Y, month-end, pp | `processed/monthly.csv` `diff_2y` |
| x_t | 100·[ln CPI_JP,t − ln CPI_US,t], **reference month** t | `raw/jp_cpi.csv`, `raw/us_cpi.csv` |

Expected signs (they are not gates; see §7.2): θ > 0 on x (PPP benchmark θ = 1), and γ > 0
on d.

**Samples (frozen):**

| | Months | Count |
|---|---|---|
| Pre-period (levels) | 1981-01 … 2021-12 | T = 492 |
| ARDL estimation (12 presample lags taken from 1981) | 1982-01 … 2021-12 | n = 480 |
| Test window | 2022-01 … 2026-07 | m = 55; 54 observed (2025-10 missing) |

**Why m = 55, not 56.** The frozen Japan CPI file ends at 2026-07. The national CPI for
2026-08 was released after the 2026-09-15 download. ADR 0006 froze the monthly sample to
2026-08 *at most*, so ending at 2026-07 shortens the sample and does not extend it.
The alternatives would have been to:
- impute x for 2026-08 (rejected: no imputed value in the primary);
- download a new vintage (rejected: this breaks the freeze).

**Hard checks (stop on failure):**
- the ADR 0006 checksums, plus the two below;
- exactly one missing x in 1981-01…2026-07, and it is 2025-10;
- no missing s or d.

Every row carries `x_observed: bool`.

| File | SHA-256 (re-verified 2026-10-23) |
|---|---|
| raw/us_cpi.csv | `f8ecddf53a9a9a74dda92c2c4204e6039466fcb744bc74171b73b5f6aac48119` |
| raw/jp_cpi.csv | `a40f9238981868e66ca40498ff7ee2d54b3e2d2a226d6d8bc1ed30034c3fe1d0` |

## 4. CPI series compatibility (verified 2026-10-23)

### 4.1 Definitions

| | US | Japan |
|---|---|---|
| Series | FRED `CPIAUCSL`: CPI-U, all items, U.S. city average | BIS long CPI `M.JP.628` |
| Coverage | All items | All items (BIS documentation: "Consumer Price Index", Statistics Bureau, from Jan 1970). Includes imputed rent. |
| Seasonal adjustment | **SA** (FRED) | **NSA**. The BIS documentation does not state it. The evidence: calendar-month effects, p ≈ 6e-34 |
| Base in file | 1982–84 = 100 | Rebased by BIS to 2010 = 100 (verified: the 2010 mean is 100.0). `BREAKS` and `OBS_PRE_BREAK` are empty. |
| Vintage | Current vintage; SA factors revised (ADR 0002) | Current vintage. BIS lists the national source as 2025 = 100. **Whether 2026 values in the frozen file reflect the 2025-base revision is not verified** (A9). |

The base years do not matter: the regression constant absorbs them.

### 4.2 Mixing SA and NSA

x_t carries Japan's seasonal pattern; the calendar-month effects in monthly changes range
from −0.41 to +0.37 pp.

- **ARDL:** Δx_t is strongly seasonal. The UECM includes 11 centred monthly dummies. These
  are stationary deterministic terms, so they do not enter the level restrictions. Their
  finite-sample effect on the bounds statistics is captured because the critical-value
  simulation (§6.3) uses the same regressor matrix.
- **AK static regression:** the seasonal part of x enters u_t as θ·(seasonal), at most a few
  tenths of a log-point. A 55-month window sums over ≈ 4.6 full cycles, so no dummies are
  used. A US NSA series is not in the frozen vintage, and X-13 would be a new binary
  dependency, so neither is used.

### 4.3 Consumption tax and administered prices

- Tax months 1989-04, 1997-04, 2014-04 and 2019-10 all fall in the pre-period. **Primary:**
  four impulse dummies in the UECM. Step dummies in levels are not used, because they
  change the bounds and AK null distributions.
- The tax steps leave about +5.3 log-points of non-PPP level shift in x (sum of the excess
  tax-month jumps over same-month medians; the 2019 step was partly offset by free
  preschool education). Against −88.7 log-points of total movement in x over 1981–2021,
  they bias θ only modestly. Sensitivity R9 below addresses this.
- In-window administered-price shocks (for example the 2023-02 energy subsidies, about
  −0.5 pp of excess) are **not** adjusted. Choosing them would mean selecting on window
  data. They are a limitation (A8).

### 4.4 Publication lags

- US CPI is released about 2 weeks after the reference month, and Japan national CPI about
  3 weeks after.
- Under reference-month alignment, x_t is not known at month-end t. H1b is an in-sample
  levels association, not a real-time relation, so this is acceptable and stated.
- Robustness R4 uses availability-dated CPI.

### 4.5 US CPI 2025-10 and 2025-11 (BLS shutdown FAQ, read 2026-10-23)

- BLS issued no October 2025 news release, and most October indexes were not published.
  The all-items index is survey-based. BLS does not plan retroactive collection: 2025
  annual averages use the 11 published months.
- BLS carried October 2025 forward internally: commodities and services from September,
  and rent/OER from April 2025.
- November 2025 is the collected November prices relative to that carried-forward level.
  For rent/OER it is the sixth root of the May–November change.
- BLS states the rent effect resolves in April 2026. So the 2025-11…2026-03 US levels carry
  a small, unquantified rent/OER understatement (A10). Sensitivity M2 removes it.
- For seasonal factors only, BLS used the geometric mean of September and November.

## 5. Missing US CPI for 2025-10

### 5.1 Where it bites

| Component | Affected? |
|---|---|
| ARDL / bounds test / validity gates | **No.** The estimation sample ends at 2021-12. |
| AK cointegrating regression over 1…T+m | Yes: one row of 547 |
| AK statistic P | Yes: position 46 of the 55 window months |
| AK subsample statistics P_j | Only through the choice of comparator (below) |
| Exploratory dynamic models through the window | Yes: Δx is undefined at 2025-10 and 2025-11 |

### 5.2 Options compared

| Option | Imputed value enters a statistic? | Calendar spacing | Comparator matched? | Verdict |
|---|---|---|---|---|
| **A. Matched-gap complete case:** drop 2025-10; P sums the 54 observed squared residuals; each P_j omits the residual at the same relative position (46) | No | Kept; t indexes calendar months | Yes, by construction | **Primary** |
| B. Complete case, unmatched (P over 54, P_j over 55) | No | Kept | No: biased toward non-rejection by about 1/55 | Rejected |
| C. Log-linear interpolation of September–November, flagged | Yes | Kept | Imputed residual less variable than observed | Sensitivity M1 |
| D. Carry September forward | Yes | Kept | Known downward bias in x | Rejected (strictly worse than C) |
| E. State-space or multiple imputation | Yes | Kept | Model-dependent | Rejected: 1 of 55 months, not worth a model |
| F. Truncate the window at 2025-09 (m = 45) | No | Kept | Yes | Sensitivity M2 (also removes the §4.5 rent issue) |
| G. Substitute another US price index for one month | No (but splices definitions) | Kept | — | Rejected |

**Why A is valid, and what is not covered.** AK's argument (p. 381) is that
P_{T+1}(β₀) and P_j(β₀) share a distribution because {u_t} is stationary. Omitting a fixed
relative position preserves that equality for every j. Formally this is eq. (6) with
Ω = I_m minus one diagonal 1. AK define P_j(β, Ω) only for **nonsingular** Ω, so option A
is a minimal extension that the paper does not cover. Its finite-sample size is verified in
§8 by simulating the procedure exactly as applied, with the gap.

**Dynamic models (exploratory only).** Use complete cases with calendar spacing. Every
row whose regressors include x_{2025-10}, or a Δx that spans it, is dropped. No difference
is ever taken across the gap. A November–September change is a two-month change, not a
one-month change, as in the ADR 0004 exclusion rule. Dropped rows are counted and
reported.

## 6. Establishing the relationship: ARDL bounds test (pre-period only)

### 6.1 Model (PSS 2001 Case III: unrestricted intercept, no trend)

```
Δs_t = a + Σ_{k=2}^{12} κ_k D̃_k,t + Σ_{e∈E} τ_e I_e,t
       + φ s_{t−1} + π_x x_{t−1} + π_d d_{t−1}
       + Σ_{i=1}^{p−1} ψ_i Δs_{t−i} + Σ_{j=0}^{q_x−1} ω_j Δx_{t−j} + Σ_{j=0}^{q_d−1} λ_j Δd_{t−j} + ε_t
```

- D̃: centred monthly dummies.
- E = {1989-04, 1997-04, 2014-04, 2019-10}.
- t = 1982-01…2021-12 (n = 480).
- Long run: θ = −π_x/φ and γ = −π_d/φ.

### 6.2 Lags

1. Fit all (p, q_x, q_d) ∈ {1,…,12}³ by OLS on the common n = 480 sample.
2. Candidates are the models whose Breusch–Godfrey LM(12) p-value is ≥ 0.05.
3. Select the AIC minimum among the candidates. If there are no candidates → not assessable
   (V3).

The deterministic terms and dummies are identical in every candidate model.

### 6.3 Statistics and critical values

With K = 1 + 11 + 4 + 3 + (p−1) + q_x + q_d regressors:

```
F = [(RSS_R − RSS_U)/3] / [RSS_U/(n − K)]     restriction: φ = π_x = π_d = 0
t = φ̂ / se(φ̂),  se from s² = RSS_U/(n − K)    (homoskedastic OLS)
```

**Homoskedastic, not HAC.** PSS derive the bounds distributions for the conventional
statistics under their error assumptions. A HAC or HC Wald statistic has no established
bounds distribution here, so selecting HAC does not validate PSS critical values. Robustness
to conditional heteroskedasticity is checked by simulation instead (§8.3).

**Critical values (2.5 %, both bounds):**

| Statistic | Rejects "no levels relationship" if |
|---|---|
| F | F > F_{I(1), 0.975} (upper tail) |
| t | t < t_{I(1), 0.025} (lower tail) |

- Lying between the bounds = inconclusive.
- Lying on the I(0) side = not rejected.

**Source: a project simulation that matches the design.**
- n = 480, with the same constant, the same 11 dummies and the same 4 impulse dates.
- The selected (p, q_x, q_d) as short-run regressors.
- Null DGP: Δs_t i.i.d. N(0,1), independent of x and d.
- Upper bound: x and d independent Gaussian random walks. Lower bound: x and d i.i.d.
  N(0,1).
- 100,000 replications, NumPy PCG64, SeedSequence(20261023).
- Monte Carlo error of the quantiles is reported.

This mirrors the Kripfganz–Schneider (2020) approach, conditioned on the realized lag
order.

**Checks of the simulator:**
1. With n = 10,000 and no short-run terms, it must reproduce PSS (2001) Table CI(iii)
   (F) and Table CII(iii) (t), k = 2, at 2.5 %, within ±0.05. **The printed PSS values
   must be transcribed from the paper before freezing; they were not verified this
   session.**
2. Optional and non-decisive: compare with Kripfganz–Schneider response-surface p-values
   (Stata/R `ardl`), if available.

### 6.4 What statsmodels 0.15.0 does and does not provide (verified in the installed source)

| Need | statsmodels 0.15.0 | Use |
|---|---|---|
| UECM estimation with seasonal and fixed regressors | `UECM(..., seasonal=True, fixed=...)` | May be used for estimation; F and t computed manually from the fit |
| F-bounds test | `UECMResults.bounds_test`: **rebuilds the UECM with `trend` only, dropping `seasonal` and `fixed`** (verified: F = 47.90 from `bounds_test` vs 43.99 for the fitted model with dummies, same data) | **Not used** |
| Asymptotic F bounds | Tabulated only at 90/95/99/99.9 %: **no 97.5 %**. The asymptotic path looks up `k = len(ardl_order)` (= 3 for two regressors). The table keyed (3, 3) gives a 5 % upper bound of 4.32, while statsmodels' own simulator for two regressors gives 4.81, which matches the table keyed (2, 3). **This apparent off-by-one makes it liberal.** | **Not used** |
| Finite-sample simulation (`asymptotic=False`) | F only, no short-run terms or dummies, homoskedastic | Not used |
| t-bounds test | **Not available** | Own simulation (§6.3) |
| Kripfganz–Schneider values | Not available | External cross-check only |
| HAC `cov_type` | Accepted, but compared with homoskedastic critical values | Not used for bounds |

## 7. Validity conditions vs economic findings

### 7.1 Validity conditions (needed for the inference to mean what it claims)

All are run on the pre-period only. Failing any one → **not assessable**.

| # | Condition | Operationalization | What it cannot show |
|---|---|---|---|
| V1 | No I(2) variable | For each of s, x and d: ADF on the **first difference** with a constant. Δx also gets centred seasonal and tax impulse dummies. AIC lag, maximum 12, MacKinnon p-values. **Passes only if the unit-root null in Δv is rejected at 5 %**, i.e. positive evidence against I(2). KPSS on Δv is reported but does not decide. | Rejection does not exclude **near**-I(2) behaviour (persistent inflation differentials), which distorts bounds tests in finite samples. The largest AR root of Δx is reported. |
| V2 | Pre-period levels relationship | Bounds F **and** t both beyond their I(1) bounds at 2.5 % (§6.3). Requiring t as well rules out the PSS degenerate case where the lagged levels matter but there is no error correction. | Rejection shows a levels relationship in the conditional ECM. It does not show that AK's static residuals are stationary with constant β over 1981–2021 (A4). Non-rejection is not evidence of no relationship. |
| V3 | Serially uncorrelated ECM errors | §6.2 (the BG filter) | BG at 12 lags has limited power against long-memory deviations. |
| V4 | Well-defined long run | All roots of the estimated levels-AR polynomial 1 − Σ a_i z^i lie outside the unit circle (companion modulus < 1) | This is a point-estimate check with no error control. |
| V5 | AK finite-sample validity | §8.4 acceptance rule | This is valid only for the simulated DGP class. |
| V6 | Data integrity | §3 hard checks | — |

**Replacing the (−2, 0) restriction.** In the UECM, φ = −(1 − Σ_{i=1}^{p} a_i) = −a(1).
- Stability implies a(1) > 0, so it implies φ < 0.
- For p = 1, stability is exactly φ ∈ (−2, 0).
- For p ≥ 2, the restriction is **neither necessary nor sufficient**:
  - in an AR(2), φ = a₁ + a₂ − 1 ranges over (−4, 0) inside the stability region;
  - a₁ = −1.5, a₂ = 0.6 gives φ = −1.9 but is unstable (a₂ − a₁ > 1).
- So "φ < 0" is assessed inferentially by the t-bounds test (V2), and "dynamically stable"
  by V4.
- The half-life ln(0.5)/ln(1+φ̂) is valid only for p = 1. It is replaced by the half-life
  of the impulse response of the estimated ARDL. This is descriptive.

**Error control.** V2 runs at 0.025. If no relation exists, the AK null is false in the
pre-period, so a false "supported" needs only a false V2 pass. V2's size therefore bounds
H1b's false-support rate. V1 and V3 run at 0.05; their effect on that rate is not
quantified (A2).

### 7.2 Economic findings (pre-specified, secondary, unadjusted, never gating)

| Finding | Test | Role |
|---|---|---|
| **γ > 0** (positive long-run association with the differential) | One-sided 97.5 % lower bound of γ̂ = −π̂_d/φ̂, delta method. "Established" only if the bound is > 0 with **both** the homoskedastic (Pesaran–Shin 1999) and Newey–West (L = 5) covariances | Decides the **wording** of a supported outcome (below), not whether H1b can be assessed |
| θ = 1 (PPP) | Two-sided Wald, 5 % | Descriptive |
| Long-run forcing (weak exogeneity) of x and d | Loadings of Δx and Δd on the lagged equilibrium error | If significant, PSS's conditional-model assumption is doubtful; θ and γ are read with that warning |

**Why γ is not a gate.** AK tests a breakdown of the joint relation whatever the sign of
γ. The sign of γ bears on whether a breakdown can be **read** as decoupling from the
differential. It does not bear on whether the test is valid. Gating on it would also make
"not assessable" absorb a substantive economic result: no positive association with the
differential in 1981–2021, which is itself evidence relevant to H1.

## 8. Breakdown test: Andrews–Kim (2006) P test

### 8.1 Verified against the published article

Source: JBES 24(4), 379–394, DOI 10.1198/073500106000000297, in the JBES-typeset PDF on
D. W. K. Andrews' Yale page. It was read in full on 2026-10-23. The equations below are
transcribed from it.

- **Model and hypotheses, eqs. (3)–(4):** y_t = x_t'β₀ + u_t for t ≤ T, and x_t'β_t + u_t
  for t > T.
  - H0: β_t = β₀ throughout, and {u_t : t = 1…T+m} is stationary and ergodic.
  - H1: β_t ≠ β₀ for some t > T, and/or the distribution of (u_{T+1},…,u_{T+m}) differs
    from that of (u_1,…,u_m).
  - **H1 therefore includes a pure variance increase.**
- **Statistic, eqs. (7)–(8):** P = Σ_{t=T+1}^{T+m} (y_t − x_t'β̂_{1:(T+m)})², with
  β̂_{1:(T+m)} the least-squares (LS) estimate on **all** T+m observations.
- **Subsample statistics, eqs. (10)–(11):** P_j = Σ_{t=j}^{j+m−1} (y_t − x_t'β̂₂(j))² for
  j = 1,…,T−m+1.
  - β̂₂(j) is the "leave-m/2-out" LS estimate on t ∈ {1,…,T} excluding
    {j,…,j+⌈m/2⌉−1}.
  - AK motivate it as a finite-sample compromise: full-sample β̂ overrejects, and
    leave-m-out underrejects.
- **Critical value and p-value, eqs. (12)–(15):** q̂ = inf{x : F̂(x) ≥ 1−α}, with F̂ the
  empirical df of {P_j}.
  - Reject if (T−m+1)⁻¹ Σ_j 1(P > P_j) ≥ 1−α.
  - p-value: pv_P = (T−m+1)⁻¹ Σ_j 1(P ≤ P_j).
- **Assumption S:**
  - x₁ is I(1);
  - (u_t, x₂,t, v_t) is stationary and strong mixing, with Σ α(r)^{1−2/β} < ∞;
  - E[x₂,t u_t] = 0 (**stationary regressors exogenous; I(1) regressors may be
    endogenous**);
  - moments of order > 2;
  - non-redundant regressors;
  - a continuous df at the quantile.
  - Breaks in (x₂, v) are allowed (not proven). **Breaks in the u-distribution within the
    pre-period are not.**
- **Theorem 1:** Pr(P > q̂) → α as T → ∞ with **m fixed**. Theorem 2: P is **not
  consistent** under H1; it is asymptotically unbiased if P_{T+1}(β₀) is stochastically
  larger than P₁(β₀).
- **Their Monte Carlo (§6):**
  - T ∈ {100, 250}, m ∈ {1, 5, 10}, AR(1) ρ ∈ {0, .4, .8};
  - innovations N, χ²₂, t₃ and U;
  - ρ_{Dx,u} ∈ {0, .4, .8};
  - 40,000 replications.
  - Nominal-5 % P sizes at T = 250: within .014 of .05.
  - The eight-model averages for m = 10 are .057, .051 and .048 at ρ = 0, .4 and .8.
- **Typo to note:** eq. (34) has ρ_{Dx,u}^{1/2}η_t and eq. (37) has ρ_{Dx,u}η_t. Only (34)
  is used here (null cells).

### 8.2 Application

- y = s; x_t = (1, x_t, d_t); LS.
- T = 492 and m = 55, with the gap handled by option A (§5).
- T−m+1 = 438 subsamples, and ⌈m/2⌉ = 28.
- Reject at 0.025 iff #{j : P > P_j} ≥ 427.05, i.e. iff **at most 10** P_j ≥ P. Then
  pv_P ≤ 10/438 = 0.0228.
- The p-value grid has steps of 1/438.

**Known issues the simulation must quantify:**
- AK's own evidence stops at ρ = .8 and m ≤ 10. Our m/T ≈ 0.11, and PPP-type residual
  persistence (monthly ρ ≈ .98–.99) gives only about T/m ≈ 9 effectively independent
  windows for estimating a 97.5 % quantile.
- The static LS estimate of β has second-order bias under endogeneity.
- The ARDL and AK estimates of (θ, γ) are both reported.

### 8.3 Simulation design (fixed now; run before any real-data AK statistic)

**Procedure simulated:** the exact §8.2 procedure, gap included. Two reference designs are
also run: m = 55 without a gap, and m = 56 without a gap (the originally requested design).

Data-generating process: s_t = x_t'β + u_t, t = 1…547 (or 548). LS residuals are invariant
to β under H0, so β = 0 under the null and no parameter is calibrated to KAGURA data.

| Factor | Levels |
|---|---|
| Residual persistence ρ_u (AR(1)) | 0, .80, .95, .98, .99 |
| Innovation law (u) | (i) N(0,1); (ii) t₅, unit variance; (iii) GARCH(1,1) with α = .10, β = .85, N(0,1) shocks, unit unconditional variance |
| Endogeneity corr(Δx-innovation, u-innovation) | 0, .5 (AK's common-component construction, eq. 34) |
| Drift in x (mean / sd of Δx) | 0, 0.5 (fixed a priori from the known sign and rough size of the US–Japan inflation gap; not estimated) |
| d | I(1) random walk; or stationary AR(1) .97 independent of u (S(c)) |

That gives 5 × 3 × 2 × 2 × 2 = 120 null cells.

**Assumption-violation cells (reported, not used for acceptance):**
- u variance ×2 for t ≤ 108 (a 1980s-type pre-period variance break);
- d stationary and correlated with u (.5).

**Alternatives (power, reported, never gating).** Applied to window rows. σ_u is the
stationary sd of u.

| Code | Mechanism |
|---|---|
| H-a | Mean shift of u: 0.5, 1 or 2 σ_u (a level decoupling) |
| H-b | Linear ramp of the mean of u from 0 to 2 σ_u across the window (gradual decoupling) |
| H-c | u becomes a random walk, scaled as in AK eq. (37) (factor √2) |
| H-d | Variance of u × 2, no mean change (variance-only breakdown, inside AK's H1) |
| H-e | The H-a 1 σ_u shift starting 24 months **before** T (contaminated pre-period) |

Power is reported raw and size-corrected (AK's method, §6.1).

**Replications and Monte Carlo uncertainty:**
- Null cells: R = 10,000. The MC sd of a 0.025 rejection rate is ≈ .0016.
- Power cells: R = 5,000.
- Seeds: SeedSequence(20261023).spawn(n_cells), in a fixed cell order.
- Rates are reported with binomial MC standard errors.

**Implementation check (before the grid):**
- Reproduce AK Table 1: P at nominal .05, T = 250, m = 10, ρ ∈ {0, .4, .8}.
- Average over AK Models 1–8 (eqs. 31–36), with R = 10,000 per model.
- Pass: each average within ±.004 of .057, .051 and .048.
- On failure, stop and fix. No tuning.

### 8.4 Acceptance rule (V5, fixed now)

1. **Computed before P.** From pre-period-only LS residuals (t ≤ T), take the AR(1)
   coefficient ρ̂_u. Let ρ* be the smallest grid value ≥ ρ̂_u (rounding up). If ρ̂_u > .99 →
   not assessable.
2. V5 passes iff the simulated null rejection rate at nominal .025 is **≤ .035** in every
   null cell at ρ*. That is 24 cells: 3 innovation laws × 2 endogeneity levels × 2 drifts ×
   2 forms of d. The threshold .035 is about 6 MC standard errors above .025.
3. Under-rejection (< .010) does not fail V5. It is reported as "conservative".
4. Fallback if V5 fails: H1b is **not assessable**. No switch of test, estimator or window.
   A size-corrected P (using the simulated α* at ρ*) may be reported as **exploratory
   only**.

**Note.** Step 1 uses real pre-period data. It never uses window data, P, or any statistic
that depends on the H1b outcome.

## 9. Decision rules

| Outcome | Condition | Meaning |
|---|---|---|
| **Not assessable** | Any of V1–V6 fails | H1b cannot be evaluated with valid inference. Neither for nor against H1. Its 0.025 is not reallocated. |
| **Supported** | V1–V6 pass, and pv_P ≤ 0.025 (§8.2) | Evidence that the 1981–2021 relation among s, x and d did not hold over 2022-01…2026-07, through a coefficient shift, non-stationarity **or a change in residual distribution, including variance**. |
| **Breakdown not detected** | V1–V6 pass, and pv_P > 0.025 | **Not evidence of stability.** P is inconsistent with m fixed (Theorem 2), and power is limited at high ρ_u. No "ruled out" or equivalence claim exists for H1b. |

**Wording qualifier for "Supported"** (from §7.2; it does not change the category):
- **γ established positive:** "the relation, which included a positive long-run
  association with the 2Y differential, broke down". Attributing the breakdown to the
  differential still needs the §10 attribution analyses, which are descriptive.
- **γ not established:** "Supported (joint relation only)". **Must not** be described as
  decoupling from the differential.

**Descriptive companions (always reported):**
- P split into the window's squared mean residual × 54 and the within-window variation;
- the window residual path;
- the AK estimates of (θ, γ) next to the ARDL estimates.

**Multiplicity:**
- The P test at 0.025 is H1b's only claim in the H1 family.
- V2 runs at 0.025, for the reason in §7.1.
- Everything else is unadjusted and labelled secondary or exploratory.

## 10. Confirmatory vs exploratory

| Layer | Content |
|---|---|
| **Confirmatory** | V1–V6 → AK P (primary specification, option A) → category (§9) |
| **Pre-specified secondary** (unadjusted, cannot change the category) | γ, θ = 1, long-run forcing (§7.2); AK R statistic; attribution, via AK on the PPP-only relation and a decomposition of the window gap into its x and d contributions; missing-data sensitivities M1 (interpolated, flagged) and M2 (window ending 2025-09, m = 45); robustness R1–R9 |
| **Exploratory** (labelled as such; new ADR if it is to be relied on) | Size-corrected P; break dating; ECMs with break interactions; dynamic models through the window (§5.2 rule); anything not listed here |

**Robustness variants.** Each re-runs §6–§9 with one change, labelled as in ADR 0006 §9.1.

| Variant | Change |
|---|---|
| R1 | PPP imposed: q = s − x regressed on d |
| R2 | 10Y differential (pre-period from 1986-07, T = 426) |
| R3 | Case IV with a restricted trend; θ weakly identified |
| R4 | Availability-dated CPI |
| R5 | Pre-period starts in 1990-01 or 1999-01 (disclosed as informed by §1) |
| R7 | Month-average market data |
| R8 | Real-differential proxy: d minus the 12-month inflation gap |
| R9 | Tax-adjusted x: each tax-month change in excess of its 1981–2021 same-calendar-month median removed permanently from x |

R6 (carry-forward) is withdrawn and replaced by M1 and M2.

## 11. Remaining assumptions

| # | Assumption | If violated |
|---|---|---|
| A1 | Gaussian-null simulation critical values for the bounds test are adequate under the actual error law | §8.3-type size check for the bounds gate: GARCH and t₅ cells at the selected lag order. If the gate's null rejection rate is > .035, V2 is reported as unreliable and H1b is not assessable. |
| A2 | Pretests V1 and V3 at 0.05 do not materially distort V2 | Unquantified |
| A3 | Long-run forcing of x and d (PSS Assumption 3) | θ and γ are biased; checked descriptively (§7.2) |
| A4 | Pre-period stationarity of u and constant β, 1981–2021 (AK maintained hypothesis; **not tested**) | Plaza-era shifts make this doubtful. Subsample critical values widen, P loses power, and size may distort. R5 is the guard. |
| A5 | No breakdown began before 2022 | The pre-period is contaminated and power falls (H-e); this biases toward "not detected" |
| A6 | d exogenous if it is I(0) (AK S(c)) | P size distortion; covered in the violation cells |
| A7 | Option A's singular-Ω extension of AK | Verified only by simulation (§8.3) |
| A8 | In-window administered prices (2023 energy subsidies) are small relative to residual variation | x is mismeasured in the window; not adjusted |
| A9 | The BIS Japan series is consistent across the 2025-base revision | A splice step in 2026; small |
| A10 | US rent/OER understatement in 2025-11…2026-03 is negligible | M2 is the guard |
| A11 | Current-vintage CPI (not first releases) | Revisions are small; not otherwise addressed |

## 12. Order of operations

1. Close the open decisions (below). Transcribe the PSS 2.5 % values for k = 2 (Tables CI(iii)
   and CII(iii)). Freeze by committing this ADR alone and pushing.
2. Implement on synthetic data only:
   - bounds statistics and the simulator, checked against PSS;
   - the AK P test, checked against AK Table 1 (§8.3);
   - outcome categorisation tests;
   - CPI checksums added to the guard.
3. Run the §8.3 grid. Commit its tables.
4. Real-data run (`make h1b`): V6 → V1 → lags → V3 → V2 → V4 → ρ̂_u → V5 → P → secondary.

## 13. Open decisions for the reviewer

- **D1.** m = 55 (Japan CPI ends 2026-07 in the frozen vintage) instead of 56.
- **D2.** The confirmatory claim is narrowed to the joint relation, with a γ-based wording
  qualifier (§2, §9). The alternative is to restore γ as a gate.
- **D3.** V5 threshold .035 and the round-up rule for ρ*.
- **D4.** BG-filtered AIC lag selection (§6.2) instead of the "increase the offending order"
  rule.

## 14. References

Verified this session:
- **Andrews, D. W. K., and Kim, J.-Y. (2006).** *JBES* 24(4), 379–394. Read in full: eqs.
  (3)–(15) and (27)–(37), Assumption S, Theorems 1–2, §6.
- **Pesaran, Shin and Smith (2001)**, *JAE* 16(3). Cited for Case III and the statistic
  definitions. **Tables CI(iii) and CII(iii) still to be read.**
- **BLS**, "2025 federal government shutdown impact on CPI — FAQ" (read 2026-10-23).
- **BIS**, long CPI series documentation (Japan entry, read 2026-10-23).
- **statsmodels 0.15.0**, `tsa/ardl/model.py`: `bounds_test`, `_pss_pvalue`,
  `_pss_simulate` (source read; behaviour reproduced in the review session).

Cited, not re-read this session: Kripfganz and Schneider (2020), *OBES* 82(6); Pesaran and
Shin (1999); Dornbusch (1976); Frankel (1979).
