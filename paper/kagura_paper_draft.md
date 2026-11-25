# Slopes, Volatility and Horizon: What Can Be Said About USD/JPY "Decoupling" from US–Japan Rate Differentials, 1981–2026

*Provisional title. Revised draft for internal review, 2026-11-24. Not for circulation.*

Results use the frozen data vintage of 2026-09-15 and the committed outputs at `61ec40b`. Post
hoc supplementary tables are produced by `paper/supplement/post_hoc.py`. Every number is mapped
to its source in `paper/DRAFTING_NOTES.md`.

---

## Abstract

Since 2022, commentary has often said that USD/JPY has "decoupled" from the US–Japan
interest-rate differential, usually because the regression slope of the exchange rate on the
differential has fallen. We show that slope-based claims of this kind depend strongly on the
volatility of the differential, on the observation frequency and on timing.

**Sensitivity (confirmatory).** On daily data, the slope of USD/JPY changes on changes in the
2-year differential is 4.05 % per percentage point in 2022–2026, against 6.44 in 2013–2021.

- The change is −37 %, with a Fieller 95 % interval of −49 % to −22 %.
- A pre-registered test cannot tell whether the decline exceeds one third, so its verdict is
  *inconclusive*.

**Correlation and volatility (post hoc).**

- The daily correlation is 0.44 against 0.37. The difference is +0.07, with a block-bootstrap
  95 % interval of about 0.00 to 0.15, so the change in correlation is statistically uncertain.
- The daily volatility of the differential rose about 2.3-fold, which is clearly outside sampling
  noise. In the identity slope = correlation × relative volatility, that rise is arithmetically
  larger than the whole slope decline. This is an accounting decomposition, not a causal
  explanation.

**Frequency.** At the monthly frequency the pre-registered estimate moves in the opposite
direction, rising from 4.38 to 7.45, and a material monthly decline is ruled out.

- The reversal comes from within-month dynamics: same-day co-movement partly reversed within the
  month before 2022 and accumulated afterwards.
- We cannot explain it. **It is the principal limitation on any economic reading of the daily
  decline.**

**Timing of change (exploratory).** Break dates are chosen by information criteria; no test of
the number of breaks is available.

- Over 1981–2026, least-squares break estimation prefers a single break in April 2004, where the
  link strengthens.
- Over 2013–2026, BIC prefers October 2017 and LWZ prefers no break. The two criteria disagree
  clearly.

**Events and levels.**

- None of the 12 published event-proximity comparisons places a headline date within the lowest
  5 % of a random-date baseline.
- Long-run decoupling in levels is not assessable.

---

## 1. Introduction

Between December 2021 and July 2026, USD/JPY rose from 115.2 to 159.2: 32.4 log-points in
nominal terms and 36.1 in real terms. The Federal Reserve raised its policy rate rapidly, while
the Bank of Japan kept yield-curve control until 2024.

- **The standard account** attributes the yen's fall to the widening rate gap.
- **A competing account** says the yen has "decoupled" from rates, often citing a smaller
  regression slope of the exchange rate on the differential.

"Decoupling" can mean at least three things:

1. **A smaller sensitivity:** a smaller % change in USD/JPY per percentage point of differential
   change.
2. **A looser co-movement:** the differential accounts for less of the exchange rate's variation.
3. **A broken long-run relation:** the level of USD/JPY drifts away from where rates and relative
   prices would place it.

The first two need not move together. Within any sample the OLS slope satisfies the identity

$$
\hat\beta = \hat\rho \cdot \frac{\hat\sigma_{\Delta s}}{\hat\sigma_{\Delta d}} ,
$$

So a slope can fall because the differential became more volatile, with correlation unchanged.
The slope also depends on the horizon over which changes are measured. The third meaning concerns
levels, and neither statistic of changes addresses it.

**Central contribution.** We document, for USD/JPY, how slope-based claims of exchange-rate
decoupling depend on the volatility of the differential, on frequency and on timing. Over the
same post-2022 period:

- the daily slope fell;
- the change in daily correlation is statistically uncertain, and we cannot rule out either a
  modest fall or a modest rise;
- the volatility of the differential more than doubled;
- the monthly slope rose.

A reading based on the daily slope alone would therefore overstate what is known. Our
contribution is to separate these components and to quantify the uncertainty of each. Two
further elements support it:

- the pre-registered short-run test keeps its inconclusive verdict;
- we state plainly which parts of the decoupling question no validated tool here can answer.

**Evidence and status.** We address the question "has USD/JPY decoupled, and if so when and by
how much?" separately for each meaning. Each analysis has a status fixed before its results were
known:

| Analysis | Status |
|---|---|
| Short-run sensitivity test, H1a (ADR 0006) | Confirmatory |
| Long-run protocol, H1b (ADR 0008) | Confirmatory but not executable, so the question is not assessable |
| Structural-break estimation (ADR 0007, 0011, 0012) | Exploratory |
| Event-proximity comparison (ADR 0009, 0013, 0014) | Descriptive |
| Supplementary uncertainty and decomposition analyses | Post hoc descriptive |

**Findings:**

1. **The daily slope is lower after 2022, but whether the decline is material is undetermined.**
   The −37 % change has a 95 % interval of −49 % to −22 %, which contains the pre-registered
   −33 % threshold. The confirmatory verdict is *inconclusive*, which means neither "stable" nor
   "materially declined".
2. **The change in daily correlation is statistically uncertain.**
   - The point estimate rose from 0.37 to 0.44, and R² from 0.13 to 0.19.
   - The bootstrap interval for the change is about [0.00, 0.15]. A rise is not established, and
     a modest fall cannot be excluded at this precision. That the interval does not show a
     weakening is not proof that none occurred.
3. **The volatility of the differential rose markedly**, by about 2.3-fold relative to
   2013–2021. In the slope identity this term is larger than the whole slope decline. The
   decomposition is arithmetic; it says nothing about cause.
4. **The monthly estimate moves the other way.**
   - The pre-registered monthly slope rises from 4.38 to 7.45. Summing daily changes by month
     reproduces this, so the difference comes from the horizon, not the data source.
   - An exact decomposition locates it in within-month dynamics, which we cannot explain.
5. **The data do not single out 2022 as a time of change.**
   - The dominant estimated change over 1981–2026 is a *strengthening* around April 2004.
   - Over 2013–2026, BIC prefers October 2017 and LWZ no break.
   - A January 2022 break is not preferred but not ruled out.
   - All of these dates are exploratory.
6. **Event proximity is not informative about cause.** No published comparison is within the
   lowest 5 % of the baseline.
7. **The long-run question is not assessable.**

