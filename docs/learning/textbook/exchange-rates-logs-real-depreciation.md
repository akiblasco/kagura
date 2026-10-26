# Exchange rates, logarithms and real depreciation

<p class="lead">Between December 2021 and July 2026 USD/JPY rose from 115.17 to 159.16. Was that
a 38 % move, a 28 % move or a 32-point move? And how did it become a 36-point
<em>real</em> depreciation? This chapter builds the tools KAGURA uses to answer such
questions precisely, starting from scratch.</p>

<span class="chip">Chapter 1</span>
<span class="chip">Beginner → intermediate</span>
<span class="chip">Used in H1a and H1b</span>

!!! abstract "What you will be able to do"
    1. Read an exchange-rate quote and say which currency got stronger.
    2. Explain why KAGURA measures changes in **log-points**, and convert between log-points
       and percentages.
    3. Define the **real exchange rate**, and split a nominal move into a real part and a
       relative-price part.
    4. Reproduce the H1b headline numbers (+32.4 nominal, −3.8 relative prices, +36.1 real)
       from four price indices.

---

## 1. Intuition: what an exchange rate measures

An exchange rate is the price of one currency in units of another. **USD/JPY = 159.16**
means one US dollar costs 159.16 yen. Write it as

$$
S_t = \frac{\text{yen}}{\text{dollar}} \quad\text{at time } t .
$$

Because \(S\) is the price *of the dollar*, a **higher** USD/JPY means a **stronger dollar
and a weaker yen**. When \(S\) rises from 115 to 159, a Japanese buyer needs more yen for
the same dollar: the yen has *depreciated*.

!!! tip "Quote convention"
    Markets write USD/JPY as "base/quote": the price of 1 unit of the base (USD) in the
    quote currency (JPY). KAGURA uses this convention throughout, so "USD/JPY rose" always
    means "the yen weakened".

That price alone says nothing about whether Japanese goods became cheap. If Japanese
prices had also doubled, a doubling of \(S\) would leave a US tourist's purchasing power
in Japan unchanged. To ask whether the yen is *cheap*, we need prices — that is the real
exchange rate (§4). First, though, we need a good way to measure *change*.

## 2. Why percentages misbehave

Take the move from 115.17 to 159.16 and measure it two ways:

| Viewpoint | Calculation | Change |
|---|---|---|
| Price of a dollar, in yen | 159.16 / 115.17 − 1 | **+38.2 %** |
| Price of a yen, in dollars | (1/159.16) / (1/115.17) − 1 | **−27.6 %** |

The same event is a 38 % rise from one side and a 28 % fall from the other. Percentages
have two more defects:

- **They do not add over time.** +50 % followed by −50 % leaves you at 75 % of where you
  started, not 100 %.
- **They do not add across factors.** Below, a +38.2 % nominal move will be built from a
  −3.7 % relative-price move and a +43.5 % real move, and 43.5 − 3.7 ≠ 38.2.

Logarithms fix all three problems at once.

## 3. Logarithms and log-points from first principles

### 3.1 The natural logarithm

The natural logarithm \(\ln y\) is the power to which \(e \approx 2.71828\) must be
raised to give \(y\): \(e^{\ln y} = y\). Its key property turns multiplication into
addition:

$$
\ln(a \cdot b) = \ln a + \ln b, \qquad \ln\!\left(\frac{a}{b}\right) = \ln a - \ln b, \qquad \ln(a^{k}) = k \ln a .
$$

### 3.2 Log-points

KAGURA defines the **log level** of the exchange rate as

$$
s_t = 100 \cdot \ln S_t ,
$$

and a change between two dates as the **log-point change**

$$
\Delta s = s_1 - s_0 = 100 \cdot \ln\!\left(\frac{S_1}{S_0}\right).
$$

| Symbol | Meaning | Units |
|---|---|---|
| \(S_t\) | USD/JPY at month-end \(t\) | yen per dollar |
| \(s_t\) | \(100 \ln S_t\), the log level | log-points (level has no direct meaning) |
| \(\Delta s\) | difference of log levels | log-points |

**Worked example (verified KAGURA data).** From the frozen vintage, \(S_{2021\text{-}12} =
115.17\) and \(S_{2026\text{-}07} = 159.16\), so \(s\) moves from 474.64 to 506.99:

$$
\Delta s = 100 \ln\!\left(\frac{159.16}{115.17}\right) = 100 \ln(1.38196) = 32.35 \text{ log-points}.
$$

From the yen's side, the price of a yen in dollars changes by
\(100 \ln(115.17/159.16) = -32.35\). **Same size, opposite sign** — the symmetry
percentages lack.

### 3.3 Why log-points approximate percentages for small changes

Let \(r\) be the proportional change, so \(S_1 = S_0(1+r)\). Then
\(\Delta s = 100\ln(1+r)\). The Taylor expansion of \(\ln(1+r)\) around \(r = 0\) is

$$
\ln(1+r) = r - \frac{r^2}{2} + \frac{r^3}{3} - \cdots
$$

For small \(r\) the squared and higher terms are negligible, so \(\Delta s \approx 100r\),
the percentage change. The gap grows with the move:

| Percentage change \(r\) | 1 % | 5 % | 10 % | 38.2 % | 100 % |
|---|---:|---:|---:|---:|---:|
| Log-points \(100\ln(1+r)\) | 0.995 | 4.88 | 9.53 | 32.35 | 69.31 |

<div class="chart-frame" markdown>
<p class="chart-title">Log-points against percentage change</p>
<p class="chart-sub">The curve bends below the dotted 45° line: large rises shrink, large falls grow.</p>
<div class="kchart short" data-chart="log-vs-pct"></div>
<p class="chart-source">Illustrative: computed from the formula, not from data.</p>
</div>

This is why H1a can describe its daily slope "in % per percentage point": daily USD/JPY
moves are a fraction of a percent, where log-points and percentages agree to two decimals.

### 3.4 Converting back

To turn log-points into a percentage, invert the logarithm:

$$
r = e^{\Delta s / 100} - 1 .
$$

For \(\Delta s = 32.35\): \(e^{0.3235} - 1 = 0.382\), the +38.2 % from §2.

??? question "Knowledge check: a round trip"
    USD/JPY rises 50 % and then falls 50 %. What is the total change in log-points, and
    where does the rate end up?

    **Answer.** \(100\ln 1.5 + 100\ln 0.5 = 40.55 - 69.31 = -28.77\) log-points. The rate
    ends at \(e^{-0.2877} = 0.75\) of where it started. Log-points add; percentages do
    not.

## 4. The real exchange rate

### 4.1 Definition

Let \(P^{US}_t\) and \(P^{JP}_t\) be consumer price indices. The **real exchange rate** is

$$
Q_t = \frac{S_t \cdot P^{US}_t}{P^{JP}_t} .
$$

Read it as: take a US consumption basket, priced \(P^{US}\) dollars; convert it to yen at
\(S\); divide by what the Japanese basket costs in yen. \(Q\) is the price of the US basket
**in Japanese baskets**. A rise in \(Q\) is a **real depreciation of the yen**: Japanese
goods got cheaper for someone holding dollars.

Take logs (×100) and the ratio becomes a sum:

$$
q_t = s_t + p^{US}_t - p^{JP}_t = s_t - x_t,
\qquad x_t = 100\ln\!\left(\frac{P^{JP}_t}{P^{US}_t}\right).
$$

| Symbol | Meaning (as defined in ADR 0008 §2) |
|---|---|
| \(q_t\) | real exchange rate, log level |
| \(x_t\) | relative price level, Japan vs US, log |
| \(p^{US}_t, p^{JP}_t\) | \(100\ln\) of each CPI |

Rearranged, \(s_t = q_t + x_t\). Taking differences gives **the decomposition KAGURA uses
in H1b**:

$$
\boxed{\;\Delta s = \Delta q + \Delta x\;}
$$

*A nominal move is a real move plus a relative-price move — exactly, because logs add.*

!!! warning "Index levels are arbitrary"
    CPIs are indices with arbitrary base years, so the *level* of \(x\) or \(q\) has no
    meaning — only changes do. KAGURA's \(x\) is −9.2 in January 1981 purely because of
    index bases.

### 4.2 Worked example: 2021-12 → 2026-07

From the frozen vintage (CPI by reference month):

| Index | Dec 2021 | Jul 2026 | % change | Log-points |
|---|---:|---:|---:|---:|
| Japan CPI (BIS) | 105.539 | 120.413 | +14.09 % | +13.19 |
| US CPI (BLS) | 280.845 | 332.813 | +18.50 % | +16.98 |
| USD/JPY | 115.17 | 159.16 | +38.20 % | +32.35 |

