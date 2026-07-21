# Current NaS Research Pipeline

Last updated: 2026-07-20

This document explains the current research flow and what it is intended to
produce. Live implementation status, blockers, and the next engineering task
remain in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Machine-readable stage
status for the current study remains in
[`workflows/studies/tcga_brca_stage_survival/pipeline.yaml`](workflows/studies/tcga_brca_stage_survival/pipeline.yaml).

## Current program stage

NaS is qualifying Cortex with `NAS-BRCA-001`, a reproducibility study using
public/open TCGA-BRCA clinical data. TCGA-BRCA means the Breast Invasive
Carcinoma project; it does not mean a study limited to BRCA1 or BRCA2 variants.

The study tests whether Cortex can reproducibly recover the established
association between advanced pathologic stage and poorer overall survival while
preserving governance, provenance, uncertainty, and documented review.

This is a platform-qualification study. It is not a patient-level prediction,
treatment recommendation, clinical validation, or medical device.

## End-to-end flow

```text
1. Decision and question
   Define who needs to decide what, the population, outcome, and intended use.
        ↓
2. Evidence and protocol
   Review prior evidence and lock hypotheses, cohort rules, endpoints, models,
   sensitivity analyses, limitations, and success criteria before final results.
        ↓
3. Governed ingestion
   Approve each source; freeze the exact query, release, identifiers, timestamps,
   raw response, checksums, classification, and storage locations.
        ↓
4. Cohort construction and quality control
   Apply deterministic inclusion, exclusion, variable-derivation, missingness,
   and record-selection rules; retain a complete cohort-flow audit.
        ↓
5. Deterministic analysis
   Execute reviewed statistical or machine-learning code; capture code revision,
   environment, parameters, seeds, warnings, tables, figures, and diagnostics.
        ↓
6. Evidence assembly
   Link every claim to an executed result or approved external source; preserve
   contradictory evidence, null findings, uncertainty, and limitations.
        ↓
7. Independent data validation and documented review
   Test robustness in an independent population or setting, complete structured
   founder review, and resolve scientific, clinical, governance, and product findings.
        ↓
8. Frozen research release
   Freeze the protocol, snapshots, code, environment, results, evidence,
   approvals, limitations, disclosures, and a human-readable report.
        ↓
9. Translation and impact evaluation
   Only validated evidence may be converted into a decision-support output, then
   evaluated for safety, calibration, workflow utility, and real-world impact.
```

## What `NAS-BRCA-001` will produce

- a founder-reviewed, approved, and preregistered analysis plan with disclosed provenance;
- an immutable GDC query, data-release record, response, manifest, and checksums;
- a deterministic participant cohort and record-level exclusion audit;
- missing-data and baseline-characteristic tables;
- Kaplan-Meier survival estimates with numbers at risk;
- adjusted and unadjusted Cox proportional-hazards results;
- hazard ratios, confidence intervals, p-values, and effect direction;
- proportional-hazards, convergence, and influence diagnostics;
- prespecified sensitivity analyses, including null or contradictory findings;
- a machine-readable run manifest with code and environment provenance; and
- a founder-approved frozen qualification release, with any external expert
  feedback recorded separately.

The end of this study is a pass, conditional pass, or fail decision about the
research platform. A technically correct hazard ratio is not the final NaS
product and is not enough to guide an individual patient's care.

## How research becomes better decision information

NaS improves decisions only when a later study connects evidence to a defined
choice. A future breast-oncology project must specify all of the following:

| Required element | Example |
| --- | --- |
| Intended user | Breast oncologist and multidisciplinary tumor board |
| Decision | Whether additional testing, surveillance, treatment, or trial review is warranted |
| Patient context | Disease subtype, stage, prior therapy, biomarkers, comorbidities, and preferences |
| Alternatives | The actual clinically available options being compared |
| Outcome | Recurrence, response, progression, toxicity, survival, or quality of life |
| Evidence | Molecular, clinical, treatment, longitudinal outcome, and literature evidence |
| Output | Risk estimate, treatment-effect estimate, evidence summary, or trial-match rationale |
| Uncertainty | Confidence intervals, missingness, applicability limits, and abstention conditions |
| Validation | Independent, temporal, multisite, clinical, and prospective evaluation as appropriate |
| Impact test | Whether the output safely improves the intended decision and meaningful outcomes |

A possible future interaction looks like this:

```text
patient and disease context
        +
available clinical choices
        +
validated molecular and real-world evidence
        ↓
NaS decision-support output
  - estimated outcomes for relevant choices
  - supporting and conflicting evidence
  - applicability and uncertainty
  - missing information and abstention
        ↓
clinician and patient deliberation
        ↓
documented decision and outcome feedback
```

The system supports a human decision; it does not autonomously prescribe care.
Before clinical use, the output would require fit-for-purpose data, external and
clinical validation, safety and bias evaluation, appropriate regulatory and
quality review, workflow testing, monitoring, and organizational authorization.

## The role of AI

AI can retrieve literature, organize evidence, compare findings, inspect
protocol consistency, assist with reviewed code, explain results, draft reports,
and identify uncertainty. It receives selected source passages and compact
derived results—not an uncontrolled dump of raw patient or genomic data.

Deterministic executed code produces research numbers. Validated analytical or
predictive models may later estimate patient-relevant outcomes. The language
model is the reasoning and communication layer, not the source of numerical
truth and not an independent clinical decision-maker.

## Current gate and next action

`NAS-BRCA-001` is currently at the **protocol** stage. The next action is for
Dalron J. Robertson to complete the structured founder protocol review, use the
AI-assisted review as non-authoritative critique, resolve all findings, record
the founder approval, and lock and tag the analysis plan. Outcome-bearing
ingestion remains blocked until that gate is complete.

NaS has registered `NAS-BRCA-002`, robust and unstable PAM50 molecular
reclassification in clinically HR-positive/HER2-negative breast cancer, as the
proposed first discovery study. Its detailed
[project-to-publication plan](workflows/studies/breast_clinical_molecular_discordance/PROJECT_PLAN.md)
covers selection through external validation, frozen release, paper review, and
publication on `nasresearch.bio`.

`NAS-BRCA-002` is not yet selected. Structured founder review and AI-assisted
critique may proceed while qualification is completed, but literature retrieval
and data analysis remain gated. That study—not `NAS-BRCA-001`—would begin the
work toward a validated precision-medicine decision-support output.