**Roadmap.** Section 2 reviews the economics and the literature. Section 3 describes the data,
and Section 4 the empirical strategy. Section 5 presents the results by question. Section 6
discusses what can and cannot be distinguished. Section 7 sets out the limitations, and Section 8
concludes.

---

## 2. Economic background and related literature

### 2.1 Interest differentials and exchange rates

Uncovered interest parity (UIP) links the level of the interest differential to a currency's
expected depreciation. Engel's (1996) survey documents that the future change in the exchange
rate is generally *negatively* related to the forward discount, which is the forward-discount
anomaly. Over two centuries of data, Lothian and Wu (2011) find positive forward-premium slopes
that turn negative only when the sample is dominated by the 1980s.

Our short-run estimand is not UIP. It links *contemporaneous changes* in the differential to
*contemporaneous changes* in the exchange rate. This is a co-movement under the prevailing mix of
news, and no parity condition implies a particular size for it.

### 2.2 Fundamentals and instability

The difficulty of forecasting exchange rates with economic models is known as the Meese and
Rogoff (1983) puzzle: a random walk forecasts better (as summarised by Rossi, 2013). Engel and
West (2005) show that in a rational-expectations present-value model, an asset price behaves
nearly like a random walk if fundamentals are I(1) and the discount factor is near one.

Two papers model or document instability in which fundamentals matter:

- Bacchetta and van Wincoop (2004) model market participants attributing exchange-rate moves to
  a "scapegoat" variable that changes over time.
- Sarno and Valente (2009) find frequent shifts in the set of fundamentals that drive exchange
  rates.

A time-varying slope on the rate differential is consistent with these frameworks, but it does
not identify a mechanism.

### 2.3 Announcements and high-frequency co-movement

Exchange rates jump in response to macroeconomic announcement surprises (Andersen, Bollerslev,
Diebold and Vega, 2003). Exchange rates and interest rates respond jointly to such news (Faust,
Rogers, Wang and Wright, 2007).

A daily regression of exchange-rate changes on differential changes therefore measures
co-movement under the prevailing mix of shocks, not a structural transmission coefficient. If
the mix of shocks changes, the slope can change even when no single transmission channel does.

### 2.4 Correlation, slopes and volatility

Forbes and Rigobon (2002) show that correlation coefficients are conditional on market
volatility, so a measured change in correlation need not reflect a change in the underlying link.

Our setting is the converse. The object of interest is the regression slope, which depends
mechanically on the relative volatility of the two series. The identity in §1 is accounting, not
a correction for bias.

### 2.5 Japanese monetary and intervention regimes

The sample spans regimes that change how the 2-year differential behaves. The dated markers used
in this project (ADR 0004) are:

- the Plaza (1985) and Louvre (1987) accords;
- zero interest rates (1999);
- quantitative and qualitative easing (2013);
- negative rates (January 2016) and yield-curve control (September 2016);
- the 2022 Fed tightening and MOF intervention;
- the end of negative rates and yield-curve control (March 2024).

For long stretches the Japanese 2-year yield was close to fixed, so the differential moved
mainly with US yields. In 2022–2026 a descriptive two-leg split gives a US-leg coefficient of
4.21 and a JGB-leg coefficient of −0.19.

We use official intervention dates only as event markers. The effectiveness of intervention has
its own literature (for Japan, e.g. Fatum and Hutchison, 2006), which we do not test.

### 2.6 Identification

Nothing here identifies a causal effect of rates on the yen. Yields and the exchange rate respond
to common news, and possibly to each other within the day. Proximity between a break date and a
policy event is not evidence of causation (ADR 0009 §7.4).

---

## 3. Data and definitions

### 3.1 Series

| Series | Source | Frequency | Use |
|---|---|---|---|
| USD/JPY | FRED `DEXJPUS` (Federal Reserve H.10, noon New York) | Daily, monthly | All |
| US 2Y, 10Y Treasury yields | FRED `DGS2`, `DGS10` | Daily, monthly | All |
| JGB 2Y, 10Y yields | Japan Ministry of Finance | Daily, monthly | All |
| US CPI; Japanese CPI | FRED `CPIAUCSL`; BIS consumer prices `M.JP.628` (ADR 0002) | Monthly | H1b |
| Policy events | Official BOJ, FOMC, FRB and MOF releases (ADR 0009, 0010) | Event | §5.6 |

**Frozen vintage.** The market files were downloaded on 2026-09-15, and their SHA-256 checksums
were recorded before any confirmatory model ran (ADR 0006 §9.2). Every analysis, including the
supplement, refuses to run on data that do not match. BOJ-derived event material is held in
restricted storage, because its reuse terms are unresolved (ADR 0010 §1).

### 3.2 Transformations

- **Changes.** Δs_t is the change in 100·ln(USD/JPY), in %, and Δd_t the change in the US–JGB
  2-year differential, in pp. Positive Δs is a yen depreciation, and β reads as "% change in
  USD/JPY per 1 pp change in the differential".
- **Monthly variant.** This is R2 in ADR 0006. It uses consecutive month-end levels from
  `monthly.csv`.
- **H1b levels.** s is 100·ln(USD/JPY) at month-end, x is 100·ln(CPI_JP / CPI_US), and
  q = s − x is the real exchange rate.

### 3.3 Sampling, alignment and timing

- **Sample.** The daily sample runs from January 1981 to 2026-09-11, with 10,279 usable rows in
  the primary specification: 2,007 in 2013–2021 and 1,045 in 2022–2026.
- **Exclusion rule (ADR 0004).** No change is computed from a stale or filled value.
- **Asynchronous closes (ADR 0006 §4.5; ADR 0012 L19).** USD/JPY is the noon New York fix, US
  yields close around 15:30 New York, and JGB yields close in the Tokyo afternoon. Afternoon US
  news, including FOMC statements at 14:00–14:15 ET, therefore reaches the FX series one row
  after it reaches US yields.
- **Eras (ADR 0004).** 1981–89, 1990–98, 1999–2012, 2013–21 (reference) and 2022– (new). The
  2022 boundary was fixed in advance.

---

## 4. Empirical strategy

### 4.1 The estimand and its decomposition

The primary short-run estimand is the era slope β_e in

$$
\Delta s_t = \sum_e \mathbf 1[t\in e]\,(\alpha_e + \beta_e\,\Delta d_t) + \varepsilon_t,
$$

estimated by OLS with Newey–West (1987) HAC standard errors at lag 11.

**β_e was fixed as the estimand before any test.** Correlation and relative volatility are
reported only as aids to reading it. They are not alternative definitions of decoupling.

