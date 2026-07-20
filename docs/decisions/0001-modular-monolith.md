# ADR 0001: Begin as a modular monolith

- Status: Accepted
- Date: 2026-07-20

## Decision

NaS Core will begin as a single versioned Python application with explicit
module boundaries and separate PostgreSQL and object-storage services.

## Rationale

The initial risk is scientific validity and workflow design, not distributed
system scale. A modular monolith keeps deployment and testing understandable
while preserving boundaries that can later become services when justified.

## Consequences

- Modules must communicate through explicit domain contracts.
- Background jobs may run as a separate process from the same codebase.
- New databases, queues, graph stores, and services require an architecture
  decision record and demonstrated need.
