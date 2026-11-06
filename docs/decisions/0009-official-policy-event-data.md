# ADR 0009 — Official Policy-Event Dataset (BOJ, Federal Reserve, MOF Intervention)

Date: 2026-11-04. Revision 3 final: 2026-11-06.

**Status: FROZEN 2026-11-06 (revision 3 final: reviewer approval; BOJ material restricted
to private storage, §6.1). No event data had been downloaded at freezing.**

- **Freezing** means committing this file with ADR 0007, then pushing, before any event is
  collected and before any break statistic is computed.
- **After freezing,** any change needs a new ADR. Checksums of collected files are recorded
  in code and in the collection report (§6.4), not by editing this file.

## 0. Decision summary

| # | Decision | Approved |
|---|---|---|
| 1 | Scope: BOJ policy decisions, FOMC decisions, Federal Reserve Board discount-rate actions, MOF intervention from 1991-04 | 2026-11-04 (FRB split added in revision 2) |
| 2 | BOJ before 1998-04: official discount-rate changes only, with incomplete policy coverage disclosed (Q-1) | 2026-11-06 |
| 3 | Keep the all-meetings class C0 as a baseline (Q-2) | 2026-11-06 |
| 4 | MOF: individual intervention days and episodes by the 5-Tokyo-business-day rule (Q-3) | 2026-11-06 |
| 5 | Commit raw source files where the terms permit, with manifests and checksums; check terms for derived records too (Q-4) | 2026-11-06 |
| 6 | **All inclusion rules are fixed here, independently of any estimated break date** (§3.7) | 2026-11-06 |

## 1. Purpose and scope

The dataset's one v0.1 job is the descriptive comparison of ADR 0007's break dates with
official policy events (§7). It is not the v0.4 intervention-effects database; H4 work
extends it under its own ADR.

| In scope | Out of scope |
|---|---|
| BOJ monetary-policy decisions and the statements announcing them | Speeches, press conferences, Outlook Reports, minutes, summaries of opinions |
| FOMC policy decisions and statements | Minutes, SEP, speeches, testimony |
| Federal Reserve Board discount-rate actions | Reserve Bank board votes not approved by the Board |
| MOF intervention records, from 1991-04-01 | Verbal intervention, "rate checks", unconfirmed operations, other countries' operations |
| 1981-01-01 to 2026-09-11 (ADR 0006 §9.2), subject to §4 | Anything later |

**Why the exclusions.** Each excluded category lacks either a complete official record or a
bounded census. Including it would make the list depend on judgment about which items
mattered, which knowing where the yen moved can bias.

## 2. Primary sources (to be confirmed at collection)

URLs, formats and terms are confirmed and recorded in the manifest (§6). Nothing listed here
has been downloaded.

| Institution | Source | Content | Expected coverage |
|---|---|---|---|
| BOJ | Monetary Policy Meeting decisions and statements (boj.or.jp, `mopo/mpmdeci`); MPM schedule archive | Decisions, statements, meeting dates | From the first MPM under the 1998 BOJ Act |
| BOJ | Time-Series Data Search: official discount rate / basic loan rate | Change dates | Whole sample |
| FOMC | federalreserve.gov FOMC calendars and statements; historical materials (Record of Policy Actions, minutes) | Meetings, conference calls, decisions, statements | Statements from 1994-02-04; decisions whole sample |
| FOMC | FRED `DFEDTAR` (to 2008-12-15), `DFEDTARU`/`DFEDTARL` (from 2008-12-16) | Target levels; change dates are derived and cross-checked | From 1982-09-27 |
| Federal Reserve Board | (a) frbdiscountwindow.org "Historical Discount Rates": `adjustment.xls` (adjustment credit, discontinued 2003-01-09) and `primarysecondary.xlsx` (primary/secondary credit). (b) Board discount-rate meeting minutes: federalreserve.gov `discount-rate-minutes.htm` (2016 onward) and `discountrate-archive.htm` (2001–2016). (c) Board press releases. | Rate levels and effective dates by credit program (a). Board approvals and dates (b, c). | **Documented:** minutes from 2001-05 onward (pages read 2026-11-06). **Not documented:** the start date and per-district detail of the (a) files. These pages state no coverage, so it is established from the files at collection. Before 2001, no Board primary record has been identified yet. C5 is "not covered" there until one is found (§4). |
| MOF | "Foreign Exchange Intervention Operations" (mof.go.jp `english/policy/international_policy/reference/feio/`): monthly releases (index `feio/monthly/`), quarterly releases, and the "Historical Data" CSV `foreign_exchange_intervention_operations.csv` | Daily date, amount, currencies, direction | The page states no coverage. "From 1991-04-01" is an expectation to be confirmed from the CSV, not a documented fact. Whether dates are trade or settlement dates is also not stated on the page, and is confirmed at collection. |

