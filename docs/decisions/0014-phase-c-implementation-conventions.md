# ADR 0014: Phase C implementation conventions and public-output restrictions

Date: 2026-11-20.

Status: FROZEN, 2026-11-20. Approved by the reviewer 2026-11-20, together with the Phase C results. ADR 0009, ADR 0010 and ADR 0013 stay frozen and unedited.

## Context

ADR 0009 §7.2 and ADR 0013 fix the Phase C statistics, classes, headline set and reading rule.
Writing `research/adr0007/phase_c.py` required six choices that those ADRs do not fully
specify.

**Timing:** these choices were made after the Phase A break dates were known, and before any
Phase C comparison was computed. They were not prespecified, and this ADR does not present them
as if they were. It records them after the run so that a reviewer can see each choice and its
effect.

Phase C also produces statistics derived from BOJ data. ADR 0010 §1 forbids committing,
pushing or publishing BOJ-derived rows, and does not say whether aggregates count. §7 below
records how public outputs handle this pending a decision.

## Decision: the six conventions

For each choice, the alternatives were recomputed for every computed headline cell. That check
ran after the Phase C results were known. It is a **post-result sensitivity check**, not a selection, and it did not change any reported value.

The figures below cover the publicly reported cells, C2–C5. The withheld C0 cells (§7) are
reported only in the restricted record.

### 1. Rows for C4 markers

- **Implementation:** the 13 ADR 0004 markers have no announcement time. Each maps to the first
  USD/JPY row on or after its date.
- **Rationale:** this is the same rule ADR 0009 §4 uses for releases without an observable time.
- **Alternative:** the last row on or before the date. Only the two Sunday markers move (Plaza
  1985-09-22 and Louvre 1987-02-22). HC1 and HC2 headline values are unchanged.

### 2. Ties in the distance percentile

- **Implementation:** the percentile is the share of baseline positions whose nearest-event
  distance is ≤ the break's distance. Ties count inclusively.
- **Rationale:** on a month-start grid many positions tie. Counting ties inclusively makes
  "within the lowest 5 %" harder to reach, which is the conservative direction for a closeness
  reading.
- **Alternatives:** strict (<) and mid-rank counting.
  - Each lowers a public headline percentile by at most 1.8 points: HC2 C5 all goes from 66.0
    to 64.2.
  - The minimum over the public headline cells and all alternatives in this ADR is 41.9 (HC1
    C3, strict ties with the MOF +1-row shift).
  - The exploratory E1 2019-11-01 value goes from 5.0 to 3.5 (mid-rank) or 2.0 (strict). It
    stays within the lowest 5 % under every rule.

### 3. Baseline positions for multi-break partitions

- **Implementation:** each break in a partition with m > 1 uses the cell's whole eligible
  month-start set as G, the same set used for m = 1.
- **Rationale:** ADR 0009 §7.2 defines G_c per cell, not per segment.
- **Effect:** S2 and E1 only. For the m = 1 headline breaks there is no alternative to compare.

### 4. Class coverage starts

| Class | Start | Basis |
|---|---|---|
| C0 | 1998-04-01 | No BOJ member before it (ADR 0009 §7.3 split) |
| C2 | 1990-01-01 | ADR 0010 R2: earlier `policy_change` is missing |
| C3 | 1991-04-01 | ADR 0009 §4 MOF coverage |
| C4 | 1981-01-01 | Sample start |
| C5 | 2001-05-01 | ADR 0010 R5 |

- Every class runs to the sample end, 2026-09-11.
- Statistics before a class's start are "not covered" and never zero.
- **Consequence:** C0 excludes FOMC releases before 1998-04. C2 is therefore contained in C0 only
  from 1998-04, which matters for S2 breaks before 1998.
- **Alternatives:** C2 starting 1994-02-04, when statements begin; C3 starting at its first event,
  1991-05-13; C5 starting at its first event, 2001-06-27.
  - These change headline percentiles by up to 4.7 points, with HC1 C2 same_day going from 51.0
    to 55.7.
  - No nearest distance changes.

### 5. Events outside the cell's sample

- **Implementation:** events dated before the cell's first row or after its last row are
  excluded.
- **Defect history:** a first draft clamped earlier events to row 0. It was found and fixed
  before any result was reported. `tests/test_phase_c.py` fails against the clamped version.
- **Alternative:** keep pre-sample events and measure distances on the full-sample calendar.
  - No headline nearest distance changes.
  - HC2 C3's percentile rises from 69.8 to 88.7, because baseline positions near 2013 then see
    the 2011 MOF episodes.

### 6. Late-day MOF rows

- **Implementation:** S1 also reports every MOF row moved one row later, because the data do not
  identify which operations fell in the New York afternoon (ADR 0012 L21).
- **Alternative:** apply the same shift to headline C3. HC1 changes from −59 / 42.8 to
  −58 / 42.5, and HC2 from +1102 / 69.8 to +1103 / 69.8.

## Decision: public outputs (§7)

Applied pending a reviewer decision under ADR 0010 §1.

- **What is withheld:** every computed C0 cell. That covers all of its statistics, including
  ones whose nearest release is an FOMC release, because each one depends on BOJ release dates.
  - Public rows keep their place in the fixed table order with status `computed; withheld from
    public output: BOJ-derived (ADR 0010 §1)`.
  - C0 is not redefined.
- **BOJ events** in headline intervals go only to `data/events/restricted/phase_c/`.
- **C1** is pending and holds no values.
- **Complete outputs:** every Phase C output is also written, complete, to the gitignored
  `data/events/restricted/phase_c/`. Public and complete copies differ only in the withheld C0
  cells.
- **Report text:** the public report gives no C0 count, distance or percentile, and no statement
  summarising across the withheld cells.

## Rationale

The run records each convention with its implementation and its measured effect, instead of
quietly adjusting the run. Withholding the whole C0 cell is the strict reading of ADR 0010 §1,
and a reviewer can relax it later without recomputing anything.

## Risks and limitations

- The conventions were chosen with knowledge of the Phase A dates, and the sensitivity check was
  run after the Phase C results were known. Both limit how much these choices can be trusted.
- No listed alternative takes a public headline cell below 41.9, so none changes the headline
  reading. That holds only for the alternatives listed here.
- Public readers cannot verify the C0 results.

## Order of operations

1. Reviewer approval of this ADR and the Phase C results: done 2026-11-20. BOJ-derived C0 cells
   and BOJ release identities stay withheld from public output until BOJ reuse permissions are
   resolved.
2. Freeze this ADR, then commit the Phase C code, tests and public-safe outputs.
