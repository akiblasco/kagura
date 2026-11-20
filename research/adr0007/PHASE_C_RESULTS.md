# Phase C results: descriptive event comparison

Status: approved by the reviewer 2026-11-20. This is the public-safe version: values derived
from BOJ data are withheld (ADR 0010 §1, ADR 0014 §7). The complete record is in the gitignored
`data/events/restricted/phase_c/`. No economic interpretation is given here.

Protocol: ADR 0009 §7 and ADR 0013 (both frozen), run once on `13bc3ce`. The implementation
conventions are in ADR 0014 (frozen). Code: `research/adr0007/phase_c.py`. Public outputs:
`research/adr0007/out/phase_c/`.

## What the statistics are

Each event class is compared with a break date in two ways:

- **Interval count:** the number of class releases inside the break's nominal 95 % interval,
  set against the share of baseline positions whose same-width interval holds at least one
  release.
- **Nearest distance:** the signed distance in USD/JPY rows to the closest release, where
  negative means the event is before the break. It is set against its percentile among the
  baseline positions (G).

The baseline places the break at every eligible covered month-start. **It is a descriptive
ranking, not a p-value or a test.** The estimated break was chosen to minimise squared
residuals, not placed at random. Proximity says nothing about causation, and the absence of a
close event does not show that policy events were irrelevant to USD/JPY.

## Headline results (ADR 0013 §1)

The headline table has 24 cells plus HC3. All 24 are present, in the fixed order:

- **12 computed and published.**
- **4 computed but withheld.** These are the C0 cells. They depend on BOJ release dates, so their
  values are not published until BOJ reuse permissions are resolved (ADR 0010 §1).
- **4 pending.** C1, BOJ policy change, waits for the ADR 0010 §3a second coding pass.
- **4 not applicable.** C3 and C4 have no same-day version.
- **HC3** is the mandatory reference row: LWZ selects no break, so there is no date to compare.

| ID | Class | Version | In interval | Baseline share | Nearest (rows) | Nearest release | Percentile | G |
|---|---|---|---|---|---|---|---|---|
| HC1 | C0 | all, same_day | withheld (BOJ-derived) | | | | | |
| HC1 | C1 | all, same_day | pending | | | | | |
| HC1 | C2 | all | 1 | 0.759 | +53 | FOMC-20040630-1 | 58.7 | 349 |
| HC1 | C2 | same_day | 1 | 0.665 | +53 | FOMC-20040630-1 | 51.0 | 349 |
| HC1 | C3 | all | 6 | 0.509 | −59 | MOF-EP065 (starts 2003-12-26) | 42.8 | 334 |
| HC1 | C4 | all | 0 | 0.216 | +431 | ADR0004-2006-03-09 | 65.1 | 384 |
| HC1 | C5 | all | 1 | 0.662 | +53 | FRB-20040630-1 | 49.8 | 213 |
| HC1 | C5 | same_day | 1 | 0.601 | +53 | FRB-20040630-1 | 46.5 | 213 |
| HC2 | C0 | all, same_day | withheld (BOJ-derived) | | | | | |
| HC2 | C1 | all, same_day | pending | | | | | |
| HC2 | C2 | all | 12 | 1.000 | +48 | FOMC-20171213-1 | 66.0 | 106 |
| HC2 | C2 | same_day | 12 | 1.000 | +48 | FOMC-20171213-1 | 66.0 | 106 |
| HC2 | C3 | all | 0 | 0.453 | +1102 | MOF-EP070 (2022-09-22) | 69.8 | 106 |
| HC2 | C4 | all | 0 | 0.764 | −231 | ADR0004-2016-09-21 | 61.3 | 106 |
| HC2 | C5 | all | 12 | 1.000 | +48 | FRB-20171213-1 | 66.0 | 106 |
| HC2 | C5 | same_day | 12 | 1.000 | +48 | FRB-20171213-1 | 60.4 | 106 |
| HC3 | — | — | LWZ selects m = 0 (primary recent, ε = 15 %): no date to compare | | | | | |

C3 and C4 same_day are not applicable for both breaks.

**Break details:**

- **HC1** is the primary full sample at ε = 15 %, with a break on 2004-04-01, selected by BIC
  and LWZ. Its interval runs from 2003-07-15 to 2004-07-30.
- **HC2** is the primary recent sample at ε = 15 %, with a break on 2017-10-02. It is
  BIC-selected; LWZ prefers no break. Its interval runs from 2017-03-15 to 2020-07-20.

**Reading rule (ADR 0013 §4):** none of the 12 published computed cells is within the lowest 5 %
of the descriptive random-date baseline. Their percentiles range from 42.8 to 69.8. This report
makes no claim about the 4 withheld C0 comparisons.

**Events inside the intervals:** public identities are in `out/phase_c/headline_events_in_interval.csv`.

