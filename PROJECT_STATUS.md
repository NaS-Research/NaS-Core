# NaS Core Project Status

Last updated: 2026-07-22

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Complete the NAS-BRCA-002 novelty and data-feasibility audit

Determine whether the proposed classification-stability study has a defensible
novel contribution and an executable discovery/validation data path before
preregistration. This gate may inspect literature metadata, source terms, variable
availability, and non-outcome feasibility counts after explicit founder approval;
it does not authorize molecular outcome analysis or a novelty claim.

Definition of done:

- Founder authorization for the bounded, non-outcome Phase 0 audit is recorded.
- The search strategy is locked before retrieval and the evidence matrix records
  every included and excluded source with a reproducible search trail.
- A novelty memo separates established knowledge, the unresolved gap, the proposed
  contribution, competing explanations, and the value of a null result.
- Discovery and validation variable/file identifiers, access class, terms,
  independence, cohort overlap, assay compatibility, and export constraints are
  documented without retrieving outcome-bearing molecular data.
- Preliminary group and event feasibility is assessed only under a separately
  approved, logged query and does not test the scientific hypothesis.
- Founder records `go`, `change`, `hold`, or `reject`; only `go` advances to a
  versioned, preregistered analysis plan.

Current gate state:

- Question version `0.2.0` remains proposed; no scientific selection decision has
  been recorded.
- Typed Phase 0 plan, literature-search strategy, evidence matrix, and data-
  feasibility specification are implemented.
- AI-assisted question review is complete and advisory; founder review is pending.
- The search and source-feasibility specifications are locked. Literature retrieval
  and non-outcome source assessment are authorized; outcome access is disabled.
- PubMed and Europe PMC are registered for bounded evidence synthesis. Locked
  strategy `0.1.1` produced verified immutable execution `9eec1656…c185` with
  457 unique records; human screening has not started.
- The typed screening-queue engine is complete and validated with synthetic
  records. The real queue awaits execution from its pushed code revision.
- TCGA/GDC is the proposed discovery source; the candidate independent validation
  source is unassessed and not approved in the source registry.
- NAS-BRCA-001 remains an immutable conditional platform-qualification pass with
  a pending founder results/remediation decision.

## Next implementation queue

1. Build the immutable title/abstract queue from the verified 457-record inventory
   using the pushed screening-engine revision.
2. Record founder title/abstract decisions, adjudicate unclear records, populate
   the evidence matrix, and produce a novelty memo with an explicit no-go test.
3. Complete discovery and validation source feasibility, including exact variable
   mappings, terms, compatibility, independence, overlap, and source-registry review.
4. Decide `go`, `change`, `hold`, or `reject`; preregister a full analysis plan only
   after a documented `go` decision.
5. Complete the NAS-BRCA-001 founder results review and authorize, hold, or reject
   a transparent versioned remediation.
6. If authorized, remediate only declared NAS-BRCA-001 technical defects and
   preserve the original immutable run.
7. Implement persisted evidence claims, citations, provenance, contradictory
   evidence, null findings, limitations, and review state.
8. Add license-aware permitted passage ingestion and hybrid keyword and semantic
   retrieval after the Phase 0 evidence inventory is screened.
9. Add the replaceable model gateway with structured outputs, minimum-necessary
   context, citations, uncertainty, abstention, and governance enforcement.
10. Build evaluation suites for retrieval, citation validity, numerical
   fidelity, unsupported claims, and appropriate abstention.
11. Generate an immutable research release containing the protocol, dataset
   manifest, code revision, environment, results, figures, literature,
   limitations, approvals, and disclosures.
12. Generate a reviewable white-paper draft whose substantive claims trace to
   executed artifacts, external sources, or labeled interpretation.
13. Build the internal workbench for projects, protocols, datasets, runs,
   evidence review, and publication releases.
14. Complete repeated internal oncology pilots before selecting the first
    external commercial product surface.

## Recently completed

### 2026-07-22 — Governed title/abstract screening-queue engine

Implemented a fail-closed builder that reads only an independently verified
literature snapshot, rechecks the normalized-object size and checksum, validates
record counts and unique keys, and creates content-addressed queue, summary, and
manifest artifacts outside Git. Every record begins pending. Typed contracts forbid
an exclusion without one reason plus human reviewer and timestamp; the initial
manifest records zero human and zero AI decisions. Development used synthetic
bibliographic records only.

Validation: Ruff, strict MyPy, focused tamper/invariant tests, and all 101 repository
tests passed; real queue execution awaits the pushed engine revision.

### 2026-07-22 — First immutable NAS-BRCA-002 literature search

Executed locked search strategy `0.1.1` against PubMed and Europe PMC using the
founder-authorized contact identity. A count-only gate detected that strategy
`0.1.0` expanded to 79,501 Europe PMC records; the source-syntax correction was
versioned before record storage and without viewing scientific results. The final
execution retrieved 391 PubMed and 123 Europe PMC records, yielding 457 unique
records after 57 duplicates. Raw responses and normalized abstracts are confined
to the Seagate object store. No screening, evidence extraction, molecular outcome
access, or scientific conclusion occurred.

Validation: execution `9eec1656…c185`; manifest `1f041638…dec2`; all eight
objects, hashes, sizes, and count invariants independently verified; typed aggregate
receipt created; Ruff, strict MyPy, and all 97 repository tests passed.

### 2026-07-22 — Governed PubMed and Europe PMC retrieval engine

