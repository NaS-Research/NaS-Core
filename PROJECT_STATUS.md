# NaS Core Project Status

Last updated: 2026-07-23

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Founder-screen the NAS-BRCA-002 direct priority evidence

The question-`0.3.0` review is authorized and active. Coverage-repaired strategy
`0.2.4`, its 100-record all-pending queue, and its prior-inventory reconciliation
are independently verified. Founder-adjudicate the 13 direct-priority records first,
confirm the five author-year-only links, screen the remaining candidates, and then
complete sequential backward-plus-forward citation passes. Preserve the
metadata-only, nonclinical boundary until founder review supports a new decision.

Definition of done:

- Question version `0.3.0` defines a fixed single-sample method and a specific
  contribution not already answered by the SCAN-B perturbation study.
- The minimum implementation set and all margin, stability, uncertainty,
  unclassifiable, and abstention rules are declared without outcome inspection.
- Exact centroids, reference vector, platform transformations, technical-error
  model, numerical tolerances, and reliability thresholds are lawfully sourced,
  checksummed, evidence-backed, and locked before molecular access.
- The revised evidence review satisfies its locked stopping rule and retains
  contradictory and null evidence.
- Metadata-only checks verify receptor fields and PAM50 gene coverage in TCGA and
  GSE96058 without accessing outcomes.
- Separate founder scientific/product, molecular/pathology, and statistical review
  passes record conflicts and knowledge limitations.
- A new `go`, `change`, `hold`, or `reject` decision is recorded; only `go` may
  authorize a versioned preregistration.

Current gate state:

- Question version `0.2.0` and its founder-authorized `change` decision are
  preserved. Version `0.3.0` is the active proposed revision; preregistration and
  outcome access remain prohibited.
- Draft method specification `0.1.0` is typed and mechanically validated. It cannot
  authorize molecular execution while any scientific dependency remains unresolved.
- Revised evidence protocol `0.2.4` and priority set `1.0.0` are typed. All 13
  direct candidates are pending question-`0.3.0` founder adjudication; no prior
  decision was silently carried forward.
- Typed Phase 0 plan, literature-search strategy, evidence matrix, and data-
  feasibility specification are implemented.
- AI-assisted question review is advisory; the founder Phase 0 decision is recorded,
  while the revised scientific, molecular, and statistical reviews remain pending.
- The search and source-feasibility specifications are locked. Literature retrieval
  and non-outcome source assessment are authorized; outcome access is disabled.
- Coverage QA stopped the interim 96-record queue before screening because four
  mandatory priority papers were absent. Replacement execution `a2500aba…f1ea9f`
  contains 100 unique records and 55 cross-source duplicates from 56 PubMed and 99
  Europe PMC hits. Its verified all-pending queue contains complete abstracts and
  all 13 priority papers.
- Reconciliation `075aa083…397891` classifies all 100 records against the prior
  inventory: 55 exact matches, 5 author-year-only candidates, and 40 new candidates.
  No previous screening decision was transferred.
- PubMed and Europe PMC are registered for bounded evidence synthesis. Replacement
  execution `83d33fb2…4434` contains 457 unique records with complete abstracts.
- Verified queue `b02c2abf…f042` has progress state `dd27a686…ac21`: 27 founder-
  included records, 7 excluded, 423 pending, zero unclear, and zero AI decisions.
- The append-only founder-review workflow is implemented with resumable batches,
  immutable decision events, explicit supersession, and verified progress receipts.
  The first founder decision batch has been submitted and independently verified.
- The governed AI advisory screener, OpenAI gateway, locked structured prompt, and
  immutable provenance contracts are implemented and validated without live model
  use. The founder selected zero-API Phase 0 screening, so policy `1.0.2` disables
  live provider execution. No API credential is required for the active workflow.
- Deterministic prioritization `1.0.0` ranked all 452 initially pending records
  locally. The 29-record core tier is fully founder-reviewed. Supporting/context
  safety screening and full-text eligibility and quality appraisal remain required.
- TCGA/GDC is approved as the proposed discovery source. Processed SCAN-B GSE96058
  is now registered and approved as the external-validation candidate; PAM50 gene
  coverage and cross-platform transformations still require metadata verification.
