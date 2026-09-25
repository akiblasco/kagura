.PHONY: sync data test lint

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
