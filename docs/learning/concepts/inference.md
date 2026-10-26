# Statistical inference concepts

<p class="lead">How KAGURA estimates relationships and decides what the evidence supports:
regression slopes, robust standard errors, one-sided decision rules, error budgets, ratio
intervals, joint tests and simulation checks. The machinery behind H1a's "inconclusive" and
behind the rejection of two H1b methods.</p>

Status labels:
<span class="status implemented">Implemented</span>
<span class="status exploratory">Exploratory</span>
<span class="status rejected">Rejected</span>
<span class="status planned">Planned</span>
<span class="status background">Background</span>.
See the [concept index](../INDEX.md#concept-index).

---

## OLS slope as covariance over variance

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · H1a (ADR 0006 §4.3)</p>

**Plain English.** The least-squares slope says how much \(y\) moves on average per unit move in
\(x\). It equals their covariance divided by the variance of \(x\).

**Why it exists.** It condenses a cloud of points into one interpretable number with known
statistical properties.

**Definition.**

$$
\hat\beta = \frac{\sum_i (x_i - \bar x)(y_i - \bar y)}{\sum_i (x_i - \bar x)^2} = \frac{\operatorname{Cov}(x,y)}{\operatorname{Var}(x)} = \rho\,\frac{\operatorname{sd}(y)}{\operatorname{sd}(x)} .
$$

\(\rho\): correlation; sd: standard deviation.

**How KAGURA used it.** H1a's fully era-interacted regression
\(\Delta s_t = \sum_e \mathbb 1[t\in e](\alpha_e + \beta_e\Delta d_t) + \varepsilon_t\) gives one
slope per era, in % per pp (`kagura.models.era_regression`). A unit test checks that the pooled
coefficients equal separate era regressions.

**What we found.** β: 0.67 (1981–89), −0.14 (1990–98), 2.68 (1999–2012), **6.44** (2013–21),
**4.05** (2022–): these are the formal estimates (notebook 02). Separately, ADR 0006 §1.1 disclosed
that \(\rho\cdot\)sd ratios published in the exploration already gave *exploratory approximations*
of ≈ 6.3 and ≈ 4.0. Those were never estimates and never entered the test.

**Assumptions and limits.** It is a linear projection: always defined, never causal on its own
(ADR 0006 A3). Constant within an era by assumption (A1); otherwise an average.

**Common mistake.** Comparing correlations to infer how much the slope changed. The correlation
rose (0.37 → 0.44) while the slope fell.

**Go deeper.** [Chapter 2 §3–§4](../textbook/regression-coefficients.md#3-least-squares-derived-step-by-step) ·
[Inference cheatsheet](../cheatsheets/inference.md) · [H1a report](../reports/01-h1a-short-run-comovement.md) ·
[`models.py`](https://github.com/akiblasco/kagura/blob/main/src/kagura/models.py)

---

## R² and why it is descriptive {#r-squared}

<p class="concept-meta"><span class="status implemented">Implemented</span> (descriptive only) Level B · ADR 0006 §4.3, §5.2</p>

**Plain English.** R² is the share of the variance of \(y\) that the fitted line accounts for.

**Why it exists.** It summarises fit. But it mixes the strength of the link with how much the
regressor happened to move.

**Definition.** \(R^2 = 1 - \operatorname{Var}(e)/\operatorname{Var}(y)\). With one regressor,
\(R^2 = \rho^2 = \beta^2\operatorname{Var}(x)/\operatorname{Var}(y)\).

**How KAGURA used it.** Reported per era, never a decision input.

**What we found.** R² 0.133 (2013–21) → 0.191 (2022–) while β fell 6.44 → 4.05, because the
differential's daily changes became much more variable.

**Assumptions and limits.** Falls whenever the regressor is quiet, "even if the link is unchanged"
(ADR 0006 §4.3).

**Common mistake.** "R² rose, so the link strengthened."

**Go deeper.** [Chapter 2 §7](../textbook/regression-coefficients.md#7-r2-share-of-variance-not-strength-of-a-link)

---

## HAC (Newey–West) standard errors {#hac-standard-errors}

<p class="concept-meta"><span class="status implemented">Implemented</span> Level I · ADR 0006 §4.4; ADR 0008 §9.0</p>

**Plain English.** Standard errors that remain valid when error variance changes over time
(heteroskedasticity) and when nearby errors are correlated (autocorrelation).

**Why it exists.** Classical standard errors assume constant variance and no correlation. Daily FX
data have volatility clustering, and the timing mismatch creates short-lag dependence.

**Definition.** The variance of the score sum is estimated with Bartlett-weighted autocovariances
up to lag \(L\):

$$
\hat\Omega = \hat\Gamma_0 + \sum_{\ell=1}^{L}\Big(1 - \frac{\ell}{L+1}\Big)(\hat\Gamma_\ell + \hat\Gamma_\ell'), \qquad L = \lfloor 4(T/100)^{2/9}\rfloor .
$$

\(\hat\Gamma_\ell\): sample autocovariance of the scores at lag \(\ell\).

**How KAGURA used it.** H1a: Bartlett kernel, \(L = 11\) for 10,279 daily rows, about 5 monthly,
no small-sample correction (`kagura.models.hac_lag`; a test matches a manual Newey–West). H1b
exploratory: Bartlett kernel with Andrews (1991) automatic bandwidth.

**What we found.** HAC se of β_ref 0.504, of β_new 0.316.

**Assumptions and limits.** Needs weak dependence and finite fourth moments (A2). Heavy tails or
very persistent errors can still give intervals that are too narrow. It does not fix bias.

**Common mistake.** Thinking HAC makes a coefficient causal or unbiased. It only corrects the
standard error.

**Go deeper.** [Chapter 2 §9](../textbook/regression-coefficients.md#9-how-precise-is-a-slope-standard-errors) ·
[ADR 0006 §4.4](../../decisions/0006-h1-formal-testing-protocol.md)

---

## One-sided tests, confidence bounds and p-values {#one-sided-tests-bounds-and-p-values}

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · ADR 0006 §5.1</p>

**Plain English.** A one-sided test asks about one direction only ("is it below?"). A one-sided
97.5 % bound is the value the parameter is unlikely to exceed. Rejecting at 2.5 % and the bound
excluding the null value are the same decision.

**Why it exists.** H1a's claims are directional: decline of at least a third (S), or not (R).

**Definition.** With \(c = \Phi^{-1}(0.975) = 1.959964\), \(z = \hat\delta/\operatorname{se}\):

| Test | Null | p-value | Bound | Reject if |
|---|---|---|---|---|
| S | \(\delta \ge 0\) | \(\Phi(z)\) | \(U = \hat\delta + c\,\operatorname{se}\) | \(U < 0\) |
| R | \(\delta \le 0\) | \(1-\Phi(z)\) | \(L = \hat\delta - c\,\operatorname{se}\) | \(L > 0\) |

**How KAGURA used it.** `kagura.models.contrast`, `rejects_below`, `rejects_above`. A bound exactly
at 0 is "not rejected" (tested).

**What we found.** \(\hat\delta = -0.2418\), se 0.4615, \(z = -0.52\), \(p_S = 0.30\), \(p_R = 0.70\),
\(U = 0.66\), \(L = -1.15\). Neither rejects.

**Assumptions and limits.** Normal approximation (A7), supported by large era samples.

**Common mistake.** Reading \(p_S = 0.30\) as "30 % chance the decline is less than a third".

**Go deeper.** [Chapter 4 §4–§6](../textbook/hypothesis-testing-uncertainty.md#4-confidence-intervals-derived) ·
[Inference cheatsheet](../cheatsheets/inference.md)

---

## Pre-registration, gates and outcome categories {#pre-registration-gates-and-outcome-categories}

<p class="concept-meta"><span class="status implemented">Implemented</span> Level I · ADR 0006 §1.1, §5; ADR 0008</p>

**Plain English.** Write down the test, the threshold and what each possible result will be
called, and freeze it publicly, before running it on real data. A **gate** is a precondition
that must pass for the main question to make sense.

**Why it exists.** Choosing thresholds, samples or wording after seeing results inflates
false-positive rates (the "garden of forking paths"). Naming the outcomes in advance stops a
non-result from being spun as support for either side.

**Definition.** H1a's categories:

| Outcome | Condition |
|---|---|
| Not assessable | gate fails (\(L_{\text{ref}} \le 0\)) |
| Supported | gate passes, S rejects |
| Material decline ruled out | gate passes, R rejects |
| Inconclusive | gate passes, neither rejects |

**How KAGURA used it.** ADR 0006 frozen 2026-10-09 and run once on 2026-10-21; ADR 0008 frozen
before any H1b levels model. The ⅓ threshold is "a preselected operational definition of
materiality", not an economic constant.

**What we found.** H1a: inconclusive. H1b: not assessable (no valid method). ADR 0006 §1.1 discloses
that approximate slopes were already visible, so the test was "pre-specified, not blind".

**Assumptions and limits.** Pre-registration does not remove prior knowledge. Error rates
*conditional* on passing the gate are not controlled.

**Common mistake.** Treating "inconclusive" as a failed study. It is a pre-defined, informative
outcome.

**Go deeper.** [Chapter 4 §6.5](../textbook/hypothesis-testing-uncertainty.md#65-four-outcomes-fixed-in-advance) ·
[Methodology: confirmatory vs exploratory](methodology.md#confirmatory-vs-exploratory-analysis) ·
[ADR 0006](../../decisions/0006-h1-formal-testing-protocol.md)

---

## Multiple testing and Bonferroni α splits {#multiple-testing-and-bonferroni}

<p class="concept-meta"><span class="status implemented">Implemented</span> Level I · ADR 0006 §8; ADR 0008 §0</p>

**Plain English.** The more tests you run, the more likely one gives a false positive. Bonferroni
splits the total error budget across tests so the chance of *any* false positive stays within it.

**Why it exists.** H1 has two confirmatory claims (H1a, H1b); without adjustment the family-wise
false-support rate could approach 10 %.

**Definition.** \(P(\bigcup_k A_k) \le \sum_k P(A_k)\), so \(\alpha_k = \alpha_{FW}/K\) bounds the
family-wise error at \(\alpha_{FW}\) under any dependence.

**How KAGURA used it.** H1 family α = 0.05, split 0.025 each. Bonferroni over Holm so H1a could be
finalised before H1b was specified. R (a claim against H1) is outside the family.

**What we found.** H1b spent nothing; its 0.025 is unused and not reallocated. Realised family-wise
bound: ≤ 0.025.

**Assumptions and limits.** Conservative when tests are correlated. Secondary and robustness
results are unadjusted and labelled so.

**Common mistake.** Reallocating unused α after seeing that one test failed or could not be run.

**Go deeper.** [Chapter 4 §9](../textbook/hypothesis-testing-uncertainty.md#9-many-tests-controlling-the-family-wise-error)

---

## Fieller confidence sets for ratios {#fieller-confidence-sets}

<p class="concept-meta"><span class="status implemented">Implemented</span> Level A · ADR 0006 §5.2</p>

**Plain English.** A confidence set for a ratio of two estimates, built by asking which ratios are
compatible with the data, rather than by assuming the ratio is normal.

**Why it exists.** A ratio's distribution is skewed and heavy-tailed when the denominator is
imprecise; the delta method then gives misleadingly tight, symmetric intervals.

**Definition.**
\(\{\rho : (\hat\beta_{\text{new}} - \rho\hat\beta_{\text{ref}})^2 \le c^2(V_{nn} - 2\rho V_{nr} + \rho^2 V_{rr})\}\),
a quadratic inequality. Bounded if and only if \(\hat\beta_{\text{ref}}\) is significant at the same
level; otherwise unbounded or a union of two intervals.

**How KAGURA used it.** `kagura.models.fieller`, tested against brute force and at the
bounded/unbounded boundary. Required to be reported "never truncated or replaced by the delta method".

**What we found.** Relative change −37.1 %, Fieller 95 % **[−49.4 %, −21.7 %]**.

**Assumptions and limits.** Normal approximation of the linear combination. Descriptive in H1a: the
decision uses δ.

**Common mistake.** Using the delta method because it is the software default.

**Go deeper.** [Chapter 4 §7](../textbook/hypothesis-testing-uncertainty.md#7-uncertainty-of-a-ratio-fiellers-method)

---

## Wald tests

<p class="concept-meta"><span class="status implemented">Implemented</span> (secondary) Level I · ADR 0006 §6.1</p>

**Plain English.** A test of several restrictions at once, such as "all five era slopes are equal".

**Why it exists.** Testing restrictions one at a time misses their joint evidence and inflates errors.

**Definition.** \(W = (R\hat\beta)'[R\hat VR']^{-1}(R\hat\beta) \sim \chi^2(q)\) approximately, \(q\)
= number of restrictions.

**How KAGURA used it.** Era equality, HAC covariance, χ²(4), α = 0.05, unadjusted, secondary
(`kagura.models.era_equality`; matches statsmodels in a test).

**What we found.** \(W = 239\), \(p \approx 10^{-50}\): slopes differ strongly across eras. 2013–2021 is
an unusually high reference.

**Assumptions and limits.** Says the slopes are not all equal, not which differ or when.

**Common mistake.** Reading a Wald rejection as support for H1a. It never decides H1a.

**Go deeper.** [Chapter 4 §8](../textbook/hypothesis-testing-uncertainty.md#8-testing-several-restrictions-at-once-the-wald-test)

---

## Rolling-window estimates

<p class="concept-meta"><span class="status exploratory">Exploratory</span> Level B · ADR 0004; ADR 0006 §6.3</p>

**Plain English.** Re-estimate a correlation or slope over a moving window (for example the last
250 trading days) to see how it drifts.

**Why it exists.** It shows *when* a relationship changed, descriptively, without assuming a break date.

**Definition.** For window length \(w\), \(\hat\beta_t\) = OLS slope over rows \(t-w+1,\dots,t\).
KAGURA reports a value only if ≥ 80 % of the window survives exclusion.

**How KAGURA used it.** 1-year (250 rows) and 3-year (750 rows) rolling correlations (ADR 0004)
and rolling β and R² (`kagura.models.rolling_beta`).

**What we found.** Rolling β declined before 2022 (ADR 0008 §1), one reason H1a's 2022-01 boundary
may be mis-dated (A6) and a motivation for Stage 2.

**Assumptions and limits.** Overlapping windows are strongly autocorrelated; pointwise bands
understate uncertainty. "Not a structural-break test" (ADR 0004).

**Common mistake.** Dating a break where the rolling line crosses a threshold.

**Go deeper.** [H1a report §4](../reports/01-h1a-short-run-comovement.md#4-results)

---

## Monte Carlo critical values and size/power simulation {#monte-carlo-size-and-power}

<p class="concept-meta"><span class="status implemented">Implemented</span> (synthetic data) Level A · ADR 0008 §3–§5, §8.3</p>

**Plain English.** Check whether a test really rejects a true null at its stated rate, and how often
it detects a real change, by running it on thousands of synthetic datasets where the truth is known.

**Why it exists.** Asymptotic theory may not hold at your sample size, persistence or tuning rules.

**Definition.** Size estimate \(\hat p = \#\text{rejections}/R\) under \(H_0\), with Monte Carlo
standard error \(\sqrt{\hat p(1-\hat p)/R}\). KAGURA used exact Clopper–Pearson intervals and a screen
at 1.5α = 0.0375, a project convention (ADR 0008 §3).

**How KAGURA used it.**
- Pilots of Andrews–Kim (4,000 replications per cell) and Wagner–Wied (2,000 null, 1,000 power),
  archived under `research/methodology/adr0008-h1b-confirmatory-pilots/`.
- Simulated 95 % full-procedure quantiles for the bounds test (`kagura.longrun.simulate_bounds_quantiles`).
- Implementations validated first: Andrews–Kim reproduced the published Table 1 (e.g. 0.0554 vs 0.057).

**What we found.** Andrews–Kim size 0.047–0.107 at nominal 0.025; Wagner–Wied size depended on the
bandwidth rule (0.02 to 0.90) and power was 0.02–0.08. Simulated bounds quantiles are stricter than
asymptotic ones (F 4.93 vs PSS I(1) bound 4.85 for k = 2).

**Assumptions and limits.** Results hold for the simulated data-generating process. The pilot
persistence values were design points, **not estimates for USD/JPY** (ADR 0008 §7).

**Common mistake.** Treating simulation results as empirical evidence about the data.

**Go deeper.** [Chapter 4 §10](../textbook/hypothesis-testing-uncertainty.md#10-does-the-test-do-what-it-says-monte-carlo-size-and-power) ·
[H1b case study](../journal/h1b-methodological-journey.md) · [ADR 0008](../../decisions/0008-h1b-long-run-protocol.md)