- Full-text progress is now mechanically reconciled: 8 of 27 founder inclusions have
  verified full text and completed appraisals. Roles are 3 supporting and 5 context-only;
  4 additional papers are access-restricted or non-open-access. No anchor
  study or scientific conclusion exists yet. One Research Square preprint is
  durably linked to its already-appraised peer-reviewed version and is not double-counted.
- The structured evidence matrix, novelty/no-go memorandum, field-level source
  feasibility assessment, governed GSE96058 registration, and Phase 0 gate decision
  are complete. The locked evidence stopping rule was not claimed as satisfied:
  review terminated through an explicit no-go trigger.
- NAS-BRCA-001 remains an immutable conditional platform-qualification pass with
  a pending founder results/remediation decision.

## Next implementation queue

1. Screen and appraise the 13-record direct priority set, beginning with the
   single-subject uncertainty, AIMS, MiniABS, SSP, MPAM50, and BreastSubtypeR reports.
2. Founder-confirm or reject the five author-year-only inventory links, then screen
   every remaining record in the 100-record revised queue.
3. Execute sequential backward-plus-forward Europe PMC citation passes until two
   consecutive complete passes add zero eligible methods or external validations.
4. Resolve and approve the exact centroid and external-reference artifacts,
   redistribution rights, expression transformations, and numerical tolerances.
5. Define an independently calibrated technical-error model and lock the margin
   and canonical-label-retention thresholds without molecular or outcome inspection.
6. Verify TCGA receptor-field completeness and PAM50 gene coverage in TCGA and
   GSE96058 through logged metadata-only queries.
7. Complete the founder scientific/product, molecular/pathology, and statistical
   reviews for question `0.3.0`, then record a new gate decision.
8. Complete the NAS-BRCA-001 founder results review and authorize, hold, or reject
   a transparent versioned remediation.
9. If authorized, remediate only declared NAS-BRCA-001 technical defects and
   preserve the original immutable run.
10. Implement persisted evidence claims, citations, provenance, contradictory
   evidence, null findings, limitations, and review state.
11. Add license-aware permitted passage ingestion and hybrid keyword and semantic
   retrieval after the Phase 0 evidence inventory is screened.
12. Expand the screening model gateway into general evidence reasoning with
   minimum-necessary context, citations, uncertainty, abstention, and governance.
13. Build evaluation suites for retrieval, citation validity, numerical
   fidelity, unsupported claims, and appropriate abstention.
14. Generate an immutable research release containing the protocol, dataset
   manifest, code revision, environment, results, figures, literature,
   limitations, approvals, and disclosures.
15. Generate a reviewable white-paper draft whose substantive claims trace to
   executed artifacts, external sources, or labeled interpretation.
16. Build the internal workbench for projects, protocols, datasets, runs,
   evidence review, and publication releases.
17. Complete repeated internal oncology pilots before selecting the first
    external commercial product surface.

## Recently completed

### 2026-07-23 — Revised screening corpus verified and reconciled

Built an immutable all-pending queue from the focused search, then stopped it before
screening when coverage QA found only 9 of 13 mandatory priority papers. Strategy
`0.2.4` explicitly unions the locked priority identifiers and passed count-only
feasibility at 56 PubMed and 99 Europe PMC hits.

Replacement execution `a2500aba…f1ea9f` contains 100 unique records and 55
cross-source duplicates. Queue `af08a334…8a2a3` has 100 complete abstracts, all 13
priority papers, zero human or AI decisions, and independently verified identities,
hashes, sizes, summaries, and pending states. Reconciliation against the prior
457-record inventory found 55 exact matches, 5 author-year-only candidates, and 40
new candidates. It transferred zero prior decisions and generated no scientific
conclusion.

### 2026-07-23 — Revised reliability search locked and captured

Recorded founder Phase 0 authorization for question `0.3.0`, implemented a
metadata-only feasibility specification, and refined the search through four
count-only iterations. The final strategy `0.2.3` narrowed the result to 52 PubMed
and 95 Europe PMC hits without storing preview records.

Executed the locked query once. Immutable execution `7c57c576…8fbee` contains 96
unique bibliographic records and 51 cross-source duplicates. A separate verifier
reloaded the manifest and all five data objects from external storage, recomputed
hashes and sizes, checked normalized-record schema and uniqueness, reconciled source
and duplicate counts, and issued the aggregate receipt in Git. No molecular or
outcome data were accessed, and no scientific conclusion was generated.