Within any sample, β̂ = ρ̂ · σ̂_Δs / σ̂_Δd and R² = ρ̂², so the change in the slope between two
periods splits exactly into three log terms:

$$
\Delta\ln\hat\beta = \Delta\ln\hat\rho + \Delta\ln\hat\sigma_{\Delta s} - \Delta\ln\hat\sigma_{\Delta d}.
$$

### 4.2 Uncertainty for the decomposition (post hoc)

Each term of the identity is estimated with sampling error. The supplement (S1–S2) therefore
attaches intervals to them as follows.

- **Resampling.** A moving-block bootstrap (Künsch, 1989) resamples (Δd, Δs) pairs in contiguous
  blocks within each period. This keeps their contemporaneous dependence and their serial and
  volatility dependence up to the block length.
- **Block length and draws.** The headline block length is 21 trading days, about one month,
  fixed before the run. A 63-day block length is reported as a sensitivity. There are 2,000
  draws and a fixed seed.
- **Independence.** Periods are resampled independently.
- **Intervals.** Intervals are 95 % percentile intervals. A difference is called *statistically
  established* only if its interval excludes zero under both block lengths. Otherwise it is an
  *observed* difference.

**This analysis is post hoc.** It was designed after the H1a and Phase A results were known, and
it does not test H1a's frozen hypothesis.

For the estimated regime boundaries (2004-04, 2017-10), the intervals ignore that the boundaries
were selected to fit the data, so they understate uncertainty. The H1a era boundary at 2022-01
was fixed in advance, so the reference-versus-new comparison is the cleanest.

### 4.3 H1a: the materiality test (confirmatory)

A material decline was defined in advance as β falling below two-thirds of its 2013–2021 value.
With δ = β_new − ⅔β_ref, which uses the joint HAC covariance of the two estimates, the protocol
runs three one-sided tests, each at α = 0.025:

- **Gate (G):** is the reference association positive?
- **S:** is δ < 0?
- **R:** is δ > 0?

The α of 0.025 is half the H1 family's 0.05; the other half was reserved for H1b (Bonferroni).

| Outcome | Verdict |
|---|---|
| S rejects | Material decline |
| R rejects | Material decline ruled out |
| Neither rejects | Inconclusive |

**Robustness variants (labels fixed in ADR 0006):**

- R1: the US leg lagged one day;
- R2: monthly data;
- R3: the 10-year differential.

Fieller's (1954) interval for β_new / β_ref is reported as a description.

### 4.4 H1b: long-run level decoupling (confirmatory protocol, not executable)

ADR 0008 specifies two steps:

1. A bounds-test gate for a pre-2022 levels relation among s, x and d (1981-01 to 2021-12,
   T = 492).
2. A single end-of-sample cointegration-breakdown test (2022-01 to 2026-07, m = 55) at
   α = 0.025.

A candidate test had to meet four requirements, fixed in advance:

- its theory covers this design;
- its full-procedure size is close to its nominal level at these dimensions;
- its tuning is fixed in advance;
- its published equations and critical values can be reproduced.

Two candidates were evaluated by Monte Carlo before any use on real data: Andrews and Kim
(2006), and Wagner and Wied (2017).

An exploratory follow-up applies ARDL bounds tests (Pesaran, Shin and Smith, 2001) to four
specifications over 1981–2021.

### 4.5 Structural-break estimation (exploratory)

**Model.** The model is the H1a regression with no era dummies, and a slope that may change at m
unknown dates.

**Estimation:**

- Global least-squares partitions for m = 0…5 are found by dynamic programming (theory: Bai and
  Perron, 1998; algorithm: Bai and Perron, 2003).
- Candidate dates are month-start rows, plus a daily-grid sensitivity for m = 1.
- Trimming is ε ∈ {15 %, 10 %, 5 %}, with 15 % the conventional choice.
- The number of breaks is chosen by BIC (Schwarz, 1978) and by LWZ (Liu, Wu and Zidek, 1997).

**The criteria as implemented.** Both are computed per observation (ADR 0007 §5.2;
`kagura.breaks`), with S the sum of squared residuals, p* the number of estimated parameters
including break dates, n the number of rows, c₀ = 0.299 and δ₀ = 0.1:

$$
\text{BIC} = \ln(S/n) + p^*\ln(n)/n
$$

$$
\text{LWZ} = \ln\!\left(S/(n-p^*)\right) + p^*\,c_0\,(\ln n)^{2+\delta_0}/n
$$

Differences are reported on this scale and multiplied by n, which is the more familiar scale of
n·ln S plus penalty.

**Specifications.** The primary specification and four variants: lagged US leg (V1), 10-year
(V2), monthly (V3), and a lag-augmented model. The lag-augmented model has a different estimand.

**Samples.** Each specification is run on the full sample (1981–2026) and the recent sample
(2013–2026).

**Intervals.** Bai (1997) intervals are reported as nominal 95 % intervals. Their simulated
coverage ranged from 76.5 % to 97.2 %, which is not a bound for these estimates.

**Tests of the number of breaks are withheld**, because the project's critical-value validation
failed (ADR 0007 §9.1). A least-squares partition always places m breaks, whether or not any
exists.

**Eligibility.** In the full sample at ε = 15 % the last eligible date is 2019-10-01.

### 4.6 Event proximity (descriptive)

**Classes.** Headline break dates are compared with six classes of official events (ADR 0009
§3.8):

| Class | Events |
|---|---|
| C0 | All BOJ and FOMC policy releases |
| C1 | BOJ policy changes |
| C2 | FOMC funds-target changes |
| C3 | MOF intervention-episode starts |
| C4 | The 13 ADR 0004 markers |
| C5 | FRB discount-rate actions |

**Statistics.** Each class gets two statistics:

- the count of events in the break's nominal interval, against the share of random same-width
  intervals that contain one;
- the signed nearest-event distance, against its percentile among baseline positions.

**Fixed in advance (ADR 0013):**

- The headline set: HC1, the full-sample break; HC2, the BIC-only recent break; and HC3, a
  mandatory row recording that LWZ selects no recent break.
- The only permitted closeness wording: "within the lowest 5 % of the descriptive random-date
  baseline".

**Fixed after the Phase A dates but before Phase C (ADR 0014):** the implementation conventions.

**A known bias.** The baseline treats the estimated date as random, but the date was chosen to
minimise residuals. Proximity is therefore biased toward ranking close.

### 4.7 Status of each result