- **HC1:**
  - Six MOF episode starts, EP060–EP065, run from 2003-08-29 to 2003-12-26. All are mapped by
    trade date and flagged as having an uncertain row.
  - The 2004-06-30 FOMC rate increase falls 53 rows after the break, with its linked FRB
    action.
- **HC2:**
  - There are 12 FOMC funds-target changes. Seven are increases from 2017-03 to 2018-12, at −125
    to +278 rows. Five are decreases from 2019-07 to 2020-03, at +410 to +544 rows.
  - The 12 linked FRB actions fall on the same days.
  - There is no MOF episode in the interval.

At HC2's interval width, every baseline position also holds a C2 and a C5 event, so those
interval counts carry no information.

## Secondary and exploratory sets

### S1: daily-grid sensitivity

S1 uses the daily break dates 2004-04-02 and 2017-09-14. Phase A computed no daily interval, so
only distances are reported.

| Break | C2 | C3 | C4 | C5 |
|---|---|---|---|---|
| 2004-04-02 | +52, 58.2 | −60, 44.9 | +430, 65.1 | +52, 50.9 |
| 2017-09-14 | +58, 65.7 | +1112, 72.1 | −221, 63.4 | +58, 65.7 |

- Each entry is the nearest distance in rows, then the percentile. Only the all-release
  versions are shown here; C0 is withheld.
- Moving every MOF row one row later changes C3 only, to −59 / 44.6 and +1113 / 72.1.
- No public S1 value is within the lowest 5 %.

### S2: appendix family, not individually interpretable

S2 covers 448 other breaks from `break_table.csv`. They overlap heavily across ε and m.

| Class | Version | Breaks | Share with ≥1 event in interval | Mean baseline share | Share within lowest 5 % | Median percentile |
|---|---|---|---|---|---|---|
| C2 | all | 397 | 0.940 | 0.897 | 0.020 | 56.6 |
| C2 | same_day | 397 | 0.914 | 0.884 | 0.020 | 54.0 |
| C3 | all | 384 | 0.500 | 0.507 | 0.010 | 58.3 |
| C4 | all | 448 | 0.607 | 0.612 | 0.025 | 50.9 |
| C5 | all | 338 | 0.929 | 0.873 | 0.033 | 55.4 |
| C5 | same_day | 338 | 0.769 | 0.824 | 0.033 | 51.9 |

C0 is withheld. Breaks before a class's coverage starts are "not covered" and are not counted.

### E1: exploratory m = 4 partition, selected by neither criterion

E1 is the primary recent partition at ε = 15 %, with breaks at 2015-06-01, 2017-10-02,
2019-11-01 and 2021-12-01. Full values are in `out/phase_c/e1_m4.csv`; C0 is withheld.

The 2019-11-01 break is −1 row from FOMC-20191030-1, a −25 bp funds-target cut whose row is
2019-10-31, and from the linked FRB-20191030-1. That places it **within the lowest 5 % of the
descriptive random-date baseline**: the percentile is 5.0 under inclusive ties, and 3.5 or 2.0
under the ADR 0014 alternatives. Three things limit what this shows:

- It is one announcement counted in four cells: C2 and C5, each in the all and same_day
  versions.
- The partition is exploratory, and neither BIC nor LWZ selects it.
- A month-start break sits one row from any end-of-month release by construction.

It is not a headline result.

## Limitations

- **Selection:** the headline set (ADR 0013) and the conventions (ADR 0014) were fixed after
  the Phase A dates were known. The analysts knew the event history beforehand.
- **Multiplicity:** the 24 headline cells are nested and dependent. C5 duplicates C2 on linked
  days, and same_day is a subset of all. S2 is a family of overlapping breaks.
- **Post-selection:** τ̂ is estimated, not random. The baselines ignore this, which biases
  proximity towards ranking close.
- **Temporal alignment:**
  - Every MOF row, and many FOMC rows, are flagged `fx_row_uncertain`, so distances can be off
    by one row (ADR 0012 L19 and L21).
  - The C4 markers have no announcement time.
- **Coverage and classification:**
  - C1 is pending.
  - C0 is withheld from public output.
  - C3 counts episode starts only. The episode starting 2003-12-26 ran to 2004-03-16, about two
    weeks before HC1. That is noted as context, not as a comparison.
  - C2 is funds-target changes only.
- **Causal interpretation:** proximity is not causation, and distance is not evidence of
  irrelevance. The comparison speaks only to timing coincidence at row resolution.

## Reproducibility

Run: `uv run python research/adr0007/phase_c.py`.

- The script verifies the event checksums and the headline inputs before it runs.
- Repeated runs are byte-identical.
- The complete copies matched the first Phase C run byte for byte after the public-output change.
- The tests are in `tests/test_phase_c.py`.
