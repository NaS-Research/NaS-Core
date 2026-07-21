# NaS Core Agent Guidance

## Purpose

NaS Core is a precision-medicine research and evidence platform. Preserve
traceability, reproducibility, data minimization, and scientific uncertainty in
every implementation decision.

## Required checks

Run `make check` before handing off code changes.

## Living project status

- Read `PROJECT_STATUS.md` before starting material implementation work.
- Update `PROJECT_STATUS.md` as part of every completed implementation.
- When the current focus is finished, move it to **Recently completed**, promote
  the next ordered item to **Current focus**, and add or refine future steps.
- Keep only the five most recent completed items; Git history preserves older
  detail.
- Do not mark work complete until its stated validation passes.
- Record blockers and consequential architecture or governance decisions.

## Data safety

- Never commit credentials, PHI, PII, controlled-access data, raw biomedical
  datasets, database dumps, embeddings, or generated research artifacts.
- Use only synthetic fixtures in tests.
- Treat model output as unverified until it is linked to evidence and reviewed.
- Numerical research results must originate from executed deterministic code,
  not from a language model.
- NaS is currently a founder-led one-person organization. Do not invent staff,
  committees, collaborators, independent review, or peer-review status.
- AI-assisted review is advisory and cannot authorize a scientific gate.
- Founder self-review is permitted only when typed and publicly disclosed as
  internal self-review; external expert feedback and journal peer review remain
  separate provenance states.

## Architecture

- Keep the system a modular monolith until demonstrated scaling or security
  boundaries justify service extraction.
- Keep model providers behind the NaS-owned gateway.
- Keep storage and data-source integrations behind explicit interfaces.
- Make research inputs, code versions, parameters, outputs, and provenance
  immutable or versioned.
