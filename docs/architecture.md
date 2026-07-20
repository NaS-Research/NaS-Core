# Initial Architecture

NaS Core begins as a modular monolith with one Python package and explicit
internal boundaries for ingestion, analysis, evidence, retrieval, AI,
publication, security, audit, and storage.

## Initial services

- FastAPI exposes system and future research APIs.
- PostgreSQL stores metadata, provenance, evidence, and audit records.
- An S3-compatible object store holds datasets and generated artifacts outside
  Git.
- Background execution will be added when the first ingestion and analysis
  workflow is implemented.

## Architectural rules

1. Model providers remain replaceable behind an internal gateway.
2. Numerical results originate from deterministic analysis code.
3. Research inputs and outputs are versioned and traceable.
4. Data-source and storage integrations use explicit interfaces.
5. Service extraction requires a demonstrated operational or security need.

See [decisions/0001-modular-monolith.md](decisions/0001-modular-monolith.md).
