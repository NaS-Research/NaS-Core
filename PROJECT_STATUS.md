# NaS Core Project Status

Last updated: 2026-07-24

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Appraise the remaining accessible NAS-BRCA-002 priority evidence

The question-`0.3.0` review is authorized and active. Founder batch
`b0c31f7e…00945f` advances all 13 direct-priority records to full-text review.
Seven have verified CC-BY full text; three question-specific appraisals are
complete. Four are restricted or unavailable through the approved endpoint, and
two require a lawful alternative source. Appraise the remaining four accessible
papers, resolve access where possible, then screen the remaining 87 candidates.

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
- The priority access inventory reconciles all 13 inclusions: 7 verified CC-BY full
  texts, 4 restricted or repository-unavailable records, and 2 records without a
  verified lawful full-text source. No restricted text was stored.
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
- Living manuscript `0.2.0-working` contains traceable Phase 0 methods,
  the three completed appraisals, an evidence-to-text ledger, explicit interpretation
  labels, and prohibited placeholders for NaS results and conclusions.
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

1. Complete question-`0.3.0` full-text appraisal of the four remaining verified
   CC-BY priority papers, next addressing the improved absolute single-sample
   classifier (`PMC7761033`).
2. Update the living manuscript and its evidence-to-text ledger after every material
   appraisal, protocol decision, executed analysis, figure, and review decision.
3. Pursue lawful access for AIMS (PMID `25479802`) and the single-subject uncertainty
   method (PMID `28062443`) without paywall circumvention or unlicensed storage.
4. Founder-confirm or reject the five author-year-only inventory links, then screen
   every remaining record in the 100-record revised queue.
5. Execute sequential backward-plus-forward Europe PMC citation passes until two
   consecutive complete passes add zero eligible methods or external validations.
6. Resolve and approve the exact centroid and external-reference artifacts,
   redistribution rights, expression transformations, and numerical tolerances.
7. Define an independently calibrated technical-error model and lock the margin
   and canonical-label-retention thresholds without molecular or outcome inspection.
8. Verify TCGA receptor-field completeness and PAM50 gene coverage in TCGA and
   GSE96058 through logged metadata-only queries.
9. Complete the founder scientific/product, molecular/pathology, and statistical
   reviews for question `0.3.0`, then record a new gate decision.
10. Complete the NAS-BRCA-001 founder results review and authorize, hold, or reject
   a transparent versioned remediation.
11. If authorized, remediate only declared NAS-BRCA-001 technical defects and
   preserve the original immutable run.
12. Implement persisted evidence claims, citations, provenance, contradictory
   evidence, null findings, limitations, and review state.
13. Add license-aware permitted passage ingestion and hybrid keyword and semantic
   retrieval after the Phase 0 evidence inventory is screened.
14. Expand the screening model gateway into general evidence reasoning with
   minimum-necessary context, citations, uncertainty, abstention, and governance.
15. Build evaluation suites for retrieval, citation validity, numerical
   fidelity, unsupported claims, and appropriate abstention.
16. Generate an immutable research release containing the protocol, dataset
   manifest, code revision, environment, results, figures, literature,
   limitations, approvals, and disclosures.
17. Generate a reviewable white-paper draft whose substantive claims trace to
   executed artifacts, external sources, or labeled interpretation.
18. Build the internal workbench for projects, protocols, datasets, runs,
   evidence review, and publication releases.
19. Complete repeated internal oncology pilots before selecting the first
    external commercial product surface.

## Recently completed

### 2026-07-24 — RNA-seq reference sensitivity appraised

Completed the question-specific appraisal of verified CC-BY paper `PMC7442834`
as `supporting` evidence. In 4,731 public RNA-seq tumors, the study directly
demonstrates dependence of standard PAM50 calls on reference construction,
reports substantially higher pairwise stability from AWCA centering, and tests
precomputed RSEM- and FPKM-matched references plus regularized multiclass
logistic-regression classifiers on additional datasets.

The study is not anchor evidence. Published PAM50 labels are a technical
benchmark rather than a biological gold standard, possible TCGA/PanCancer
sample overlap is unresolved, reference transport remains preprocessing-specific,
and small exploratory prognostic comparisons do not establish clinical validity
or utility. The living manuscript and evidence ledger now preserve both the
positive implementation evidence and those limitations.

### 2026-07-24 — Governed living manuscript initialized

Created the dedicated NAS-BRCA-002 manuscript workspace and seeded working version
`0.1.0` with the study boundary, Phase 0 literature methods, the first two completed
appraisals, limitations, references, and an evidence-to-text ledger. The draft
strictly separates external literature from NaS-generated results and labels the
current discussion as provisional interpretation.

Abstract, NaS analytical results, and conclusions remain explicit prohibited
placeholders because molecular and outcome access, method lock, preregistration,
analysis, and review are incomplete. The manuscript rulebook requires an update
after each material appraisal or research artifact and permits publication only
from a frozen research release.

### 2026-07-24 — Subgroup-specific centering appraised

Completed the question-specific appraisal of verified CC-BY paper `PMC4365540`.
The method directly shows that standard cohort median centering can produce radically
different PAM50 assignments when a study cohort is clinically skewed. Its proposed
percentile correction improved agreement within selected UNC subgroups and shifted
two small external cohorts toward clinically expected subtype proportions.

The paper is `context_only`. Development and most accuracy testing reuse the PAM50
training resource, external comparators do not establish independent molecular
truth, and the method requires clinicopathological composition plus sufficient
cohort size. The authors explicitly state it is unsuitable for a one-patient
dataset. It strengthens the rationale for a patient-independent external reference
but cannot serve as that reference or validate the NaS procedure.

### 2026-07-24 — Measurement-uncertainty evidence appraised

Locked question-`0.3.0` full-text appraisal protocol `1.1.0` and completed the first
revised appraisal against the verified CC-BY text of `PMC3275466`. The paper is
eligible and directly relevant: it models how laboratory measurement error can
alter PAM50 calls and proposes patient-level uncertainty reporting.

The record is `context_only`, not anchor or supporting evidence. Its error model
comes from 12 replicates of four archetypal specimens, assumes Gaussian independent
gene errors, is applied to independent tumors by simulation rather than repeat
measurement, lacks external laboratory/platform validation, and contains a material
100,000-versus-1,000 simulation-count inconsistency. It demonstrates the problem and
narrows novelty, but does not provide the independently calibrated, transportable
error model required by the proposed NaS method.

### 2026-07-24 — Founder priority batch and lawful-access inventory completed

Recorded and independently verified the first question-`0.3.0` append-only founder
batch: 13 direct-priority inclusions, 87 pending records, zero exclusions, zero
unclear, and zero AI decisions. Updated the typed priority set and evidence-review
ledger without carrying forward question-`0.2.0` decisions.

Built and persisted the 13-paper access inventory. Seven Europe PMC full texts
passed exact article identity, approved CC-BY license, checksum, and size
verification. Four records are restricted or unavailable through the approved
endpoint, and two have no verified repository full text. Restricted material was
not stored. The reconciled appraisal ledger reports 7 retrieved, 4 restricted,
2 awaiting lawful access, and 0 question-specific appraisals complete.

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
- AIMS and the single-subject PAM50 uncertainty paper do not have a verified PMCID
  in the locked snapshot. Lawful full-text access remains unresolved.
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
