# Regression and interpreting coefficients

<p class="lead">H1a's headline is one number per era: when the 2-year US–Japan yield gap rose by one
percentage point, USD/JPY rose on average by 6.44 % in 2013–2021 and by 4.05 % after 2022.
This chapter derives where such a number comes from, what it measures, what it does
<em>not</em> measure, and how its uncertainty is computed, starting from a line through a
cloud of points.</p>

<span class="chip">Chapter 2</span>
<span class="chip">Beginner → intermediate</span>
<span class="chip">Used in H1a; foundations for H1b</span>

!!! abstract "What you will be able to do"
    1. Derive the ordinary least squares (OLS) intercept and slope from scratch.
    2. Show that the slope equals covariance over variance, and equals correlation times
       a ratio of standard deviations.
    3. Read a coefficient in its units ("% per pp") and convert it (per 10 bp, per 100 bp).
    4. Explain why H1a's R² *rose* after 2022 while its slope *fell*.
    5. Say precisely why a regression slope is an *association*, not a causal effect.
    6. Explain what a standard error is, and why H1a uses Newey–West (HAC) standard errors.

**Prerequisites.** [Chapter 1](exchange-rates-logs-real-depreciation.md) (log-points). Summation
notation is introduced below.

---

## 1. Intuition: one number for "how much does it move with?"

Every trading day, USD/JPY changes and so does the gap between US and Japanese 2-year
yields. Plot each day as a point: horizontal position the change in the gap, vertical
position the change in USD/JPY. If the cloud slopes upward, days on which the gap widened
tended to be days on which the dollar gained against the yen.

A **regression line** summarises that tendency with a single slope: "on average, a
one-unit move in \(x\) comes with a \(b\)-unit move in \(y\)". The rest of this chapter
makes "on average" precise.

<div class="chart-frame" markdown>
<p class="chart-title">Monthly USD/JPY changes against monthly 2Y-differential changes</p>
<p class="chart-sub">Each dot is one month. Lines are each era's least-squares fit. Hover a dot
for its month.</p>
<div class="kchart" data-chart="monthly-scatter"></div>
<p class="chart-source">Source: KAGURA frozen vintage, month-end s = 100·ln(USD/JPY) and 2Y
differential d (kagura.longrun.load_monthly); fits computed in the browser. The 2013–2021 slope
(108 months) reproduces H1a robustness variant R2 in notebook 02 (4.38). The 2022– line uses the
55 months to 2026-07 available to this chart and gives 7.50. R2 used 56 months to 2026-08 and
reports 7.45. These are monthly figures; H1a's primary result uses <em>daily</em> data (§9).</p>
</div>

## 2. Notation you need

| Notation | Read as | Meaning |
|---|---|---|
| \(x_i,\ y_i\) | "x sub i" | the \(i\)-th observation, \(i = 1, \dots, n\) |
| \(\sum_{i=1}^{n} x_i\) | "sum of \(x_i\) from 1 to \(n\)" | \(x_1 + x_2 + \dots + x_n\) |
| \(\bar x = \frac{1}{n}\sum_i x_i\) | "x bar" | sample mean |
| \(\hat b\) | "b hat" | an *estimate* of an unknown quantity \(b\) |
| \(\operatorname{Var}(x),\ \operatorname{Cov}(x,y)\) | variance, covariance | defined in §4 |

Two facts about sums are used repeatedly. Constants come out of sums, and sums split:

$$
\sum_i (c\,x_i) = c \sum_i x_i, \qquad \sum_i (x_i + y_i) = \sum_i x_i + \sum_i y_i, \qquad \sum_i c = n\,c .
$$

A consequence: deviations from the mean sum to zero,

$$
\sum_i (x_i - \bar x) = \sum_i x_i - n\bar x = n\bar x - n\bar x = 0 .
$$

## 3. Least squares, derived step by step

### 3.1 The model

We describe each \(y_i\) as a line plus a remainder:

$$
y_i = a + b\,x_i + e_i .
$$

| Symbol | Meaning |
|---|---|
| \(a\) | intercept: the fitted \(y\) when \(x = 0\) |
| \(b\) | slope: the change in fitted \(y\) per unit of \(x\) |
| \(e_i\) | residual: what the line misses for observation \(i\) |

For any candidate line \((a, b)\), the residual is \(e_i = y_i - a - b x_i\). **Least
squares** picks the line that makes the sum of squared residuals as small as possible:

$$
S(a, b) = \sum_{i=1}^{n} (y_i - a - b x_i)^2 .
$$