Secondary sources (news, academic event lists, Wikipedia) never add or date events. They may
only flag a possible error, which is then resolved against another primary record or logged
as an unresolved discrepancy.

## 3. Inclusion rules

### 3.1 Record structure and stable IDs

- **One row per action.** A release that announces several distinct actions has one row per
  action. An action is one item in the decision section of the statement (or, for MOF, one
  intervention day and currency pair).
- **`release_id`** = `{INST}-{YYYYMMDD}-{n}`, with INST ∈ {BOJ, FOMC, FRB, MOF}, the
  decision (or trade) date in the institution's local calendar, and n = 1, 2, … for
  successive releases on that date, ordered by announcement time, then by the source's own
  order.
- **`event_id`** = `{release_id}-{k}`, k = 1, 2, … in the order the actions appear in the
  release.
- IDs are assigned by script and **never reused or renumbered** after the first collection
  is checksummed. A correction adds a row with a new ID and marks the old row `superseded_by`.
- **Density counts in §7 use releases, not actions,** so a statement with four actions counts
  once.

### 3.2 BOJ, 1998-04 onward

- **Every** MPM with a published decision, scheduled or unscheduled, is a release, including
  "no change" decisions (recorded as a single action with `policy_change = false`).
- `policy_change = true` for an action if, and only if, the statement announces a change to:
  - the guideline for money-market operations (operating target or level);
  - the target or guideline for asset purchases, or a yield-curve-control target or band;
  - the introduction or end of a negative rate or of yield-curve control;
  - forward guidance stated in the statement itself.
- Anything else is `policy_change = false` with a note. The rule is applied to the statement
  text, never to market reaction.

### 3.3 BOJ, 1981 to 1998-03

- Official discount-rate changes only, `policy_change = true`.
- **Disclosure carried by every output:** before 1998-04 the dataset covers BOJ discount-rate
  changes, not BOJ monetary policy. Changes in market operations, guidance or other
  instruments in that period are absent from the record, **not** absent from history.

### 3.4 FOMC

- **Every** scheduled meeting and every unscheduled meeting or conference call with a policy
  decision, 1981 to 2026-09-11, including "no change".
- `policy_change = true` if the federal-funds target or target range, or the size or pace of
  an asset-purchase programme, is changed, as stated in the statement or, before 1994, the
  Record of Policy Actions.
- Intermeeting decisions are separate releases.
- **The discount rate is not an FOMC decision** (§3.5).

### 3.5 Federal Reserve Board discount-rate actions

- Discount-rate changes are established by Reserve Bank boards of directors, subject to
  review and determination by the Board of Governors. The dataset records the **Board's**
  approval as the event, with institution FRB.
- **Coordinated actions stay distinguishable.** When FOMC and Board actions are announced
  together (for example a joint press release), each is its own row, and both carry
  `linked_ids` naming the other.
- Actions coordinated with other central banks are flagged `coordinated = true` only if the
  official release says so. The other central banks' actions are not added.

### 3.6 MOF intervention, 1991-04-01 onward

- **Every** day in the MOF daily record is one release, with one action per currency pair:
  amount (100 million yen), currency pair, direction.