| Analysis | Status | What it can establish |
|---|---|---|
| H1a | Confirmatory (ADR 0006) | Material decline, ruled out, or inconclusive at the 2022 boundary |
| Correlation, volatility and decomposition intervals (S1–S2) | Post hoc descriptive | Whether observed component changes exceed sampling noise |
| Daily vs monthly decomposition (S6) | Post hoc descriptive | Where the horizon difference arises, arithmetically |
| Structural breaks | Exploratory (ADR 0007) | Least-squares boundaries; criterion preferences |
| Forced-2022 profile, pooled-slope split (S4–S5) | Post hoc descriptive | Fit of 2022 relative to other dates; reconciling eras with regimes |
| H1b confirmatory | Not assessable (ADR 0008) | Nothing; α unused, not reallocated |
| H1b ARDL, Stage 1 | Exploratory | Whether a stable pre-2022 levels anchor is visible |
| Event proximity | Descriptive (ADR 0013, 0014) | Timing coincidence at row resolution, never cause |

---

## 5. Results

### 5.1 Is daily sensitivity lower after 2022?

**Table 1. Era slopes, primary specification** (daily, 2-year differential, same-day changes)

| Era | β (% per pp) | HAC se | R² |
|---|---:|---:|---:|
| 1981–1989 | 0.67 | 0.17 | 0.017 |
| 1990–1998 | −0.14 | 0.28 | 0.000 |
| 1999–2012 | 2.68 | 0.26 | 0.055 |
| **2013–2021 (reference)** | **6.44** | 0.50 | 0.133 |
| **2022–2026 (new)** | **4.05** | 0.32 | 0.191 |

*Source: `notebooks/02_h1a_formal.ipynb`.*

**Size of the change.** The gate passes: the lower bound of β_ref is 5.46. The absolute change
is −2.39 % per pp, with a 95 % interval of [−3.56, −1.22]. The relative change is −37 %, with a
Fieller interval of [−49 %, −22 %].

**Materiality tests.** For δ the point estimate is −0.24.

- S does not reject: the upper bound is +0.66 and p_S = 0.30.
- R does not reject: the lower bound is −1.15 and p_R = 0.70.

**The pre-registered verdict is inconclusive.** The slope is lower, but the data cannot say
whether the decline exceeds one third.

**Long-run context.** The 2013–2021 reference is the highest era slope in 45 years, not a
historical norm. Equality of the five era slopes is rejected strongly (Wald χ²(4) = 239; a
secondary test, not adjusted).

### 5.2 Has co-movement loosened?

**Table 2. Components of the daily slope, with 95 % moving-block bootstrap intervals** (block
length 21 days)

| Period | Rows | corr | sd Δd (pp) | sd Δs (%) | Slope |
|---|---:|---|---:|---:|---:|
| 1981-01 – 2004-03 | 5,258 | 0.07 [0.03, 0.11] | 0.093 | 0.68 | 0.51 |
| 2004-04 – 2012-12 | 1,969 | 0.34 [0.28, 0.39] | 0.056 | 0.67 | 4.14 |
| 2013-01 – 2017-09 | 1,063 | 0.36 [0.29, 0.43] | 0.030 | 0.66 | 7.97 |
| 2017-10 – 2021-12 | 944 | 0.42 [0.33, 0.49] | 0.033 | 0.40 | 5.03 |
| 2022-01 – 2026-09 | 1,045 | 0.44 [0.39, 0.49] | 0.073 | 0.68 | 4.05 |
| *H1a reference 2013–2021* | 2,007 | 0.37 [0.31, 0.42] | 0.032 | 0.56 | 6.44 |

*Sources: point estimates from `research/adr0007/out/phase_a/figures/04_rate_volatility.csv`;
intervals from `paper/supplement/out/s1_period_components.csv`. In each row,
slope = corr × sd Δs / sd Δd.*

**Table 3. Log decomposition of slope changes, with bootstrap intervals** (block length 21; the
63-day results are in S2)

| From → to | Δ ln slope | Δ ln corr | Δ ln sd Δs | −Δ ln sd Δd | Δ corr |
|---|---|---|---|---|---|
| **H1a ref 2013–21 → 2022–26** | −0.46 [−0.67, −0.23] | +0.18 [0.00, 0.37] | +0.20 [0.06, 0.34] | −0.84 [−1.01, −0.69] | +0.07 [0.00, 0.15] |
| 1981–2004 → 2004–12 | +2.09 [1.61, 3.01] | +1.58 [1.07, 2.57] | −0.01 [−0.12, 0.10] | +0.52 [0.34, 0.66] | +0.27 [0.20, 0.34] |
| 2004–12 → 2013–17 | +0.66 [0.38, 0.93] | +0.05 [−0.20, 0.33] | −0.02 [−0.15, 0.12] | +0.62 [0.45, 0.76] | +0.02 [−0.07, 0.12] |
| 2013–17 → 2017–21 | −0.46 [−0.76, −0.18] | +0.14 [−0.16, 0.42] | −0.50 [−0.68, −0.30] | −0.10 [−0.28, 0.10] | +0.06 [−0.06, 0.16] |
| 2017–21 → 2022–26 | −0.22 [−0.45, 0.07] | +0.05 [−0.16, 0.33] | +0.52 [0.32, 0.70] | −0.79 [−1.01, −0.59] | +0.02 [−0.07, 0.13] |

*Source: `paper/supplement/out/s2_log_decomposition.csv`. Post hoc. Rows after the first use
estimated boundaries, so their intervals understate uncertainty.*

**Correlation: observed, not statistically established.**

- Against the pre-specified H1a reference, correlation rose by 0.07, with an interval of
  [0.000, 0.146]; the 63-day block gives [−0.001, 0.150]. The lower end sits at zero, so the
  rise does not meet our standard for being statistically established.
- Against 2017–2021 the change is +0.02, with interval [−0.07, 0.13].
- 0.44 is the highest point estimate in the sample, but its interval overlaps those of 2013–2017
  and 2017–2021.

**What the evidence supports:**

- The change in correlation after 2022 is statistically uncertain.
- The point estimate rose, and the interval gives no indication of a fall.
- A modest fall cannot be excluded at this precision, so failing to detect a weakening is not
  evidence that none occurred.

**Volatility: statistically established.** Relative to 2013–2021, the differential's daily
volatility rose by a factor of e^0.84 ≈ 2.3. Its term in the decomposition is −0.84, with
interval [−1.01, −0.69]. That term alone is larger than the whole decline in the slope:

- Δln β = −0.46 = +0.18 (correlation) + 0.20 (FX volatility) − 0.84 (differential volatility).
- FX volatility rose as well. It partly offsets the differential term, with interval
  [0.06, 0.34].

**Earlier episodes:**

- **The 2004 strengthening is a correlation change.** Correlation rose by +0.27, with interval
  [0.20, 0.34], from near-zero co-movement.
