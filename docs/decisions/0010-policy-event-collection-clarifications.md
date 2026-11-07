# ADR 0010 — Policy-Event Collection: Clarifications of ADR 0009

Date: 2026-11-07.

**Status: PROPOSED (for reviewer approval with the collected dataset).** ADR 0009 stays
frozen and unedited. This ADR records (a) one conflict resolved by the stricter rule, (b) the
collection rules that ADR 0009 left to "collection" and that code now fixes, and (c) one open
decision. Every rule below was fixed before any break date was estimated (ADR 0009 §3.7).

## 1. BOJ material: the stricter rule applies

ADR 0009 conflicts with itself. §6.2 (BOJ row) says unaltered raw BOJ files "are committed
with attribution". §6.1, approved later by the reviewer, keeps BOJ source documents and every
coded BOJ row in `data/events/restricted/`.

**Decision:** §6.1 governs.

- No BOJ file and no BOJ-derived row is committed, pushed or published. This includes the
  coding log (`restricted/boj_coding_log.csv`) and the full table
  (`restricted/policy_events_full.csv`).
- The committed manifest lists BOJ files by URL, retrieval time and SHA-256 only, as §6.1
  allows.

## 2. Collection rules fixed in code (`kagura.events`)

| # | Item left open by ADR 0009 | Rule as implemented |
|---|---|---|
| R1 | FOMC meeting list | **Sources:** the Fed's historical pages `fomchistorical{1981..2020}.htm` and `fomccalendars.htm` (2021 onward). **Included:** every scheduled or unscheduled meeting, plus calls and notation votes that have a statement link or a target change (§3.4). **Excluded and logged:** 84 calls, 4 notation votes, 1 cancelled meeting. **`decision_date`:** the last day of the meeting. |
| R2 | FOMC target changes | **Source:** the Board's tables `openmarket_archive.htm` (1990–2002) and `openmarket.htm` (2003 onward). **Attribution:** each change goes to a meeting, call or vote decided on the table date, the day before, or the business day before. It also goes to one whose statement was released on any of those days. **Otherwise** it is a separate intermeeting release (7 cases, 1990–1992). **Before 1990:** no Board table, so `policy_change` is left empty. |
| R3 | FOMC announcement | **Date:** the date printed on the statement page, not the URL date. They differ once: the 2007-06-28 statement sits at a URL dated 06-18. **Time:** from the "For release at" line, checked against the IANA daylight-saving rule. If the page has no such line, `ts_precision = day`. |
| R4 | FOMC asset purchases (§3.4) | **Not coded.** From 2008-11-25 `policy_change` reflects the funds target only, and every row says so. Coding this needs the statement-by-statement double pass of ADR 0009 §6.4. |
| R5 | FRB discount rate (§3.5) | **Source:** the Board's discount-rate minutes, 2001-05 onward. **Event:** an entry whose heading reports an increase or decrease in the discount or primary credit rate and whose outcome line is "Approved."; dated by that outcome line. **Linking:** if an FOMC release announced that day mentions the rate, in the statement or its Implementation Note, the two rows are linked and the FRB row takes the FOMC announcement fields. Otherwise the announcement is `unknown`. **Before 2001-05:** not covered. |
| R6 | BOJ meeting list | **Sources:** MPM dates from the BOJ minutes indexes, and decision documents from the yearly statement indexes. Every meeting matches across the two (0 mismatches). **Announcement time:** taken from the BOJ's own "Announced at" label, Tokyo time. |
| R7 | BOJ `policy_change` (§3.2), first pass by script | **Order of rules:** (1) the BOJ's own label "unchanged" or "maintained" means false. (2) A specific decision title means true. Titles about facilities or operations only are §3.2 "anything else" and false. (3) A generic title is decided by the statement's decision sentence. **Status:** this is a first pass. A second, independent pass and a scripted diff are still required before C1 is used. |
| R8 | BOJ before 1998-04 (§3.3) | **Source:** effective dates in the BOJ discount-rate series. The decision and announcement dates are not in the source, so `observable` is `unknown`. |
| R9 | `coordinated` | Set to true only when the FOMC statement or Implementation Note mentions joint or coordinated action with other central banks. The FRB row takes the flag from its linked FOMC row. |
| R10 | Re-collection | `collect()` never overwrites a file it already has. The collected vintage is what gets checksummed (§8 D5). |
| R11 | Checksums (§6.4) | `EVENTS_SHA256` pins three files: the manifest (which holds the SHA-256 of every raw file), the public table and the full table. `vintage.events_mismatches` checks both levels. |

## 3. Open decision: New Year bank holidays in MOF episodes (Q-5)

ADR 0009 §3.6 defines Tokyo business days by the Cabinet Office public-holiday calendar.
That calendar does not include the bank holidays of 31 December to 3 January.

| | Cabinet calendar only (as frozen) | Adding 31 Dec – 3 Jan |
|---|---|---|
| Episodes | 75 | 74 |
| Affected gap | none | 1999-12-24 → 2000-01-04: 7 business days becomes 5, so the two days join one episode |

Interventions occurred on two New Year bank holidays: 2003-12-31 and 2004-01-02. Under either
rule these fall in the same episode.

**The build keeps the frozen rule (75 episodes) until the reviewer decides.**

## 4. Risks

- **R2:** before 1994 the date in the Board's table can be the implementation date, so the
  attribution window is a judgment. FRED `DFEDTAR` disagrees with the table by one day on
  1990-11-13 and 1990-12-18, and again where the table gives the effective date
  (2015-12-17, 2016-12-15).
- **R5:** two change entries print no outcome line and are left out rather than dated by
  guess. They are the approvals of 2008-01-30 and 2010-02-18, in the minutes released
  2008-02-26 and 2010-04-13.
- **R7:** a scripted reading of statements can miss changes that are stated only in the body
  of a statement, such as some forward-guidance edits. The second pass exists to catch them.
