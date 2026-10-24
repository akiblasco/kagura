# Superseded ADR 0008 drafts (history only, not authoritative)

The authoritative document is `docs/decisions/0008-h1b-long-run-protocol.md`. The files
below record how its central decision was reached. None was frozen.

| File | Date | Content |
|---|---|---|
| `r2-protocol.md` | 2026-10-23 | Full protocol with AK P as the confirmatory test. Byte-identical to the former `docs/decisions/0008-…PROPOSED-r2.md` (sha256 `3a770758e82091ee…`). |
| `r3-delta.md` | 2026-10-23 | PSS bounds verified; AK reproduces Table 1 but cannot attain 2.5 % here (B1) |
| `r4-decision-report.md` | 2026-10-23 | Candidate screen; WW the only verifiable option |
| `r4b-wagner-wied-pilot-report.md` | 2026-10-23 | WW pilot; NO-GO |
| `r5-first-draft.md` | 2026-10-23 | First revision-5 draft, before the E1–E4 decisions |

**Errata:**
- In `r4-decision-report.md`, "Table 10" should read Table 11.
- In `r4b-…` §6, "559 months" should read 679.
- The `sim/` and `sim2/` paths in these reports correspond to
  `research/methodology/adr0008-h1b-confirmatory-pilots/{ak_bounds,wagner_wied}/`.
