---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>
<div markdown>
<p class="eyebrow">KAGURA · USD/JPY research</p>

# Has the yen decoupled from interest rates?

<p class="lead">For two decades the yen was read as a function of the gap between US and
Japanese interest rates. After 2022 it fell to its weakest real level in our 45-year
sample. KAGURA tests, with pre-registered methods and frozen data, whether that
rate–currency link has really changed.</p>

<span class="chip">v0.1 · research foundation</span>
<span class="chip">2 hypotheses tested</span>
<span class="chip">local preview · not published</span>
</div>

<div class="kpi-grid" markdown>
<div class="kpi" markdown>
<div class="label">USD/JPY, Dec 2021 → Jul 2026</div>
<div class="value">115 → 159</div>
<div class="note">+32.4 log-points nominal (month-end)</div>
</div>
<div class="kpi" markdown>
<div class="label">Real depreciation, same span</div>
<div class="value">+36.1 <small>log-pts</small></div>
<div class="note">Weakest real yen of 1981–2026: June 2026</div>
</div>
<div class="kpi" markdown>
<div class="label">Daily rate link, β</div>
<div class="value">6.44 → 4.05</div>
<div class="note">% per pp, 2013–21 → 2022–; change −37 %</div>
</div>
<div class="kpi verdict" markdown>
<div class="label">Formal verdicts so far</div>
<div class="value">Unresolved</div>
<div class="note">H1a inconclusive · H1b not assessable</div>
</div>
</div>
</div>

<div class="chart-frame" markdown>
<p class="chart-title">USD/JPY since 1981</p>
<p class="chart-sub">Month-end. Hover a point for the policy event; shaded bands are the five
eras used in H1a. Switch to the real index to remove the effect of relative inflation.</p>
<div class="kchart-toggle" role="group" aria-label="Series">
<button data-target="home-history" data-mode="nominal" aria-pressed="true">Nominal ¥ per $</button>
<button data-target="home-history" data-mode="real" aria-pressed="false">Real index</button>
</div>
<div class="kchart tall" id="home-history" data-chart="usdjpy-history" data-mode="nominal"></div>
<p class="chart-source">Source: KAGURA frozen vintage 2026-09-15 (FRED DEXJPUS; CPI: BLS via FRED, BIS),
1981-01 to 2026-07. Real index = 100·exp((q − q<sub>1981-01</sub>)/100), q = s − x; higher = weaker
yen. Events: ADR 0004.</p>
</div>

## What we have found

<div class="two-col" markdown>
<div class="finding" markdown>
### H1a · the daily link weakened, but not provably by a third

- The % move in USD/JPY per 1 pp move in the 2Y US–Japan yield gap fell from **6.44**
  (2013–21) to **4.05** (2022–), a −37 % change, 95 % interval −49 % to −22 %.
- The pre-registered test asked whether the drop exceeds one-third. Neither "yes" nor
  "no" can be shown: **inconclusive**.
- The link is still the second-strongest of five eras since 1981, and at the monthly
  horizon and for 10-year yields a material decline is ruled out.

[Read the H1a report →](learning/reports/01-h1a-short-run-comovement.md)
</div>
<div class="finding" markdown>
### H1b · no defensible long-run anchor for the yen

- The planned test of a long-run levels relation could not be run validly: both
  candidate methods failed simulation checks. Verdict: **not assessable**.
- Exploratory models of 1981–2021 found no stable relation linking USD/JPY, relative
  prices and the rate gap, so no model-implied "benchmark" yen exists to measure against.
- The 2022–26 depreciation was entirely *real*: Japanese prices rose less than US prices.

[Read the H1b report →](learning/reports/02-h1b-long-run-fundamentals.md)
</div>
</div>

## Research timeline

<div class="two-col" markdown>
<div markdown>
<ol class="timeline">
<li><span class="when">2026-09-11</span><span class="what"><strong>Sample fixed</strong> — modelling sample from 1981 (ADR 0001)</span></li>
<li><span class="when">2026-09-15</span><span class="what"><strong>Data vintage frozen</strong> — downloads checksummed; later write-protected</span></li>
<li><span class="when">2026-09-23</span><span class="what"><strong>Exploration</strong> — eras, events and change definitions frozen (ADR 0004)</span></li>
<li><span class="when">2026-10-09</span><span class="what"><strong>H1a pre-registered</strong> — test and decision rule frozen before estimation (ADR 0006)</span></li>
<li><span class="when">2026-10-21</span><span class="what"><strong>H1a run once</strong> — inconclusive</span></li>
</ol>
</div>
<div markdown>
<ol class="timeline">
<li class="fail"><span class="when">2026-10-23</span><span class="what"><strong>H1b methods fail</strong> — Andrews–Kim and Wagner–Wied rejected in simulation <a href="learning/journal/h1b-methodological-journey/">case study</a></span></li>
<li><span class="when">2026-10-24</span><span class="what"><strong>H1b frozen as not assessable</strong> (ADR 0008); exploratory Stage 1 and audit: no defensible benchmark</span></li>
<li class="planned"><span class="when">next</span><span class="what"><strong>Stage 2</strong> — exploratory dating of breaks in the H1a relationship, compared with BOJ, Fed and MOF events <span class="tag">plan under review</span></span></li>
<li class="planned"><span class="when">later</span><span class="what"><strong>Mechanisms</strong> — what replaced rates: hedging, flows, intervention, risk (H2–H7; <a href="ROADMAP/">roadmap</a>)</span></li>
</ol>
</div>
</div>

## Learn the methods

<div class="card-grid">
<a href="learning/textbook/"><strong>Textbook · four chapters</strong><span>Exchange rates and logs; regression; stationarity and unit roots; hypothesis tests and uncertainty. Derivations, worked problems, solutions.</span></a>
<a href="learning/INDEX/#concept-index"><strong>Concept reference</strong><span>Every method KAGURA used, investigated, rejected or plans, with its role in the research.</span></a>
<a href="learning/cheatsheets/"><strong>Cheatsheets</strong><span>FX and PPP, inference, time series, and KAGURA's results and limits on one page each.</span></a>
<a href="learning/journal/h1b-methodological-journey/"><strong>Case study · How H1b became "not assessable"</strong><span>Two published tests, thousands of simulations, and why we stopped looking for a third.</span></a>
<a href="learning/reports/"><strong>Research reports</strong><span>Overview, H1a and H1b: question, data, method, results and limits.</span></a>
<a href="decisions/0006-h1-formal-testing-protocol/"><strong>Decision log</strong><span>The frozen ADRs that fix each test before it is run.</span></a>
</div>
