# Project KAGURA

Quantitative research on the Japanese yen, USD/JPY, and Japanese monetary policy.

Current question (v0.1): has USD/JPY structurally decoupled from the US-Japan
interest-rate differential, and if so, when and by how much?

## Layout

```text
src/kagura/       reusable research code (the installable package)
tests/            data-quality and unit tests
notebooks/        exploratory work; nothing here is a source of truth
data/raw/         downloaded source files, gitignored
data/processed/   derived datasets, gitignored
reports/figures/  generated figures
docs/             research spec, roadmap, hypotheses, decision records
```

## Commands

```bash
make sync      # create the environment
make test      # run tests
make lint      # ruff + mypy
```

Research documents: `docs/RESEARCH_SPEC.md`, `docs/ROADMAP.md`, `docs/HYPOTHESES.md`.
Decisions: `docs/decisions/`.
