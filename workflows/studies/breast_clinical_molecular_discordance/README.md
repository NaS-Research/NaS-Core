# NAS-BRCA-002: Single-Sample PAM50 Reliability

**Reliability and Abstention in HR-Positive/HER2-Negative Breast Cancer**

This directory contains versioned definitions, deterministic code, tests, and
reviews for one NaS study. It must not contain raw data, credentials, PHI,
embeddings, model weights, or generated research artifacts.

## Identity

- Program: `NAS-ONC-001`
- Role: `discovery`
- Artifact namespace: `studies/NAS-BRCA-002`

Update `pipeline.yaml` only when a stage's completion gate is supported by
reviewed artifacts. Large artifacts belong under `NAS_DATA_ROOT`, keyed by the
artifact namespace and immutable snapshot, run, or release identifiers.

## Current state

The project remains at the question stage. Version `0.2.0` received changes
requested and is preserved; version `0.3.0` is now the active proposed revision.
Read the
[project-to-publication plan](PROJECT_PLAN.md), the draft
[research-question intake](question/research_question.yaml), its
[change-resolution trace](reviews/QUESTION_v0.3.0_CHANGE_RESOLUTION.md), the bounded
[Phase 0 plan](question/phase_zero_plan.yaml), and the non-authoritative
[AI question review](reviews/AI_QUESTION_REVIEW_v0.2.0.md).

The founder authorized the bounded Phase 0 novelty and feasibility audit on
2026-07-22. That audit produced a `change` decision on 2026-07-23 because direct
prior work substantially overlaps the broad stability thesis. TCGA discovery and
processed SCAN-B GSE96058 validation paths are mapped, but biomedical outcome
ingestion, molecular or survival analysis, preregistration, novelty claims, and
clinical claims remain prohibited until a revised question passes review.

Question `0.3.0` now has a governed
[living manuscript](manuscript/WORKING_MANUSCRIPT.md). It contains traceable Phase 0
methods and evidence-appraisal text only. All seven verified CC-BY priority papers
are appraised: two are context-only and five are supporting. Four priority records
are access-restricted and two still require a verified lawful source. The reviewed
evidence leaves only a narrow technical-calibration and abstention question.
Unsupported analysis, results, and conclusions remain explicit placeholders.

Founder-authorized field-isolated metadata audit `1.0.1` now closes the bounded
input-feasibility gate: both sources contain all 50 historical PAM50 genes,
receptor completeness is quantified, and all 136 GSE96058 technical replicates
link to 3,273 primary records with zero unclassified records. This does not
authorize cohort construction, molecular or outcome analysis, classifier
execution, or clinical conclusions.
