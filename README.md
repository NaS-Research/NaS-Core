# NaS Core

NaS Core is the private research and evidence platform behind the NaS Cortex.
It is being built to turn approved biomedical data and literature into
reproducible analyses, structured evidence, and traceable research releases.

The project has its infrastructure and governance foundations and is now
preparing its first governed TCGA-BRCA reproduction study. It does not provide
clinical advice and must not be used with protected health information or
controlled-access data until the relevant governance controls are approved.

## Local requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker with Compose (for PostgreSQL and object storage)

## Quick start

```bash
cp .env.example .env
uv sync
uv run nas-core storage init
docker compose up -d postgres minio-init
uv run uvicorn nas_core.api.main:app --reload
```

The API will be available at `http://localhost:8000`.

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Development checks

```bash
make check
```

## First study protocol

The first pilot plan is
[`workflows/tcga_brca_stage_survival/analysis_plan.yaml`](workflows/tcga_brca_stage_survival/analysis_plan.yaml).
It remains pending scientific review. Validate its structure and data-governance
permissions without downloading study data:

```bash
make plan-validate
```

## Repository boundaries

Git contains source code, schemas, workflow definitions, prompts, tests, small
synthetic fixtures, and permitted dataset manifests. Raw datasets, credentials,
embeddings, generated artifacts, database dumps, PHI, and controlled-access
data never belong in Git.

See [docs/architecture.md](docs/architecture.md) for the initial system shape.

## Project direction

The continuously updated implementation status and next-step queue live in
[PROJECT_STATUS.md](PROJECT_STATUS.md). Read it before beginning material work
and update it whenever an implementation is completed.

The complete phased build plan lives in
[docs/research-engine-plan.md](docs/research-engine-plan.md).
