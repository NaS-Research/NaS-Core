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
- PubMed and Europe PMC are registered for bounded evidence synthesis. Replacement
  execution `83d33fb2…4434` contains 457 unique records with complete abstracts.
- Verified queue `b02c2abf…f042` has progress state `9c2322a8…9473`: 19 founder-
  included records, 6 excluded, 432 pending, zero unclear, and zero AI decisions.
- The append-only founder-review workflow is implemented with resumable batches,
  immutable decision events, explicit supersession, and verified progress receipts.
  The first founder decision batch has been submitted and independently verified.
- The governed AI advisory screener, OpenAI gateway, locked structured prompt, and
  immutable provenance contracts are implemented and validated without live model
  use. The founder selected zero-API Phase 0 screening, so policy `1.0.2` disables
  live provider execution. No API credential is required for the active workflow.
- Deterministic prioritization `1.0.0` ranked all 452 pending records locally: 29
  core, 158 supporting, and 265 context. It wrote zero screening decisions and drew
  no conclusion; founder eligibility review and later full-text quality appraisal
  remain required.
- TCGA/GDC is the proposed discovery source; the candidate independent validation
  source is unassessed and not approved in the source registry.
- NAS-BRCA-001 remains an immutable conditional platform-qualification pass with
  a pending founder results/remediation decision.

## Next implementation queue

1. Present the 29 core-priority records in small founder-review batches and record
   only explicit include, exclude, or unclear decisions against the locked protocol.
2. Retrieve permitted full text for founder-included records and implement a
   study-design-specific quality-appraisal form; do not infer quality from rank.
3. Review supporting records and citation chains until the locked stopping rule is
   satisfied; preserve eligible contradictory and null evidence regardless of rank.
4. Complete founder decisions, populate the evidence matrix, and produce a novelty
   memo with an explicit no-go test.
5. Complete discovery and validation source feasibility, including exact variable
   mappings, terms, compatibility, independence, overlap, and source-registry review.
6. Decide `go`, `change`, `hold`, or `reject`; preregister a full analysis plan only
   after a documented `go` decision.
7. Complete the NAS-BRCA-001 founder results review and authorize, hold, or reject
   a transparent versioned remediation.
8. If authorized, remediate only declared NAS-BRCA-001 technical defects and
   preserve the original immutable run.
9. Implement persisted evidence claims, citations, provenance, contradictory
   evidence, null findings, limitations, and review state.
10. Add license-aware permitted passage ingestion and hybrid keyword and semantic
   retrieval after the Phase 0 evidence inventory is screened.
11. Expand the screening model gateway into general evidence reasoning with
   minimum-necessary context, citations, uncertainty, abstention, and governance.
12. Build evaluation suites for retrieval, citation validity, numerical
   fidelity, unsupported claims, and appropriate abstention.
13. Generate an immutable research release containing the protocol, dataset
   manifest, code revision, environment, results, figures, literature,
   limitations, approvals, and disclosures.
14. Generate a reviewable white-paper draft whose substantive claims trace to
   executed artifacts, external sources, or labeled interpretation.
15. Build the internal workbench for projects, protocols, datasets, runs,
   evidence review, and publication releases.
16. Complete repeated internal oncology pilots before selecting the first
    external commercial product surface.

## Recently completed

### 2026-07-22 — Third founder title/abstract decision batch

Recorded and independently verified ten explicit founder decisions from the second
deterministic core-priority batch: seven inclusions and three protocol-based
exclusions. The cumulative immutable state is 25 of 457 records decided: 19
included, 6 excluded, 432 pending, zero unclear, and zero AI decisions. Nine records
remain in the locked core-priority tier. No quality judgment or scientific
conclusion was drawn.

Validation: exact prior-state binding, queue membership, reviewer provenance,
exclusion taxonomy, event-chain and artifact hashes, reconciled cumulative counts,
and the human-only boundary independently verified.

### 2026-07-22 — Second founder title/abstract decision batch

Recorded and independently verified ten explicit founder decisions from the first
deterministic core-priority batch: seven inclusions and three protocol-based
exclusions. The cumulative immutable state is 15 of 457 records decided: 12
included, 3 excluded, 442 pending, zero unclear, and zero AI decisions. Inclusion
advances a record to full-text eligibility review; it does not establish quality or
evidentiary weight. No scientific conclusion was drawn.

Validation: queue membership, exact prior-state binding, reviewer provenance,
exclusion taxonomy, cumulative event-chain identities and hashes, artifact hashes
and sizes, reconciled progress counts, and human-only boundary verified.

### 2026-07-22 — Zero-cost deterministic literature prioritization

Implemented transparent local ranking for every pending NAS-BRCA-002 title and
abstract without a model, credential, network request, or usage charge. Versioned
signals cover PAM50/intrinsic subtype, stability, uncertainty, discordance,
preprocessing, validation, human cohorts, methods, and outcomes, with explicit
caution signals. The first diagnostic threshold was rejected as too permissive;
the locked thresholds now identify 29 core, 158 supporting, and 265 context records.
Ranking creates no eligibility or quality decision and cannot write the human ledger.
Founder policy `1.0.2` disables live AI execution for Phase 0.

Validation: deterministic scoring and no-decision tests, complete verified pending-
queue ranking, Ruff, strict MyPy, study validation, and all 116 tests passed.

### 2026-07-22 — Founder-authorized AI provider retention path

Recorded Dalron J. Robertson's prospective authorization of the standard API
abuse-monitoring retention path for the exact verified NAS-BRCA-002 public/open
title-and-abstract queue. Policy `1.0.1` enables only governed advisory execution,
keeps provider application storage disabled, caps calls at ten records, requires
human review and calibration, and continues to prohibit autonomous decisions.
Licensed full text, controlled data, PHI, patient-level data, other queues,
scientific conclusions, and publication claims remain outside authorization. No
live request was made because the local API credential is absent.

Validation: checked-in policy contract, fail-closed disabled-policy test, explicit
founder authorization record, and scope-aligned runbook and study status.

### 2026-07-22 — Governed AI advisory screening engine

Implemented a replaceable model gateway and a NAS-BRCA-002 advisory screener using
the OpenAI Responses API with typed structured outputs. The workflow sends only a
bounded title/abstract batch, converts source text into deterministic sentence IDs,
requires recommendation, confidence, matched criteria, evidence references,
protocol exclusion reason, concise rationale, and human-review status, and rejects
missing records or unverifiable evidence. Requests, recommendations, summaries,
and manifests are immutable external artifacts. Git stores only policy, prompt,
schemas, tests, runbook, and future aggregate receipts. AI cannot write the human
ledger, authorize routing before calibration, or create a conclusion. No live model
request or AI recommendation was generated because the API credential is absent.

Validation: official SDK adapter, provider-free synthetic gateway, tamper and
evidence-reference boundaries, fail-closed credential test, network-free real-study
dry run, canonical schemas, Ruff, strict MyPy, study-contract validation, and all
114 repository tests passed.

## Current blockers

- Docker is not currently available in the development environment, so the
  Compose services have been syntax-validated but not started locally.
- Paid AI advisory screening is intentionally inactive under founder policy `1.0.2`;
  the active deterministic Phase 0 workflow requires no API credential.
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
- AI literature recommendations remain separate from the append-only founder
  decision ledger. NAS-BRCA-002 prohibits autonomous exclusions; calibration and
  locked routing rules are required before AI output may prioritize human review.
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
