# NaS Core Project Status

Last updated: 2026-07-21

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Implement release provenance and capture the first governed snapshot

With `NAS-BRCA-001` protocol `1.1.0` founder-approved and preregistered, complete
the ingestion controls required to retrieve the exact public/open GDC clinical
snapshot without overstating its Data Release provenance.

Definition of done:

- The approved protocol commit is tagged before network retrieval.
- The snapshot records an official GDC Data Release reference and checksum
  separately from the API software status.
- The exact paginated requests, raw response bytes, warnings, case identifiers,
  retrieval time, object locations, and checksums are frozen.
- Source governance remains `public_open` and only approved clinical fields are requested.
- Synthetic tests prove preregistration enforcement, immutable writes,
  pagination consistency, release provenance, and duplicate-case rejection.
- The real snapshot is stored under the `NAS-BRCA-001` external artifact
  namespace and its manifest is independently rechecked before cohort building.

Current gate state:

- Protocol `1.1.0`: founder-approved and preregistered.
- Protocol tag: `NAS-BRCA-001-protocol-v1.1.0` identifies the approval commit.
- Data Release provenance: implemented and tested against official GDC-host references.
- Seagate filesystem object store: configured and marker-validated.
- First real snapshot: ready to execute; no case data has yet been retrieved.

## Next implementation queue

1. Complete and test Data Release provenance, tag the locked protocol, execute
   the first GDC snapshot, and independently verify its manifest, checksums,
   record count, warnings, and external-drive location.
2. Implement the deterministic TCGA-BRCA cohort and analysis pipeline with
   captured code version, environment, parameters, random seeds, warnings,
   tables, figures, effect sizes, and uncertainty.
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

### 2026-07-21 — NAS-BRCA-001 adversarial protocol review

Completed the non-authoritative AI-assisted review without retrieving GDC case
data or inspecting outcomes. Revised the pending protocol to version `1.1.0` to
use GDC's primary-disease diagnosis flag, deterministic diagnosis identifiers,
a verified diagnosis time-origin rule, positive survival durations, AJCC edition
provenance, explicit model-failure thresholds, nonlinear-age and stage-edition
sensitivities, and prespecified scientific-reproduction and Cortex qualification
outcomes. Added the full finding-resolution record and a founder review
checklist. The protocol remains unapproved and ingestion remains blocked.

Validation: protocol `1.1.0` and the study workspace passed governed validation;
Ruff passed, strict MyPy passed, and 61 tests passed.

### 2026-07-20 — Founder-led research review and publication governance

Aligned NaS Core with the present one-person operating reality. Added typed
review provenance for founder self-review, AI-assisted advisory review,
independent human expert feedback, and journal peer review. Founder approval may
authorize an internal gate when conflicts and limitations are disclosed; AI can
identify issues but cannot approve or authorize any gate. Updated both breast
cancer studies, templates, policies, publication states, and public-disclosure
requirements. External dataset validation remains scientifically independent,
while external expert critique is planned near manuscript completion and remains
distinct from journal peer review. No study gate was approved and no biomedical
data was retrieved as part of this implementation.

Validation: the question template, both study workspaces, the oncology charter,
and the analysis plan passed governed validation; Ruff passed, strict MyPy
passed, and 61 tests passed.

### 2026-07-20 — NAS-BRCA-002 proposal-to-publication operating plan

Registered PAM50 classification stability in clinically HR-positive/HER2-negative
breast cancer as the proposed first discovery study. Added its standardized study
workspace, decision-led intake, provisional 30/40 selection score, explicit
nonclinical claim boundary, independent-validation requirement, and gated plan from question
review through literature, feasibility, preregistration, ingestion, analysis,
validation, evidence release, scientific paper, website production, publication,
and correction handling. Added a human-readable live phase tracker, current
blockers, immediate queue, and evidence requirement alongside the
machine-readable lifecycle. Added the proposal to oncology charter v1.1.0. It
remains unselected; no literature or biomedical data was retrieved.

Phase 1 preparation: narrowed question version 0.2.0 to distinguish robust
non-luminal biology from unstable classification and added a structured reviewer
packet covering scientific/product, molecular/pathology, statistical, governance,
and publication gates. Added a task-level Phase 1 execution board, decision
paths, review agenda, implemented-versus-deferred boundary, validation commands,
and objective definition of done. Tightened lifecycle enforcement so every
recorded gate-required review must be approved before selection or literature
work. Dalron J. Robertson is recorded as Founder and Study Lead; Phase 1 task
P1.4 is complete. The newer founder-led governance entry above supersedes the
original multi-reviewer staffing assumption.

Validation: the study, question, and oncology program manifests passed; Ruff
passed, strict MyPy passed, and 55 tests passed.

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
