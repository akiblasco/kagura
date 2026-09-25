# ADR 0003 — Calendar and time alignment

Date: 2026-09-22 (revised 2026-09-22: Japan CPI lag, change flag)

## Context

The long table from ADR 0002 mixes daily series traded on different
calendars (New York, Tokyo, London) and monthly macro series that are
published weeks after the month they describe. Aligning them is where
look-ahead bias enters: a row dated t must contain only what a market
participant could have known at t. Implemented in `src/kagura/align.py`.

## Options considered

Calendar:
1. Keep only days on which every series has a value (intersection).
2. Use the USD/JPY calendar and carry the other markets' last value.
3. Use a full business-day calendar and fill USD/JPY too.

Monthly availability:
1. Stamp each value on its reference month (ignores publication lag).
2. Fixed conservative lag per series.
3. Actual historical release dates / ALFRED vintages.

Frequency:
1. One daily table with monthly series forward-filled into it.
2. Separate daily and monthly datasets.

## Decision

1. **Calendar = USD/JPY observation days.** USD/JPY is never filled.
   Every other daily market series takes its latest value dated on or before
   t (an as-of join), at most 5 business days old (implemented as 7
   calendar days). Older values are left missing. Each series gets a boolean
   `<series>_carried` column, true when the value comes from an earlier day,
   so robustness checks can drop carried observations.
   `diff_2y_carried` and `diff_10y_carried` are true when either leg is.

   For daily-change work, each of those series also gets
   `<series>_change_carried`: true on every carried row **and** on the first
   row after a run of carried rows. Example, Golden Week 2024 for JGBs:

   | date | jgb_2y_carried | jgb_2y_change_carried | why |
   |---|---|---|---|
   | Fri 26 Apr | F | F | live, previous row live |
   | Mon 29 Apr | T | T | Tokyo closed: change is a fake zero |
   | Tue 30 Apr | F | T | change spans 26 → 30 Apr, two days of movement |
   | Wed 1 May | F | F | ordinary one-day change |

   Rule: `change_carried[t] = carried[t] or carried[t-1]`, on the USD/JPY
   row order. Dropping rows where it is true leaves only changes between two
   consecutive live observations of that series. The flag only exists in
   `daily.csv`; it says nothing about month-to-month changes.
2. **Time of day.** USD/JPY is the noon New York rate. JGB yields (Tokyo
   close) are known by then. US Treasury yields (about 3:30 pm New York),
   VIX (4:15 pm), and the effective fed funds rate (published next morning)
   are not yet known at the fixing on the same date. The dataset stores
   same-date values. Daily-change models must report a robustness
   specification that uses these series lagged one row (the previous
   USD/JPY day). Brent (London assessment) is roughly contemporaneous and
   gets the same lagged check. This does not affect level or monthly work.
3. **Monthly availability = fixed conservative lag.** A value for month m
   is assumed known on: US CPI, the 15th of m+1; Japan CPI, the **last day**
   of m+1; Japan call rate (a monthly average of a daily rate), the 1st of m+1. The
   value is carried until the next release. The reference month of the value
   in use is stored beside it (`<series>_month`).
4. **Frequency.** Two datasets. `daily.csv` holds the market series only
   (USD/JPY, yields, fed funds, Brent, VIX, 2Y and 10Y differentials).
   `monthly.csv` holds the last daily row of each completed month plus
   the monthly macro series available on that date. The current,
   unfinished month is dropped.

Both datasets keep the full history. The 1981 modeling start (ADR 0001) is
applied at modeling time.

## Rationale

- The intersection calendar would drop about one day in twenty for Japanese
  holidays alone and discard valid USD/JPY observations. Carrying a closed
  market's last quote is what a trader knew that day, so it is not look-ahead.
- An as-of join, not reindex-then-forward-fill, is required: the MOF file has
  472 Saturday JGB quotes (Saturday trading before 1989). A reindex would
  drop them and carry the stale Friday value into the next Monday holiday.
- The cap stops a long data outage from being hidden as a flat price.
- Storing the reference month makes the lag inspectable and testable. A test
  checks that no monthly value appears before its availability date.
- Forcing CPI into a daily table would create about 21 identical rows per
  release, inflating apparent sample size.

Japan CPI was first set to the 25th of m+1, then moved to the last day of
m+1. **This is deliberately conservative.** For much of the sample Japan's
national CPI was published around the end of the following month, so the
25th could have let values in a few days early. Using the last day means
the dataset may know Japan CPI later than the market did, but not earlier.
When month-end is a weekend or holiday, the last trading day comes before
the assumed release. Japan CPI is then two months old in about 30% of
monthly rows (201 of 668), against one month otherwise.

## Risks and limitations

- **The fixed CPI dates are a v0.1 approximation, not the real history.**
  They should be replaced with actual historical release dates, and with
  first-release vintages where they exist (ALFRED for US CPI, Statistics
  Bureau of Japan release calendars for Japan CPI). Known and suspected
  failures of the fixed rule, not yet verified against source calendars:
  - Japan national CPI: the last-day rule should be safe for the whole
    sample, but release dates have not been checked against the source.
  - The 2025 US government shutdown delayed the September 2025 CPI to late
    October, and the October 2025 CPI was not published.
  - US CPI release days in earlier decades were not always by the 15th.
  Where the rule is too early, a value enters the dataset a few days before
  it was public. Where it is too late (by design for Japan CPI), the data
  looks staler than it was, which biases toward finding weaker CPI effects.
  Both go away once real release dates replace the fixed rules.
- CPI values are current vintages (ADR 0002). Revisions are small for
  these indices but make the series not strictly real-time.
- `change_carried` covers only one-row changes. A k-day change touches a
  carried value if any of the k+1 rows is carried. Build that flag as a
  rolling max of `<series>_carried` over k+1 rows when multi-day changes
  are used.
- The USD/JPY calendar itself spans US holidays: the change from the day
  before a US holiday to the day after is a two-day change for every
  series, flagged or not. That is inherent in the chosen calendar.
- Month-end sampling uses a single day; a month-average variant is a
  possible robustness check once modeling starts.