- **Episodes:** runs of intervention days whose consecutive days are at most 5 Tokyo
  business days apart (Japanese public holidays from the official cabinet calendar). Derived
  by script; the rule is not tuned.
- Joint operations are flagged only if the MOF record says so.

### 3.7 Independence from break results

- Every rule in §3 and every class in §3.8 is fixed in this ADR, before any break date is
  estimated, and is not revised after.
- Data errors found after break results are seen may be corrected only against a primary
  source, logged with the date found, and never limited to events near estimated breaks.
  Every correction is reported.

### 3.8 Fixed comparison classes

| Class | Members (releases) | Coverage |
|---|---|---|
| C0 All meetings | All BOJ and FOMC releases, including no change | BOJ from 1998-04; FOMC per §4 |
| C1 BOJ change | BOJ releases with a `policy_change = true` action | Discount rate only before 1998-04 (§3.3) |
| C2 FOMC change | FOMC releases with a `policy_change = true` action | From 1982-09-27 (§4) |
| C3 MOF episode start | First day of each §3.6 episode | From 1991-04-01 |
| C4 ADR 0004 markers | The 13 fixed markers, unchanged | Whole sample |
| C5 FRB discount rate | FRB discount-rate change releases | Per §2, confirmed at collection |

Classes are not added, merged or split after break estimation.

## 4. Coverage gaps (known before collection)

| Gap | Consequence |
|---|---|
| BOJ before 1998-04: discount-rate changes only | C1 changes definition at 1998-04. §7 reports the two periods separately. C0 has no BOJ members before 1998-04. |
| FOMC schedule varies over time: number of scheduled meetings per year, unscheduled meetings, conference calls | Count checks use the Fed's own historical calendar per year, never an assumed number (§6.5). |
| FOMC archive: older conference calls and intermeeting actions may be recorded only in minutes or transcripts | Each such action is recorded with its source document. Years where the calendar and the records disagree are listed. |
| FOMC before 1994-02: decisions not announced | Decision dates are known; same-day observability is not (§5). |
| FOMC 1981 to 1982-09: reserve-targeting regime; `DFEDTAR` starts 1982-09-27 | No C2 target-change coverage before 1982-09-27. |
| BOJ MPM frequency changed over time | Count checks use the BOJ schedule archive per year. |
| MOF before 1991-04: no official daily record | C3 covers 1991-04-01 onward only. Plaza and Louvre remain C4 markers. |
| Institutional archives may have missing documents | Logged per release; never filled from secondary sources. |

**Missing coverage is not an absence of events.** No statistic treats a period outside a
class's coverage as having zero events of that class (§7.2).

## 5. Three dates per release, and alignment with USD/JPY rows

### 5.1 Fields

| Field | Meaning |
|---|---|
| `decision_date` | Date the institution took the decision (BOJ/FOMC/FRB) or traded (MOF), local calendar |
| `announce_ts` | Time the decision was **first made public by the institution**, with time zone. Null if it was not announced. |
| `announce_ts_source` | The primary document that states this time (the release itself, or an official release-time schedule), or `none` |
| `ts_precision` | `minute` (time stated in a primary document), `day` (date known, time not), or `not_announced` |
| `record_publication_date` | Date the official record of the decision became public, where later than `announce_ts` (pre-1994 FOMC minutes or Record of Policy Actions; MOF daily details) |
| `observable` | `same_day` if `announce_ts` exists; `delayed` if the decision became public only through a later record; `unknown` otherwise |
| `fx_row_date` | USD/JPY row whose change window contains `announce_ts` (§5.2); null if `observable ≠ same_day` |
| `fx_row_decision` | USD/JPY row containing the end of `decision_date`, always filled |
| `fx_row_uncertain` | True if the release could fall in either of two adjacent rows |

### 5.2 Mapping rule

USD/JPY row t covers the change from the New York noon fix on the previous row to the noon
fix on t (ADR 0003, ADR 0006 §4.5). A release belongs to the first row whose noon fix is at
or after `announce_ts`. Conversion uses Python `zoneinfo` (IANA database), so daylight-saving
rules are applied by code, not by hand.