**Step 1, relative prices.**
\(\Delta x = 13.19 - 16.98 = -3.79\). Japanese prices rose *less* than US prices.

**Step 2, real exchange rate.**
\(\Delta q = \Delta s - \Delta x = 32.35 - (-3.79) = 36.14\) log-points.

**Step 3, interpret.** \(e^{0.3614} - 1 = 43.5\,\%\): a US basket buys 43.5 % more Japanese
baskets than in December 2021. The yen fell *more* in real terms than in nominal terms,
because lower Japanese inflation made Japan cheaper still.

<div class="chart-frame" markdown>
<p class="chart-title">Decomposing the 2021-12 → 2026-07 move</p>
<p class="chart-sub">Δs = Δq + Δx, in log-points. Hover for values.</p>
<div class="kchart short" data-chart="decomp" data-from="2021-12" data-to="2026-07"></div>
<p class="chart-source">Source: KAGURA frozen vintage, computed live from s, x and q (kagura.longrun.load_monthly).
Matches notebook 03: Δs +32.35, Δx −3.79, Δq +36.14.</p>
</div>

Now try percentages instead: relative prices moved \(1.1409/1.1850 - 1 = -3.72\,\%\) and
the real rate \(+43.54\,\%\). But \(43.54 - 3.72 = 39.82 \ne 38.20\). Percentages only
compound: \(1.4354 \times 0.9628 = 1.3820\). Logs give a decomposition that adds.

??? question "Knowledge check: which way did the yen move in real terms since 1981?"
    Nominally, USD/JPY fell from 206.70 (Jan 1981) to 159.16 (Jul 2026): \(\Delta s =
    -26.1\). Over the same period \(\Delta x = -92.5\). Did the yen strengthen or weaken
    in real terms?

    **Answer.** \(\Delta q = -26.1 - (-92.5) = +66.4\) log-points: a large **real
    depreciation**, a factor of \(e^{0.664} = 1.94\). The yen buys fewer dollars' worth of
    *goods* than in 1981, even though it buys more *dollars*. Japan's much lower inflation
    did the work.

### 4.3 Forty-five years of s, x and q

<div class="chart-frame" markdown>
<p class="chart-title">Nominal, relative-price and real components since 1981</p>
<p class="chart-sub">Log-points relative to January 1981. At every date, the blue line equals
orange plus green. Dotted line: January 2022.</p>
<div class="kchart" data-chart="sxq"></div>
<p class="chart-source">Source: KAGURA frozen vintage, 1981-01 to 2026-07, month-end USD/JPY and CPI by
reference month; US CPI for 2025-10 is missing.</p>
</div>

Three things stand out:

1. **Relative prices fell steadily** (green): Japanese inflation ran below US inflation for
   most of 45 years, so \(x\) declined by about 92 log-points.
2. **Nominal and real paths diverge.** The nominal yen strengthened on balance; the real
   yen weakened.
3. **The real rate is not mean-reverting in this sample.** Purchasing-power parity (PPP)
   predicts that \(q\) fluctuates around a constant. Instead \(q\) ends near its highest
   value (the weakest real yen, June 2026). Consistently, H1b's ADF/KPSS tests classify
   \(q\) as I(1) over 1981–2021 — no mean reversion detected.

## 5. Connections to KAGURA's hypotheses

| Where | How these tools are used |
|---|---|
| **H1a** | Daily change \(\Delta s_t = 100(\ln S_t - \ln S_{t-1})\) is regressed on the change in the 2Y yield gap. Its slope β is "% per pp" because daily log changes ≈ % changes. |
| **H1b, specs (a), (c), (d)** | Regress \(s\) on \(x\) and the rate gap; PPP would imply a coefficient of 1 on \(x\). |
| **H1b, spec (b)** | Uses \(q = s - x\) directly, i.e. imposes that coefficient of 1 ("PPP imposed"). |
| **H1b Stage 1** | The headline "+36.1 real vs +32.4 nominal" is exactly §4.2. |
| **ADR 0008 §7.2** | Bans "fair value": a real exchange rate is a measurement, not a benchmark. |

## 6. Common mistakes

1. **Reading the quote backwards.** USD/JPY up = yen *weaker*.
2. **Adding percentages** across time or across components. Add log-points, or multiply
   gross returns.