Why squares? They treat misses above and below the line alike, penalise large misses more
than small ones, and, crucially, give a smooth function whose minimum we can find with
calculus.

### 3.2 First-order conditions

At a minimum, the slope of \(S\) in every direction is zero. Differentiate with respect to
\(a\), using the chain rule \(\frac{d}{da}(u^2) = 2u\frac{du}{da}\) with \(u = y_i - a - b x_i\)
and \(\frac{du}{da} = -1\):

$$
\frac{\partial S}{\partial a} = \sum_i 2(y_i - a - b x_i)(-1) = -2\sum_i (y_i - a - b x_i) = 0 .
$$

Now with respect to \(b\), where \(\frac{du}{db} = -x_i\):

$$
\frac{\partial S}{\partial b} = \sum_i 2(y_i - a - b x_i)(-x_i) = -2\sum_i x_i(y_i - a - b x_i) = 0 .
$$

These are the **normal equations**. Divide each by \(-2\).

### 3.3 Solving for the intercept

From the first equation, split the sum:

$$
\sum_i y_i - n a - b \sum_i x_i = 0 .
$$

Divide by \(n\) and rearrange:

$$
\bar y - a - b\bar x = 0 \quad\Longrightarrow\quad \boxed{\hat a = \bar y - \hat b\,\bar x} .
$$

So the fitted line always passes through the point of means \((\bar x, \bar y)\). The
equation also says the residuals sum to zero.

### 3.4 Solving for the slope

Substitute \(a = \bar y - b\bar x\) into the second normal equation:

$$
\sum_i x_i\big(y_i - \bar y + b\bar x - b x_i\big) = 0
\quad\Longrightarrow\quad
\sum_i x_i (y_i - \bar y) = b \sum_i x_i (x_i - \bar x).
$$

One more step makes the result symmetric. Because \(\sum_i (y_i - \bar y) = 0\), we may
subtract \(\bar x \sum_i (y_i - \bar y) = 0\) from the left side without changing it, and
likewise \(\bar x\sum_i (x_i - \bar x) = 0\) from the right:

$$
\sum_i (x_i - \bar x)(y_i - \bar y) = b \sum_i (x_i - \bar x)^2 .
$$

Hence

$$
\boxed{\hat b = \frac{\sum_i (x_i - \bar x)(y_i - \bar y)}{\sum_i (x_i - \bar x)^2}} .
$$

This needs \(\sum_i (x_i - \bar x)^2 > 0\): \(x\) must vary. If \(x\) never moves, no slope
can be learned. (This matters for H1a's two-leg decomposition: the JGB 2Y yield barely moved
in 1999–2022, so its own coefficient is imprecise there *by construction*, ADR 0006 §6.3.)

??? info "Is it really a minimum?"
    The second derivatives are \(\partial^2 S/\partial a^2 = 2n > 0\) and
    \(\partial^2 S/\partial b^2 = 2\sum x_i^2\), with cross-derivative \(2\sum x_i\). The
    determinant of this matrix is \(4\big(n\sum x_i^2 - (\sum x_i)^2\big) = 4n\sum(x_i -
    \bar x)^2 > 0\) when \(x\) varies, so \(S\) is a bowl with a single lowest point.

### 3.5 A hand-sized example

*Illustrative numbers, not KAGURA data.* Five days of changes in the yield gap \(x\) (pp)
and in USD/JPY \(y\) (%):

| \(i\) | \(x_i\) | \(y_i\) | \(x_i - \bar x\) | \(y_i - \bar y\) | product | \((x_i-\bar x)^2\) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | −0.10 | −0.5 | −0.10 | −0.6 | 0.060 | 0.0100 |
| 2 | −0.05 | 0.1 | −0.05 | 0.0 | 0.000 | 0.0025 |
| 3 | 0.00 | −0.2 | 0.00 | −0.3 | 0.000 | 0.0000 |
| 4 | 0.05 | 0.4 | 0.05 | 0.3 | 0.015 | 0.0025 |
| 5 | 0.10 | 0.7 | 0.10 | 0.6 | 0.060 | 0.0100 |
| **sum** | 0.00 | 0.5 | 0 | 0 | **0.135** | **0.0250** |

Means: \(\bar x = 0\), \(\bar y = 0.1\). Slope \(\hat b = 0.135/0.025 = 5.4\) % per pp.
Intercept \(\hat a = 0.1 - 5.4 \times 0 = 0.1\).

## 4. The slope as covariance over variance

