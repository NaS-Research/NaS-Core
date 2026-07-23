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
- Full-text progress is now mechanically reconciled: 2 of 27 founder inclusions have
  verified full text and completed appraisals. `PMC10587090` is supporting evidence;
  `PMC3275466` is context-only evidence because its modeled uncertainty lacks empirical
  external validation. No anchor study or scientific conclusion exists yet.
- NAS-BRCA-001 remains an immutable conditional platform-qualification pass with
  a pending founder results/remediation decision.

## Next implementation queue

1. Retrieve and appraise the next high-value lawful full text, prioritizing the
   contemporary intrinsic-subtyping robustness study `PMC10052604` if its exact
   identity and item-level license pass the governed checks.
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

### 2026-07-22 — Classification-uncertainty paper appraised as context-only

Completed the full-text appraisal of `PMC3275466`, an analytical-validation study
using Monte Carlo perturbation to characterize PAM50 uncertainty. It is eligible for
problem framing but locked as `context_only`: the central error model was estimated
from 12 replicates of four archetypal specimens, assumes gene-wise Gaussian measurement
errors, and was applied to 847 independent GEICAM tumors without empirical repeat
testing of those tumors. Reported simulation counts are also inconsistent between the
methods/results text and Figure 3 caption. The record transparently reports the PAM50
inventor/licensing conflict and AI-assisted appraisal boundary. The progress ledger now
reconciles 2 retrieved and 2 appraised papers: 1 supporting, 1 context-only, 0 anchor.

Validation: exact full-text identity and checksum binding, appraisal schema validation,
ledger reconciliation, Ruff, strict MyPy across 54 source files, and all 136 tests passed.

### 2026-07-22 — Second verified full text and version-aware CC BY policy

The next direct classification-uncertainty paper, `PMC3275466`, declared CC BY 2.0
rather than CC BY 4.0, so the first governed attempt failed closed and stored no
artifact. Expanded the explicit allowlist to standard CC BY 2.0, 2.5, 3.0, and 4.0
licenses, with canonical SPDX identifiers and URLs; restrictive or ambiguous licenses
remain rejected. After tests and push of revision `967b94c`, retrieved and independently
verified the 72,003-byte article with SHA-256 `a09221f7…2481e`. The progress ledger now
records 2 full texts retrieved and 1 of 27 appraisals complete. No evidence role or
scientific conclusion was assigned to the second paper.

Validation: Ruff, strict MyPy across 54 source files, all 135 tests, the checked-in
receipt contract, and reconciled progress passed.

### 2026-07-22 — First full-text appraisal and resumable progress ledger

Completed a section-located methodological appraisal of `PMC10587090`. The study is
eligible as `supporting` evidence, not anchor evidence: its large population-based
cohort and systematic PAM50 perturbation are valuable, while complete-case selection,
bulk-tissue heterogeneity, incomplete multiplicity/model-diagnostic reporting, and
the absence of independent end-to-end validation limit its role. AI assistance is
explicitly disclosed, founder authorization is required, and the record itself draws
no scientific conclusion. Implemented a deterministic progress ledger that derives
state from the verified 27-record founder inclusion set, full-text receipts, and
completed appraisals; rejects missing receipts, duplicates, identity/checksum drift,
stale screening state, and invalid verification flags; and reports 1 of 27 complete.

Validation: appraisal schema validation, Ruff, strict MyPy across 54 source files,
and all 133 tests passed.

### 2026-07-22 — First verified licensed full-text artifact

Retrieved `PMC10587090`, “Perturbation and stability of PAM50 subtyping in
population-based primary invasive breast cancer,” from the official Europe PMC XML
endpoint using pushed engine revision `42d9752`. Item-level metadata explicitly
declares CC BY 4.0. The 137,087-byte XML and hashed manifest are immutable outside
Git; the aggregate receipt records SHA-256 `2ca3db6f…0e2a`. Independent verification
reloaded both artifacts and rechecked size, checksum, PMCID, PMID, DOI, bounded title
normalization, license URL/text, copyright, and the no-conclusion boundary. Two
failed attempts—incorrect Accept header and terminal-title punctuation—stored no
artifact and prompted tested, pushed fixes before retry. No quality role or
scientific conclusion was assigned.

Validation: checked-in receipt contract, immutable artifact verification, Ruff,
strict MyPy, study validation, and all 129 tests passed.

### 2026-07-22 — License-enforced immutable full-text retriever

Implemented one-record-at-a-time retrieval from the official Europe PMC full-text
endpoint for current founder inclusions. The engine requires an explicit PMCID,
allowlists CC BY 4.0 only, and verifies PMCID, PMID, DOI, exact title, license URL,
license text, and copyright statement before storing content. Raw XML and a hashed
manifest remain immutable in external object storage. Verification independently
reloads both artifacts, rechecks size, checksums, identity, license, and the no-
conclusion boundary, and emits only an aggregate Git receipt. Missing, ambiguous,
restricted, or altered content fails closed. Founder authorization is recorded;
no real durable full text was retrieved before the engine revision was pushed.

Validation: synthetic licensed retrieval, unapproved-license rejection, tamper
detection, Ruff, strict MyPy, and all 127 tests passed.

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