| Case | Rule |
|---|---|
| `ts_precision = minute` | Mapped exactly. Flagged uncertain only if within 15 minutes of the noon fix. |
| `ts_precision = day` | Mapped to the row of the announcement date; `fx_row_uncertain = true` if any time that day would change the row. |
| BOJ statement | Time taken from the release when stated. Tokyo midday is the late evening of the previous New York day, so it maps to the same-Tokyo-date row. |
| FOMC statement, 1994 onward | Release time from the statement or the Fed's published release schedule. ADR 0006 §4.5's 14:15/14:00 ET were checked only against secondary sources and are **not** used unless confirmed in a primary document. Without one, `ts_precision = day` and the release is flagged. **Checked 2026-11-06:** current press releases carry a primary time line (2024-09-18: "For release at 2:00 p.m. EDT"). The 1994-02-04 statement says only "For immediate release", with no clock time, so that release gets `ts_precision = day`. The year from which time lines appear is established per release at collection, and none is inferred. |
| BOJ statement (checked 2026-11-06) | The 2024-03-19 statement PDF shows the date and "Bank of Japan" only, with no clock time. BOJ statements therefore get `ts_precision = day` unless a primary BOJ document states the time. `fx_row_uncertain` is decided by the day rule above. |
| FOMC, pre-1994 | `announce_ts` null, `observable = delayed`, `record_publication_date` from the minutes or Record of Policy Actions. **Not treated as a same-day announcement anywhere.** |
| MOF | `announce_ts` null (the operation is confirmed only in later official releases); `ts_precision = day`; `observable = unknown`; `fx_row_decision` uses the trade date; `fx_row_uncertain = true` |

ADR 0007's break dates are row dates on the same calendar, so comparisons are in **USD/JPY
business rows**.

## 6. Provenance, storage, licensing and checksums

### 6.1 Storage

- Raw source files: `data/events/raw/<institution>/`. Derived table:
  `data/events/policy_events.csv`.
- **Restricted materials** are kept in `data/events/restricted/`, which is git-ignored by the
  existing `data/*` rule. They are never committed, pushed, or included in a website build.
  This covers BOJ source documents, every coded BOJ row, and any source whose terms are
  unread or unclear (frbdiscountwindow.org, FRED). The rule was approved by the reviewer on
  2026-11-06.
  - The public `policy_events.csv` therefore excludes BOJ rows. The complete table
    (`data/events/restricted/policy_events_full.csv`) is built locally by the same code.
  - Restricted files keep their source URL, retrieval timestamp and SHA-256 in a committed
    manifest. Only these metadata are committed, never the content.
  - BOJ material moves out of `restricted/` only after its reuse permission or legal basis
    has been clarified and recorded here.
- The public research site may show independently written findings and properly sourced
  figures, once their publication rights have been checked.
- `data/raw` and `data/processed` are frozen by path (`kagura.vintage`), so nothing goes
  there. Event data are not part of the ADR 0006 vintage.

### 6.2 Licensing

Checked per source before committing anything, and recorded in the manifest. The README
already states that source data are not relicensed under the repository's MIT licence.

