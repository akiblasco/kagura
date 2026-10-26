# Case study: how H1b became "not assessable"

<p class="lead">H1b was meant to be KAGURA's long-run test: did USD/JPY, prices and interest
rates share an equilibrium that broke after 2022? Two published tests were implemented,
verified against their papers, and then failed in simulation at our sample dimensions. The
project froze the hypothesis as <strong>not assessable</strong> rather than keep searching —
and learned more from the failure than a quick test would have taught.</p>

<div class="kpi-grid" markdown>
<div class="kpi" markdown>
<div class="label">Protocol drafts</div>
<div class="value">5</div>
<div class="note">Revisions 2–5 archived; r5 frozen</div>
</div>
<div class="kpi" markdown>
<div class="label">Andrews–Kim size at 2.5 %</div>
<div class="value">4.7–10.7 <small>%</small></div>
<div class="note">Every main simulation cell</div>
</div>
<div class="kpi" markdown>
<div class="label">Wagner–Wied power</div>
<div class="value">2–8 <small>%</small></div>
<div class="note">Against 1–2 σ breaks, high persistence</div>
</div>
<div class="kpi verdict" markdown>
<div class="label">Final decision</div>
<div class="value">Not assessable</div>
<div class="note">α = 0.025 unused · ADR 0008</div>
</div>
</div>

!!! info "How to read this page"
    **Verified record** comes from ADRs, archived drafts, commits and notebook outputs, and
    is linked. Passages marked *Reconstruction* are inferences about reasons not written
    down at the time. All simulation results are on **synthetic data**: they describe the
    methods, not USD/JPY (ADR 0008 §0, decision 3).

## Timeline

<ol class="timeline">
<li><span class="when">2026-10-09</span><span class="what"><strong>H1b deferred.</strong> ADR 0006 freezes H1a and reserves α = 0.025 for H1b, whose test is left to a later ADR. <a href="../../../decisions/0006-h1-formal-testing-protocol/">ADR 0006 §10</a></span></li>
<li><span class="when">2026-10-21</span><span class="what"><strong>H1a result:</strong> inconclusive. H1b becomes the remaining confirmatory test. <span class="tag">2c5b446</span></span></li>
<li><span class="when">2026-10-23</span><span class="what"><strong>Revision 2:</strong> the protocol — an ARDL bounds-test gate, then an Andrews–Kim end-of-sample test. <span class="tag">r2</span></span></li>
<li><span class="when">2026-10-23</span><span class="what"><strong>Revision 3:</strong> corrections — tax impulses must propagate through lagged differences; size must be simulated for the <em>full</em> procedure. <span class="tag">r3</span></span></li>
<li class="fail"><span class="when">2026-10-23</span><span class="what"><strong>Revision 4:</strong> Andrews–Kim verified against its paper, then fails at T = 492, m = 55. Candidate screen leaves only Wagner–Wied. <span class="tag">r4</span></span></li>
<li class="fail"><span class="when">2026-10-23</span><span class="what"><strong>Wagner–Wied pilot:</strong> theory does not cover the design; size depends on bandwidth; power near zero. NO-GO. <span class="tag">r4b</span></span></li>
<li><span class="when">2026-10-23</span><span class="what"><strong>Revision 5:</strong> the reviewer approves "not assessable", unused α, and an exploratory plan. <span class="tag">r5</span></span></li>
<li><span class="when">2026-10-24</span><span class="what"><strong>ADR 0008 frozen</strong> with a last correction: q may be I(2), so every transformed series needs its own integration test. <span class="tag">a37f5d6</span></span></li>
<li><span class="when">2026-10-24</span><span class="what"><strong>Exploratory Stage 1:</strong> four long-run specifications, none defensible. <span class="tag">8fba5b6</span></span></li>
<li><span class="when">2026-10-24</span><span class="what"><strong>Specification audit:</strong> Stage 1 had simplified the draft design; re-run as a sensitivity analysis, no classification changes. <span class="tag">ca8ebd3</span></span></li>
</ol>

Archived drafts: [`docs/decisions/superseded/0008/`](../../decisions/superseded/0008/README.md).
Pilot code and reference outputs:
`research/methodology/adr0008-h1b-confirmatory-pilots/` (`run_all.sh` reproduces them).

