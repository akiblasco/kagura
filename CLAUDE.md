# Project KAGURA

KAGURA is an academic-quality quantitative research project studying the Japanese yen, USD/JPY, Japanese monetary policy, FX intervention, market regimes, and Japanese macroeconomic outcomes.

This project-level file supplements the user's global CLAUDE.md. Do not override global workflow preferences unless this file explicitly requires a research-specific constraint.

## Source of truth

Before substantial work, read:

- `docs/RESEARCH_SPEC.md`
- `docs/ROADMAP.md`
- `docs/HYPOTHESES.md`

Important research and methodological decisions should be recorded in:

- `docs/decisions/`

## Current research question

Has USD/JPY structurally decoupled from the US-Japan interest-rate differential, and if so, when and by how much?

## Current milestone

KAGURA v0.1 — research and data foundation.

Focus on:

- reproducible project architecture
- trustworthy data ingestion
- USD/JPY
- US/Japan policy rates and government yields
- core macro controls
- correct observation/release-date handling
- exploratory visualizations
- rolling relationships
- baseline econometric models
- structural-break analysis
- Yen Fundamental Gap
- tests and documentation

Do not build deep learning, LLM pipelines, the public dashboard, trading systems, or policy optimization yet.

## Research principles

1. Economics before machine learning.
2. Simple statistical baselines before complex models.
3. Preserve temporal ordering. Never randomly shuffle time-series observations for model evaluation.
4. Prevent look-ahead bias and data leakage.
5. Distinguish observation date, release date, and vintage date whenever relevant.
6. Do not describe correlation as causation.
7. Do not introduce complexity unless it answers a specific research question.
8. Report negative or inconclusive results rather than optimizing the analysis for an exciting conclusion.
9. Quantify uncertainty whenever reasonably possible.
10. Keep exploratory work separate from reusable research code.

## Working with the user

The user wants to understand and build the project, not merely delegate it.

For every substantial milestone:

1. Explain what we are about to build.
2. Explain why it matters economically/statistically.
3. Identify important assumptions.
4. Identify likely failure modes or data-quality problems.
5. Propose the implementation plan.
6. Wait for the user's instruction to implement when the user has explicitly requested a review-first workflow.
7. After implementation, explain the important code paths and how the user can inspect/run them.

When introducing an unfamiliar statistical, econometric, ML, finance, or software concept, explain it clearly rather than assuming familiarity.

Do not silently make economically consequential assumptions.

## Engineering expectations

Prefer modern Python and a small dependency surface.

Likely tools:

- `uv`
- `pandas` and/or `polars`
- `numpy`
- `scipy`
- `statsmodels`
- `scikit-learn`
- `pydantic`
- `matplotlib`
- `plotly` when interactivity is useful
- `pytest`
- `ruff`
- `mypy`
- `pre-commit`

Do not introduce a new framework merely because it is fashionable.

## Research decision log

Create an ADR-style markdown file under `docs/decisions/` for consequential decisions such as:

- data frequency
- sample period
- yield maturities
- interpolation/filling rules
- release-date treatment
- transformation choices
- model specification
- structural-break methodology
- regime interpretation
- forecast-validation protocol

Each decision should record:

- context
- options considered
- decision
- rationale
- risks/limitations
- date

## Reproducibility

Important empirical results should be reproducible from code.

Avoid manual spreadsheet transformations that cannot be reproduced.

Do not commit proprietary data or secrets.

Prefer commands such as:

```bash
make data
make test
make research
```

or equivalent documented `uv run ...` commands.

## Before substantial implementation

Inspect the repository and referenced research documents, then state:

- what you found
- what you propose to change
- assumptions
- data/econometric risks
- how the user will verify the result
