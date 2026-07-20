.PHONY: install dev test lint format typecheck check gdc-plan-dry-run plan-validate study-validate program-validate question-template-validate research-foundation-check storage-init storage-check services-up services-down

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
	uv run nas-core plan validate workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml

study-validate:
	uv run nas-core study validate workflows/studies/tcga_brca_stage_survival

gdc-plan-dry-run:
	uv run nas-core ingest gdc-plan workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml

program-validate:
	uv run nas-core program validate workflows/oncology/program_charter.yaml

question-template-validate:
	uv run nas-core question validate workflows/templates/research_question_intake.yaml

research-foundation-check: program-validate question-template-validate

storage-init:
	uv run nas-core storage init

storage-check:
	uv run nas-core storage check

services-up:
	docker compose up -d postgres minio-init

services-down:
	docker compose down
