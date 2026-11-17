# KAGURA — Independent Audit Handoff (before ADR 0011 Phase A)

Prepared 2026-11-17 by the implementing session, for a fresh session that has not seen its
reasoning. **Updated 2026-11-18 after ADR 0012:** see §0. Sections 1–8 are the pre-audit
handoff as given to the auditor, with only the ADR table extended.

## 0. Status after the independent audit and ADR 0012 (2026-11-18)

- **Audit (2026-11-17):** CONDITIONAL PASS. The report itself is not reproduced or rewritten
  here.
- **ADR 0012:** frozen 2026-11-18.
- **Phase A:** not yet run. No historical break statistic has been computed.

| Audit finding | Kind | Resolution |
|---|---|---|
| H1: robust Bai interval `phi2s` divided by Δ'Q₁Δ (inherited from `mbreaks`) | **Fixed defect** | Δ'Ω₂Δ/Δ'Q₂Δ (`breaks.break_intervals`). Derivation, independent limit-simulation tests at η = 0.25, 1, 4, and a coverage study on the Phase A grids (ADR 0012 §1–§3). |
| M1: R comparison ±1-row tolerance; described as more than fidelity | **Fixed** | Exact bounds; every difference reproduced by a named convention (309 pass / 90 convention / 0 FAIL); described as implementation fidelity (ADR 0012 §4). |
| M2: interval validation did not match Phase A | **Fixed** (validation added) | `adr0012-bai-interval/coverage.txt`, month-start grids, η ≠ 1. Coverage 80.0–97.2 % for the corrected method: not calibrated. |
| M3: FX/yield intraday timing varies by era | Remaining limitation | ADR 0012 L19. State it beside every break date; V1 is the check. |
| M4: Phase C multiplicity | Remaining limitation | ADR 0012 L20. Freeze the headline cell and m before Phase C. |
| L1: Phase A memory | **Fixed** | 4 workers. |
| L2: blocklist guard | **Fixed** | Explicit `ALLOWED` columns, with a test that the list contains no withheld-statistic name. |
| L3: no h > q check in `global_partitions` | Not changed | Cannot occur with real h. |
| L4: New York-afternoon MOF interventions one row early | Remaining limitation | ADR 0012 L21; flagged `fx_row_uncertain`. |
| L5: robustness wording in `README.md` / H1a report | Not changed | Open documentation item. |
| L6: monthly month-end carried JGB | Not changed | Deliberate (ADR 0006 §9.1). |
| Not audited: H1b re-run, restricted BOJ data, critical-value simulator internals, live R re-run | Remaining limitation | ADR 0012 L22. |

**Still failed or unresolved** (unchanged):
- ADR 0007 §9.1 critical-value check: FAILED (ADR 0011 §1).
- q = 2 seq(2|1) discrepancy (ADR 0011 §4).
- BG power and non-MDS bootstrap designs D1/D2.

**Withheld from Phase A** (ADR 0011 §3–§5):
- sup F(k), UDmax, WDmax;
- sequential sup F(l + 1 | l) and sequential break counts;
- the WF bootstrap and any "approximately tested" or "bootstrap-supported" label;
- the Phase C event comparison.

Phase A reports descriptive estimates and BIC/LWZ model selection only. Its Bai intervals are
nominal; coverage is not established.

**Phase A gate:**
- the five ADR 0011 §5 hashes;
- `comparison_adr0012.txt` at its ADR 0012 §7 hash, with 0 FAIL;
- the frozen data checksums.

- **No historical structural-break estimate has been computed.** Phase A is not yet run.
- **Treat everything below as claims to verify**, not as established.

## 1. Decisions (`docs/decisions/`)

| ADR | Subject | Status |
|---|---|---|
| 0001–0003 | Sample period; data sources; calendar and time alignment | Accepted 2026-09 |
| 0004 | H1 exploratory specification (frozen before viewing results) | Frozen 2026-09-23 |
| 0005 | Carried-share guard after a Brent source change | Accepted 2026-09-25 |
| 0006 | H1 formal testing protocol (H1a) | Frozen |
| 0007 | Exploratory structural-break dating of the H1a short-run relation | Frozen 2026-11-06 |
| 0008 | H1b long-run levels: confirmatory claim not assessable (earlier version in `superseded/`) | Frozen 2026-10-24 |
| 0009 | Official policy-event dataset (BOJ, Fed, MOF) | Frozen 2026-11-06 |
| 0010 | Policy-event collection clarifications (Tokyo bank calendar; 74 MOF episodes) | Accepted 2026-11-11 |
| 0011 | ADR 0007 validation resolution; Phase A (descriptive) authorised | Frozen 2026-11-17 |
| 0012 | Bai interval correction (`phi2s`); audit resolution; amended Phase A gate | Frozen 2026-11-18 |

## 2. Research question and frozen estimands

- **Question** (`docs/HYPOTHESES.md` H1): has USD/JPY decoupled from the US–Japan
  rate differential, and if so, when and by how much?
- **H1a** (ADR 0006): the short-run relation, regressing the daily 100·Δlog USD/JPY on the
  Δ(US − JGB) 2-year differential with a constant. The ADR 0006 tests are complete and
  closed (ADR 0008 §7.1).
- **H1b** (ADR 0008): the long-run levels relation. The confirmatory claim is not assessable.
- **ADR 0007 break dating** is exploratory only.
  - **Model:** pure structural change, M = 5, month-start candidate grid.
  - **Samples:** 1981+ and 2013+, at ε = 15/10/5 %.
  - **Variants:**
    - V1: lagged timing;
    - V2: 10-year differential;
    - V3: monthly data;
    - lag-augmented, p = 1, chosen at step 1 (`research/adr0007/out/step1_lags.csv`).
  - Nothing confirms or rejects H1.

