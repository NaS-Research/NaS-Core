.PHONY: install dev test lint format typecheck check plan-validate storage-init storage-check services-up services-down

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

plan-validate:
	uv run nas-core plan validate workflows/tcga_brca_stage_survival/analysis_plan.yaml

storage-init:
	uv run nas-core storage init

storage-check:
	uv run nas-core storage check

services-up:
	docker compose up -d postgres minio-init

services-down:
	docker compose down
