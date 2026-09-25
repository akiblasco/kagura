.PHONY: sync data test lint

sync:
	uv sync

data:
	uv run python -m kagura.data

test:
	uv run pytest -q

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