### 2026-07-23 — Revised evidence-review phase implemented

Implemented a question-`0.3.0` evidence protocol and targeted PubMed/Europe PMC
strategy focused on fixed single-sample classifiers, centering, mapping,
patient-level uncertainty, technical error, perturbation, abstention, and unchanged
external transport. The direct priority set contains 13 high-relevance candidates
and remains capped at 30 final studies. It explicitly prioritizes the previously
unappraised single-subject PAM50 uncertainty method, AIMS, MiniABS, RNA-seq SSP,
MPAM50, BreastSubtypeR, and current centering implementations.

Added typed priority, citation-pass, and progress contracts plus CLI validation.
The ledger cannot claim saturation unless the search, prior-inventory deduplication,
founder screening, appraisal/access accounting, and two latest consecutive complete
backward-plus-forward Europe PMC passes all reconcile with zero newly eligible
methodological or external-transport evidence. AI cannot finalize screening
decisions, and the phase cannot authorize novelty, molecular data, or outcomes.

Validation: checked-in schema parity, CLI binding, false-saturation and founder-
authority invariants, focused tests, Ruff, strict MyPy, and the full test suite.

### 2026-07-23 — Single-sample reliability method contract implemented

Implemented typed method specification `0.1.0` for NAS-BRCA-002 question `0.3.0`.
It fixes the historical PAM50 50-gene panel and aliases, one-tumor input boundary,
five-centroid Spearman score, runner-up and margin formulas, deterministic 50-run
leave-one-gene-out panel, and the governed boundary for an independent technical-
error sensitivity panel. The patient-level contract now preserves all quality
failures, canonical and runner-up scores, margin, perturbation validity, label
retention, reliability state, reason codes, provenance, and limitations.

Only a `reliable` state may report a research subtype. Unstable, unclassifiable,
and insufficient-data results must abstain. Exact centroids, external reference,
platform transforms, technical-error calibration, numerical tolerances, and margin
and retention thresholds remain explicit unresolved dependencies. The typed
validator prohibits a draft from authorizing molecular execution and prohibits
outcome- or validation-guided tuning.

Validation: checked-in schema parity, CLI validation, focused contract and invariant
tests, Ruff, strict MyPy, and the full test suite.

### 2026-07-23 — Question v0.3.0 narrows the study to reliability and abstention

Preserved question `0.2.0` and its review packet as immutable versioned history,
then drafted active question `0.3.0`. The new primary object is a frozen,
patient-independent research procedure that returns the subtype and runner-up
scores, margin, perturbation repeatability, data-quality state, reliability state,
and an explicit abstention reason. The primary estimands are analytical reliability
and repeatability—not biological truth, prognosis, treatment response, or clinical
utility.

The v0.3.0 change-resolution trace maps every Phase 0 requirement to a resolved or
pending state. The founder and AI review states reset to `pending`; prior v0.2.0
work is not carried forward as approval. No preregistration, ingestion, molecular
analysis, outcome access, or clinical use was authorized.

Validation: active and archived question validation, version-history tests, Ruff,
strict MyPy across 54 source files, and all 156 tests passed.

## Current blockers

- Docker is not currently available in the development environment, so the
  Compose services have been syntax-validated but not started locally.
- Paid AI advisory screening is intentionally inactive under founder policy `1.0.2`;
  the active deterministic Phase 0 workflow requires no API credential.
- `NAS-BRCA-002` version `0.3.0` is proposed. Method specification `0.1.0` is
  nonexecuting until its exact artifacts, transforms, technical-error calibration,
  numerical tolerances, and thresholds are resolved. The complete evidence stopping
  rule and founder scientific/product, molecular/pathology, and statistical reviews
  are also required before selection.
- Revised search strategy `0.2.4`, its queue, and prior-inventory reconciliation are
  complete. Founder screening, full-text appraisal, and the citation-chain stopping
  rule remain incomplete.
- GSE96058 is approved only as a processed-data validation candidate. PAM50 gene
  coverage and the locked cross-platform transformation remain unresolved.
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
