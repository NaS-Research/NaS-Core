# NaS Core Agent Guidance

## Purpose

NaS Core is a precision-medicine research and evidence platform. Preserve
traceability, reproducibility, data minimization, and scientific uncertainty in
every implementation decision.

## Required checks

Run `make check` before handing off code changes.

## Data safety

- Never commit credentials, PHI, PII, controlled-access data, raw biomedical
  datasets, database dumps, embeddings, or generated research artifacts.
- Use only synthetic fixtures in tests.
- Treat model output as unverified until it is linked to evidence and reviewed.
- Numerical research results must originate from executed deterministic code,
  not from a language model.

## Architecture

- Keep the system a modular monolith until demonstrated scaling or security
  boundaries justify service extraction.
- Keep model providers behind the NaS-owned gateway.
- Keep storage and data-source integrations behind explicit interfaces.
- Make research inputs, code versions, parameters, outputs, and provenance
  immutable or versioned.