## 3. Data provenance and checksums

| Item | Where | Check |
|---|---|---|
| Frozen market vintage (USD/JPY, US 2y/10y, JGB, manifest, processed daily/monthly) | `data/raw/`, `data/processed/` (gitignored, local only) | `kagura.vintage.FROZEN_SHA256`; `kagura.h1a.verify_checksums()` passed 2026-11-17 |
| CPI files (H1b) | `data/raw/` | `kagura.vintage.CPI_SHA256` |
| Policy events (public FOMC/FRB/MOF) | `data/events/` (committed) | `kagura.vintage.EVENTS_SHA256`, `events_mismatches(Path("data/events")) == []` on 2026-11-17 |
| BOJ events | `data/events/restricted/` (gitignored; never committed) | ADR 0009 §6.1 |

`kagura.data` and `kagura.align` (`make data`) build the vintage. ADR 0002 lists the
sources.

## 4. Entry points

| What | Where |
|---|---|
| Break DP, ICs, HAC/QS long-run variance, sup F, sequential, Bai intervals | `src/kagura/breaks.py` |
| Limit simulations, quantiles, robust BG, WF bootstrap | `src/kagura/breaksim.py` |
| Samples, regressors, grids, checked against frozen counts | `research/adr0007/data.py` |
| Phase A runner (gate, guard; computes no tested statistics) | `research/adr0007/run_breaks.py` |
| Validation scripts and outputs | `research/methodology/adr0007-break-grid/` |
| R cross-check (fixtures, R script, reference output, comparison) | `.../adr0007-break-grid/r-crosscheck/` (README has the environment and commands) |
| Tests | `tests/test_breaks.py`, `tests/test_phase_a.py` |
| H1a / H1b | `src/kagura/h1a.py`, `longrun.py`; `notebooks/02–04` |

## 5. Validation status (ADR 0007 §9 and ADR 0011)

| Check | Result |
|---|---|
| DP vs brute force; grid reproduction; known breaks; Nile fixture | Pass |
| **§9.1 critical values, 4,000 points, within 0.35** | **FAILED**: 11/72 (9/66 in the frozen scope). Unresolved (ADR 0011 §1) |
| 1,000-point table diagnostic | 72/72 within 0.35. Supporting only, not a pass |
| q = 2, ε = 15 % seq(2\|1) | +0.29 even at 1,000 points. Plausibly a table Monte Carlo error; unresolved (ADR 0011 §4) |
| WF bootstrap size (GARCH) | 0.058 and 0.066, CP intervals contain 0.05 |
| Robust BG size | 0.052 and 0.063, pass. **Power design defective (D1)** |
| Non-MDS bootstrap design | **Too weak to show distortion (D2)** |
| Bai interval coverage at nominal 95 % | **76.5–92.7 %**, reported, not tuned |
| §9.2 R (strucchange 1.6-0, mbreaks 1.0.1, R 4.5.3) | 359 pass, 40 documented conventions, 0 FAIL; fixtures, R output and comparison reproduced byte-identically 2026-11-17 |
| Not checked independently | Bartlett LRV (statsmodels only); limit simulator (tables only); robust BG (statsmodels); WF bootstrap (no independent implementation) |

## 6. Limitations and open questions

- ADR 0007 L1–L12 and ADR 0011 L13–L18.
- **Withheld from reporting:** sequential break counts; every tested claim (sup F(k),
  UDmax, WDmax, WF).
- **Proposed, not approved:** S1–S3 (ADR 0011 §5).
- **Primary sources not read:** Bai (1997); Bai–Perron (1998, 2003a). The sequential
  procedure and the intervals come from `mbreaks` code.
- **Required before BOJ C1 is used:** a second BOJ coding pass (ADR 0010 §3a).

## 7. Instructions for the auditor

1. **Do not run** `research/adr0007/run_breaks.py`, or any break estimation on historical
   data, unless the user explicitly asks. Do not edit frozen ADRs or validation outputs.
2. **Reproduce first:**
   - `make lint`
   - `make test`
   - `uv run python -c "from kagura.h1a import verify_checksums; verify_checksums()"`
   - the R cross-check per its README, in a copy of `r-crosscheck/`
3. **Verify claims against code, not against this document or the ADR prose.** Priorities:
   - month-start grid and sample construction (`research/adr0007/data.py`, ADR 0007 §3);
   - `breaks.break_intervals` against Bai (1997);
   - whether `run_breaks.guard` can be bypassed;
   - look-ahead and timing (ADR 0003, ADR 0006 §4.5);
   - consistency of every number quoted in ADR 0011 with the output files.
4. **Report findings ranked by severity.** Separate defects from disagreements of judgement,
   and stop. Do not fix.

## 8. Phase A, when authorised

```
uv run python research/adr0007/run_breaks.py
```

- **Gate:**
  - the R comparison must show 0 FAIL;
  - the five original validation outputs must match the ADR 0011 §5 hashes;
  - the frozen data checksums must pass.
- **Writes `research/adr0007/out/phase_a/`:**
  - `selection.csv`: BIC and LWZ m per cell;
  - `partitions.csv`: m = 0…5 SSR, BIC, LWZ and dates;
  - `break_table.csv`: dates; nominal 90/95 % Bai intervals with widths in rows, days and
    share of the eligible range; truncation flags; coverage note;
  - `regime_table.csv`: coefficients and HAC SEs;
  - `daily_sensitivity.csv`;
  - `README.txt` with the disclosures.
- **Scope:** 30 cells:
  - primary, V1, V2 and V3, each × full/recent × 3 ε;
  - lag-augmented × full/recent × 3 ε.
- **Content limits:** every row is "descriptive estimate" or "model selection". No sup F,
  critical value, p-value, sequential or bootstrap field appears.
