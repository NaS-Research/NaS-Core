# NaS Core Project Status

Last updated: 2026-07-21

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Implement the prespecified NAS-BRCA-001 survival analysis pipeline

Implement the deterministic statistical pipeline against founder-approved,
immutable cohort build `73bfc986…d2e53`. Produce the protocol-specified primary,
secondary, diagnostic, and sensitivity results without changing the frozen
cohort or inventing conclusions through a language model.

Definition of done:

- Load only the approved cohort receipt and fail closed unless its gate and
  required founder review are approved and its external artifacts reverify.
- Implement the prespecified descriptive, Kaplan–Meier, log-rank, and Cox models
  with their declared reference groups, covariates, estimands, and alpha.
- Implement proportional-hazards diagnostics and all prespecified sensitivity
  analyses, including five-year censoring, nonlinear age, and AJCC edition.
- Capture dependency versions, code revision, parameters, seeds, warnings,
  model failures, tables, figures, effect sizes, confidence intervals, and p-values.
- Preserve null, contradictory, unstable, and failed results alongside positive findings.
- Write a content-addressed immutable run manifest and verify every output checksum.
- Cover statistical transformations, gate failures, edge cases, and deterministic
  reruns with synthetic tests before executing the real analysis.

Current gate state:

- Protocol tag: `NAS-BRCA-001-protocol-v1.1.0` complete.
- Data Release 45 snapshot and deterministic cohort build: complete and verified.
- Founder cohort-QA approval: recorded for build `73bfc986…d2e53`.
- Frozen cohort tag: `NAS-BRCA-001-cohort-v1.0.0` designates this approval commit.
- Outcome analysis: not started.

## Next implementation queue

1. Implement the prespecified survival analysis pipeline with
   captured code version, environment, parameters, random seeds, warnings,
   tables, figures, effect sizes, and uncertainty.
2. Execute and independently verify the immutable analysis run, then complete
   founder results review and AI-assisted statistical critique.
3. Complete structured founder review and AI-assisted critique of proposed
   `NAS-BRCA-002`, resolve its classification mapping, intended decision, claim
   boundaries, and external-validation path, then select, revise, hold, or
   reject it. Only a founder-approved selection may be marked ready for a formal
   literature-review protocol.
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

### 2026-07-21 — Founder-approved NAS-BRCA-001 cohort gate

Recorded Dalron J. Robertson's explicit approval of immutable cohort build
`73bfc986…d2e53` for prespecified modeling. The typed receipt now enforces the
approved founder self-review, timestamp, rationale, conflicts, accepted
limitations, and mandatory AJCC-edition and five-year-censoring sensitivities.
The cohort remains immutable, and any correction requires a preserved prior
build plus a new algorithm version. No outcome analysis was performed.

Validation: typed approval receipt and review record passed Ruff, strict MyPy,
and the full test suite; frozen tag `NAS-BRCA-001-cohort-v1.0.0` created from the
approval commit.

### 2026-07-21 — First governed NAS-BRCA-001 analysis cohort

Built the first immutable analysis-ready cohort from the verified Data Release
45 snapshot using only protocol `1.1.0` rules and code revision `912e281`.
Selected one primary diagnosis per case, normalized stage and survival fields,
and applied mutually exclusive exclusions with a case-level audit log. The
result contains 1,037 included cases and 61 excluded cases. Independently
recomputed the build manifest and all artifact checksums, confirmed a unique,
disjoint, complete 1,098-case partition, and recorded a typed receipt plus
AI-assisted QA review. No stage-by-outcome comparison or survival model was run.

Validation: build `73bfc986…d2e53`; cohort, exclusions, and QA artifacts verified;
Ruff, strict MyPy, and the full test suite passed.

### 2026-07-21 — First governed NAS-BRCA-001 dataset snapshot

Retrieved 1,098 public/open TCGA-BRCA case records from GDC Data Release 45.0
under preregistered protocol `1.1.0`. Stored three immutable response pages, the
GDC API status response, official Data Release notes, and the content-addressed
manifest on the marker-validated Seagate object store. Independently recomputed
all five stored-object checksums and the manifest payload checksum; every check
passed and the API returned no warnings. Added a Git-tracked provenance receipt
without patient-level fields. No cohort derivation, survival modeling, or result
inspection was performed.

Validation: snapshot `ec9cac7c…ef435`, manifest `0ea0d00b…64b7`, 1,098 records,
three pages, five verified objects, and zero warnings.

### 2026-07-21 — GDC release provenance and Seagate object storage

Separated GDC Data Release evidence from API software status in the immutable
snapshot model. Execution now requires an official HTTPS GDC release-notes URL,
verifies that its content identifies the declared release, freezes its bytes and
checksum, and rejects non-GDC hosts. Added a path-safe local filesystem
object-store adapter behind the existing replaceable storage contract, configured
this checkout to use the marker-validated Seagate data root, and preserved S3 as
the future deployment option. The Data Release 45 dry run performed no network
or storage activity; no case data was retrieved.

Validation: the Seagate root passed integrity validation; Ruff passed, strict
MyPy passed, and 71 tests passed.

### 2026-07-21 — NAS-BRCA-001 founder approval and preregistration

Recorded Dalron J. Robertson's explicit approval of protocol `1.1.0`, including
the founder/author/analyst/approver conflict and accepted limitations. Completed
the structured founder checklist, changed the plan to `preregistered`, and
advanced the machine-readable lifecycle from protocol to ingestion. No GDC case
data or outcome-bearing results were retrieved. The approved commit must be
tagged before the first network retrieval.

Validation: the preregistered plan and ingestion-stage workspace passed governed
validation; Ruff passed, strict MyPy passed, and 61 tests passed.

## Current blockers

- Docker is not currently available in the development environment, so the
  Compose services have been syntax-validated but not started locally.
- `NAS-BRCA-002` is the proposed first decision-led discovery question but
  remains unselected pending founder scientific/product, molecular/pathology,
  and statistical self-review plus AI-assisted critique; formal literature
  retrieval waits on founder approval.
- The independent external validation source for `NAS-BRCA-002` has not been
  selected or approved. Its license, compatible variables, cohort overlap, and
  export terms must be established before preregistration.
- The Seagate volume currently reports approximately 4.2 TiB available. It is
  primary local storage, not an independent backup.

## Durable decisions and boundaries

- `nas-website` and `NaS-Core` remain separate repositories.
- NaS Core begins as a modular monolith.
- OpenAI is a replaceable reasoning provider, not the NaS product or knowledge
  store.
- Numerical research results come from deterministic executed code.
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
