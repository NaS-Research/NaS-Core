# NaS Core Research Engine Plan

## Objective

Build an internal research and evidence system that converts approved biomedical
data and literature into reproducible analyses, structured evidence, and
traceable research releases. OpenAI models assist with bounded reasoning and
drafting; they do not store the authoritative knowledge or create numerical
research results.

## Operating model

Every project follows one lineage:

`project -> plan -> dataset snapshot -> analysis run -> artifact -> evidence claim -> release`

Git stores code, protocols, schemas, and synthetic tests. PostgreSQL stores the
catalog and lineage. Object storage holds large data and artifacts. Search
indexes are rebuildable derivatives rather than authoritative records.

## Phase 1: Reproducible pilot protocol

Define a public/open TCGA-BRCA study, register its hypothesis and methods before
examining final results, and validate the plan against a machine-readable
schema.

Exit criteria:

- The question, cohort, endpoint, covariates, models, missing-data rules,
  sensitivity analyses, multiplicity policy, and limitations are explicit.
- Required data types are confirmed public/open and governance-authorized.
- Scientific review responsibility is recorded.

## Phase 2: Dataset catalog and GDC ingestion

Create immutable dataset snapshots from exact GDC queries and manifests. Store
the source release, file IDs, sizes, checksums, timestamps, classification,
permissions, and object-store locations.

Exit criteria:

- A second machine can recreate the same manifest and verify all files.
- Downloaded bytes never enter Git.
- Ingestion is impossible without an active source registration and approved
  purpose.

## Phase 3: Deterministic analysis execution

Execute cohort construction, quality control, statistics, and figures in
versioned Python or R workflows. Capture code revision, environment, parameters,
random seeds, warnings, logs, inputs, and outputs.

Exit criteria:

- A clean environment reproduces the primary result within defined numerical
  tolerances.
- Every table, figure, estimate, interval, and p-value resolves to an immutable
  analysis artifact.

## Phase 4: Evidence and provenance

Represent supported, unsupported, contradictory, and null claims. Link each
claim to analysis artifacts or external source passages and record uncertainty,
limitations, evidence quality, and human review state.

Exit criteria:

- No substantive verified claim can exist without support.
- Derived claims retain their complete source and analysis lineage.

## Phase 5: Literature retrieval

Register permitted literature sources, normalize bibliographic metadata, index
approved passages, and provide hybrid keyword and semantic retrieval.

Exit criteria:

- Citations resolve to real sources and supporting passages.
- Source permissions govern storage, embeddings, model use, and publication.

## Phase 6: Model gateway

Connect OpenAI behind a replaceable NaS interface. Transmit only the minimum
retrieved evidence and compact derived results needed for a task. Require typed
outputs, citations, uncertainty, abstention, and governance approval.

Exit criteria:

- Controlled data and PHI are rejected.
- Model or prompt changes pass regression evaluations.
- Model text cannot become verified evidence without review.

## Phase 7: Evaluation and release gates

Measure retrieval recall, citation validity, numerical fidelity, unsupported
claims, appropriate abstention, and end-to-end reproducibility.

Release gates:

- 100% of numerical claims trace to executed artifacts.
- 100% of citations resolve to real sources.
- Zero fabricated citations in the release evaluation set.
- No unreviewed model text is marked verified.
- The scientific reviewer approves the frozen release.

## Phase 8: Research release and white paper

Freeze the protocol, dataset manifest, code revision, environment, results,
figures, evidence, literature, limitations, approvals, and disclosures. Generate
a draft in which every substantive sentence has claim-level provenance.

Exit criteria:

- Rebuilding the paper cannot silently change its evidence.
- The release remains reproducible after newer data and code arrive.

## Phase 9: Internal workbench

Build interfaces for projects, plans, datasets, runs, artifacts, evidence
review, approvals, and publication releases only after the underlying workflow
is proven.

## Phase 10: Repeated pilots and product selection

Run multiple internal oncology projects. Use observed research value, workflow
bottlenecks, and partner needs to select the first commercial surface, such as
biomarker intelligence, trial intelligence, or pharmaceutical research support.

## Storage progression

The current local object store is rooted on the Seagate volume. All stored
objects receive stable identifiers, classification, checksums, and lineage.

Planned progression:

1. Seagate local primary storage for public/open v0 research.
2. Independent local or cloud backup with tested restoration.
3. Encrypted S3-compatible production storage with lifecycle policies.
4. Archival tiers for frozen research releases and source snapshots.

The local drive is not itself a backup. Controlled data and PHI remain
prohibited regardless of available disk capacity.