- **The 2004–2017 rise in the slope is a volatility change.** The differential's volatility fell
  as Japanese yields were close to fixed (−Δ ln sd Δd = +0.62, [0.45, 0.76]), while correlation
  was unchanged.

**Interpretation, limited to accounting.** After 2022, each percentage point of differential
movement is associated with a smaller daily exchange-rate move, and the differential moves much
more. The volatility term in the identity is larger than the whole slope decline.

The identity shows *which* component moved. It does not show *why* the per-unit association is
smaller, and it is not a causal explanation. It also does not establish that the share of FX
variance explained by the differential rose, because the R² rise has the same uncertainty as the
correlation rise.

### 5.3 Why do the daily and monthly results differ?

The pre-registered monthly variant (R2) gives the opposite picture: β rises from 4.38 to 7.45,
and a material monthly decline is ruled out. We checked four candidate explanations using
existing results and one exact decomposition (S6). We did not search for new models.

**Table 4. Daily and monthly slope components in the H1a eras**

| Era | Series | Rows | corr | Slope | Same-day share of covariance | Same-day share of var Δd | Same-day share of var Δs |
|---|---|---:|---:|---:|---:|---:|---:|
| 2013–2021 | Daily | 2,007 | 0.37 | 6.44 | — | — | — |
| 2013–2021 | Monthly, R2 (month-end levels) | 108 | 0.27 | 4.38 | — | — | — |
| 2013–2021 | Daily changes summed by month | 108 | 0.29 | 4.65 | 1.44 | 1.04 | 1.28 |
| 2022–2026 | Daily | 1,045 | 0.44 | 4.05 | — | — | — |
| 2022–2026 | Monthly, R2 (month-end levels) | 56 | 0.74 | 7.45 | — | — | — |
| 2022–2026 | Daily changes summed by month | 57 | 0.69 | 7.80 | 0.67 | 1.28 | 0.87 |

*Source: `paper/supplement/out/s6_daily_vs_monthly.csv`; R2 slopes from notebook 02.*

**How to read the share columns.** A share is the same-day part of a monthly cross-product of
daily data, demeaned within each era.

- A share of 1 means a random-walk-like series.
- A share above 1 means same-day moves partly reverse within the month.
- A share below 1 means moves accumulate across days.

**The four candidates:**

1. **Data source and aggregation.** Summing the daily changes in each month gives 4.65 → 7.80,
   close to R2's 4.38 → 7.45. The reversal is therefore not caused by month-end values or by the
   exclusion rule. It is a property of the horizon.
2. **Within-month dynamics. This accounts for the difference exactly.**
   - **2013–2021:** the same-day covariance is 1.44 times the monthly covariance, so cross-day
     pairs *subtract* 44 %. Daily co-movement partly reversed within the month, and FX changes
     partly reversed too (share 1.28).
   - **2022–2026:** same-day pairs give only 67 % of the monthly covariance, so co-movement
     *accumulated* across days. Daily changes in the differential partly reversed (share 1.28),
     which shrinks the monthly variance in the denominator.
   - Together these turn a daily decline into a monthly rise: 6.44 × (1.04/1.44) ≈ 4.65 and
     4.05 × (1.28/0.67) ≈ 7.8.
3. **Precision.** The monthly reference slope is very imprecise, with a 95 % interval of
   [0.59, 8.18]; the 2022– monthly slope has interval [5.97, 8.93]. The monthly rise itself is
   therefore weakly determined, but a material monthly decline is ruled out by the protocol.
4. **Timing (an untested hypothesis, from Phase A report §8).** The asynchronous closes (§3.3)
   push part of the response to afternoon US news into the next row. That would create positive
   cross-day covariance, the sign seen in 2022–2026. The lagged-US-leg variant (R1), however,
   finds small next-day slopes in both eras (1.43 and 0.75). We have not tested how much of the
   cross-day pattern timing explains.

**The conflict is accounted for, not explained.** We do not know why same-day co-movement
reversed within the month before 2022 and accumulated afterwards. Until that is understood, the
daily decline cannot be read as a decline in the link at horizons relevant to valuation. **This
is the main limitation of the daily-frequency evidence** (§7).

### 5.4 Where do the data place the changes?

**Full sample (exploratory).** At ε = 15 %, both BIC and LWZ select one break, at
**2004-04-01**.

- The slope rises from 0.51 (se 0.14) to 4.44 (0.22).
- The nominal 95 % interval runs from 2003-07-15 to 2004-07-30.
- The criteria agree strongly. Relative to no break, ΔBIC = −0.0358 per observation, which is
  −368 on the n-scale, and ΔLWZ = −0.0289, or −297.
- The date agrees across the lag-augmented model (2004-04), the 10-year differential (2004-02)
  and monthly data (2005-03).
- At smaller trimming BIC adds 1980s dates. These are not promoted (ADR 0007 §3.4).

**Recent sample, 2013–2026 (exploratory). BIC selects one break at 2017-10-02, and LWZ selects
none.**

| Criterion, m = 1 vs m = 0 | Per observation | × n (n = 3,052) | Selected m |
|---|---:|---:|---:|
| BIC | −0.00486 | −14.8 | 1 |
| LWZ | +0.01154 | +35.2 | 0 |

*Source: `paper/supplement/out/s3_ic_margins.csv`, from `out/phase_a/partitions.csv`.*

- **What the values mean.** On the total-sample scale, one break improves fit by
  n·ln(S₁/S₀) = −38.9.
  - BIC's penalty for one break is 3·ln n = +24.1, so BIC prefers the break, with a net −14.8.
  - LWZ's penalty is about +71.1, so LWZ prefers no break, with a net +35.2.
  - The criteria therefore disagree clearly, not marginally. An earlier project description
    called BIC's margin "small" by quoting the per-observation value. It is corrected in a dated
    erratum to the Phase A report.
- **What they do not mean.** These are model-selection preferences under each criterion's
  penalty. They are not tests that a break exists, and they are not posterior probabilities. Both
  rest on assumptions that are not validated for these heteroskedastic, serially correlated
  daily errors, and tests of the number of breaks are withheld (§4.5).
- The m = 1 slopes are 7.97 (0.87) before the break and 4.21 (0.29) after.
- The nominal interval runs from 2017-03-15 to 2020-07-20, which is 27–35 % of the eligible
  range.
- The monthly and lagged-US-leg specifications select no recent break.

**2022: not preferred, not excluded (post hoc).** A profile over the 115 eligible single-break
dates (S4) gives:

