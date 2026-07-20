# NaS Core Project Status

Last updated: 2026-07-20

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Scientifically review and lock the first TCGA-BRCA analysis plan

Review `NAS-BRCA-001`, which tests the established association between advanced
pathologic stage and poorer overall survival using public/open TCGA-BRCA
clinical data. Resolve review comments and lock the protocol before downloading
the study dataset or inspecting final outcomes.

Definition of done:

- An independent scientific reviewer is named in the plan.
- The reviewer evaluates the question, cohort rules, diagnosis-record
  precedence, endpoint derivation, covariates, statistical model, missing-data
  plan, multiplicity rules, sensitivity analyses, and limitations.
- Every requested change is resolved in Git with a traceable protocol-version
  update when required.
- The reviewer records an approval decision and timestamp.
- The plan status changes from `pending_review` to `preregistered` and continues
  to pass `make plan-validate` and `make check`.
- The approved protocol commit is tagged before any outcome-bearing data is
  ingested.

## Next implementation queue

1. After protocol approval, tag the locked plan and execute the first GDC Data
   Release snapshot; independently verify its manifest, object checksums,
   record count, warnings, and external-drive location.
2. Implement the deterministic TCGA-BRCA cohort and analysis pipeline with
   captured code version, environment, parameters, random seeds, warnings,
   tables, figures, effect sizes, and uncertainty.
3. Independently review proposed `NAS-BRCA-002`, resolve its classification
   mapping, intended decision, claim boundaries, and external-validation path,
   then select, revise, hold, or reject it. Only an approved selection may be
   marked ready for a formal literature-review protocol.
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

### 2026-07-20 — NAS-BRCA-002 proposal-to-publication operating plan

Registered clinical-molecular subtype discordance in primary breast cancer as
the proposed first discovery study. Added its standardized study workspace,
decision-led intake, provisional 29/40 selection score, explicit nonclinical
claim boundary, independent-validation requirement, and gated plan from question
review through literature, feasibility, preregistration, ingestion, analysis,
validation, evidence release, scientific paper, website production, publication,
and correction handling. Added the proposal to oncology charter v1.1.0. It
remains unselected; no literature or biomedical data was retrieved.

Validation: the study, question, and oncology program manifests passed; Ruff
passed, strict MyPy passed, and 54 tests passed.

### 2026-07-20 — Current pipeline and decision-support translation map

Documented the complete research flow from decision-led question through
evidence, independent validation, frozen release, and impact evaluation.
Separated the current TCGA-BRCA platform-qualification outputs from patient-level
decision support and defined the user, choice, patient context, alternatives,
outcome, evidence, uncertainty, validation, and impact requirements that a
future translational study must satisfy. No clinical claim or product status was
assigned.

Validation: documentation formatting passed; Ruff passed, strict MyPy passed,
and 53 tests passed.

### 2026-07-20 — Standardized study workspaces and lifecycle pipeline

Implemented typed study and pipeline manifests, canonical JSON Schemas, a
collision-safe CLI scaffold, manifest validation, ordered stage gates, stable
artifact namespaces, and a documented boundary between versioned Git content
and external research artifacts. Migrated `NAS-BRCA-001` into the canonical
question, literature, protocol, ingestion, analysis, evidence, release, tests,
and reviews layout without changing its pending scientific-review gate. No
biomedical data was downloaded or generated.

Validation: the migrated study and analysis plan passed governance validation;
the GDC dry run performed no network or storage activity; Ruff passed, strict
MyPy passed, and 53 tests passed.

### 2026-07-20 — Biomedical data-source landscape

Documented the major candidate sources for cancer multi-omics, population
oncology, longitudinal biobanks, real-world clinical data, functional genomics,
variants, single-cell and spatial biology, imaging and pathology, drugs and
targets, trials and safety, literature, and protein structure. Added access
classes, important limitations, project-to-source examples, and the governed
workflow for promoting a candidate into the approved source registry. This was
a documentation change only: no data was downloaded and no new source was
approved.

Validation: documentation links and formatting passed; Ruff passed, strict
MyPy passed, and 48 tests passed.

### 2026-07-20 — Decision-led oncology program and pre-literature gates

Established the machine-readable NaS Oncology Research Program, separated
platform qualification from discovery and product claims, and documented stage
gates through external validation, translation, and deployment. Added a typed
research-question intake covering the intended user, decision, scientific
question, evidence needs, data feasibility, analysis family, validation path,
system output, and scientific, decision, and product success criteria. Added a
40-point selection rubric, review approval gate, literature-readiness gate,
checked-in schemas, CLI validation, topic-selection guidance, and a reproducible
literature-review template. No articles were collected and no product wedge was
assumed.

Validation: oncology program and question-template validation passed; Ruff
passed, strict MyPy passed, and 48 tests passed.

## Current blockers

- Docker is not currently available in the development environment, so the
  Compose services have been syntax-validated but not started locally.
- An independent scientific reviewer has not yet been assigned to approve and
  lock `NAS-BRCA-001`; ingestion of outcome-bearing pilot data waits on this.
- `NAS-BRCA-002` is the proposed first decision-led discovery question but
  remains unselected pending scientific/product, molecular/pathology, and
  statistical review; formal literature retrieval waits on approval.
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
- `NAS-BRCA-002` is a proposed discovery and external-validation study of
  prespecified classification disagreement. Neither receptor categories nor
  intrinsic subtypes are assumed to be a universal gold standard, and the work
  cannot support patient-level testing or treatment claims.
- Public website publication must derive from an approved frozen research
  release. The version-of-record PDF, web edition, tables, figures, citations,
  and displayed numbers must agree and follow visible versioning and correction
  procedures.
- Study plans must be typed, governance-validated, independently reviewed, and
  locked before outcome-bearing data ingestion.
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