???+ abstract "Concepts behind this case study"
    [Monte Carlo size and power](../concepts/inference.md#monte-carlo-size-and-power) ·
    [Andrews–Kim](../concepts/time-series.md#andrewskim-end-of-sample-cointegration-breakdown-test) ·
    [Wagner–Wied](../concepts/time-series.md#wagnerwied-cointegration-monitoring) ·
    [cointegration](../concepts/time-series.md#cointegration-and-error-correction) ·
    [specification search](../concepts/methodology.md#specification-search-and-the-garden-of-forking-paths) ·
    [confirmatory vs exploratory](../concepts/methodology.md#confirmatory-vs-exploratory-analysis) ·
    [testing code on synthetic data](../concepts/methodology.md#testing-econometric-code-on-synthetic-data).
    Textbook: [ch. 4 §10](../textbook/hypothesis-testing-uncertainty.md#10-does-the-test-do-what-it-says-monte-carlo-size-and-power).

## 1. The original hypothesis

ADR 0008 §2 records the intended claim: *the long-run levels relation among \(s\)
(log USD/JPY), \(x\) (log relative CPI) and \(d\) (the 2Y yield gap) held over
1981–2021 (T = 492 months) and did not hold over 2022-01 to 2026-07 (m = 55 months).*

The plan had two steps:

1. **Gate.** An ARDL bounds test (Pesaran–Shin–Smith, Case III) must first find a
   pre-2022 levels relation; otherwise there is nothing to break.
2. **Breakdown test.** One end-of-sample test at α = 0.025.

**What we expected.** *Reconstruction:* the drafts treat the gate and the end-of-sample
test as standard tools with published theory, so the work was expected to be
implementation, not method selection. The eligibility rules (ADR 0008 §3) were written to
check that assumption, and they are what caught the problems.

## 2. Four rules a test had to pass

Fixed in revisions 2–3, before any candidate was simulated:

| Rule | Requirement |
|---|---|
| Theory | Covers drifting relative prices and a rate gap of uncertain integration order |
| Size | Simulated full-procedure rejection rate at nominal 2.5 % close to 2.5 % at T = 492, m = 55 |
| Tuning | All tuning fixed in advance |
| Verifiability | Published equations and critical values reproduced |

The size screen used a 1.5α = 3.75 % tolerance with Clopper–Pearson intervals, as a
project convention. Neither rejection depended on that tolerance.

## 3. Andrews–Kim: verified, then infeasible

**Verification first.** The P test was transcribed from the paper (JBES 24(4)) and
reproduced its Table 1 within Monte Carlo error — for example 0.0554 against the paper's
0.057 at ρ = 0. The fast implementation matched a direct loop to 10⁻¹⁴.

**Then the failure.** At our dimensions, 4,000 replications per cell:

- null rejection at nominal 2.5 % was **4.7–10.7 %** in every main cell — across error
  persistence, normal and GARCH errors, with and without the missing month;
- even an oracle that knew the true coefficients distorted (6.5 %).

**Why.** The test's p-value comes from comparing the end-sample statistic with 438
overlapping pre-sample windows. Those windows carry only about T/m ≈ 9 independent pieces
of information. The paper's theory holds m fixed and its evidence used m ≤ 10; our m/T is
0.11.

**The decisive point.** The smallest p-value the test can produce is 1/438, and under
the null that p-value already occurred 3.5–8.7 % of the time. **No critical value, nominal
or corrected, can give a 2.5 % test.** This is structural, not a tuning problem.

## 4. Wagner–Wied: three independent problems

1. **A source discrepancy.** Only the working-paper and R-package form of the monitoring
   detector reproduced the published critical values; the journal's equation (12) did not.
   The supplementary appendix was unavailable, so the discrepancy is documented, not
   resolved.
2. **Theory that does not cover the design — decisive on its own.** The method assumes
   every regressor is a *driftless* random walk. Relative prices drift, and the rate gap may
   be stationary. Simulation can measure the damage but cannot restore the theory.
3. **Size and power.** Size swung with the bandwidth rule (fixed Newey–West bandwidth: up
   to 90 %), and with the best rule power against 1–2 σ breaks at realistic persistence was
   2–8 %.

<div class="chart-frame" markdown>
<p class="chart-title">Simulated null rejection rates at nominal 2.5 %</p>
<p class="chart-sub">Each bar spans the range across simulation cells. A valid test sits near
the solid line; the dashed line is the project's 3.75 % screen.</p>
<div class="kchart short" data-chart="size-ranges"></div>
<p class="chart-source">Synthetic data, not USD/JPY. Values from ADR 0008 §4 (Andrews–Kim, 4,000 replications per cell)
and §5.3 (Wagner–Wied, 2,000 per cell). Log scale.</p>
</div>

| Wagner–Wied power (FM-OLS, Andrews bandwidth, size-corrected) | Error persistence ρ | Power |
|---|---|---|
| 1–2 σ level or slope shift, loss of cointegration, variance × 2 | 0.95–0.98 | 0.02–0.08 |
| 4 σ shift | 0.95–0.98 | 0.38–0.45 |
| 6 σ shift | 0.95–0.98 | 0.75–0.88 |
| 4 σ shift | 0.8 | 0.92 |

## 5. Deciding to stop

Revision 4 had screened other candidates (Kejriwal–Perron, sieve bootstraps); none could
be verified to the fourth rule. The binding constraints came from the design itself — a
55-month window against 492 months, persistent equilibrium errors, an uncertain
integration order for \(d\), drifting prices and a 2.5 % budget.

**Decision (ADR 0008 §0, approved 2026-10-23):**

- H1b's confirmatory claim is **not assessable** with the methods evaluated;
- its α = 0.025 is **unused** and not reallocated to anything;
- the method search **ends** — continuing would be a specification search over tests;
- H1b continues as **explicitly exploratory** work.

!!! warning "What the decision does not say"
    It does not say "no decoupling", "decoupling", or that USD/JPY residuals are "too
    persistent to test": no test ran on real data, and the persistence values were design
    points, not estimates (ADR 0008 §7).

## 6. Exploratory Stage 1 and the audit

With no confirmatory claim at stake, Stage 1 asked a descriptive question: *does the
pre-2022 data identify a long-run relation good enough to give a model-implied benchmark?*

- **Integration.** Over 1981–2021 every series is I(1), with no I(2) risk, so the
  ARDL, FM-OLS and D-OLS estimators all apply.
- **Bounds tests.** Four specifications; no F or t statistic crosses an I(1) bound.
- **Estimators disagree.** ARDL gives a relative-price coefficient at or below zero;
  FM-OLS and D-OLS give about 0.8 with a near-zero rate effect.
- **Instability.** Adjustment speed and long-run coefficients swing across eras.
- **Verdict:** all four **not defensible**; no benchmark is computed
  ([notebook 03](https://github.com/akiblasco/kagura/blob/main/notebooks/03_h1b_exploratory.ipynb)).

**The audit.** A review then found that Stage 1 had simplified the ARDL design proposed
in the superseded drafts: no seasonal dummies, no tax impulses, and one shared lag order.
The design was re-run as a labelled sensitivity analysis (notebook 04, `ca8ebd3`):

- F fell for three specifications and **rose for one** (1.88 → 2.05), still inside its
  I(0) bound; every |t| fell; no classification changed.
- A first draft of the audit called the variant "protocol-aligned" and said every F
  declined. Both were corrected before committing: the variant is a *sensitivity analysis
  based on the earlier proposed design*, and frozen ADR 0008 requires only Case III with
  BG-filtered AIC lags up to 12, which both versions satisfy.

## 7. Problems found along the way

| Problem | Where | How it was handled |
|---|---|---|
| Andrews–Kim size 2–4× nominal; 2.5 % unattainable | r4 pilots | Rejected (ADR 0008 §4) |
| Wagner–Wied published equation ≠ critical values | r4b | Documented, not adjudicated (§5.1) |
| Wagner–Wied theory excludes drift and stationary d | r4b | Rejected regardless of simulation (§5.2) |
| r4 cited "Table 10" for values from Table 11 | r4 | Corrected in ADR 0008 §5.1 |
| q = s − x could be I(2) even if s and x are I(1) | r5 review | §9.3: each transformed series classified separately |
| Stage 1 simplified the draft design | audit | Sensitivity re-run; deviations disclosed |
| Half-life bootstrap rebuilds data from a stable model, so cannot represent a unit root | audit | Intervals not used as evidence |
| Audit wording overstated ("every F declined", "protocol-aligned") | review | Corrected before commit |

## 8. What we learned

1. **Verify against the paper before trusting it, then test it at *your* dimensions.**
   Both methods reproduced their published tables and still failed at T = 492, m = 55.
2. **Some failures are structural.** No amount of tuning makes 1/438 smaller than 2.5 %.
   Recognising that ended the search cleanly.
3. **Theory coverage is a hard gate.** Wagner–Wied's assumptions excluded our data; good
   simulated size elsewhere would not have fixed that.
4. **Stopping is a result.** Searching test after test until one "works" is a
   specification search. Declaring "not assessable" kept the H1 family error rate honest:
   at most 0.025 spent, within the 0.05 budget.
5. **Exploratory work needs the same discipline.** Labels, disclosed deviations and an
   audit caught both a simplified specification and overstated wording.

## 9. Still open

- Breaks (Stage 2) may reveal sub-period relations that a full-sample test averages away.
- Bounds tests have low power with persistent deviations; "not defensible" ≠ "no relation".
- Simulated critical values assume driftless Gaussian random walks.

## Sources

| Record | Link |
|---|---|
| Frozen protocol | [ADR 0008](../../decisions/0008-h1b-long-run-protocol.md) (`a37f5d6`) |
| Superseded drafts r2–r5 | [`docs/decisions/superseded/0008/`](../../decisions/superseded/0008/README.md) |
| Pilot archive | `research/methodology/adr0008-h1b-confirmatory-pilots/` |
| Stage 1 | `notebooks/03_h1b_exploratory.ipynb` (`8fba5b6`) |
| Audit | `notebooks/04_h1b_stage1_audit.ipynb` (`ca8ebd3`) |
| Results summary | [H1b report](../reports/02-h1b-long-run-fundamentals.md) |