- 2022-01-05 ranks 31st, and 2021-12-01 ranks 30th.
- The 12 best dates all lie between 2017-03 and 2018-03.
- A January 2022 break achieves 70.8 % of the best break's SSR reduction.
- BIC would still prefer it to no break: −0.00112 per observation, or −3.4 on the n-scale.
- LWZ prefers no break to *any* single date.

The unselected m = 4 partition has a step at 2021-12, with slopes 7.52 | 8.26 | 4.08 | 6.66 |
4.05.

**Reconciling eras and regimes (post hoc, S5).** An OLS slope pooled over groups is an exact
weighted sum of the within-group slopes plus a between-group term. Splitting the H1a reference
era at 2017-10:

$$
6.4446 = 0.4780 \times 7.9737 + 0.5209 \times 5.0326 + 0.0114 .
$$

H1a's 6.44 therefore averages two sub-periods, at about 8 and about 5. Relative to 2017–2021
alone, the post-2022 slope is 19 % lower (5.03 → 4.05). Its bootstrap interval for Δln β,
[−0.45, 0.07], includes zero (Table 3). Most of the decline from the 2013–2021 average had
happened before 2022. Both the fixed-era and estimated-regime descriptions are correct; they
answer different questions.

### 5.5 Do the levels still share an equilibrium?

**The confirmatory test could not be run.**

- **Andrews and Kim.** The implementation reproduced the published Table 1 (0.0554 against
  0.057), but at our dimensions its null rejection rate at nominal 0.025 was 0.047–0.107.
  - With 438 sub-sample windows, the smallest attainable p-value is 1/438.
  - Under the null, P(p ≤ 1/438) was already 0.035–0.087.
- **Wagner and Wied.** Its theory assumes driftless random-walk regressors, but relative prices
  drift. Its size ranged from 0.02 to 0.90 across bandwidth rules, and its power was 0.02–0.08.

**H1b is therefore not assessable.** Its α is unused and was not reallocated.

**The exploratory analysis found no defensible levels anchor.**

- Over 1981–2021, ADF and KPSS tests classify s, q, x and both differentials as I(1).
- No ARDL bounds statistic, in any of four specifications, passes its I(1) bound. This holds in
  both the original run and a design-sensitivity variant.
- Long-run coefficients are imprecise and in places have the wrong sign. In (a), relative prices
  enter at −0.30, with se 0.73.
- FM-OLS and D-OLS disagree with the ARDL estimates.

**What the levels do show.**

- From 2021-12 to 2026-07 the move was entirely real: +32.4 nominal, +36.1 real, while relative
  prices fell 3.8.
- The move is large but not unprecedented. The pre-2022 95th percentile of 55-month real moves
  is 34.8, and the maximum is 47.4.

No "fair value" or misalignment can be computed (ADR 0008 §7.2).

### 5.6 Do the estimated breaks coincide with policy events?

**The headline set has 24 comparisons:**

- 12 computed and published;
- 4 computed but withheld, because they derive from BOJ material whose reuse terms are
  unresolved;
- 4 pending;
- 4 not applicable.

HC3 records that LWZ selects no recent break, so there is no date to compare.

**None of the 12 published comparisons is within the lowest 5 % of the descriptive random-date
baseline.** Their percentiles range from 42.8 to 69.8. This paper makes no claim about the
withheld comparisons.

| Break | Nearest event (published classes) | Distance (rows) | Percentile |
|---|---|---:|---:|
| HC1, 2004-04-01 | MOF episode starting 2003-12-26 | −59 | 42.8 |
| HC1 | FOMC and FRB rate increase, 2004-06-30 | +53 | 58.7 and 49.8 |
| HC2, 2017-10-02 (BIC only) | FOMC funds-target increase, 2017-12-13 | +48 | 66.0 |
| HC2 | ADR 0004 marker: yield-curve control, 2016-09-21 | −231 | 61.3 |

*Source: `research/adr0007/out/phase_c/headline.csv`.*

**An exploratory proximity, not a headline result.** The unselected m = 4 partition has a date
of 2019-11-01, one row after the 2019-10-30 FOMC rate cut. That is within the lowest 5 % of the
baseline: the percentile is 5.0, or 2.0–3.5 under alternative tie rules. Three things limit
what it shows:

- it is one announcement counted in four overlapping cells;
- neither criterion selects the partition;
- month-start dates sit next to end-of-month releases by construction.

**What this shows.** Distance from events does not show that policy was irrelevant, and the
comparison was never a causal test. The analysis shows only that neither headline date is tied,
at row resolution, to a single published policy event.

---

## 6. Discussion: what the evidence can and cannot distinguish

Claims that the yen "decoupled" from rates bundle five separate quantities. The evidence bears
on each differently.

| Quantity | Evidence | Status |
|---|---|---|
| Daily sensitivity (slope) | Lower after 2022 (−37 %); materiality undetermined | Confirmatory, inconclusive |
| Daily correlation | +0.07, interval ≈ [0.00, 0.15] | Post hoc; change uncertain |
| Volatility of the differential | ≈ 2.3-fold rise | Post hoc; well outside sampling noise |
| Monthly slope | 4.38 → 7.45; material decline ruled out | Confirmatory robustness variant |
| Timing of change | 2004 strengthening; recent break BIC 2017-10, LWZ none | Exploratory |

**1. The daily slope and the volatility identity.**

- The daily slope is lower, and its decline is arithmetically matched by a larger rise in the
  differential's volatility.
- The identity is not an explanation. It does not show that higher volatility *caused* a smaller
  per-unit response.
- Two interpretations from the Phase A report remain **untested hypotheses**:
  - *shock composition:* with broad-based rate volatility, the slope averages over more kinds of
    news;
  - *observation timing:* see point 2.
- Testing either needs announcement-level or intraday evidence, which this paper does not have.

**2. Frequency.**

- The monthly slope rises, and the difference is fully accounted for by within-month dynamics
  (§5.3).
- Before 2022, part of the same-day co-movement reversed within the month. After 2022, it
  accumulated.
- Asynchronous closes would create cross-day co-movement of the post-2022 sign. This hypothesis is
  untested, and the lagged-leg variant does not show a large next-day effect.
- **Until this is understood, the daily decline cannot be read as a weakening of the link at
  horizons relevant for valuation, and it cannot be read as the absence of one.**

**3. Correlation.** The evidence neither establishes a rise nor shows a fall. We therefore make
no claim that co-movement became closer, and no claim that it did not weaken.

**4. Timing of change.**

- Least squares does not prefer 2022. The largest estimated change over 1981–2026 is a
  strengthening around 2004, driven by correlation.
- The 2004 date lies near the end of the 2003–2004 intervention period and a few months before
  the June 2004 Fed tightening. These coincidences were known before the event analysis. They
  cannot count as findings (ADR 0013), and neither is tested as a cause.

