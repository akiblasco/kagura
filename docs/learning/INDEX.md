# KAGURA Research & Learning Companion

A companion to the research, not part of it: it explains what KAGURA found and teaches the
methods. The authoritative records stay in `docs/decisions/` (ADRs),
the notebooks and the Git history; this companion links to them instead of copying them.

**Rules.** Numbers are copied from executed notebooks or committed outputs, never
recomputed by hand. Every page marks what is a *verified record* (ADR, commit, notebook
output) and what is a *reconstruction* (an inference about why something was done).
Documentation is updated after a research milestone is validated and never blocks it.

## Layout

| Folder | Contents | Status |
|---|---|---|
| [`reports/`](reports/index.md) | One visual report per completed research stage | 00, 01, 02 drafted |
| [`textbook/`](textbook/index.md) | Full chapters, beginner → intermediate, with derivations, worked problems and solutions | chapters 1–4 drafted |
| [`concepts/`](concepts/economics.md) | Concept reference: one entry per concept, linked below | 5 pages drafted |
| [`cheatsheets/`](cheatsheets/index.md) | Compact summaries: formulas, decision rules, diagrams, KAGURA numbers | 4 drafted |
| [`journal/`](journal/index.md) | Dated research history: attempts, expectations, mistakes, decisions | H1b case study drafted |

Figures for the reports are produced by `reports/make_figures.py` from committed notebook
outputs (`uv run python docs/learning/reports/make_figures.py`).

## Reports

| # | Report | Stage | Status |
|---|---|---|---|
| 00 | [Research overview](reports/00-research-overview.md): motivation, data foundation, frozen vintages, roadmap | v0.1 | **draft for review** |
| 01 | [H1a: short-run comovement](reports/01-h1a-short-run-comovement.md) | ADR 0006 | **draft for review** |
| 02 | [H1b: long-run fundamentals and the missing benchmark](reports/02-h1b-long-run-fundamentals.md) | ADR 0008 | **draft for review** |

## Journal (planned entries)

| Period | Entry | Main sources |
|---|---|---|
| 2026-09 | Data foundation: sources, alignment, release lags, frozen vintage | ADR 0001–0003, 0005; `data/raw/manifest.json` |
| 2026-09 | Exploration and the split of H1 into H1a / H1b | ADR 0004; notebook 01 |
| 2026-10 | Pre-registering and running H1a | ADR 0006; notebook 02; `2c5b446` |
| 2026-10 | [H1b confirmatory search](journal/h1b-methodological-journey.md): Andrews–Kim and Wagner–Wied pilots, why both were rejected | ADR 0008 r2–r5; `research/methodology/adr0008-h1b-confirmatory-pilots/` |
| 2026-10 | H1b exploratory Stage 1 and its specification audit | notebooks 03–04; `8fba5b6`, `ca8ebd3` |

## Concept index

Every concept KAGURA has used, investigated or planned, with a reference entry (plain-English meaning,
purpose, definition, KAGURA use, findings, limits, a common mistake and links) and, where written, a
textbook chapter. **Status:** **impl.** used in a KAGURA result · **expl.** used descriptively or in
exploratory work · **rejected** investigated and not used · **planned** in a plan, not run ·
**background** context only. Level: **B** beginner, **I** intermediate, **A** advanced.

### Economics and finance

