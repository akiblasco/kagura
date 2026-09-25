.PHONY: sync data test lint research

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