**5. Levels.** No valid confirmatory test exists for this design, and no stable levels anchor is
identified. The paper is silent on long-run decoupling and on any notion of "fair value".

**What a decoupling claim would require.**

- **Short run:** a confirmed material decline in sensitivity, together with weaker co-movement,
  holding across horizons. The evidence has a daily slope decline of undetermined materiality, an
  uncertain change in correlation, and a monthly slope that moves the other way.
- **Long run:** a valid test of a levels relation.

Neither is available. Neither "the yen decoupled from rates" nor "the link is intact" is
established. Slope-based claims in either direction are sensitive to the volatility of the
differential, to the frequency of observation and to timing.

---

## 7. Limitations

1. **The daily and monthly results conflict.** This is the principal limitation.
   - The daily slope decline reverses at the monthly horizon.
   - The reversal is accounted for by within-month dynamics that we cannot explain (§5.3).
   - The monthly reference slope is itself imprecise: 95 % [0.59, 8.18].
   - No economic reading of the daily decline is secure until the reversal is understood.
2. **The confirmatory verdict is inconclusive.** That means neither "stable" nor "materially
   declined". The H1 α is split with an H1b test that could not be run.
3. **Correlation and volatility intervals are post hoc.**
   - They come from a moving-block bootstrap with blocks of 21 and 63 days, 2,000 replications
     and fixed seeds (`paper/supplement/README.md`).
   - They assume stationarity within each period, independence between periods, and dependence
     captured within a block.
   - **The 2004 and 2017 boundaries were selected from the data.** Intervals for periods bounded
     by them are conditional on the selected dates, do not account for date-selection
     uncertainty, and are too narrow.
   - Only the comparison with the 2013–2021 era, whose boundary was fixed in advance, avoids
     this.
4. **The decomposition is not causal.** The slope identity apportions the slope change
   arithmetically. It does not explain it.
5. **Long-run identification.** No confirmatory test of level decoupling attained valid size. The
   exploratory bounds tests have low power under persistent deviations, so failing to find a
   levels relation does not show that none exists.
6. **Model-selection uncertainty.**
   - Break counts are information-criterion preferences, not tests, because the critical-value
     validation failed.
   - Over 2013–2026, BIC and LWZ disagree clearly: −14.8 against +35.2 on the total-sample scale.
   - Dates depend on trimming, maturity, frequency and criterion.
   - The ε = 15 % full-sample cell cannot place a break after 2019-10.
7. **Approximate break intervals.** Bai intervals are nominal. Their simulated coverage ranged
   from 76.5 % to 97.2 %, which does not bound the coverage for these estimates.
8. **Post hoc elements.** The supplementary analyses S1–S6 and the ADR 0014 conventions were all
   designed after earlier results were known.
9. **Event selection and coverage.**
   - The headline event set was fixed after the Phase A dates were known.
   - BOJ policy changes are pending, and the all-meetings comparisons are withheld from
     publication.
   - MOF classes count episode starts only.
   - Rows can be misaligned by one trading day.
   - The baselines treat estimated dates as random.
10. **No causal mechanism is verified.** All associations are conditional on the prevailing mix
    of shocks.
11. **The timing assumption may fail.** H1a assumes the timing distortion is stable across eras
    (ADR 0006 A5). The JGB leg's movement since 2024 and the within-month evidence in §5.3 both
    bear on that assumption.

---

## 8. Conclusion

**Has USD/JPY decoupled from the US–Japan interest-rate differential?** The evidence does not
establish it, and it does not rule it out. What it does show is that the answer depends on how
"decoupling" is measured.

- **Daily sensitivity.**
  - The slope is 37 % lower than in 2013–2021 (interval −49 % to −22 %). Whether the decline is
    material is undetermined, and the confirmatory verdict is inconclusive.
  - The change in daily correlation is statistically uncertain.
  - The volatility of the differential more than doubled. In the slope identity that rise is
    larger than the slope decline, which is an arithmetic statement, not a cause.
- **Frequency.** The monthly slope moves in the opposite direction. The reversal arises within
  the month, and we cannot explain it.
- **Timing.**
  - Least squares does not prefer 2022.
  - The largest estimated change over 45 years is a strengthening around 2004.
  - Over 2013–2026, BIC prefers 2017-10 and LWZ prefers no break.
  - All of these break dates are exploratory.
- **Levels.** Not assessable.

**The lesson for the decoupling debate.** A falling regression slope alone is weak evidence of
decoupling. It can reflect a more volatile differential, and it can reverse with the frequency
of observation.

**Open questions.** These follow from the limitations; none was run.

1. What drives the change in within-month dynamics?
2. How much of the daily pattern reflects asynchronous observation times?
3. Can the long-run question be posed with a design for which a valid test exists?
4. What do the BOJ event classes show, once they are coded and their reuse terms resolved?

---

## References

**How these were checked.**

- **Metadata:** Crossref records (2026-11-24); the *Statistica Sinica* website for Liu, Wu and
  Zidek; RePEc for two page ranges and one subtitle.
- **Claim support:** abstracts from Crossref, OpenAlex or Semantic Scholar; for Engel (1996) and
  Lothian and Wu (2011), the abstracts of their working-paper versions; for Meese and Rogoff
  (1983), Rossi's (2013) abstract.
- **Not read:** no full text was read. Each claim in the text is worded to match the verified
  passage.
- **Per-reference status:** `paper/DRAFTING_NOTES.md` §3.

- Andersen, T. G., Bollerslev, T., Diebold, F. X. and Vega, C. (2003). Micro effects of macro
  announcements: Real-time price discovery in foreign exchange. *American Economic Review*,
  93(1), 38–62. doi:10.1257/000282803321455151
- Andrews, D. W. K. and Kim, J.-Y. (2006). Tests for cointegration breakdown over a short time
  period. *Journal of Business & Economic Statistics*, 24(4), 379–394.
  doi:10.1198/073500106000000297
- Bacchetta, P. and van Wincoop, E. (2004). A scapegoat model of exchange-rate fluctuations.
  *American Economic Review*, 94(2), 114–118. doi:10.1257/0002828041301849
- Bai, J. (1997). Estimation of a change point in multiple regression models. *Review of
  Economics and Statistics*, 79(4), 551–563. doi:10.1162/003465397557132
- Bai, J. and Perron, P. (1998). Estimating and testing linear models with multiple structural
  changes. *Econometrica*, 66(1), 47–78. doi:10.2307/2998540
