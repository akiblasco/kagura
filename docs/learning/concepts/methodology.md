# Research methodology concepts

<p class="lead">The rules that decide what KAGURA is allowed to claim: what counts as
confirmatory, how decisions are frozen, how results are worded, and how the code that produces
them is checked.</p>

Status labels:
<span class="status implemented">Implemented</span>
<span class="status exploratory">Exploratory</span>
<span class="status rejected">Rejected</span>
<span class="status planned">Planned</span>
<span class="status background">Background</span>.
See the [concept index](../INDEX.md#concept-index).

---

## Confirmatory vs exploratory analysis {#confirmatory-vs-exploratory-analysis}

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · ADR 0004, ADR 0006, ADR 0008 §7</p>

**Plain English.** A *confirmatory* analysis tests a claim fixed before the data were analysed, with a
controlled error rate. An *exploratory* analysis looks at data to describe them and generate ideas;
its p-values carry no error-rate guarantee.

**Why it exists.** If the analysis is chosen after seeing data, a "5 % test" rejects far more than 5 %
of the time. Separating the two keeps confirmatory claims honest without forbidding exploration.

**Definition.**

| | Confirmatory | Exploratory |
|---|---|---|
| Specification | frozen in an ADR before data contact | may adapt to what is seen |
| Error budget | α from the H1 family (0.025 each) | none; 5 % is a descriptive reference |
| Allowed language | "supported", "ruled out", "inconclusive" | numbers, associations, "consistent with" |
| Can it confirm H1? | yes | **never** (ADR 0008 §7.1) |

**How KAGURA used it.** ADR 0004 (exploration) was frozen before plots were made; ADR 0006 (H1a) was
frozen before any regression; H1b Stage 1 and the audit are labelled "exploratory (ADR 0008 §9)".

**What we found / decided.** H1a is the only confirmatory result (inconclusive). Everything in H1b is
exploratory; nothing there "can be promoted to confirmatory by meeting a stricter level".

**Assumptions and limits.** Prior knowledge cannot be removed, only disclosed (ADR 0006 §1.1, ADR 0008 §1).

**Common mistake.** Quoting an exploratory p < 0.05 as "significant evidence for H1".

**Go deeper.** [Overview §4](../reports/00-research-overview.md#4-how-kagura-guards-its-conclusions) ·
[KAGURA results cheatsheet](../cheatsheets/kagura-results.md) ·
[ADR 0008 §7](../../decisions/0008-h1b-long-run-protocol.md)

---

## ADRs and freezing decisions before results

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · `docs/decisions/`</p>

**Plain English.** An Architecture Decision Record (ADR) is a short dated document recording the
context, options, decision, rationale and risks of one consequential choice. *Freezing* means
committing and pushing it before the analysis runs; changing it afterwards needs a new ADR.

**Why it exists.** It makes the order of events verifiable: anyone can check from Git that the test
predates its result.

**Definition.** Sections: context · options considered · decision · rationale · risks/limitations · date.

**How KAGURA used it.** ADRs 0001–0006 and 0008 cover sample, sources, alignment, the exploratory spec,
the carried-share guard, the H1a protocol and the H1b protocol. Superseded drafts of ADR 0008 are kept
in `docs/decisions/superseded/0008/` as "history, not authority".

**What we found / decided.** ADR 0008 freeze commit `a37f5d6`; Stage 1 `8fba5b6`; audit `ca8ebd3`.
ADR 0004 notes it had no Git timestamp at writing (Git was blocked on the machine), a limit it states
openly.

**Assumptions and limits.** Freezing fixes procedure, not wisdom: a frozen bad choice stays frozen and
is reported, as with ADR 0008's departure from ADR 0006's expectation of an H1b primary test.

**Common mistake.** Editing a frozen ADR to match what was done. The audit instead re-ran the
superseded drafts' design as a labelled sensitivity analysis.

**Go deeper.** [ADR 0006](../../decisions/0006-h1-formal-testing-protocol.md) ·
[ADR 0008](../../decisions/0008-h1b-long-run-protocol.md) · [Case study](../journal/h1b-methodological-journey.md)

---

## Association vs causation language {#association-vs-causation}

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · ADR 0006 §3; CLAUDE.md principle 6</p>

**Plain English.** A regression slope says two things move together, not that one moves the other.
KAGURA writes "is associated with", never "drives", "raises" or "causes".

**Why it exists.** Rates and the yen respond to common news and possibly to each other. Nothing in
KAGURA's designs isolates causal variation.

**Definition.** Causal claims need identification (an experiment, an instrument, a credible
event-study design). KAGURA's slopes are linear projections: \(\operatorname{Cov}/\operatorname{Var}\).

**How KAGURA used it.** In every report, caption and summary; ADR 0008 §7.2 extends it to banning
"fair value", "misalignment" and "over/undervalued".

**What we found / decided.** "A 1 pp wider 2Y differential is associated with a 4.05 % higher USD/JPY
(2022–)." Event matching in the Stage 2 plan uses "coincides with".

**Assumptions and limits.** Language cannot fix design, but it stops readers inferring more than the
design supports.

**Common mistake.** "The BOJ's YCC exit weakened the rate link." Dates coinciding are not a mechanism.

**Go deeper.** [Chapter 2 §8](../textbook/regression-coefficients.md#8-association-not-causation)

---

## Specification search and the garden of forking paths

<p class="concept-meta"><span class="status implemented">Implemented</span> (as a rule) Level I · ADR 0008 §6</p>

**Plain English.** Trying many tests, samples or models until one gives the hoped-for answer, even
without intending to, makes the final p-value meaningless.

**Why it exists.** Each extra choice is another chance for noise to look like signal.

**Definition.** With \(K\) roughly independent tries at level α, P(at least one rejection under the null)
= \(1 - (1-\alpha)^K\): 22 % for K = 10 at 2.5 %.

**How KAGURA used it.** The search for a confirmatory H1b method was **closed** after two candidates
failed, because "further searching would amount to a specification search over tests" (ADR 0008 §6).
Robustness variants were fixed in advance and can qualify, never replace, the primary result.

**What we found / decided.** H1b's α left unspent rather than searching for a test that "works".

**Assumptions and limits.** Closing the search may miss a valid method; that cost is accepted and stated.

**Common mistake.** Reporting only the variant that "worked".

**Go deeper.** [Case study](../journal/h1b-methodological-journey.md) ·
[ADR 0008 §6](../../decisions/0008-h1b-long-run-protocol.md)

---

## Reporting negative and inconclusive results

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · H1a, H1b; CLAUDE.md principle 8</p>

**Plain English.** Publish what the test said even when it is "we cannot tell" or "the method doesn't
work here", with the same prominence as a positive finding.

**Why it exists.** Suppressing null results biases the literature, and in a project, it biases the next
decision.

**Definition.** Pre-defined categories (supported, ruled out, inconclusive, not assessable) and an
explicit "established / not established" table in every report.

**How KAGURA used it.** H1a inconclusive; H1b not assessable; Stage 1 "no defensible benchmark"; the
audit reported that (b)'s F *rose* (1.88 → 2.05), against the direction of the other three.

**What we found / decided.** ADR 0008 §7 lists what may and may not be said, e.g. "not assessable" ≠ "no
decoupling" ≠ "decoupling".

**Assumptions and limits.** "Inconclusive" invites over-reading in both directions; the reports pair it
with what *was* established (e.g. a decline of half or more is ruled out in sensitivity).

**Common mistake.** "No significant change, so the relationship is stable."

**Go deeper.** [H1a report §6](../reports/01-h1a-short-run-comovement.md#6-what-this-does-and-does-not-establish) ·
[H1b report §5](../reports/02-h1b-long-run-fundamentals.md#5-what-this-does-and-does-not-establish)

---

## Reproducible pipelines: uv, make, nbconvert, pytest

<p class="concept-meta"><span class="status implemented">Implemented</span> Level B · `Makefile`</p>

**Plain English.** Every result can be regenerated from raw files with one command, in a pinned
environment, and the run stops if inputs differ from the frozen ones.

**Why it exists.** Manual spreadsheet steps and unpinned libraries make results impossible to check.

**Definition.** KAGURA's chain:

| Command | Does |
|---|---|
| `make sync` | install the locked environment (`uv sync`, `uv.lock`) |
| `make data` | download and align (refuses to overwrite the frozen vintage) |
| `make test` | pytest suite, including the carried-share guard |
| `make lint` | ruff and mypy |
| `make h1a` / `make h1b-explore` | verify checksums, execute the notebook (nbconvert) |
| `make docs-build` | build this site |

**How KAGURA used it.** Notebook 02 records its environment (Python 3.12.8, pandas 3.0.5, numpy 2.5.3,
statsmodels 0.15.0) and HEAD commit. Stage 1 simulations use fixed seeds.

**What we found / decided.** The H1a notebook recorded HEAD `dd8d04f` with a modified working tree at
run time; the result commit is `2c5b446`. This is disclosed in the report's provenance table.

**Assumptions and limits.** Raw data are not redistributed, so reproduction needs the same downloads.

**Common mistake.** Re-running a notebook cell by cell out of order and committing the outputs.

**Go deeper.** [Overview report](../reports/00-research-overview.md) ·
[Makefile](https://github.com/akiblasco/kagura/blob/main/Makefile)

---

## Testing econometric code on synthetic data

<p class="concept-meta"><span class="status implemented">Implemented</span> Level I · `tests/`; ADR 0008 §9.7</p>

**Plain English.** Before trusting a function on real data, feed it artificial data where you know the
right answer, and check it recovers that answer, matches a hand calculation or a reference library,
and handles edge cases.

**Why it exists.** Econometric code fails silently: a wrong sign or lag still returns a number.

**Definition.** Three kinds of checks: **recovery** (known parameters recovered), **agreement** (equals a
manual formula or statsmodels to numerical precision), **invariants** (S and R never both reject;
a bound of exactly 0 is not a rejection).

**How KAGURA used it.** 49 tests in `tests/test_models.py` and 10 in `tests/test_longrun.py`, among others.
Examples: "coefficients match separate era OLS and R² is squared correlation"; "HAC covariance matches
manual Newey–West"; "Fieller set matches brute force"; "era equality matches statsmodels Wald test".
In the pilots, Andrews–Kim reproduced its paper's Table 1, and the WW detector matched a direct loop to 4e-17.

**What we found / decided.** Validation came first in both rejected H1b methods. Andrews–Kim was
rejected *after* it was shown to be implemented correctly, so the failure is the method's, not a bug's.

**Assumptions and limits.** Tests show code does what the spec says, not that the spec is right.

**Common mistake.** Testing only that code runs.

**Go deeper.** [`tests/test_models.py`](https://github.com/akiblasco/kagura/blob/main/tests/test_models.py) ·
[`tests/test_longrun.py`](https://github.com/akiblasco/kagura/blob/main/tests/test_longrun.py)
