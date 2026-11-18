# ADR 0013: Phase C event-comparison protocol

Status: FROZEN, 2026-11-18. Approved by the reviewer 2026-11-18. Not yet executed.

Changing this protocol requires a new ADR written before Phase C is run. Headline dates, classes,
windows and the reading rule may not change after event data are compared with breaks.

## Context

Phase A (ADR 0011 §7) is complete: commit `02032cb`, report `research/adr0007/PHASE_A_REPORT.md`.
ADR 0009 §7 fixes the statistics, event classes, coverage rules and language for comparing
events with break dates. It does not fix *which* break estimates are compared.

ADR 0012 L20 requires that choice to be frozen before Phase C. There are 30 cells × m = 1…5 ×
breaks × 6 classes × 2 observability versions, which is too many comparisons to read
individually.

This ADR is written after the Phase A dates were seen. **No event data have been opened against
them.** The choices below follow from rules fixed before Phase A, namely ADR 0007 §3.4 and ADR
0011 §7, and not from where events lie.

## Options considered

1. **Report every cell and m as one family.** This is complete, but hundreds of descriptive
   proximities would invite reading the closest matches.
2. **Freeze a small headline set by rule, and report everything else as a labelled appendix
   family.** Chosen.
3. **Headline only the selected models.** Rejected on its own, because it would hide the
   recent-sample disagreement in which LWZ selects no break.

## Decision

### 1. Headline set

These are fixed by rule: the primary static 2Y specification, ε = 15 % (ADR 0007 §3.4
"conventional"), and the month-start grid.

| ID | Cell | Estimate | Selected by | Break date | Nominal 95 % interval |
|---|---|---|---|---|---|
| HC1 | primary, full, ε = 15 % | m = 1 | BIC and LWZ | 2004-04-01 | 2003-07-15 .. 2004-07-30 |
| HC2 | primary, recent, ε = 15 % | m = 1 | BIC only | 2017-10-02 | 2017-03-15 .. 2020-07-20 |
| HC3 | primary, recent, ε = 15 % | m = 0 | LWZ | none | none |

- **HC3 is reported in every headline table** as a row that reads "LWZ selects no break; no date
  to compare". HC2 is always labelled "BIC-selected; LWZ prefers no break".
- **No 2022 comparison is added to the headline set.** Adding one because of the hypothesis
  would be selection on the expected answer.

### 2. Secondary and exploratory sets

These are reported, but not in headline tables.

- **S1, the daily-grid sensitivity** (ADR 0009 §7.2): HC1 and HC2 on the daily grid, at
  2004-04-02 and 2017-09-14, with daily-row baselines.
- **S2, the appendix family:** every other cell, m and break in `break_table.csv`, with the same
  statistics. It is labelled "appendix family, not individually interpretable". This family
  includes the lag-augmented cells, labelled as a different estimand.
- **E1, the exploratory recent ε = 15 % m = 4 partition:** 2015-06, 2017-10, 2019-11 and
  2021-12. It is reported once, labelled "exploratory, selected by neither criterion", and
  never summarised as a finding.

### 3. Event classes and coverage

ADR 0009 §3.8 applies unchanged: C0–C5, with no class added, merged, split or re-windowed.

- **Coverage** follows ADR 0009 §4 and §7.2: statistics outside coverage are "not covered",
  never zero.
- **Class by headline:**
  - HC1 (2003–04) and HC2 (2017–20) lie inside the documented coverage of C0, C1 (post-1998-04
    rules), C2, C3 and C4.
  - C5 coverage is "confirmed at collection" (ADR 0009 §2), so it is taken from the manifest at
    run time, not assumed here.
- **BOJ split:** BOJ results are split at 1998-04 (§7.3). HC1 and HC2 are both after the split.
- **C1 status:** C1 is used only after the ADR 0010 §3a second BOJ coding pass is complete
  (ADR 0012 L22). Until then, C1 is reported as "pending".
- **Observability:** every statistic is reported twice, for all releases and for
  `observable = same_day` releases (§7.2).
- **Late-day releases:** MOF New York-afternoon days stay flagged `fx_row_uncertain` (L21).
  Daily-grid statistics are also reported with those rows moved one row later.