Define the sample variance and covariance (dividing by \(n\); dividing by \(n-1\) instead
changes nothing below, because it cancels):

$$
\operatorname{Var}(x) = \frac{1}{n}\sum_i (x_i - \bar x)^2, \qquad
\operatorname{Cov}(x, y) = \frac{1}{n}\sum_i (x_i - \bar x)(y_i - \bar y).
$$

Divide the numerator and the denominator of \(\hat b\) by \(n\):

$$
\hat b = \frac{\operatorname{Cov}(x,y)}{\operatorname{Var}(x)} .
$$

The **correlation** rescales covariance to lie between −1 and 1:
\(\rho = \operatorname{Cov}(x,y)/(\operatorname{sd}(x)\operatorname{sd}(y))\), where
\(\operatorname{sd} = \sqrt{\operatorname{Var}}\). Substituting
\(\operatorname{Cov} = \rho\,\operatorname{sd}(x)\operatorname{sd}(y)\) and
\(\operatorname{Var}(x) = \operatorname{sd}(x)^2\):

$$
\boxed{\hat b = \rho \cdot \frac{\operatorname{sd}(y)}{\operatorname{sd}(x)}} .
$$

**Slope is not correlation.** Correlation measures how tightly points hug a line; the
slope measures how steep the line is. A weak correlation with a very quiet \(x\) can still
give a steep slope.

!!! example "KAGURA example: the H1a slopes were visible before the test (verified record)"
    ADR 0006 §1.1 discloses that the exploratory notebook had already published era
    correlations and standard deviations from which the slopes could be approximated.
    The table separates these **exploratory approximations** (computed before the test,
    not estimates) from the **formal estimates** of notebook 02:

    | Era | \(\rho\) | sd(Δs), % | sd(Δd), pp | Exploratory approximation \(\rho\cdot\)sd(Δs)/sd(Δd) | Formal OLS estimate (notebook 02) |
    |---|---:|---:|---:|---:|---:|
    | 2013–2021 | 0.37 | 0.549 | 0.032 | ≈ 6.3 | **6.44** (se 0.50) |
    | 2022– | 0.44 | 0.666 | 0.073 | ≈ 4.0 | **4.05** (se 0.32) |

    Only the formal estimates enter the H1a test. The approximation is crude (an era mean of
    rolling correlations is not the era correlation), but it shows why ADR 0006 states
    that the formal test "does not add surprise": its value is exact estimation, valid
    uncertainty and a decision rule fixed in advance. Note also that the correlation *rose*
    (0.37 → 0.44) while the slope *fell*, because sd(Δd) more than doubled.

## 5. Reading a coefficient: units first

A slope has units of "\(y\)-units per \(x\)-unit". In H1a (ADR 0006 §4.1):