| Source | Status (2026-11-06) |
|---|---|
| BOJ | **Read.** Site content may be copied or reproduced with the Bank credited. Prior permission is needed for commercial use, for graphics and images, and for items marked as such. Contents "may not be altered or erased" without permission. **Open:** whether a coded derived table (dates, times, `policy_change`) counts as alteration. Until resolved, unaltered raw files are committed with attribution, and the derived table's status is decided by the reviewer (§10). |
| MOF | **Read** (mof.go.jp `english/about_mof/notice/`). The Public Data License 1.0 (PDL 1.0) applies unless other rights are indicated. PDL 1.0 (Digital Agency, read): content may be "freely used, copied, publicly transmitted, translated or otherwise modified", including commercially. Edited content must state that it was edited and by whom, and must not be presented as the government's own. PDL 1.0 is compatible with CC BY 4.0. **Consequence:** the raw CSV and monthly releases may be committed with a source citation. The derived table is permitted, labelled "Created by editing … (Ministry of Finance)". MOF's site-specific citation examples were not visible in the fetched copy and are checked at collection. |
| Federal Reserve Board | **Read** (federalreserve.gov `disclaimer.htm`). Board website information is public domain unless noted otherwise, "may be copied and distributed without permission", with the Board cited as the source. Third-party copyrighted material and seals/logos are excluded. Press releases, minutes and statements may therefore be committed, and the derived table is permitted. |
| frbdiscountwindow.org | Run by the Reserve Banks, not the Board. Its terms have **not** been read. The files are not committed until they are; only their URL and checksum go in the manifest. |
| FRED | **Read** (fred.stlouisfed.org `legal/`). FRED content may not be redistributed or "incorporated in any other database or compilation" without written permission. Series-level copyright notes override this. **Consequence:** FRED files are **not** committed. `DFEDTAR`/`DFEDTARU`/`DFEDTARL` serve only as a cross-check of FOMC target dates taken from Fed primary releases (public domain). The manifest records the series ID, retrieval date and checksum. Before use, each series' copyright note is checked, and the result recorded. |

### 6.3 Manifest

`data/events/manifest.json`, per raw file: URL, download time (UTC), HTTP status, size,
SHA-256, licence note, and whether the file is committed.

### 6.4 Building the table

- Built by script (`kagura.events`) from the raw files. No hand editing.
- If a source is available only as HTML or PDF and parsing is unreliable, rows may be
  transcribed by hand **only** with a second, independent pass and a scripted diff. Every
  hand-entered row is flagged.
- **Checksums:** the SHA-256 of every raw file and of the derived table go into a new
  `EVENTS_SHA256` dictionary in `kagura.vintage`, separate from the frozen ADR 0006/0008
  tables. ADR 0007's run verifies them first.
- The collection is reported for review, with per-source counts, coverage and every flag,
  before any break statistic is computed.

### 6.5 Validation

| Check | Rule |
|---|---|
| Meeting counts | Per year, against the Fed's historical FOMC calendar and the BOJ MPM schedule archive. Every mismatch is listed. |
| Known anchors | 1999-02-12, 2001-03-19, 2013-04-04, 2016-01-29, 2016-09-21 and 2024-03-19 are BOJ releases with a `policy_change = true` action; 2022-09-22 is an MOF intervention day. A mismatch is investigated against the primary source, not corrected to ADR 0004. |
| Target series | Every `DFEDTAR`/`DFEDTARU` change date matches an FOMC decision. Pre-1994 differences between decision and implementation dates are logged. |
| IDs | Unique, and matching the §3.1 pattern. |
| Dates | `decision_date` ≤ `announce_ts` date ≤ `record_publication_date` where present; all within 1981-01-01 to 2026-09-11. |
| Time zones | A test covers each daylight-saving transition affecting a minute-precision release. |

## 7. Comparing events with estimated break dates

Fixed now, before any break is estimated.

### 7.1 Inputs

For every ADR 0007 break estimate τ̂ (each sample × ε × specification × grid × m): its 95 %
interval [a, b], its eligible candidate set G (ADR 0007 §3.3), and its §2.1 label.

### 7.2 Coverage-aware statistics, per class

Each class has a coverage period (§3.8, §4). Let G_c be the candidates in G that lie inside
class c's coverage, with the interval of the same widths around them also inside coverage.

1. **Events in the interval.** Every release of the class with `fx_row_date` (or, where null,
   `fx_row_decision`, marked) in [a, b]. If part of [a, b] lies outside coverage, the result
   is reported as **"partially uncovered"**, never as a count of zero for that part.
2. **Nearest event.** Signed distance in rows from τ̂ to the nearest release of the class
   (negative = before τ̂), searched only inside coverage. If the nearer side is uncovered, the
   distance is reported as a lower bound.
