# ADR 0004 — H1 exploratory specification (frozen before viewing results)

Date: 2026-09-23. Written before any rolling correlation, scatter, or
stationarity statistic was computed on the data. Implemented as constants
in `src/kagura/explore.py`; the notebook is `notebooks/01_exploration.ipynb`.

## Context

`docs/HYPOTHESES.md` requires tests to be frozen before the analyses are run.
The exploratory checkpoint gives the first direct view of H1 (USD/JPY
decoupling from the US-Japan yield differential). If the windows, variants
or event markers are chosen after seeing the plots, they can be tuned to
the picture, even without meaning to. This ADR fixes them in advance.

## Status of these results: exploratory, not confirmatory

Everything in this checkpoint is an **exploratory diagnostic**: it describes
the data and informs the choice of model specification. None of it is a
formal test of H1. In particular:

- Rolling correlations with pointwise bands are not a structural-break test.
  Overlapping windows are strongly autocorrelated, and the bands assume
  independent observations, so they understate uncertainty.
- Formal H1 tests (baseline regression with HAC errors, parameter-stability
  and structural-break tests) come later and get their own frozen spec.
- A specification added after seeing these results must be labelled
  **exploratory / post-hoc** in the notebook and recorded in a new ADR. It
  never replaces a specification in this ADR.

## Decision (frozen)

**Sample.** From 1981-01-01 (ADR 0001) to the last date in `daily.csv`.
`diff_10y` starts in July 1986 (ADR 0002).

**Variables.**
- FX change: `dfx[t] = 100 * (log usdjpy[t] - log usdjpy[t-1])`, in percent,
  on consecutive rows of the USD/JPY calendar.
- Differential change: `ddiff[t] = diff[t] - diff[t-1]`, in percentage points.
- Primary differential: `diff_2y`. Robustness: `diff_10y`.

**Timing variants** (ADR 0003, decision 2). Both are always reported.
- Same-day: `diff[t] = us[t] - jgb[t]`. The US leg closes after the noon
  New York fix, so this includes about 3.5 hours of information the FX
  rate could not yet reflect.
- Lagged: `diff_lag[t] = us[t-1] - jgb[t]`, the US leg lagged one row.
  Everything in it was known at the fix, but the US leg's change overlaps
  the FX change window only partly.

**Exclusion rule.** A row enters a correlation only if both changes are
between two consecutive live observations:
- Same-day: drop row t if `diff_<m>_change_carried[t]`.
- Lagged: drop row t if `jgb_<m>_change_carried[t]` or
  `us_<m>_change_carried[t-1]`.

USD/JPY is never carried, so it needs no flag. The exclusion is always
applied. The number of excluded rows is reported.

**Rolling windows.** 1 year = 250 rows and 3 years = 750 rows of the USD/JPY
calendar. Each window is trailing (ends at t). A value is reported only if at
least 80% of the window's rows survive exclusion (200 and 600 rows).
Statistic: Pearson correlation of `dfx` with `ddiff`. Band: pointwise 95%
Fisher-z interval with n = surviving rows. It is descriptive only (see above).

That gives 8 series: 2 windows × 2 differentials × 2 timing variants.

**Event markers (fixed, chosen ex ante from policy history, not from the
data).**

| Date | Event |
|---|---|
| 1985-09-22 | Plaza Accord |
| 1987-02-22 | Louvre Accord |
| 1999-02-12 | BOJ zero interest rate policy |
| 2001-03-19 | BOJ quantitative easing |
| 2006-03-09 | BOJ exits quantitative easing |
| 2008-09-15 | Lehman Brothers failure |
| 2013-04-04 | BOJ quantitative and qualitative easing (QQE) |
| 2016-01-29 | BOJ negative interest rate |
| 2016-09-21 | BOJ yield curve control (YCC) |
| 2022-03-16 | Fed begins 2022 hiking cycle |
| 2022-09-22 | MOF yen-buying intervention (first since 1998) |
| 2022-12-20 | BOJ widens YCC band |
| 2024-03-19 | BOJ ends negative rate and YCC |

**Descriptive eras** (for the scatter and the change statistics), bounded
by the policy regimes above: 1981–1989, 1990–1998, 1999–2012, 2013–2021,
2022–end. They are labels for description, not estimated breaks.

**Stationarity diagnostics.** ADF (constant, lag length by AIC) and KPSS
(level-stationary null, automatic lag length). Series: log USD/JPY,
`diff_2y`, `diff_10y`, in levels and first differences. Data: month-end
values from `monthly.csv`, same sample. They are read together: ADF's null is
a unit root and KPSS's null is stationarity. The results inform whether
later models use levels (which then needs a cointegration analysis) or
changes. They do not choose the specification alone.

**Inflation.** Year-on-year CPI inflation, `100 * (cpi[m] / cpi[m-12] - 1)`,
for the US and Japan. Plotted by reference month, as description. Any later
real-rate variable must use the availability dating in `monthly.csv`
(ADR 0003) instead.

**Data-quality screen.** For each daily market series and each differential:
the 10 largest absolute one-row changes, with dates, the gap in days since
the previous row, and the change-carried flag. These are **flagged for
investigation**. An observation is classified as a data error only after
checking it against the raw source file *and* an independent source. A
move with no known event is not presumed to be an error.

## Rationale

- One-year and three-year windows are the conventional short and medium
  horizons, set before looking. The 80% rule stops windows around sparse
  periods from reporting correlations on a handful of rows.
- The two timing variants bracket the time-of-day problem from both sides
  rather than picking one.
- Fixing the eras and events in advance stops the eye from putting a
  boundary where the plot happens to change.

## Risks and limitations

- The event list reflects the author's prior knowledge of yen history, which
  includes knowing roughly when the relationship is *said* to have weakened.
  Fixing it in advance limits tuning; it cannot remove that prior knowledge.
- Daily correlations of changes mix news-driven comovement with
  microstructure noise, and say nothing about the levels relationship.
- Unit-root tests have low power in samples of around 500 months with regime
  changes. A break in the mean can look like a unit root.
- The spec was frozen in writing on the date above. It has no git
  timestamp, because git is blocked on this machine until the Xcode
  license is accepted. Committing this ADR on its own before the notebook
  would give it one.