- \(\Delta s_t = 100(\ln S_t - \ln S_{t-1})\): daily log change of USD/JPY, in % (log-points,
  equal to % at daily sizes, [chapter 1 §3.3](exchange-rates-logs-real-depreciation.md#33-why-log-points-approximate-percentages-for-small-changes));
- \(\Delta d_t\): daily change in the 2Y differential, in percentage points (pp).

So \(\beta\) is in **% per pp**. Conversions:

| Statement | Calculation with \(\beta = 4.05\) |
|---|---|
| per 1 pp (100 bp) widening | +4.05 % |
| per 10 bp widening | \(4.05/10 = +0.405\) % |
| per 100 bp *narrowing* | −4.05 % (sign reverses) |

**Functional forms.** What a coefficient means depends on whether each side is in logs:

| \(y\) | \(x\) | \(b\) means |
|---|---|---|
| level | level | units of \(y\) per unit of \(x\) |
| \(100\ln y\) | level | % change in \(y\) per unit of \(x\) (approximately, for small changes) |
| \(100\ln y\) | \(100\ln x\) | % change in \(y\) per 1 % change in \(x\): an elasticity |

H1b's specification (a) regresses \(s = 100\ln S\) on \(x = 100\ln(P^{JP}/P^{US})\), a
log-on-log form. That is why purchasing-power parity predicts a coefficient of **1** on
\(x\): a 1 % rise in relative prices should come with a 1 % rise in the exchange rate.

**The intercept** in H1a (\(\alpha_e\)) is a daily drift and "is not interpreted" (ADR 0006
§4.3). Its value depends on where \(x = 0\) lies, which is often not an interesting place.

## 6. One regression, five eras: interaction terms

H1a does not run five separate regressions. It runs one pooled regression with an
**indicator** (dummy) per era (ADR 0006 §4.3):

$$
\Delta s_t = \sum_{e} \mathbb{1}[t \in e]\,(\alpha_e + \beta_e\,\Delta d_t) + \varepsilon_t .
$$

| Symbol | Meaning |
|---|---|
| \(\mathbb{1}[t \in e]\) | equals 1 if day \(t\) lies in era \(e\), else 0 |
| \(\alpha_e,\ \beta_e\) | intercept and slope specific to era \(e\) |
| \(\varepsilon_t\) | error term |

On a day in 2015, every indicator except "2013–2021" is zero, so the equation reduces to
\(\Delta s_t = \alpha_{2013\text{–}21} + \beta_{2013\text{–}21}\Delta d_t + \varepsilon_t\).
Because each coefficient pair only "sees" its own era's days, the least-squares problem
splits into five independent problems, and **the point estimates equal five separate
regressions**.

Why pool, then? Because the test needs the *joint* uncertainty of two era slopes, i.e. their
covariance (chapter 4). A pooled model delivers one covariance matrix for all ten
coefficients, and its HAC standard errors let each era have its own error variance (ADR 0006
§4.4).

## 7. R²: share of variance, not strength of a link

Split each \(y_i\) into fitted value and residual, \(y_i = \hat y_i + e_i\). Least squares
makes the residuals uncorrelated with the fitted values, so the variance splits too:

$$
\operatorname{Var}(y) = \operatorname{Var}(\hat y) + \operatorname{Var}(e) .
$$

The **coefficient of determination** is the share explained:

$$
R^2 = \frac{\operatorname{Var}(\hat y)}{\operatorname{Var}(y)} = 1 - \frac{\operatorname{Var}(e)}{\operatorname{Var}(y)} .
$$

With one regressor, \(\hat y_i = \hat a + \hat b x_i\), so \(\operatorname{Var}(\hat y) = \hat
b^2 \operatorname{Var}(x)\), and

$$
R^2 = \hat b^2\,\frac{\operatorname{Var}(x)}{\operatorname{Var}(y)}
= \left(\rho\,\frac{\operatorname{sd}(y)}{\operatorname{sd}(x)}\right)^2 \frac{\operatorname{sd}(x)^2}{\operatorname{sd}(y)^2} = \rho^2 .
$$

This is exactly ADR 0006 §4.3's definition \(R^2_e = \beta_e^2\operatorname{Var}_e(\Delta d)
/ \operatorname{Var}_e(\Delta s)\).

!!! example "Why H1a's R² rose while β fell (verified numbers, notebook 02)"
    | Era | β | R² |
    |---|---:|---:|
    | 2013–2021 | 6.44 | 0.133 |
    | 2022– | 4.05 | 0.191 |

    R² depends on \(\beta^2\) *and* on how much the differential moved. In 2022– the
    differential's daily changes were more than twice as variable (sd 0.073 vs 0.032 pp in
    the exploratory data), which more than offsets the smaller slope. **R² can rise when a
    link weakens** and fall when the regressor is quiet even if the link is unchanged. That
    is why ADR 0006 makes the slope the primary quantity and R² "descriptive only".

## 8. Association, not causation

The slope formula \(\operatorname{Cov}/\operatorname{Var}\) can be computed for any two
series. It is the **best linear predictor** coefficient (the linear projection): the \(b\)
minimising average squared prediction error. That interpretation needs no assumption
beyond finite variances. ADR 0006 assumption A3 says exactly this: the residual is
uncorrelated with \(\Delta d\) *by construction*, "not an assumption of exogeneity".

To read \(\beta\) as "the effect of a rate move on the yen", we would need \(\Delta d\) to
be as good as randomly assigned relative to everything else that moves the yen. It is not:

- **Common shocks.** A strong US payrolls report raises US yields *and* the dollar. Both
  move, neither causes the other.
- **Reverse causality.** A falling yen can raise Japanese inflation expectations and move
  JGB yields.
- **Timing.** USD/JPY is fixed at noon New York; US yields close about 3.5 hours later
  (ADR 0006 §4.5). The same-day slope includes post-fix US news. It is a contemporaneous
  association, not a real-time-feasible or forecasting relationship.

Hence KAGURA's rule: write "a 1 pp wider differential *is associated with* a 4.05 % higher
USD/JPY", never "raises" or "drives".

## 9. How precise is a slope? Standard errors

### 9.1 The idea

