# Data and measurement concepts

<p class="lead">Most errors in empirical finance happen before any model runs: a value used
before it was public, a holiday turned into a fake zero change, a file silently revised.
These concepts are how KAGURA's pipeline guards against them.</p>

Status labels:
<span class="status implemented">Implemented</span>
<span class="status exploratory">Exploratory</span>
<span class="status rejected">Rejected</span>
<span class="status planned">Planned</span>
<span class="status background">Background</span>.
See the [concept index](../INDEX.md#concept-index).

---

## Observation, release and vintage dates; look-ahead bias

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · ADR 0003</p>

**Plain English.** A number has three dates: the period it describes (*observation* or
reference month), the day it was published (*release*), and the version you downloaded
(*vintage*). Using a value in a row dated before its release is **look-ahead bias**:
the analysis "knows" something no market participant could have known.

**Why it exists.** Look-ahead bias makes relationships look tighter and forecasts look better
than they could have been in real time.

**Definition.** A value for month \(m\) may enter a row dated \(t\) only if
\(t \ge \text{release}(m)\). ADR 0003 uses fixed conservative release rules:

| Series | Assumed known on |
|---|---|
| US CPI for month m | 15th of m+1 |
| Japan CPI for month m | last day of m+1 |
| Japan call rate for month m | 1st of m+1 |

**How KAGURA used it.** `monthly.csv` stores the reference month of each macro value beside it
(`<series>_month`), and a test checks that no value appears before its availability date
(`kagura.align.build_monthly`). H1b, which asks about levels relations by reference month,
aligns CPI by reference month instead and says so (ADR 0008 §2).

**What we found / decided.** Japan CPI was first set to the 25th of m+1, then moved to the last
day: "deliberately conservative", so the dataset may know Japan CPI later than the market did,
never earlier. As a result, Japan CPI is two months old in 201 of 668 monthly rows (ADR 0003).

**Assumptions and limits.** Fixed rules, not historical release calendars. Known failures: the
2025 US shutdown delayed September 2025 CPI, and October 2025 CPI was never published (hence the
missing 2025-10 in H1b). Values are current vintages, not first releases (ADR 0002).

**Common mistake.** Forward-filling monthly data into a daily table by reference month. That
uses CPI weeks before it was published.

**Go deeper.** [ADR 0003](../../decisions/0003-time-alignment.md) ·
[Overview report §3](../reports/00-research-overview.md#3-the-data-foundation) ·
[`align.py`](https://github.com/akiblasco/kagura/blob/main/src/kagura/align.py)

---

## Asynchronous market closes (noon fix vs Tokyo close)

<p class="concept-meta"><span class="status implemented">Implemented</span> Level I · ADR 0003 decision 2, ADR 0006 §4.5, robustness R1</p>

**Plain English.** "Daily" series are recorded at different times of day. USD/JPY is the noon
New York fix; US Treasury yields close about 3.5 hours later; JGB yields close in Tokyo, about
11 hours before the fix. A "same-day" change therefore covers different 24-hour windows for
different series.

**Why it exists.** If windows differ, a same-day regression mixes contemporaneous movement with
lead–lag effects, and can include information from after the FX fix.

**Definition.** Windows of daily changes (New York time, ADR 0006 §4.5):

| Series | Observed at | Change window |
|---|---|---|
| USD/JPY | 12:00 | (12:00 t−1, 12:00 t] |
| US yields | ≈ 15:30 | (15:30 t−1, 15:30 t] |
| JGB yields | ≈ 01:00–02:00 | (≈ 01:00 t−1, ≈ 01:00 t] |

Every variant estimates a projection coefficient \(\beta = \operatorname{Cov}(\Delta s,\Delta
d)/\operatorname{Var}(\Delta d)\), whose relation to an "instantaneous" response depends on the
data-generating process.

**How KAGURA used it.** Two timing variants are always reported: same-day (primary) and lagged US
leg, \(d^{lag}_t = us_{t-1} - jgb_t\) (robustness R1). Monthly changes (R2) make the misalignment
negligible (≈ 0.5–1.5 % of the window).

**What we found.** R1: β 1.43 → 0.75, inconclusive. R2 (monthly): 4.38 → 7.45, material decline
ruled out. The disagreement is information: the daily same-day 2Y link is where weakening, if
any, shows.

**Assumptions and limits.** Observation times are approximate and unverified against source
methodology (ADR 0006 A8). Reading the era change as a change in the underlying link assumes the
timing distortion is stable across eras (A5); JGB yields moving again since 2024 may violate this.

**Common mistake.** Calling the lagged variant "same-day without look-ahead". It is a different
estimand: mostly a lead–lag relationship.

**Go deeper.** [H1a report §5](../reports/01-h1a-short-run-comovement.md#5-robustness) ·
[Chapter 2 §8](../textbook/regression-coefficients.md#8-association-not-causation) ·
[ADR 0006](../../decisions/0006-h1-formal-testing-protocol.md)

---

## Frozen data vintages and checksums

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · ADR 0006 §9.2, ADR 0008 §8.2, `vintage.py`</p>

**Plain English.** Before a confirmatory test runs, the exact data files are fixed and
fingerprinted. If any byte changes, the analysis refuses to run.

**Why it exists.** Sources revise and lose history (ADR 0005 documents 890 Brent values vanishing
from FRED). Without a frozen vintage, a result cannot be reproduced, and data could be quietly
updated until a result looks better.

**Definition.** A **SHA-256 checksum** maps a file to a 64-character fingerprint; any change to the
file changes the fingerprint with overwhelming probability.

**How KAGURA used it.**
- ADR 0006 §9.2 lists eight checksums (raw downloads of 2026-09-15 and processed files).
  `kagura.h1a.verify_checksums` raises `IntegrityError` on any mismatch.
- H1b added the two CPI files (ADR 0008 §8.2), stored in `vintage.FROZEN_SHA256`.
- `kagura.vintage.ensure_writable` makes `make data` refuse to overwrite the frozen directory;
  fresh downloads go elsewhere via `KAGURA_DATA`.
- Samples are fixed too: daily to 2026-09-11, monthly to 2026-08. Later downloads do not extend them.

**What we found.** All checksums re-verified on 2026-10-23. The Japan CPI file was checked to be
one consistently linked 2025-base index with no in-window splice (ADR 0008 §8.2).

**Assumptions and limits.** Raw data are not committed (redistribution). Anyone reproducing needs
the same downloads; a checksum mismatch tells you they differ, not how.

**Common mistake.** "Refreshing the data" before re-running a frozen analysis. That changes the
evidence the result is about.

**Go deeper.** [Overview report §3](../reports/00-research-overview.md#3-the-data-foundation) ·
[`vintage.py`](https://github.com/akiblasco/kagura/blob/main/src/kagura/vintage.py) ·
[`h1a.py`](https://github.com/akiblasco/kagura/blob/main/src/kagura/h1a.py) ·
[ADR 0006](../../decisions/0006-h1-formal-testing-protocol.md)

---

## Carried values, the exclusion rule and the carried-share guard

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · ADR 0003, ADR 0004, ADR 0005</p>

**Plain English.** When Tokyo is closed but New York is open, there is a USD/JPY observation but no
new JGB yield. KAGURA carries the last JGB value forward and *flags* it, then excludes any change
that touches a carried value. A guard fails the tests if too many values are carried.

**Why it exists.** A carried value creates a fake zero change on the holiday and a two-day change
the day after. Both distort a regression of daily changes. Silent filling can also hide a source
that lost data.

**Definition.**

$$
\texttt{change\_carried}_t = \texttt{carried}_t \lor \texttt{carried}_{t-1}.
$$

A row enters H1a only if both changes are between consecutive live observations. Carry is capped at
5 business days (7 calendar days). `MAX_CARRIED_SHARE` = 8 %.

**How KAGURA used it.** The calendar is USD/JPY's (never filled). Other series use an as-of join
(`kagura.align.build_daily`). In H1a, 1,187 of 11,466 rows with a 2Y differential were excluded,
leaving 10,279 (notebook 02). `kagura.align.carried_share` warns in `make data` and fails `make
test` if an H1 input exceeds 8 %.

**What we found / decided.** The guard exists because Brent's carried share jumped from 1.5 % to
10.0 % after a FRED change, unnoticed by tests (ADR 0005). Market holidays alone give up to about
6 %; 8 % leaves room for that.

**Assumptions and limits.** HAC treats retained rows as consecutive across excluded rows (ADR 0006
A9). The flag covers one-row changes only; k-day changes need a rolling flag. The monthly
robustness check deliberately does not apply carried flags.

**Common mistake.** Reindexing to a business-day calendar and forward-filling. ADR 0003 explains
why that fails: the MOF file has 472 Saturday JGB quotes from before 1989, which a reindex would drop.

**Go deeper.** [ADR 0003](../../decisions/0003-time-alignment.md) ·
[ADR 0005](../../decisions/0005-carried-share-guard.md) ·
[`align.py`](https://github.com/akiblasco/kagura/blob/main/src/kagura/align.py) ·
[H1a report §2](../reports/01-h1a-short-run-comovement.md)
