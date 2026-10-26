.PHONY: sync data test lint research h1a h1b-explore docs-figures docs-build docs-serve

sync:
	uv sync

data:
	uv run python -m kagura.data
	uv run python -m kagura.align

test:
	uv run pytest -q

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

research:
	uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_exploration.ipynb

# H1a formal test (ADR 0006). Verifies the frozen data checksums first and stops on any
# error; executes notebooks/02_h1a_formal.ipynb in place and writes reports/figures/h1a_*.
h1a:
	uv run jupyter nbconvert --to notebook --execute --inplace notebooks/02_h1a_formal.ipynb

# H1b exploratory Stage 1 (ADR 0008 §9.1-§9.4). Verifies the frozen data checksums first;
# executes notebooks/03_h1b_exploratory.ipynb in place and writes reports/figures/h1b_*.
h1b-explore:
	uv run jupyter nbconvert --to notebook --execute --inplace notebooks/03_h1b_exploratory.ipynb

# Learning companion site (MkDocs Material, local only). Figures are read from committed
# notebook outputs; site/ is generated and gitignored.
docs-figures:
	uv run python docs/learning/reports/make_figures.py

docs-build: docs-figures
	uv run --group docs mkdocs build --strict

docs-serve: docs-figures
	uv run --group docs mkdocs serve --dev-addr 127.0.0.1:8000
