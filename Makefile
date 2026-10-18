.PHONY: sync data test lint research h1a

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
