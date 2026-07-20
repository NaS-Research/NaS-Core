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
3. Use the governed research-question intake and selection rubric to compare
   decision-led breast-oncology candidates, approve one first discovery
   question, and mark it ready for a formal literature-review protocol.
4. Implement persisted evidence claims, citations, provenance, contradictory
   evidence, null findings, limitations, and review state.
5. Register approved bibliographic sources, execute the selected question's
   literature-review protocol, and add permitted metadata and passage ingestion
   with hybrid keyword and semantic retrieval.
6. Add the replaceable model gateway with structured outputs, minimum-necessary
   context, citations, uncertainty, abstention, and governance enforcement.
7. Build evaluation suites for retrieval, citation validity, numerical
   fidelity, unsupported claims, and appropriate abstention.
8. Generate an immutable research release containing the protocol, dataset
   manifest, code revision, environment, results, figures, literature,
   limitations, approvals, and disclosures.
9. Generate a reviewable white-paper draft whose substantive claims trace to
   executed artifacts, external sources, or labeled interpretation.
10. Build the internal workbench for projects, protocols, datasets, runs,
   evidence review, and publication releases.
11. Complete repeated internal oncology pilots before selecting the first
    external commercial product surface.

## Recently completed

### 2026-07-20 — Standardized study workspaces and lifecycle pipeline

Implemented typed study and pipeline manifests, canonical JSON Schemas, a
collision-safe CLI scaffold, manifest validation, ordered stage gates, stable
artifact namespaces, and a documented boundary between versioned Git content
and external research artifacts. Migrated `NAS-BRCA-001` into the canonical
question, literature, protocol, ingestion, analysis, evidence, release, tests,
and reviews layout without changing its pending scientific-review gate. No
biomedical data was downloaded or generated.

Validation: the migrated study and analysis plan passed governance validation;
the GDC dry run performed no network or storage activity; Ruff passed, strict
MyPy passed, and 53 tests passed.

### 2026-07-20 — Biomedical data-source landscape

Documented the major candidate sources for cancer multi-omics, population
oncology, longitudinal biobanks, real-world clinical data, functional genomics,
variants, single-cell and spatial biology, imaging and pathology, drugs and
targets, trials and safety, literature, and protein structure. Added access
classes, important limitations, project-to-source examples, and the governed
workflow for promoting a candidate into the approved source registry. This was
a documentation change only: no data was downloaded and no new source was
approved.

Validation: documentation links and formatting passed; Ruff passed, strict
MyPy passed, and 48 tests passed.

### 2026-07-20 — Decision-led oncology program and pre-literature gates

Established the machine-readable NaS Oncology Research Program, separated
platform qualification from discovery and product claims, and documented stage
gates through external validation, translation, and deployment. Added a typed
research-question intake covering the intended user, decision, scientific
question, evidence needs, data feasibility, analysis family, validation path,
system output, and scientific, decision, and product success criteria. Added a
40-point selection rubric, review approval gate, literature-readiness gate,
checked-in schemas, CLI validation, topic-selection guidance, and a reproducible
literature-review template. No articles were collected and no product wedge was
assumed.

Validation: oncology program and question-template validation passed; Ruff
passed, strict MyPy passed, and 48 tests passed.

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

## Current blockers

- Docker is not currently available in the development environment, so the
  Compose services have been syntax-validated but not started locally.
- An independent scientific reviewer has not yet been assigned to approve and
  lock `NAS-BRCA-001`; ingestion of outcome-bearing pilot data waits on this.
- The first decision-led oncology discovery question and product surface remain
  intentionally unselected; formal article collection waits on an approved
  research-question intake.
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
- NaS research begins with an intended user and decision. Datasets, articles,
  models, and interesting patterns do not define a research program by
  themselves.
- Every approved research question receives a permanent study ID and canonical
  workspace. Multiple prespecified hypotheses may share one study; a material
  change in decision, population, principal exposure, primary outcome, or
  validation claim requires a new study.
- Study manifests define stable external artifact namespaces. Git contains
  definitions, deterministic code, synthetic tests, and review records; data
  snapshots, run artifacts, and frozen releases remain in external storage.
- The oncology program separates platform qualification, discovery, external
  validation, translation, and deployment claims.
- Study plans must be typed, governance-validated, independently reviewed, and
  locked before outcome-bearing data ingestion.
- GDC ingestion is fail-closed unless the plan is `preregistered`; every
  snapshot records the exact request, API provenance, explicitly supplied data
  release, raw response checksums, and immutable object locations.
- Public/open and explicitly approved licensed data are the only v0 data
  classes; controlled data and PHI remain prohibited.
- The data-source landscape is an informational candidate catalog, not an
  authorization list. A project selects the minimum necessary sources for its
  approved question, and only entries approved in `data/source-registry.yaml`
  may be ingested.
- Data confined to a provider's secure workspace must remain there unless its
  agreement explicitly permits export; it cannot automatically be copied to
  the Seagate data root.
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
