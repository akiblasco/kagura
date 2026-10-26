# Economics and finance concepts

<p class="lead">The economic ideas behind KAGURA's questions: how exchange-rate moves are
measured, why interest-rate gaps should matter for a currency, what "real" means, and
the Japanese policy regimes that bound KAGURA's eras.</p>

Each entry has a **status**:
<span class="status implemented">Implemented</span> used in a KAGURA result ·
<span class="status exploratory">Exploratory</span> used descriptively ·
<span class="status rejected">Rejected</span> investigated and not used ·
<span class="status planned">Planned</span> in a plan, not yet run ·
<span class="status background">Background</span> context only, not estimated.
The full list is in the [concept index](../INDEX.md#concept-index).

---

## Log returns and percentage changes

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · ADR 0004, ADR 0006 §4.1, ADR 0008 §2</p>

**Plain English.** A log-point change is 100 times the difference of natural logs. For
small moves it equals the percentage change; for large ones it is smaller, but it has
better arithmetic.

**Why it exists.** Percentage changes are asymmetric (+38 % for the dollar is −28 % for
the yen), do not add over time, and do not add across components. Log changes fix all three.

**Definition.**

$$
\Delta s_t = 100\,(\ln S_t - \ln S_{t-1}) = 100\ln\frac{S_t}{S_{t-1}}, \qquad r = e^{\Delta s/100} - 1 .
$$

\(S_t\): USD/JPY (yen per dollar); \(\Delta s_t\): log-point change; \(r\): proportional change.

**How KAGURA used it.** H1a's dependent variable is the daily log change of USD/JPY
(`kagura.explore.changes`). H1b works with the log level \(s = 100\ln S\) and log relative prices.

**What we found.** 2021-12 → 2026-07: \(\Delta s = 100\ln(159.16/115.17) = 32.35\)
log-points = +38.2 %. Daily moves are fractions of a percent, so H1a's slope can be stated
"in % per pp" without approximation error that matters.

**Assumptions and limits.** The level \(s\) has no direct meaning, only changes do. For
large moves, convert back with \(e^{\Delta s/100} - 1\).

**Common mistake.** Reporting 32 log-points as "a 32 % rise". It is 38.2 %.

**Go deeper.** [Chapter 1 §2–§3](../textbook/exchange-rates-logs-real-depreciation.md#2-why-percentages-misbehave) ·
[FX cheatsheet](../cheatsheets/fx-inflation-ppp.md) · [ADR 0004](../../decisions/0004-h1-exploratory-specification.md) ·
[`explore.py`](https://github.com/akiblasco/kagura/blob/main/src/kagura/explore.py)

---

## Interest-rate differential and carry

<p class="concept-meta"><span class="status implemented">Implemented</span> (differential) · <span class="status background">Background</span> (carry) · Level B · H1a, H1b</p>

**Plain English.** The differential is how much more a US government bond yields than a
Japanese one of the same maturity. A *carry trade* borrows in the low-yield currency (yen)
and invests in the high-yield one (dollar), earning the gap as long as the exchange rate
does not move against it.

**Why it exists.** If investors chase yield, a wider gap should raise demand for dollars
relative to yen. That intuition underlies the popular reading of USD/JPY as "a function of
rate differentials", which KAGURA tests.

**Definition.**

$$
d_t = i^{US}_t - i^{JP}_t \quad\text{(percentage points)} .
$$

\(i^{US}\): US Treasury constant-maturity yield (FRED `DGS2`/`DGS10`); \(i^{JP}\): JGB par
yield (Ministry of Finance). Primary maturity: 2 years; robustness: 10 years (from 1986-07).

**How KAGURA used it.** H1a regresses daily \(\Delta s\) on daily \(\Delta d\) (2Y primary,
10Y as robustness R3). H1b uses the level \(d\) (\(d2\), \(d10\)) and a real-rate proxy
\(r = d2 - (\pi^{US} - \pi^{JP})\) built from realised 12-month inflation (ADR 0008 §9.1).

**What we found.**
- The JGB 2Y yield was pinned near zero from about 1999 to 2022, so the 2Y differential was
  essentially the US 2Y yield. Since 2024 the JGB leg moves again (2Y ≈ 1.8 %, 10Y ≈ 3.0 %
  in September 2026; notebook 01).
- In H1a's descriptive two-leg split for 2022–, the US-leg coefficient is 4.21 and the JGB
  leg's −0.19 (ADR 0006 §6.3): the "differential" link is mostly a US-yield link.

**Assumptions and limits.** Government yields, not money-market or policy rates; the call
rate starts in 1985-07 (ADR 0002). Carry returns and positioning were **not** measured: they
belong to later hypotheses (H2–H7, [roadmap](../../ROADMAP.md)).

**Common mistake.** Treating the differential as one variable when one leg barely moves. A
narrowing can come from either leg, with possibly different associations.

**Go deeper.** [H1a report §2](../reports/01-h1a-short-run-comovement.md) ·
[Chapter 2](../textbook/regression-coefficients.md) · [ADR 0002](../../decisions/0002-data-sources.md) ·
[ADR 0006 §6.3](../../decisions/0006-h1-formal-testing-protocol.md)

---

## Uncovered interest parity and its failure

<p class="concept-meta"><span class="status background">Background</span> Level I · H1a interpretation, ADR 0008 §9.4</p>

**Plain English.** UIP says that, if investors are risk-neutral, the higher-yielding
currency should be expected to *depreciate* by exactly the yield gap, so that holding either
currency earns the same expected return.

**Why it exists.** It is the benchmark no-arbitrage condition linking interest rates and
expected exchange-rate changes.

**Definition.** With \(s\) the log price of the dollar in yen and horizon-matched yields,

$$
E_t[s_{t+h}] - s_t = \big(i^{JP}_t - i^{US}_t\big)\cdot h \quad(\text{annualised rates, horizon } h \text{ in years}) .
$$

A higher US yield implies an expected *fall* in USD/JPY.

**How KAGURA used it.** Not tested. It shapes interpretation: ADR 0008 §9.4 uses
"uncovered-interest-parity / real-interest-differential reasoning" to expect a *positive*
long-run coefficient on the differential (a higher US rate goes with a stronger dollar
*level*). That is consistent with UIP when a rate rise causes an immediate jump followed
by expected depreciation (overshooting, Dornbusch 1976).

**What we found.** Nothing about UIP itself. H1a's positive contemporaneous slope says
nothing about expected *future* changes.

**Assumptions and limits.** UIP assumes risk neutrality and rational expectations.
Empirically, high-yield currencies have tended to appreciate rather than depreciate (the
"forward premium puzzle", Fama 1984), which is what makes carry trades profitable on average.

**Common mistake.** Reading a positive same-day association between rate gaps and the
dollar as "UIP holds" or "UIP fails". UIP concerns expected future changes, not
contemporaneous co-movement.

**Go deeper.** [H1b report §1](../reports/02-h1b-long-run-fundamentals.md) ·
[ADR 0008 §9.4](../../decisions/0008-h1b-long-run-protocol.md)

---

## Purchasing power parity; nominal vs real exchange rate

<p class="concept-meta"><span class="status implemented">Implemented</span> Level I · H1b Stage 1 (ADR 0008 §9.1, §9.4)</p>

**Plain English.** The real exchange rate compares what a basket of goods costs in the two
countries after converting currencies. PPP says that, over the long run, it should return to
a constant: exchange rates offset inflation differences.

**Why it exists.** A nominal move can reflect inflation differences rather than a change in
competitiveness. The real rate separates the two.

**Definition.**

$$
q_t = s_t - x_t, \qquad x_t = 100\ln\frac{P^{JP}_t}{P^{US}_t}, \qquad \Delta s = \Delta q + \Delta x .
$$

\(q\): real exchange rate (rising = real yen depreciation); \(x\): relative price level;
\(P\): CPI. PPP implies a coefficient \(\theta = 1\) on \(x\) in a regression of \(s\) on
\(x\), and a stationary \(q\).

**How KAGURA used it.** The Stage 1 decomposition of the 2021-12 → 2026-07 move;
specification (b) imposes PPP (\(\theta = 1\)) by modelling \(q\) directly; the economic
plausibility layer asks whether \(\hat\theta\)'s interval overlaps (0, 2) (ADR 0008 §9.4).

**What we found.**
- Δs = +32.35, Δx = −3.79, so Δq = **+36.14**: the depreciation was entirely real.
- 1981–2026: Δs = −26.1 and Δx = −92.5, so Δq = +66.4. The yen buys more dollars but fewer
  dollars' worth of goods.
- \(q\) classified I(1) over 1981–2021 (ambiguous from 1990): mean reversion not
  established. ARDL estimates of \(\theta\) had the wrong sign in (a) (−0.30, se 0.73), while
  FM-OLS/D-OLS gave ≈ 0.8.

**Assumptions and limits.** CPI baskets differ; bilateral, not trade-weighted; current-vintage
CPI; US CPI for 2025-10 missing. ADR 0008 §7.2 bans "fair value" and "undervalued".

**Common mistake.** Calling a high real exchange rate "undervaluation". That requires an
equilibrium model, and none was defensible.

**Go deeper.** [Chapter 1 §4](../textbook/exchange-rates-logs-real-depreciation.md#4-the-real-exchange-rate) ·
[FX cheatsheet](../cheatsheets/fx-inflation-ppp.md) · [H1b report](../reports/02-h1b-long-run-fundamentals.md) ·
`kagura.longrun.load_monthly` ([`longrun.py`](https://github.com/akiblasco/kagura/blob/main/src/kagura/longrun.py))

---

## Yield-curve control, QQE and the zero lower bound

<p class="concept-meta"><span class="status background">Background</span> Level I · ADR 0004 eras and events</p>

**Plain English.** When short-term rates hit zero (the **zero lower bound**), the Bank of
Japan used other tools: buying large amounts of assets (**QQE**, from 2013), a negative policy
rate (2016), and **yield-curve control** (YCC, 2016–2024), a target for the 10-year JGB yield.

**Why it exists.** These are the policy regimes whose effect on the yen–rate link KAGURA
studies. They also explain why the JGB leg of the differential barely moved for two decades.

**Definition.** Not a formula: a set of dated regime changes, fixed in advance in ADR 0004.

| Date | Event |
|---|---|
| 1999-02-12 | BOJ zero interest rate policy |
| 2001-03-19 / 2006-03-09 | BOJ quantitative easing / exit |
| 2013-04-04 | QQE |
| 2016-01-29 | negative interest rate |
| 2016-09-21 | yield curve control |
| 2022-12-20 | YCC band widened |
| 2024-03-19 | negative rate and YCC end |

**How KAGURA used it.** The eras 1981–89, 1990–98, 1999–2012, 2013–21 and 2022– are bounded
by these regimes "for description, not estimated breaks" (ADR 0004). H1a's reference era is
2013–2021 (QQE/YCC); its new era starts at the candidate boundary 2022-01.

**What we found.** H1a's slope is near zero before 1999 and peaks in 2013–2021 (6.44), so
the QQE/YCC era is an unusually *high* reference, not a historical norm.

**Assumptions and limits.** The event list reflects prior knowledge of yen history (ADR 0004
risks). Fixing it in advance limits tuning but cannot remove that knowledge.

**Common mistake.** Treating era boundaries as estimated break dates. They are labels; break
dating is Stage 2.

**Go deeper.** [ADR 0004](../../decisions/0004-h1-exploratory-specification.md) ·
[H1a report §4](../reports/01-h1a-short-run-comovement.md) · [Home timeline](../../index.md)

---

## FX intervention (Ministry of Finance)

<p class="concept-meta"><span class="status planned">Planned</span> Level I · ADR 0004 event marker; Stage 2 plan</p>

**Plain English.** Japan's Ministry of Finance (MOF) sometimes buys or sells yen directly to
influence its price. The Bank of Japan executes the trades.

**Why it exists.** Intervention is a candidate reason why the yen might move differently
from rate differentials in some periods.

**Definition.** A dated event with a direction (yen-buying or yen-selling) and an amount.

**How KAGURA used it.** Only as an event marker: 2022-09-22, "MOF yen-buying intervention
(first since 1998)" (ADR 0004). The 1985 Plaza and 1987 Louvre Accords (coordinated policy
agreements) are also markers. Matching estimated break dates to intervention records is part
of the Stage 2 plan, which is **under review and has not been run**.

**What we found.** Nothing yet.

**Assumptions and limits.** Intervention data are not in the frozen vintage; using them needs
a data ADR. ADR 0001 notes the 1980s were heavily influenced by coordinated intervention, so a
weak 1980s rate link is "not evidence for the modern decoupling claim by itself".

**Common mistake.** Inferring that an intervention "caused" a move because the dates
coincide. Coincidence of dates is association, and KAGURA's planned wording is "coincides with".

**Go deeper.** [ADR 0001](../../decisions/0001-sample-period.md) ·
[ADR 0004](../../decisions/0004-h1-exploratory-specification.md) · [Roadmap](../../ROADMAP.md)

---

## Consumption-tax steps in Japanese CPI

<p class="concept-meta"><span class="status exploratory">Exploratory</span> Level I · H1b Stage 1 spec (d) and audit</p>

**Plain English.** Japan raised its consumption tax in April 1989, April 1997, April 2014 and
October 2019. Each rise lifted the CPI in one month. That is a price-level jump, not ongoing
inflation, and it shifts relative prices \(x\).

**Why it exists.** A one-off jump can distort unit-root tests and long-run regressions of
\(s\) on \(x\). A tax-adjusted \(x\) checks whether results depend on it.

**Definition (KAGURA's adjustment).** For each tax month, the excess of that month's
\(\Delta x\) over its 1981–2021 same-calendar-month median (tax months excluded) is removed
permanently from \(x\) from that month on (`kagura.longrun.tax_adjusted`). Together the four
steps shift \(x\) by up to about 4.8 log-points.

**How KAGURA used it.**
- Specification (d) uses tax-adjusted \(x\) (ADR 0008 §9.4).
- Unit-root tests on \(\Delta x\) include tax-month impulse dummies (§9.2).
- The audit's sensitivity variant adds lagged tax impulses from superseded draft r3
  (notebook 04).

**What we found.** Tax-adjusted \(x\) is I(1), like raw \(x\). Specification (d) was "not
defensible", like (a): t = −1.88, F = 3.97, \(\hat\theta = -0.27\). The tax treatment did
not change any classification.

**Assumptions and limits.** The median-based step size is a modelling choice. 2023 energy
subsidies also distort \(x\) and are not adjusted (ADR 0008 A8).

**Common mistake.** Treating tax months as inflation. They are level shifts.

**Go deeper.** [H1b report §3–§4](../reports/02-h1b-long-run-fundamentals.md) ·
[Chapter 1 §6](../textbook/exchange-rates-logs-real-depreciation.md#6-common-mistakes) ·
[`longrun.py`](https://github.com/akiblasco/kagura/blob/main/src/kagura/longrun.py)
