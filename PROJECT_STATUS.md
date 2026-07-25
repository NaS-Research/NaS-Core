# NaS Core Project Status

Last updated: 2026-07-24

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Founder-confirm the NAS-BRCA-002 remaining-queue screening packet

The question-`0.3.0` review is authorized and active. All 13 direct-priority
records now have a terminal access state: 12 completed appraisals and one
identity-verified subscription restriction. The next evidence task is founder
screening of the remaining 87 revised-queue records, followed by sequential
backward and forward citation chaining to the locked two-zero-pass stopping rule.
The advisory pass is complete: 17 inclusions and 70 exclusions are proposed, and
all five author-year-only candidate links are recommended for rejection. These
recommendations remain nonbinding until the founder confirms or edits the packet.

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
- Every read-only appraisal reconciles to an identity-verified source URL and
  ephemeral-content checksum; no restricted full text enters Git or object storage.
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
  direct candidates have founder `include` decisions for full-text review; no prior
  question-`0.2.0` decision was silently carried forward.
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
- Question-`0.3.0` title/abstract protocol `1.1.0` is locked. The founder priority
  packet contains all 13 direct records. Verified founder progress records 13
  inclusions, 87 pending, zero exclusions, zero unclear, and zero AI decisions.
- The priority access inventory reconciles all 13 inclusions: 7 verified CC-BY
  full texts, 5 governed read-only reviews, and 1 subscription restriction. No
  restricted text was retained or redistributed.
- The question-specific `PMC3275466` appraisal is complete as `context_only`.
  Its technical-error framework directly challenges the novelty boundary, but sparse
  calibration, unvalidated independence assumptions, inconsistent simulation counts,
  and no external repeat-measure validation prevent it from supplying a transportable
  NaS error model.
- The subgroup-centering paper `PMC4365540` is also `context_only`. It demonstrates
  that cohort composition can radically change PAM50 calls, but its proposed fix
  uses the study cohort's clinical composition and explicitly cannot classify one
  patient independently. It supports—not resolves—the fixed-reference requirement.
- The RNA-seq reference-sensitivity paper `PMC7442834` is `supporting`. Across
  4,731 tumors, it demonstrates reference-subset sensitivity, materially improves
  within-method stability with AWCA, and tests preprocessing-matched external
  references and regularized classifiers. Published PAM50 calls remain a technical
  target rather than biological truth, transport is normalization-specific, and
  clinical validity is unproven, so it is not anchor evidence.
- MiniABS paper `PMC7761033` is `supporting`. It establishes that an 11-gene,
  pairwise-ratio classifier can operate on a single sample across RNA-seq,
  microarray, NanoString, and qRT-PCR datasets. Its PAM50-derived target labels,
  feature-selection sequence, Normal-like sensitivity, and absence of calibrated
  uncertainty or abstention prevent an anchor role. NaS cannot claim single-sample
  execution alone as novel.
- SCAN-B SSP paper `PMC9381586` is `supporting` and is the strongest reviewed
  validation so far. It uses a non-overlapping 2,412-patient test set, long
  follow-up, adjusted outcome models, external Prosigna comparisons, public data,
  and executable code. It also establishes that subtype and recurrence-risk
  prediction already exist; retrospective treatment emulation and absent
  patient-level uncertainty prevent anchor or clinical-utility claims.
- Population-scale stability paper `PMC10587090` is `supporting` and directly
  overlaps the proposed contribution: it evaluates runner-up correlation margins,
  leave-one-gene-cluster-out stability, stable/prototypical labels, and refined
  single-sample centroids in 6,233 tumors. Its perturbations are biological-module
  deletions rather than calibrated technical error, and the method lacks independent
  validation and a prespecified abstention rule.
- BreastSubtypeR paper `PMC12501779` is `supporting`. It unifies ten classifiers,
  reproduces original outputs, computes inter-method entropy, and performs
  cohort-aware method selection. AUTO is not patient-independent, and entropy is
  not calibrated to classification error or abstention.
- All seven retrieved CC-BY priority papers are now appraised: five supporting,
  two context-only, and zero anchor studies.
- A governed read-only review receipt is implemented for lawfully viewable content
  that may not be durably stored. It records identity, access terms, checksum,
  access time, and verification state while mechanically prohibiting storage and
  redistribution claims. Appraisal progress distinguishes durable retrieval from
  read-only review and allows a storage restriction to coexist with completed
  ephemeral appraisal.
- Five governed read-only reviews are complete. PBCMC directly establishes
  single-subject empirical permutation confidence, false-discovery control, a
  runner-up margin, and Assigned/Ambiguous/Not Assigned states as prior art. Its
  gene-label null does not estimate repeatability under independently measured
  technical error, and its thresholds lack unchanged external validation.
- The AIMS publisher record is identity-verified and subscription-restricted.
  No paywall was bypassed, no full text was stored, and no appraisal was inferred
  from the abstract. All 13 priority records therefore reconcile to 12 completed
  appraisals and one explicit access restriction: nine supporting, three
  context-only, and zero anchor studies.
- Living manuscript `0.8.0-working` contains traceable Phase 0 methods,
  all 12 completed appraisals, an evidence-to-text ledger, explicit interpretation
  labels, and prohibited placeholders for NaS results and conclusions.