3. **Chance baseline for the interval.** The share of candidates in G_c at which an interval
   of the same left and right widths contains at least one release of the class.
4. **Chance baseline for the distance.** The distribution of nearest-release distances over
   G_c, and the percentile of τ̂'s distance in it.
- If τ̂ is outside coverage, statistics 2–4 are **not computed** for that class ("not
  covered").
- Baselines use the **same grid** as the estimate: month-start candidates for multi-break
  estimates, daily rows for the daily single-break sensitivity.
- **Unobservable releases.** Pre-1994 FOMC releases and MOF days enter by `fx_row_decision`.
  Every statistic is reported twice: all releases, and `observable = same_day` releases only.

Statistics 3 and 4 are descriptive. They answer how often a date placed anywhere in the
covered eligible range would look this close to an event of the class. They are not p-values
and do not account for the date being estimated rather than random.

### 7.3 Reporting

- All statistics, for every class and every break, including breaks with no nearby event and
  events with no nearby break.
- BOJ results split at 1998-04 (§3.3).
- No class, window width or event is chosen after seeing break dates (§3.7).

### 7.4 Language

| Allowed | Not allowed |
|---|---|
| "The estimated break lies 12 rows after the 2013-04-04 BOJ release" | "QQE caused the break" |
| "Its 95 % interval contains 3 C1 releases; in the covered eligible range, an interval of the same width contains at least one in 64 % of positions" | "The break coincides with, and is explained by, …" |
| "No C3 episode starts within the interval" | "Intervention had no effect" |
| "C3 does not cover this interval (before 1991-04)" | "No intervention occurred" |

Banned for any event–break pair, in any table, figure or summary: "caused", "triggered",
"led to", "drove", "because of", "explained by", "effect of".

**Why.** Policy events respond to market conditions, cluster in turbulent periods, and are
dense (C0 has roughly 16–22 releases a year since 1998). Proximity is expected by chance and
is confounded with the conditions that prompted the event.

## 8. Limitations

| # | Item |
|---|---|
| D1 | `policy_change` codes statement text; borderline cases are logged, not resolved by market reaction. |
| D2 | Coverage differs by institution and period (§4); comparisons across periods are not like for like. |
| D3 | MOF time of day and same-day observability are unknown. |
| D4 | Pre-1994 FOMC decisions were not public on the decision date. |
| D5 | Official records can be revised; the collected vintage is what is checksummed. |
| D6 | Excluded categories may matter economically; their absence is a scope choice, not a finding. |
| D7 | Pre-1998 BOJ coverage is discount-rate changes only (§3.3). |

## 9. Remaining blockers to freezing

Status 2026-11-06 (third pass):

| # | Item | Status |
|---|---|---|
| 1 | MOF, Board and FRED terms (§6.2) | **Resolved.** Read and applied: commit MOF and Board files; do not commit FRED. |
| 2 | BOJ derived-table question | **Decided by the reviewer (2026-11-06).** Collect and code privately in `data/events/restricted/` (§6.1). No public redistribution of BOJ documents or coded BOJ rows until reuse permission or a legal basis is clarified. |
| 3 | Board discount-rate source (§2) | **Acceptable with disclosure.** Sources are identified. Coverage is documented from 2001-05 (minutes). Before that, coverage is unknown and C5 is "not covered" until a primary record is found. The start of the frbdiscountwindow.org files is established at collection, and their terms must be read before they are committed. |
| 4 | Release times (§5.2) | **Acceptable with disclosure.** Current FOMC releases state a time. The 1994 FOMC and 2024 BOJ statements do not, so `ts_precision = day` and `unknown` are used there. Nothing is inferred. |

## 10. Order of operations

1. Reviewer approval of this revision and ADR 0007; decisions on §9.
2. Freeze with ADR 0007 (one commit), push.
3. Download into `data/events/raw/`; build the manifest.
4. Build and validate the table (§6.4–§6.5); add `EVENTS_SHA256`.
5. Report the collection for review. Only then run ADR 0007.