Registered PubMed and Europe PMC for bounded evidence synthesis and implemented a
fail-closed, content-addressed search runner. It validates founder authorization,
locked queries, source status, roles, and purpose before network access; captures
exact requests and raw responses outside Git; normalizes and deduplicates by DOI,
PMID, and title; hashes the required API contact address in provenance; enforces
NCBI-compatible request pacing; and supports a network-free CLI preview. No live
search or scientific screening was performed.

Validation: Ruff, strict MyPy, focused provenance tests, and all 94 repository
tests passed; live execution requires a valid API contact email.

### 2026-07-22 — Founder-authorized NAS-BRCA-002 Phase 0 audit

Recorded Dalron J. Robertson's explicit authorization for the bounded novelty and
data-feasibility audit under question version `0.2.0`. Locked the literature-search
and source-feasibility specifications and authorized bibliographic retrieval,
source assessment, and non-outcome metadata queries. Outcome-bearing data access,
hypothesis testing, question selection, novelty claims, and clinical claims remain
prohibited. The authorization includes role-conflict disclosure and a permanent
human-readable review record.

Validation: typed authorization and cross-artifact fail-closed rules passed Ruff,
strict MyPy, and all 89 repository tests.

### 2026-07-22 — NAS-BRCA-002 Phase 0 audit infrastructure

Implemented typed, cross-validated contracts for the novelty plan, reproducible
literature-search strategy, and data-feasibility assessment. Added schemas and CLI
validation, a question-specific search protocol, an empty provenance-ready evidence
matrix, discovery/validation variable requirements, explicit no-go criteria, and an
AI-assisted advisory review. At completion of this scaffold, retrieval and outcome-
data access were disabled, and no scientific result or novelty claim was generated.

Validation: Ruff, strict MyPy, and all 87 repository tests passed; founder
authorization was required before executing the bounded Phase 0 audit.

## Current blockers

- Docker is not currently available in the development environment, so the
  Compose services have been syntax-validated but not started locally.
- `NAS-BRCA-002` remains unselected pending founder scientific/product,
  molecular/pathology, and statistical self-review. Its bounded Phase 0 audit is
  authorized, but outcome work and formal question selection are not.
- The independent external validation source for `NAS-BRCA-002` has not been
  selected or approved. Its license, compatible variables, cohort overlap, and
  export terms must be established before preregistration.
- The Seagate volume currently reports approximately 4.2 TiB available. It is
  primary local storage, not an independent backup.
- NAS-BRCA-001 public release is blocked by pending founder results review, a
  failed S4 nonlinear-age sensitivity, nonconvergent S3, a material exposure PH
  violation, and Kaplan–Meier figure-layout failure.

## Durable decisions and boundaries

- `nas-website` and `NaS-Core` remain separate repositories.
- NaS Core begins as a modular monolith.
- OpenAI is a replaceable reasoning provider, not the NaS product or knowledge
  store.
- Numerical research results come from deterministic executed code.
- Survival analysis uses pinned, replaceable statistical libraries behind NaS
  typed result contracts; library output is not accepted until serialized,
  checksummed, and independently verified.
- Outcome-bearing runs are immutable. Post-result defect corrections require a
  written amendment, new algorithm version, new run ID, and retained provenance
  for both the original and replacement runs.
- Cohort construction is frozen before outcome modeling. An unexpected result
  cannot justify silently changing eligibility, normalization, or exclusions;
  any correction requires a preserved prior build and a new algorithm version.
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
- The qualification study ends in a pass, conditional pass, or fail judgment
  about Cortex; its hazard ratios and figures are not patient-level decision
  support or evidence of clinical utility.
- A decision-support study must define the user, choice, patient context,
  alternatives, outcome, evidence, uncertainty, validation path, abstention
  conditions, and real-world impact evaluation before translation.
- `NAS-BRCA-002` is a proposed discovery and external-validation study of PAM50
  classification stability in clinically HR-positive/HER2-negative disease. No
  implementation is assumed to be a universal gold standard, and the work cannot
  support patient-level testing or treatment claims.
- Phase 0 discovery artifacts may define searches, source requirements, falsification
  criteria, and no-go rules before question selection, but retrieval remains disabled
  until the founder explicitly authorizes the bounded audit.
- Novelty is an evidence-backed conclusion, not an assumption. NAS-BRCA-002 cannot
  claim novelty until the reproducible evidence matrix and novelty memo are reviewed.
- An external validation source must be independently assessed, registered, legally
  usable, sufficiently independent, and analytically compatible before it enters a
  preregistered validation plan.
- Public website publication must derive from an approved frozen research
  release. The version-of-record PDF, web edition, tables, figures, citations,
  and displayed numbers must agree and follow visible versioning and correction
  procedures.
- Study plans must be typed, governance-validated, reviewed with explicit
  provenance, and locked before outcome-bearing data ingestion.
- A research question cannot become selected or literature-ready until every
  gate-required review is approved. Founder self-review may authorize the
  current internal gate when conflicts and knowledge limits are disclosed.
- AI-assisted review is advisory: it cannot be gate-required, approve a study,
  authorize ingestion, or be represented as human review.
- External expert feedback is recorded separately from founder self-review.
  Public NaS reports remain labeled founder-led, internally reviewed, and not
  peer reviewed until a journal completes formal peer review.
- Bibliographic API exports and normalized records remain in external object
  storage. Git may contain only aggregate receipts, screening decisions, and
  concise evidence extraction; copyrighted abstracts and full text are not
  redistributed, embedded, or used for model training without item-level rights.
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
- Local v0 snapshots use the path-safe filesystem object-store adapter rooted at
  the marker-validated Seagate `NAS_DATA_ROOT`; S3 remains a replaceable future
  deployment backend.
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