- The remaining-queue founder packet covers every one of the 87 pending records
  exactly once. It proposes 17 inclusions and 70 exclusions, preserving the
  30-record evidence cap when combined with the 13 priority records. Five
  author-year-only reconciliation candidates are documented as false-positive
  identity links. No recommendation has been submitted as a founder decision.
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

1. Founder-confirm or edit
   `literature/FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md`, including the five
   rejected author-year links, 17 proposed inclusions, and 70 proposed exclusions;
   then submit and verify the append-only decision batch.
2. Execute sequential backward-plus-forward Europe PMC citation passes until two
   consecutive complete passes add zero eligible methods or external validations.
3. Update the living manuscript and its evidence-to-text ledger after every material
   appraisal, protocol decision, executed analysis, figure, and review decision.
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

### 2026-07-24 — Remaining 87 records screened for founder review

Completed a protocol-grounded advisory title/abstract pass for every pending record
in the revised 100-record queue. The founder packet proposes 17 inclusions and 70
exclusions, covers record numbers 1 through 87 exactly once, and documents a
primary exclusion reason for every exclusion. Combined with the 13 priority
inclusions, the recommendation preserves the locked 30-study evidence cap.

The packet also recommends rejecting all five author-year-only prior-inventory
links because their PMIDs and titles differ and the match signal is only a common
surname and year. The packet is deliberately nonbinding: no immutable founder
decision event was written, and tests mechanically prevent incomplete record
coverage from passing unnoticed.

### 2026-07-24 — Direct-priority evidence set terminally resolved

Completed five governed read-only appraisals and recorded the AIMS article as an
identity-verified subscription restriction. All 13 direct-priority records now
have a terminal state: 12 completed appraisals and one access restriction, with no
paywall circumvention or restricted full text retained.

PBCMC is the most important novelty correction. It already implements per-patient
permutation confidence, false-discovery control, a runner-up margin, and explicit
Assigned, Ambiguous, and Not Assigned states. NaS therefore cannot claim uncertainty
or abstention alone. The surviving candidate contribution is narrower: an unchanged
patient-independent classifier whose reliability is calibrated to independently
measured technical error, prespecified without outcome tuning, and externally
validated. No reviewed priority paper is anchor evidence.

### 2026-07-24 — Governed read-only evidence appraisal implemented

Implemented a separate, auditable receipt for lawfully viewable articles whose
terms do not authorize durable full-text storage. The receipt retains only article
identity, source and rights metadata, access timestamps, byte count, an ephemeral
content checksum, code revision, and verification flags. Its contract rejects any
claim that content was stored, redistribution was authorized, or scientific
conclusions were drawn by the receipt itself.

Appraisal reconciliation now accepts exactly one evidence source state: a verified
durable CC-BY retrieval or a verified ephemeral read-only receipt. A prior
restricted-storage decision may coexist with read-only review, while durable
retrieval and read-only review for the same record are rejected. Progress reports
the two modes separately and requires every completed appraisal to match the exact
source URL and checksum. The CLI validates read-only receipts and automatically
includes them in progress generation. The complete test, lint, and type-check suite
passes.

### 2026-07-24 — All accessible priority evidence appraised

Completed the question-specific appraisal of verified CC-BY paper `PMC12501779`
as `supporting` evidence, bringing the accessible priority set to seven of seven
complete. BreastSubtypeR unifies ten published classifiers, reproduces original
implementations, exposes separate calls and inter-method entropy, and provides
cohort-aware method selection through a versioned Bioconductor package.

This removes generic multi-method comparison and discordance entropy as standalone
NaS novelty claims. AUTO depends on cohort composition, its thresholds are developed
substantially within SCAN-B, and entropy is not calibrated to patient-level error
or abstention. Across the seven appraisals, five records are supporting, two are
context-only, and none qualifies as anchor evidence.

### 2026-07-24 — Population-scale PAM50 stability appraised

Completed the question-specific appraisal of verified CC-BY paper `PMC10587090`
as `supporting` evidence. In 6,233 SCAN-B tumors, the study directly analyzes the
leading-versus-runner-up correlation delta, removes seven co-expression modules
one at a time, identifies perturbation-stable tumors, and derives refined
single-sample centroids from stable cases.

This substantially overlaps the NaS proposal. Margin reporting, perturbation
testing, and stable/prototypical labeling cannot be claimed as novel alone. The
remaining distinction is narrow but testable: published perturbations remove
biological modules rather than model independently measured technical error, the
refined method lacks independent replication, and no calibrated reliability
probability or prespecified abstention threshold is validated.

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
  complete. The remaining 87-record advisory screen awaits founder confirmation;
  full-text appraisal of new inclusions and the citation-chain stopping rule remain
  incomplete.
- AIMS is identity-verified at the publisher but subscription-restricted. Its
  full text cannot be appraised unless the founder supplies lawful access; the
  evidence review must retain this limitation and cannot infer novelty from it.
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
- Lawfully viewable articles without durable-storage authorization may be appraised
  only through an ephemeral read-only receipt. The content is not retained; the
  receipt records source identity, access basis, rights observation, checksum, and
  verification state, and never grants redistribution rights.
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