Re-run history with different daily news and you would get a different \(\hat\beta\).
The **standard error** \(\operatorname{se}(\hat\beta)\) estimates how much \(\hat\beta\) would
vary across such re-runs (its sampling standard deviation). Chapter 4 turns it into
intervals and tests. Here we need only its formula.

Write the slope as a weighted sum of errors. If \(y_i = a + b x_i + \varepsilon_i\), then

$$
\hat b = b + \frac{\sum_i (x_i - \bar x)\,\varepsilon_i}{\sum_i (x_i - \bar x)^2} .
$$

(Substitute \(y_i - \bar y = b(x_i - \bar x) + (\varepsilon_i - \bar\varepsilon)\) into the
formula of §3.4; the \(\bar\varepsilon\) term vanishes because deviations of \(x\) sum to zero.)

### 9.2 The classical formula and its assumptions

If the errors all have the same variance \(\sigma^2\) (**homoskedasticity**) and are
uncorrelated with one another, the variance of a sum of uncorrelated terms is the sum of
their variances:

$$
\operatorname{Var}(\hat b) = \frac{\sum_i (x_i - \bar x)^2 \sigma^2}{\big(\sum_i (x_i - \bar x)^2\big)^2}
= \frac{\sigma^2}{\sum_i (x_i - \bar x)^2} .
$$

Larger samples and more variation in \(x\) give more precise slopes.

### 9.3 Why KAGURA uses HAC standard errors

Daily FX data violate both assumptions:

- **Heteroskedasticity.** Volatility clusters: calm months, then turbulent ones.
- **Autocorrelation.** The timing mismatch spreads a US news shock across two FX days, so
  errors on consecutive days can be correlated (ADR 0006 §6.2).

The general variance replaces \(\sigma^2\sum(x_i-\bar x)^2\) by the variance of the *sum* of
scores \(g_i = (x_i - \bar x)\varepsilon_i\), including the covariances between nearby days.
The **Newey–West** estimator approximates it as

$$
\widehat{\operatorname{Var}}\Big(\sum_i g_i\Big) = \sum_i \hat g_i^2 + 2\sum_{\ell=1}^{L} w_\ell \sum_{i=\ell+1}^{n} \hat g_i\,\hat g_{i-\ell},
\qquad w_\ell = 1 - \frac{\ell}{L+1} .
$$

| Symbol | Meaning |
|---|---|
| \(\hat g_i\) | score built from the fitted residual \(\hat e_i\) |
| \(L\) | number of lags whose covariances are included |
| \(w_\ell\) | Bartlett weight: down-weights distant lags and keeps the variance positive |

The result is **heteroskedasticity- and autocorrelation-consistent (HAC)**. ADR 0006 §4.4
fixes \(L = \lfloor 4(T/100)^{2/9} \rfloor\). With \(T = 10{,}279\) daily rows:
\((102.79)^{2/9} = e^{(2/9)\ln 102.79} = e^{1.0295} = 2.80\), so \(L = \lfloor 11.2 \rfloor = 11\),
as notebook 02 reports.

??? question "Knowledge check: what does HAC fix, and what not?"
    HAC corrects the *standard error* for heteroskedasticity and short-range serial
    correlation. It does not change \(\hat\beta\), does not remove bias from omitted
    variables, and does not make a slope causal. With heavy tails or very persistent
    errors, its intervals can still be too narrow (ADR 0006 A2).

## 10. Where KAGURA uses this

