# NaS Core Project Status

Last updated: 2026-07-20

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Define the first TCGA-BRCA pilot and preregister its analysis plan

Select one established, reproducible breast-cancer result that can be tested
using public/open TCGA-BRCA data. Write the protocol before inspecting final
study results.

Definition of done:

- The research question and falsifiable hypothesis are explicit.
- The cohort, inclusion criteria, exclusions, exposure or biomarker, endpoint,
  and relevant subgroups are defined.
- Covariates and the primary statistical model are specified.
- Sensitivity analyses and missing-data handling are specified.
- Multiple-testing and significance rules are specified.
- Exploratory and confirmatory analyses are clearly separated.
- The required GDC data types are confirmed as public/open and covered by the
  active source registration.
- `workflows/tcga_brca_pilot/analysis_plan.yaml` passes schema validation.
- Scientific and governance limitations are recorded.

## Next implementation queue

1. Implement dataset snapshots and GDC ingestion that record the exact query,
   GDC release, manifest, file IDs, timestamps, classifications, and checksums.
2. Implement the deterministic TCGA-BRCA cohort and analysis pipeline with
   captured code version, environment, parameters, random seeds, warnings,
   tables, figures, effect sizes, and uncertainty.
3. Implement persisted evidence claims, citations, provenance, contradictory
   evidence, null findings, limitations, and review state.
4. Add permitted literature metadata and passage ingestion with hybrid keyword
   and semantic retrieval.
5. Add the replaceable model gateway with structured outputs, minimum-necessary
   context, citations, uncertainty, abstention, and governance enforcement.
6. Build evaluation suites for retrieval, citation validity, numerical
   fidelity, unsupported claims, and appropriate abstention.
7. Generate an immutable research release containing the protocol, dataset
   manifest, code revision, environment, results, figures, literature,
   limitations, approvals, and disclosures.
8. Generate a reviewable white-paper draft whose substantive claims trace to
   executed artifacts, external sources, or labeled interpretation.
9. Build the internal workbench for projects, protocols, datasets, runs,
   evidence review, and publication releases.
10. Complete repeated internal oncology pilots before selecting the first
    external commercial product surface.

## Recently completed

### 2026-07-20 — External-drive storage foundation and engine plan

Defined the phased research-engine plan, added a configurable `NAS_DATA_ROOT`,
implemented safe storage initialization and validation commands, wired MinIO to
external object storage, and added automated layout tests. The Seagate data root
is `/Volumes/AGNDJ 6TB/NaS-Core-Data`.

Validation: the physical data root initialized and validated successfully;
Ruff, strict MyPy, and 32 tests passed.

### 2026-07-20 — Cortex v0 data governance

Implemented source classifications, approval lifecycle, deny-by-default policy
enforcement, purpose and role authorization, review dates, AI and export
restrictions, an open GDC source registration, policy documents, and tests.

Validation: Ruff passed, strict MyPy passed, and 26 tests passed.

### 2026-07-20 — Initial infrastructure scaffold

Implemented the Python package, FastAPI health endpoints, configuration,
PostgreSQL readiness, S3-compatible object storage, Docker Compose, CI,
documentation boundaries, and baseline tests.

Validation: Ruff passed, strict MyPy passed, and 4 tests passed.

## Current blockers

- Docker is not currently available in the development environment, so the
  Compose services have been syntax-validated but not started locally.
- The precise TCGA-BRCA pilot question and scientific reviewer have not yet
  been selected.
- The Seagate volume currently reports approximately 4.2 TiB available. It is
  primary local storage, not an independent backup.

## Durable decisions and boundaries

- `nas-website` and `NaS-Core` remain separate repositories.
- NaS Core begins as a modular monolith.
- OpenAI is a replaceable reasoning provider, not the NaS product or knowledge
  store.
- Numerical research results come from deterministic executed code.
- Public/open and explicitly approved licensed data are the only v0 data
  classes; controlled data and PHI remain prohibited.
- Raw datasets, credentials, embeddings, and generated research artifacts do
  not belong in Git.
- Public/open v0 data and research artifacts use the configurable external
  `NAS_DATA_ROOT`; storage layout integrity is marker-validated before use.

## Update procedure

For every completed implementation:

1. Verify the implementation against its definition of done.
2. Move the completed current focus into **Recently completed**.
3. Keep the five most recent completion entries and remove older ones.
4. Promote the first unfinished queue item into **Current focus**.
5. Rewrite its definition of done so it is objectively testable.
6. Add newly discovered future work in dependency order.
7. Update blockers and durable decisions.
8. Update the date and commit the status change with the implementation.