3. **Interpreting the level of \(q\) or \(x\).** Index bases are arbitrary; only changes
   and comparisons over time mean anything.
4. **Treating log-points as percentages for large moves.** 32.35 log-points is 38.2 %,
   not 32 %.
5. **Ignoring the consumption-tax steps in Japan's CPI** (1989, 1997, 2014, 2019). They
   shift \(x\) by up to about 4.8 log-points in total; H1b uses a tax-adjusted \(x\) as a
   robustness check.
6. **Mixing timing.** KAGURA aligns CPI by *reference month* and uses month-end USD/JPY.
   Monthly averages or release-date alignment give slightly different numbers.
7. **Calling the real rate "undervaluation".** A high \(q\) says Japan is cheap relative to
   its own past, given these indices. Whether that is a misalignment needs a model of
   equilibrium — and H1b found none that is defensible.

## 7. Interpretation limits

- **CPI baskets differ** between countries; \(Q\) compares baskets, not identical goods.
- **Bilateral, not effective.** This is the yen against the dollar only, not against a
  trade-weighted basket.
- **Current-vintage CPI.** Revised data are used, not what was known in real time.
- **One missing month.** US CPI for 2025-10 is absent in the frozen vintage.

## 8. Defending it in an interview

> *"Why log-points rather than percentage changes?"*
> Log changes are symmetric — the yen's fall equals the dollar's rise in size — they add
> over time, and they turn the real-exchange-rate identity into a sum, so a nominal move
> splits exactly into real and relative-price parts. For daily moves they are numerically
> identical to percentages to two decimals.

> *"The yen is at its weakest real level since 1981. Is it undervalued?"*
> That is a statement about the real exchange rate's level relative to its history, which
> depends on index choice and assumes the history is a valid anchor. Undervaluation needs
> an equilibrium model; our pre-2022 long-run models did not provide a defensible one, so
> we don't make that claim.

## 9. Practice problems

1. USD/JPY moves from 140.00 to 147.00. Compute the percentage and log-point change.
2. Over a year, Japanese CPI rises 3 % and US CPI 2 %, while USD/JPY is unchanged. What
   happens to \(q\), in log-points, and is that a real appreciation or depreciation of the
   yen?
3. Using the table in §4.2, compute the real *percentage* change of the yen against the
   dollar from the yen's point of view.
4. Show that \(\Delta q = \Delta s - \Delta x\) follows from \(Q = S P^{US}/P^{JP}\).
5. A colleague says: "USD/JPY rose 38 % while Japan's relative price fell 4 %, so the real
   depreciation was 42 %." What is wrong, and what is the correct figure?

??? success "Solutions"
    1. \(147/140 - 1 = 5.00\,\%\); \(100\ln(1.05) = 4.88\) log-points.
    2. \(\Delta x = 100\ln 1.03 - 100\ln 1.02 = 2.96 - 1.98 = 0.98\), so
       \(\Delta q = 0 - 0.98 = -0.98\). \(q\) falls: a **real appreciation** of the yen —
       Japanese goods became relatively dearer.
    3. From the yen's side the real rate is \(1/Q\), so the log change is \(-36.14\);
       as a percentage, \(e^{-0.3614} - 1 = -30.3\,\%\).
    4. \(\ln Q = \ln S + \ln P^{US} - \ln P^{JP}\). Multiply by 100 and difference between
       two dates: \(\Delta q = \Delta s - (\Delta p^{JP} - \Delta p^{US}) = \Delta s - \Delta x\).
    5. Percentages don't add. In log-points, \(\Delta q = 32.35 - (-3.79) = 36.14\), i.e.
       +43.5 % (because \(1.382 / 0.963 = 1.435\)), not 42 %.

## Sources

- Data: KAGURA frozen vintage 2026-09-15 and the two CPI files checksummed for H1b
  (`src/kagura/vintage.py`); series built by `kagura.longrun.load_monthly`.
- Definitions: [ADR 0008 §2](../../decisions/0008-h1b-long-run-protocol.md); H1a change
  definitions: [ADR 0006 §4.1](../../decisions/0006-h1-formal-testing-protocol.md).
- Results quoted: [H1b report](../reports/02-h1b-long-run-fundamentals.md) and
  `notebooks/03_h1b_exploratory.ipynb`.
