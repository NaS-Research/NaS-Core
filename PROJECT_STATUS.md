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
- TCGA/GDC is the proposed discovery source; the candidate independent validation
  source is unassessed and not approved in the source registry.
- Full-text progress is now mechanically reconciled: 8 of 27 founder inclusions have
  verified full text and completed appraisals. Roles are 3 supporting and 5 context-only;
  4 additional papers are access-restricted or non-open-access. No anchor
  study or scientific conclusion exists yet.
- NAS-BRCA-001 remains an immutable conditional platform-qualification pass with
  a pending founder results/remediation decision.

## Next implementation queue

1. Resolve lawful full-text access and appraise the population-based
   `Perturbation and stability of PAM50 subtyping` study, prioritizing it because
   it directly tests the proposed classification-stability question.
2. Review supporting records and citation chains until the locked stopping rule is
   satisfied; preserve eligible contradictory and null evidence regardless of rank.
3. Complete founder decisions, populate the evidence matrix, and produce a novelty
   memo with an explicit no-go test.
4. Complete discovery and validation source feasibility, including exact variable
   mappings, terms, compatibility, independence, overlap, and source-registry review.
5. Decide `go`, `change`, `hold`, or `reject`; preregister a full analysis plan only
   after a documented `go` decision.
6. Complete the NAS-BRCA-001 founder results review and authorize, hold, or reject
   a transparent versioned remediation.
7. If authorized, remediate only declared NAS-BRCA-001 technical defects and
   preserve the original immutable run.
8. Implement persisted evidence claims, citations, provenance, contradictory
   evidence, null findings, limitations, and review state.
9. Add license-aware permitted passage ingestion and hybrid keyword and semantic
   retrieval after the Phase 0 evidence inventory is screened.
10. Expand the screening model gateway into general evidence reasoning with
   minimum-necessary context, citations, uncertainty, abstention, and governance.
11. Build evaluation suites for retrieval, citation validity, numerical
   fidelity, unsupported claims, and appropriate abstention.
12. Generate an immutable research release containing the protocol, dataset
   manifest, code revision, environment, results, figures, literature,
   limitations, approvals, and disclosures.
13. Generate a reviewable white-paper draft whose substantive claims trace to
   executed artifacts, external sources, or labeled interpretation.
14. Build the internal workbench for projects, protocols, datasets, runs,
   evidence review, and publication releases.
15. Complete repeated internal oncology pilots before selecting the first
    external commercial product surface.

## Recently completed

### 2026-07-22 — Ki67 measurement variability added as context evidence

Retrieved `PMC7376512` as 180,098 bytes of official Europe PMC XML under CC BY 4.0
with SHA-256 `67c85e05…c99ef` and completed its section-located appraisal. In the
limited molecular-subtype subset, IHC surrogate Luminal A/B labels agreed with PAM50
for 55.8% of tumors using the selected hotspot score and 66.3% using global Ki67.
This is relevant evidence that measurement choices can affect clinical-versus-
molecular labeling, but it is locked as `context_only`: PAM50 was available for only
111 tumors, 22 hotspot methods were evaluated without a prespecified multiplicity
strategy, neither comparator establishes the correct discordant label, and there was
no external validation. The ledger now records 8 retrieved, 8 appraised, 4 restricted,
3 supporting, 5 context-only, and 0 anchor.

Validation: receipt identity, license/checksum binding, appraisal schema, ledger
reconciliation, Ruff, strict MyPy across 54 source files, and all 149 tests passed.

### 2026-07-22 — Cross-condition classifier exposes the single-patient gap

The planned NanoString normalization article `PMC8138885` returned 404 from Europe
PMC and official NCBI metadata reported `idIsNotOpenAccess`; no full text was stored
and a restriction now prevents retries. Advanced to `PMC5001207` (CrossLink), retrieved
110,398 bytes under CC BY 4.0 with SHA-256 `a40c55e3…953fd`, and completed its appraisal.
CrossLink is `context_only`: its class-specific k-means predictions depend on the whole
test cohort, cannot classify one patient independently, achieved 73% in its main real
true-label test, and used a 20-sample ER/PR surrogate evaluation for cross-platform PAM50.
This failure mode is relevant to the NaS reliability-layer gap but cannot support a
clinical claim. The ledger now records 7 retrieved, 7 appraised, 4 restricted,
3 supporting, 4 context-only, and 0 anchor.

Validation: restriction provenance, receipt identity, license/checksum binding,
appraisal schema, ledger reconciliation, Ruff, strict MyPy across 54 source files,
and all 147 tests passed.

### 2026-07-22 — Three-gene comparison appraised; source paper marked non-open

The planned `PMC3283537` retrieval returned 404 from Europe PMC, and official NCBI
OA metadata explicitly reported `idIsNotOpenAccess`; no full text was stored and a
machine-readable restriction now prevents retries. Advanced to the directly related
`PMC3413822`, retrieved 87,244 bytes under CC BY 4.0 with SHA-256 `8d6fbf32…c63c2`,
and completed its appraisal. The head-to-head PAM50/SCMGENE reanalysis is useful for
classifier-comparison context but cannot resolve which discordant patient-level call
is biologically correct, uses heterogeneous retrospective microarrays, and discloses
PAM50 stock/patent interests. It is locked as `context_only`. The ledger now records
6 retrieved, 6 appraised, 3 restricted, 3 supporting, 3 context-only, and 0 anchor.

Validation: restriction provenance, receipt identity, license/checksum binding,
appraisal schema, ledger reconciliation, Ruff, strict MyPy across 54 source files,
and all 145 tests passed.

### 2026-07-22 — RNA-seq PAM50 reference-sensitivity study appraised as supporting

Retrieved `PMC7442834` under CC BY 4.0 as 127,968 bytes with SHA-256
`186a84b2…6518` and completed its full-text appraisal. Across 4,731 tumors, the paper
directly tests how PAM50 reference-cohort selection changes subtype calls, replicates
the issue in TCGA and SCAN-B/GSE96058, evaluates preprocessing-matched AWCA references,
and publishes code and classifiers. It is locked as `supporting`, not anchor, because
published PAM50 calls are an imperfect and partly circular benchmark, TCGA/PanCA cohort
independence is unresolved, the approach remains preprocessing-specific, and prognostic
comparisons are exploratory. The ledger now records 5 retrieved, 5 appraised, 2 access-
restricted, 3 supporting, 2 context-only, and 0 anchor.

Validation: receipt identity, license/checksum binding, appraisal schema, ledger
reconciliation, Ruff, strict MyPy across 54 source files, and all 143 tests passed.

### 2026-07-22 — Large multi-cohort classification study appraised as supporting

Retrieved `PMC4166472` under CC BY 4.0 as 121,641 bytes with SHA-256
`de6a84bd…5014` and completed its section-located appraisal. The study spans 42 public
cohorts, actively detects duplicate records, applies trained outcome coefficients to
external datasets, compares IntClust with PAM50 and SCMGENE, responds to proportional-
hazards violations, and publishes iC10 plus annotated analysis code. It is the strongest
external-scale validation appraised so far, but remains `supporting` rather than anchor
evidence because it validates a feature-adaptive IntClust research implementation across
heterogeneous retrospective cohorts, not a fixed PAM50 assay or clinical-use workflow.
The ledger now records 4 retrieved, 4 appraised, 2 restricted, 2 supporting, 2 context-
only, and 0 anchor.

Validation: exact receipt and appraisal identity, checksum/license binding, schema and
ledger reconciliation, Ruff, strict MyPy across 54 source files, and all 141 tests passed.

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