### 4. Multiple comparisons

**Family size.** The headline family has 24 cells: HC1 and HC2, × 6 classes, × 2 observability
versions. Each cell carries two statistics, so there are 48 values:

- the interval count against its baseline share (ADR 0009 §7.2 items 1 and 3);
- the nearest-event distance against its baseline percentile (items 2 and 4).

HC3 adds one fixed row with no statistics. Cells that are "not covered" or "pending" stay in the
table.

**The cells are strongly dependent:**

- C0 contains every C1 and C2 release.
- `same_day` releases are a subset of all releases.
- HC1 and HC2 share no events, but they share one estimation method.

The effective number of independent comparisons is therefore well below 24, and unknown.

- **ADR 0009 §7.2 baselines are descriptive, not p-values.** No significance threshold is
  applied, and no adjustment is reported as if it were a test.
- To prevent cherry-picking, **all headline cells are reported in one table in fixed order**
  (HC1, HC2, HC3; C0…C5; all then same_day), including empty, "not covered" and "pending"
  cells.
- A pre-stated reading rule applies:
  - **The 5 % threshold is a descriptive ranking benchmark.** It is not a p-value, not a
    statistical-significance threshold, and not a valid null-hypothesis test. The baseline
    places dates at random over covered candidates, whereas τ̂ is estimated (see Risks).
  - Only the distance statistic has a percentile. When the percentile is ≤ 5 % (one-sided,
    closeness only), the only permitted wording is: "within the lowest 5 % of the descriptive
    random-date baseline". Proximity is never called "unusual", "significant" or "unlikely by
    chance".
  - If the 24 distance cells were independent, about 24 × 0.05 = 1.2 of them would fall within
    the lowest 5 % by construction. They are not independent. Because the cells are nested, the
    count comes in clusters: a single near event can mark C0, C1 or C2, and both observability
    versions, at once.
  - Any such description therefore names the event rows behind it, so that one event counted
    several times is visible.
  - The interval statistic is reported as count against baseline share, with no threshold and
    no label.
  - The rule is descriptive language, not inference.
- S2 is summarised only as a distribution, the share of breaks with any class-c event in the
  interval against its baseline. It is never as a list of matches.

### 5. Language

ADR 0009 §7.4 applies verbatim, including the banned verbs.

## Rationale

- ε = 15 % and m = 1 follow the pre-existing ADR 0007 hierarchy.
- Keeping HC3 prevents a BIC-only date from being presented as the recent-sample result.
- A fixed table order and reporting every cell remove the freedom to show only matches.

## Risks and limitations

- The headline set was chosen after Phase A results were seen. The rule-based choice limits but
  does not remove that.
- **Prior knowledge of history.** The analysts know the event record, for example that large MOF
  operations ran in 2003–04. A proximity that was predictable before Phase C cannot count as a
  finding. The fixed table and the fixed language limit how such cases are presented; they do not
  make them informative.
- **Estimated dates.** τ̂ is chosen to minimise SSR, and large moves around events can pull it
  towards them. The baselines treat τ̂ as if it were placed at random, so proximity is biased
  towards ranking close.
- **Timing uncertainty.** FX is the New York noon fix, yields close around 15:30, and FOMC
  statements arrive at 14:00–14:15 ET (ADR 0012 L19). MOF New York-afternoon operations fall one
  row early (L21). Row-level distances can therefore be off by one row.
- **Incomplete coverage.** C1 is pending (L22) and C5 coverage depends on collection, so some
  headline cells may be "pending" or "not covered". They are reported as such.
- The baselines ignore that τ̂ is estimated. With intervals of about one and three years, many
  events will fall inside by construction, especially C0 at 16–22 releases a year.
- HC2's interval is wide (27–35 % of the eligible range), so its proximity statistics will be
  weakly informative.
- No causal reading is possible from proximity (ADR 0009 §7.4 "Why").

## Order of operations

1. Reviewer decision on this ADR, then freeze. Done 2026-11-18.
2. Confirm `EVENTS_SHA256` and the C1 coding-pass status.
3. Run Phase C once and report as specified.