| Concept | KAGURA use | Read more |
|---|---|---|
| OLS slope, Cov/Var | H1a's \(\beta_e\) by era; disclosure of approximate slopes | [H1a report §3](../reports/01-h1a-short-run-comovement.md), ADR 0006 §1.1, §4.3 |
| Interactions | Fully era-interacted pooled regression | `kagura.models.era_regression` ([src/kagura/models.py](https://github.com/akiblasco/kagura/blob/main/src/kagura/models.py)) |
| R² descriptive | R² 0.133 → 0.191 while β 6.44 → 4.05 | [Concept: R²](../concepts/inference.md#r-squared) |
| HAC | Newey–West, Bartlett, L = 11 | `kagura.models.hac_lag`; [concept: HAC](../concepts/inference.md#hac-standard-errors) |
| Log-log slopes | H1b's PPP coefficient θ on relative prices | [H1b report §3](../reports/02-h1b-long-run-fundamentals.md) |
| Association language | Every write-up | [Concept: association vs causation](../concepts/methodology.md#association-vs-causation) |

## 11. Common mistakes

1. **Reading a slope as a correlation**, or comparing slopes across eras by their R².
2. **Forgetting units.** "β = 4.05" means nothing without "% per pp".
3. **Interpreting the intercept** when \(x = 0\) is not meaningful.
4. **Treating "the residual is uncorrelated with \(x\)" as an assumption you can test.** OLS
   residuals are uncorrelated with \(x\) by construction; it says nothing about causality.
5. **Using classical standard errors on daily financial data.** They ignore volatility
   clustering and serial correlation.
6. **Calling β "the effect".** It is a projection coefficient: an association.

## 12. Defending it in an interview

> *"Your slope fell but your R² rose. Isn't that contradictory?"*
> No. R² equals β² times the variance ratio Var(Δd)/Var(Δs). After 2022 the differential
> moved more than twice as much day to day, so it accounts for a larger share of FX variance
> even with a smaller slope. That's why we test the slope and treat R² as descriptive.

> *"Doesn't the regression show that rates drive the yen?"*
> It shows a contemporaneous association. Common news moves both, and the same-day
> specification even includes US yield moves after the FX fix. We use association language
> throughout.

## 13. Practice problems

1. Using the five observations in §3.5, verify that the residuals sum to zero and compute
   \(R^2\).
2. Show that if every \(y_i\) is multiplied by 100, \(\hat b\) is multiplied by 100 and
   \(R^2\) is unchanged.
3. A regression of daily % changes in USD/JPY on daily changes in the differential measured
   in **basis points** gives a slope of 0.0644. What is the slope in % per pp?
4. In an era, \(\rho = 0.30\), sd(Δs) = 0.60 %, sd(Δd) = 0.05 pp. Compute β and R².
5. Explain, using §9.2, why the JGB-leg coefficient in H1a's two-leg decomposition is
   imprecise in 1999–2022.
6. A colleague writes: "The 2022– slope of 4.05 shows that a 100 bp BOJ hike would
   strengthen the yen by 4 %." List three problems with this sentence.

---

## Solutions

??? success "Solutions (try the problems first)"
    1. Fitted values \(\hat y = 0.1 + 5.4x\): −0.44, −0.17, 0.10, 0.37, 0.64. Residuals:
       −0.06, 0.27, −0.30, 0.03, 0.06, summing to 0.00. \(\sum e_i^2 = 0.0036 + 0.0729 +
       0.09 + 0.0009 + 0.0036 = 0.171\). \(\sum (y_i - \bar y)^2 = 0.36 + 0 + 0.09 + 0.09 +
       0.36 = 0.90\). \(R^2 = 1 - 0.171/0.90 = 0.81\). Check: \(\hat b^2 \sum(x-\bar
       x)^2/\sum(y-\bar y)^2 = 29.16 \times 0.025/0.90 = 0.81\). ✓
    2. \(\operatorname{Cov}(x, 100y) = 100\operatorname{Cov}(x,y)\) and \(\operatorname{Var}(x)\)
       is unchanged, so \(\hat b\) scales by 100. \(\rho\) is unchanged by rescaling, so
       \(R^2 = \rho^2\) is too.
    3. 1 pp = 100 bp, so the slope per pp is \(0.0644 \times 100 = 6.44\) % per pp.
    4. \(\beta = 0.30 \times 0.60/0.05 = 3.6\) % per pp; \(R^2 = 0.30^2 = 0.09\).
    5. \(\operatorname{Var}(\hat b) = \sigma^2/\sum(x_i - \bar x)^2\). With the JGB 2Y yield
       pinned near zero, its daily changes are almost all zero, so the denominator is tiny
       and the variance huge (ADR 0006 §6.3).
    6. (i) Causal language: β is an association. (ii) Extrapolation: a 100 bp BOJ hike is
       far outside typical daily moves, and the slope was estimated mostly on US-leg
       variation (US leg 4.21, JGB leg −0.19 in 2022–, a descriptive split). (iii) It ignores
       uncertainty (95 % interval 3.43 to 4.67) and the timing caveat (same-day includes
       post-fix US news).

## Sources

- Specification and assumptions: [ADR 0006](../../decisions/0006-h1-formal-testing-protocol.md)
  §1.1, §4.1–§4.5, §6.3, §7.
- Results: `notebooks/02_h1a_formal.ipynb` (β, se, R², L = 11, rows), via the
  [H1a report](../reports/01-h1a-short-run-comovement.md).
- Code: `kagura.models.era_regression`, `kagura.models.hac_lag`, `kagura.models.monthly_changes`.
