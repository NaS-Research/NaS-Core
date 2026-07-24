# NAS-BRCA-002 Question 0.3.0 Screening Protocol

Version: `1.1.0`

Input execution: `a2500aba…f1ea9f`

Input queue: `af08a334…8a2a3`

Status: **Locked before question-0.3.0 title/abstract decisions**

## Objective

Identify methodological records requiring full-text review for the fixed
single-sample PAM50 reliability and abstention question. Screening selects evidence;
it does not synthesize findings, establish novelty, or authorize molecular or
outcome analysis.

## Inclusion criteria

Use `include` when the title or abstract plausibly addresses at least one domain:

1. a fixed or absolute single-sample intrinsic-subtype classifier;
2. patient-level margin, ambiguity, uncertainty, unclassifiable state, or abstention;
3. technical measurement error, perturbation, repeatability, or label retention;
4. PAM50 reference construction, centering, transformation, mapping, or test-set bias;
5. unchanged external transport across cohorts, laboratories, or platforms; or
6. executable software exposing classifier assumptions and implementation artifacts.

The record must concern human breast-tumor gene-expression classification or a
directly applicable analytical method. Outcomes may be reported by a method paper,
but an outcome association alone is insufficient.

## Decisions

Each of the 100 records receives exactly one founder decision:

- `include`: plausibly meets an inclusion criterion and advances to full-text review;
- `exclude`: clearly fails the question-0.3.0 criteria and receives one primary reason;
- `unclear`: metadata are insufficient or conflicting and require manual resolution;
- `pending`: no founder decision has been recorded.

When uncertain, use `unclear`, not `exclude`. Journal, prestige, citation count,
author identity, and direction of findings are not eligibility criteria.

## Ordered exclusion taxonomy

1. `nonhuman_or_no_primary_human_tumor_cohort`
2. `no_molecular_intrinsic_subtype_measure`
3. `no_relevant_discordance_stability_or_classifier_method`
4. `review_editorial_or_commentary_for_citation_chaining_only`
5. `duplicate_or_superseded_report_without_distinct_contribution`
6. `outside_breast_cancer_scope`

Missing full text, uncertain cohort overlap, or uncertain assay detail is not a
title/abstract exclusion reason. Use `unclear`.

## Founder and AI roles

Dalron J. Robertson records every final decision. AI recommendations are advisory,
must state their rationale and confidence, and cannot populate the immutable founder
decision event. Previous question-0.2.0 decisions do not transfer.

## Full-text gate

Every included record advances to lawful-access assessment and versioned appraisal.
Related reports are linked rather than discarded when they provide distinct methods,
calibration, validation, software, or failure evidence.

## Completion gate

Screening is complete only when all 100 records have final founder decisions, no
record remains pending or unresolved, exclusion reasons reconcile, and the
append-only progress manifest is independently verified. Completion does not
establish novelty or authorize data analysis.
