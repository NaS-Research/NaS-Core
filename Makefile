.PHONY: install dev test lint format typecheck check services-up services-down

install:
	uv sync

dev:
	uv run uvicorn nas_core.api.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy

check: lint typecheck test

services-up:
	docker compose up -d postgres minio

services-down:
	docker compose down