- Bai, J. and Perron, P. (2003). Computation and analysis of multiple structural change models.
  *Journal of Applied Econometrics*, 18(1), 1–22. doi:10.1002/jae.659
- Engel, C. (1996). The forward discount anomaly and the risk premium: A survey of recent
  evidence. *Journal of Empirical Finance*, 3(2), 123–192. doi:10.1016/0927-5398(95)00016-X
- Engel, C. and West, K. D. (2005). Exchange rates and fundamentals. *Journal of Political
  Economy*, 113(3), 485–517. doi:10.1086/429137
- Fatum, R. and Hutchison, M. M. (2006). Effectiveness of official daily foreign exchange market
  intervention operations in Japan. *Journal of International Money and Finance*, 25(2),
  199–219. doi:10.1016/j.jimonfin.2005.11.007
- Faust, J., Rogers, J. H., Wang, S.-Y. B. and Wright, J. H. (2007). The high-frequency response
  of exchange rates and interest rates to macroeconomic announcements. *Journal of Monetary
  Economics*, 54(4), 1051–1068. doi:10.1016/j.jmoneco.2006.05.015
- Fieller, E. C. (1954). Some problems in interval estimation. *Journal of the Royal Statistical
  Society, Series B*, 16(2), 175–185. doi:10.1111/j.2517-6161.1954.tb00159.x
- Forbes, K. J. and Rigobon, R. (2002). No contagion, only interdependence: Measuring stock
  market comovements. *Journal of Finance*, 57(5), 2223–2261. doi:10.1111/0022-1082.00494
- Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations.
  *Annals of Statistics*, 17(3), 1217–1241. doi:10.1214/aos/1176347265
- Liu, J., Wu, S. and Zidek, J. V. (1997). On segmented multivariate regression. *Statistica
  Sinica*, 7(2), 497–525.
- Lothian, J. R. and Wu, L. (2011). Uncovered interest-rate parity over the past two centuries.
  *Journal of International Money and Finance*, 30(3), 448–473.
  doi:10.1016/j.jimonfin.2011.01.005
- Meese, R. A. and Rogoff, K. (1983). Empirical exchange rate models of the seventies: Do they fit
  out of sample? *Journal of International Economics*, 14(1–2), 3–24.
  doi:10.1016/0022-1996(83)90017-X
- Newey, W. K. and West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and
  autocorrelation consistent covariance matrix. *Econometrica*, 55(3), 703–708.
  doi:10.2307/1913610
- Pesaran, M. H., Shin, Y. and Smith, R. J. (2001). Bounds testing approaches to the analysis of
  level relationships. *Journal of Applied Econometrics*, 16(3), 289–326. doi:10.1002/jae.616
- Rossi, B. (2013). Exchange rate predictability. *Journal of Economic Literature*, 51(4),
  1063–1119. doi:10.1257/jel.51.4.1063
- Sarno, L. and Valente, G. (2009). Exchange rates and fundamentals: Footloose or evolving
  relationship? *Journal of the European Economic Association*, 7(4), 786–830.
  doi:10.1162/JEEA.2009.7.4.786
- Schwarz, G. (1978). Estimating the dimension of a model. *Annals of Statistics*, 6(2), 461–464.
  doi:10.1214/aos/1176344136
- Wagner, M. and Wied, D. (2017). Consistent monitoring of cointegrating relationships: The US
  housing market and the subprime crisis. *Journal of Time Series Analysis*, 38(6), 960–980.
  doi:10.1111/jtsa.12247

---

## Appendix A. Reproducibility

| Result | Command | Output |
|---|---|---|
| H1a | `make h1a` | `notebooks/02_h1a_formal.ipynb` |
| H1b Stage 1 and audit | `make h1b-explore`; notebook 04 | `notebooks/03_…`, `notebooks/04_…` |
| H1b pilots | `research/methodology/adr0008-h1b-confirmatory-pilots/run_all.sh` | `reference_outputs/` |
| Phase A | `uv run python research/adr0007/run_breaks.py`, then `phase_a_figures.py` | `research/adr0007/out/phase_a/` |
| Phase C | `uv run python research/adr0007/phase_c.py` | `research/adr0007/out/phase_c/` (public) |
| Supplement S1–S6 | `uv run python paper/supplement/post_hoc.py` | `paper/supplement/out/` |

- Every run verifies the frozen-data checksums.
- Phase A, Phase C and the supplement rebuild byte for byte. The supplement's bootstrap uses a
  fixed seed.
- The supplement checks that it reproduces the Phase A volatility table and the selected
  2017-10-02 break.

## Appendix B. Derivations

**B.1 Slope, correlation and volatility.** With an intercept,

$$
\hat\beta = \widehat{\operatorname{cov}}(\Delta s,\Delta d)/\widehat{\operatorname{var}}(\Delta d)
= \hat\rho\,\hat\sigma_{\Delta s}/\hat\sigma_{\Delta d}, \qquad R^2=\hat\rho^2 .
$$

**B.2 Pooled slope as a weighted sum.**

$$
\hat\beta_{\text{pool}}
= \frac{\sum_g S_{xx,g}\hat\beta_g + \sum_g n_g(\bar x_g-\bar x)(\bar y_g-\bar y)}
{\sum_g S_{xx,g} + \sum_g n_g(\bar x_g-\bar x)^2}.
$$

**B.3 Daily-to-monthly aggregation.** For daily deviations x_t and y_t, demeaned within an era,
and monthly sums X_m and Y_m:

$$
\sum_m X_m Y_m = \sum_t x_t y_t + \sum_m \sum_{t\ne s\in m} x_t y_s .
$$

The "same-day share" in Table 4 is the first term divided by the left-hand side. The monthly
slope of summed changes equals the daily slope times
(same-day share of var Δd) / (same-day share of cov), up to the difference between era-level and
monthly demeaning.

**B.4 The H1a contrast.** δ = β_new − ⅔β_ref avoids the instability of a ratio test when the
denominator is imprecise. The Fieller interval for the ratio is reported only as a description.

## Appendix C. Frozen validation outcomes

| Check | Outcome | Consequence |
|---|---|---|
| Andrews–Kim size at T = 492, m = 55 | Failed (0.047–0.107 at nominal 0.025) | H1b not assessable |
| Wagner–Wied theory and size | Failed (theory excludes drift; size 0.02–0.90) | H1b not assessable |
| ADR 0007 §9.1 critical-value check | Failed, remains failed | Tests of the number of breaks withheld |
| Bai-interval coverage simulations | 76.5 %–97.2 % depending on design | Intervals reported as nominal |
| Phase A R comparison | 0 FAIL | Partitions verified |
| Event checksums | 0 mismatches | Event data unchanged since freeze |