| Concept | Status | Level | Used in | Chapter |
|---|---|---|---|---|
| [Log returns and percentage changes](concepts/economics.md#log-returns-and-percentage-changes) | impl. | B | ADR 0004; H1a | [1](textbook/exchange-rates-logs-real-depreciation.md) |
| [Interest-rate differential and carry](concepts/economics.md#interest-rate-differential-and-carry) | impl. / background | B | H1a, H1b | [2](textbook/regression-coefficients.md) |
| [Uncovered interest parity and its failure](concepts/economics.md#uncovered-interest-parity-and-its-failure) | background | I | H1a, H1b interpretation | — |
| [PPP; nominal vs real exchange rate](concepts/economics.md#purchasing-power-parity-nominal-vs-real-exchange-rate) | impl. | I | H1b Stage 1 | [1](textbook/exchange-rates-logs-real-depreciation.md) |
| [Yield-curve control, QQE and the zero lower bound](concepts/economics.md#yield-curve-control-qqe-and-the-zero-lower-bound) | background | I | ADR 0004 eras | — |
| [FX intervention (MOF)](concepts/economics.md#fx-intervention-ministry-of-finance) | planned | I | ADR 0004 marker; Stage 2 plan | — |
| [Consumption-tax steps in Japanese CPI](concepts/economics.md#consumption-tax-steps-in-japanese-cpi) | expl. | I | H1b spec (d), audit | — |

### Data and measurement

| Concept | Status | Level | Used in | Chapter |
|---|---|---|---|---|
| [Observation, release and vintage dates; look-ahead bias](concepts/data.md#observation-release-and-vintage-dates-look-ahead-bias) | impl. | B | ADR 0003 | — |
| [Asynchronous market closes](concepts/data.md#asynchronous-market-closes-noon-fix-vs-tokyo-close) | impl. | I | ADR 0006 §4.5; R1 | [2 §8](textbook/regression-coefficients.md#8-association-not-causation) |
| [Frozen data vintages and checksums](concepts/data.md#frozen-data-vintages-and-checksums) | impl. | B | ADR 0006 §9.2; `vintage.py` | — |
| [Carried values, exclusion rule, carried-share guard](concepts/data.md#carried-values-the-exclusion-rule-and-the-carried-share-guard) | impl. | B | ADR 0003–0005 | — |

### Statistical inference

| Concept | Status | Level | Used in | Chapter |
|---|---|---|---|---|
| [OLS slope as covariance over variance](concepts/inference.md#ols-slope-as-covariance-over-variance) | impl. | B | H1a | [2](textbook/regression-coefficients.md) |
| [R² and why it is descriptive](concepts/inference.md#r-squared) | impl. (descriptive) | B | H1a | [2 §7](textbook/regression-coefficients.md#7-r2-share-of-variance-not-strength-of-a-link) |
| [HAC (Newey–West) standard errors](concepts/inference.md#hac-standard-errors) | impl. | I | H1a; H1b | [2 §9](textbook/regression-coefficients.md#9-how-precise-is-a-slope-standard-errors) |
| [One-sided tests, confidence bounds, p-values](concepts/inference.md#one-sided-tests-bounds-and-p-values) | impl. | B | H1a | [4](textbook/hypothesis-testing-uncertainty.md) |
| [Pre-registration, gates and outcome categories](concepts/inference.md#pre-registration-gates-and-outcome-categories) | impl. | I | ADR 0006 §5; ADR 0008 | [4 §6](textbook/hypothesis-testing-uncertainty.md#6-testing-a-combination-of-coefficients-h1as) |
| [Multiple testing and Bonferroni α splits](concepts/inference.md#multiple-testing-and-bonferroni) | impl. | I | ADR 0006 §8 | [4 §9](textbook/hypothesis-testing-uncertainty.md#9-many-tests-controlling-the-family-wise-error) |
| [Fieller confidence sets for ratios](concepts/inference.md#fieller-confidence-sets) | impl. | A | H1a | [4 §7](textbook/hypothesis-testing-uncertainty.md#7-uncertainty-of-a-ratio-fiellers-method) |
| [Wald tests](concepts/inference.md#wald-tests) | impl. (secondary) | I | H1a | [4 §8](textbook/hypothesis-testing-uncertainty.md#8-testing-several-restrictions-at-once-the-wald-test) |
| [Rolling-window estimates](concepts/inference.md#rolling-window-estimates) | expl. | B | ADR 0004; H1a §6.3 | — |
| [Monte Carlo critical values and size/power](concepts/inference.md#monte-carlo-size-and-power) | impl. (synthetic) | A | ADR 0008 pilots | [4 §10](textbook/hypothesis-testing-uncertainty.md#10-does-the-test-do-what-it-says-monte-carlo-size-and-power) |

### Time-series econometrics

| Concept | Status | Level | Used in | Chapter |
|---|---|---|---|---|
| [Stationarity, unit roots, integration order; ADF and KPSS](concepts/time-series.md#stationarity-and-unit-roots) | expl. | I | ADR 0004; H1b | [3](textbook/stationarity-unit-roots.md) |
| [Spurious regression](concepts/time-series.md#spurious-regression) | background | I | design of H1a/H1b | [3 §7](textbook/stationarity-unit-roots.md#7-spurious-regression) |
| [Cointegration and error correction](concepts/time-series.md#cointegration-and-error-correction) | expl. | A | H1b | — |
| [ARDL and the PSS bounds test](concepts/time-series.md#ardl-and-the-pesaranshinsmith-bounds-test) | expl. | A | H1b Stage 1 | — |
| [Lag selection: AIC and Breusch–Godfrey](concepts/time-series.md#lag-selection-aic-and-breuschgodfrey-filtering) | expl. | I | H1b Stage 1 | — |
| [FM-OLS and D-OLS](concepts/time-series.md#fm-ols-and-d-ols) | expl. | A | H1b Stage 1 | — |
| [Half-life of deviations; bootstrap failure](concepts/time-series.md#half-life) | expl. | A | H1b Stage 1 | [3 §3.4](textbook/stationarity-unit-roots.md#34-half-life) |
| [Andrews–Kim end-of-sample test](concepts/time-series.md#andrewskim-end-of-sample-cointegration-breakdown-test) | **rejected** | A | ADR 0008 §4 | — |
| [Wagner–Wied cointegration monitoring](concepts/time-series.md#wagnerwied-cointegration-monitoring) | **rejected** | A | ADR 0008 §5 | — |
| [Structural breaks: Bai–Perron, trimming](concepts/time-series.md#structural-breaks-baiperron-trimming-break-date-intervals) | planned | A | ADR 0006 §6.2; Stage 2 plan | — |

### Research methodology and programming

| Concept | Status | Level | Used in | Chapter |
|---|---|---|---|---|
| [Confirmatory vs exploratory analysis](concepts/methodology.md#confirmatory-vs-exploratory-analysis) | impl. | B | ADR 0006, 0008 §7 | — |
| [ADRs and freezing decisions before results](concepts/methodology.md#adrs-and-freezing-decisions-before-results) | impl. | B | `docs/decisions/` | — |
| [Association vs causation language](concepts/methodology.md#association-vs-causation) | impl. | B | ADR 0006 §3 | [2 §8](textbook/regression-coefficients.md#8-association-not-causation) |
| [Specification search and forking paths](concepts/methodology.md#specification-search-and-the-garden-of-forking-paths) | impl. (rule) | I | ADR 0008 §6 | — |
| [Reporting negative and inconclusive results](concepts/methodology.md#reporting-negative-and-inconclusive-results) | impl. | B | H1a, H1b | — |
| [Reproducible pipelines: uv, make, nbconvert, pytest](concepts/methodology.md#reproducible-pipelines-uv-make-nbconvert-pytest) | impl. | B | `Makefile` | — |
| [Testing econometric code on synthetic data](concepts/methodology.md#testing-econometric-code-on-synthetic-data) | impl. | I | `tests/` | — |
