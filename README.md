# NaS Core

NaS Core is the private research and evidence platform behind the NaS Cortex.
It is being built to turn approved biomedical data and literature into
reproducible analyses, structured evidence, and traceable research releases.

The project is currently at its infrastructure-foundation stage. It does not
provide clinical advice and must not be used with protected health information
or controlled-access data until the relevant governance controls are approved.

## Local requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker with Compose (for PostgreSQL and object storage)

## Quick start

```bash
cp .env.example .env
uv sync
docker compose up -d postgres minio
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

## Repository boundaries

Git contains source code, schemas, workflow definitions, prompts, tests, small
synthetic fixtures, and permitted dataset manifests. Raw datasets, credentials,
embeddings, generated artifacts, database dumps, PHI, and controlled-access
data never belong in Git.

See [docs/architecture.md](docs/architecture.md) for the initial system shape.
