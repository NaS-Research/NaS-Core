# NaS Core Project Status

Last updated: 2026-07-20

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Scientifically review and lock the first TCGA-BRCA analysis plan

Review `NAS-BRCA-001`, which tests the established association between advanced
pathologic stage and poorer overall survival using public/open TCGA-BRCA
clinical data. Resolve review comments and lock the protocol before downloading
the study dataset or inspecting final outcomes.

Definition of done:

- An independent scientific reviewer is named in the plan.
- The reviewer evaluates the question, cohort rules, diagnosis-record
  precedence, endpoint derivation, covariates, statistical model, missing-data
  plan, multiplicity rules, sensitivity analyses, and limitations.
- Every requested change is resolved in Git with a traceable protocol-version
  update when required.
- The reviewer records an approval decision and timestamp.
- The plan status changes from `pending_review` to `preregistered` and continues
  to pass `make plan-validate` and `make check`.
- The approved protocol commit is tagged before any outcome-bearing data is
  ingested.

## Next implementation queue

1. After protocol approval, tag the locked plan and execute the first GDC Data
   Release snapshot; independently verify its manifest, object checksums,
   record count, warnings, and external-drive location.
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

### 2026-07-20 — Governed GDC ingestion and immutable dataset snapshots

Implemented deterministic, project-scoped GDC case queries; paginated retrieval;
API and operator-confirmed data-release provenance; raw-response preservation;
SHA-256 checksums; duplicate and count-integrity checks; content-addressed object
keys; immutable writes; typed manifests; and a checked-in JSON Schema. Added a
safe CLI dry run and a fail-closed execution gate that prevents all network and
storage activity until the study plan is approved and `preregistered`. No
TCGA-BRCA study data was downloaded during this implementation.

Validation: GDC dry run made no external request; plan governance validation
passed; Ruff passed, strict MyPy passed, and 42 tests passed.

### 2026-07-20 — First governed TCGA-BRCA pilot protocol

Selected the first reproduction study, defined its falsifiable hypothesis,
cohort, exposure, endpoint, covariate, primary Cox model, sensitivity analyses,
missing-data and multiplicity rules, required outputs, and limitations. Added a
strict typed protocol model, generated JSON Schema, governance-aware loader,
CLI validation commands, and tests. The protocol remains `pending_review`, so
it cannot be represented as preregistered without a recorded approval.

Validation: plan governance validation passed; Ruff passed, strict MyPy passed,
and 37 tests passed.

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
- An independent scientific reviewer has not yet been assigned to approve and
  lock `NAS-BRCA-001`; ingestion of outcome-bearing pilot data waits on this.
- The Seagate volume currently reports approximately 4.2 TiB available. It is
  primary local storage, not an independent backup.

## Durable decisions and boundaries

- `nas-website` and `NaS-Core` remain separate repositories.
- NaS Core begins as a modular monolith.
- OpenAI is a replaceable reasoning provider, not the NaS product or knowledge
  store.
- Numerical research results come from deterministic executed code.
- The first pilot is a reproduction of the association between pathologic
  stage and overall survival in TCGA-BRCA, not a clinical validation study.
- Study plans must be typed, governance-validated, independently reviewed, and
  locked before outcome-bearing data ingestion.
- GDC ingestion is fail-closed unless the plan is `preregistered`; every
  snapshot records the exact request, API provenance, explicitly supplied data
  release, raw response checksums, and immutable object locations.
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
