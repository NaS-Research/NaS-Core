# A Patient-Independent Reliability and Abstention Framework for PAM50 Breast Cancer Subtyping

Working title—subject to revision after the evidence gate.

Manuscript version: `0.1.0-working`

Study: `NAS-BRCA-002`

Question version: `0.3.0`

Last updated: 2026-07-24

Overall status: **working—evidence review incomplete; molecular and outcome data not accessed**

## Abstract

Status: `placeholder`

The abstract will be written after the evidence review, method lock, preregistration,
executed analysis, sensitivity analyses, and internal review. No results or conclusions
are currently authorized.

## Introduction

Status: `working`

Gene-expression intrinsic subtyping is widely used in breast cancer research, with
PAM50 assigning a tumor to the most correlated subtype centroid. Published methods
show that an individual assignment may depend not only on the tumor’s expression
profile but also on measurement error, preprocessing, and the composition of other
samples used for gene centering. These dependencies complicate reproducible
interpretation when a classifier is expected to operate on one patient independently.
[PMID:22196354; PMID:25849221]

Two distinct problems are relevant. First, laboratory measurement uncertainty can
perturb gene-expression values and change a non-archetypal tumor’s assigned subtype.
Second, centering a clinically skewed cohort against its own gene-expression
distribution can produce materially different calls from those obtained in a
representative training population. Existing solutions demonstrate the importance
of both problems, but the reviewed implementations do not yet provide an independently
calibrated, fixed, cross-platform reliability rule that can be executed for one
patient without adapting to a test cohort. [Appraisals: PMC3275466-v1.0.0;
PMC4365540-v1.0.0]

This study is therefore evaluating a narrower methodological question: whether a
fully specified, patient-independent research implementation can report the leading
and runner-up PAM50 scores, their margin, perturbation repeatability, data-quality
state, and an explicit reliability or abstention state. The intended contribution
is analytical reliability and transparent non-assignment—not biological truth,
clinical validity, treatment prediction, or clinical utility.
[Research question 0.3.0; reliability specification 0.1.0]

## Methods

Status: `working—Phase 0 only`

### Study design and governance

NAS-BRCA-002 is a staged analytical-method study governed by question version
`0.3.0`. During the current Phase 0 evidence review, molecular expression values and
outcomes are prohibited. The founder authorized bibliographic retrieval, screening,
lawful full-text access, and methodological appraisal. Novelty, preregistration,
molecular analysis, outcome analysis, and clinical use remain unauthorized.
[phase_zero_plan_v0.3.0.yaml; FOUNDER_PHASE_ZERO_AUTHORIZATION_v0.3.0.md]

### Literature search and screening

A focused PubMed and Europe PMC strategy targeted fixed single-sample classifiers,
uncertainty, ambiguity, abstention, centering, test-set bias, repeatability, and
reproducible implementations. Coverage repair explicitly added the 13 mandatory
priority identifiers before screening. The locked search returned 56 PubMed and
99 Europe PMC records, yielding 100 unique records and 55 cross-source duplicates.
All 100 records had abstracts and were reset to pending under question `0.3.0`.
[search_strategy_v0.3.0.yaml; search_receipt_v0.3.1.yaml]

The founder included all 13 direct-priority records for full-text review. Seven
had verified CC-BY full text, four were restricted or unavailable through the
approved repository endpoint, and two required a lawful alternative source.
Restricted full text was not stored. At this manuscript version, 2 of the 13
priority records have completed question-specific appraisal.
[revised-screening-progress/batch-0001.yaml; revised_appraisal_progress.yaml]

### Quality appraisal

Each eligible full text is assessed across population selection, specimen and
measurement, classifier implementation, reference comparator, analysis and
statistics, validation and transportability, and reporting and reproducibility.
High-risk defects cannot be averaged away. Only evidence with low-risk analysis
and transport validation may serve as anchor evidence. AI-assisted extraction is
disclosed, and the founder authorizes each locked appraisal.
[REVISED_FULL_TEXT_APPRAISAL_PROTOCOL.md]

### Proposed analytical procedure

Status: `placeholder—method dependencies unresolved`

The draft procedure is defined in reliability specification `0.1.0`, but exact
centroids, external reference values, platform transformations, technical-error
calibration, numerical tolerances, and reliability thresholds remain unresolved.
No molecular execution is authorized.

### Data sources, cohort, and statistical analysis

Status: `placeholder—data access not authorized`

TCGA-BRCA is the proposed discovery source and processed SCAN-B GSE96058 is the
candidate external-validation source. Cohort construction, estimands, statistical
models, sensitivity analyses, multiplicity handling, and figure specifications will
be inserted only after the evidence gate and preregistration.

## Results

Status: `working—literature appraisal only; no NaS analytical results`

### Measurement-error uncertainty

Ebbert and colleagues modeled how laboratory measurement error could propagate into
PAM50 assignments. The framework is directly relevant to patient-level reliability,
but its error calibration used 12 replicates of four archetypal specimens. Independent
GEICAM tumors were perturbed by simulation rather than independently repeat-measured,
and the report contains a material inconsistency between 100,000 and 1,000 simulated
replicas. The evidence is retained as `context_only`: it establishes the problem and
narrows the contribution, but does not provide a transportable technical-error model.
[PMID:22196354; revised appraisal PMC3275466-v1.0.0]

### Cohort-specific centering

Zhao and colleagues showed that standard gene centering can change PAM50 assignments
when a study cohort’s clinicopathological composition differs from the training
cohort. Their percentile-based correction shifted selected ER-positive and
triple-negative cohorts toward expected subtype distributions. However, development
and most accuracy comparisons reused the PAM50 training resource, external
comparators did not establish independent molecular truth, and the method requires
clinical composition plus sufficient cohort size. The authors explicitly state that
it is unsuitable for a one-patient dataset. The evidence is `context_only`: it
supports the need for a fixed patient-independent reference but cannot serve as one.
[PMID:25849221; revised appraisal PMC4365540-v1.0.0]

### NaS analytical results

Status: `placeholder—no molecular or outcome data accessed`

No NaS-generated subtype, reliability, survival, concordance, calibration, or
clinical-association result exists for question `0.3.0`.

## Discussion

Status: `working interpretation—must not be cited as a result`

The first two appraisals suggest that the broad problem is established: PAM50 calls
can be sensitive to technical error and cohort-dependent centering. The remaining
research gap is narrower. A defensible NaS contribution would need to predefine
every artifact and transformation, operate on one patient without consulting the
test cohort, calibrate perturbations from independent technical evidence, and
abstain when the resulting assignment is not analytically reliable.

This interpretation may change after appraisal of absolute single-sample
classifiers, RNA-seq implementations, uncertainty methods, and software packages.
It is not an authorized novelty conclusion.

## Limitations

Status: `working`

- The primary evidence review and citation chaining are incomplete.
- Only 2 of 13 priority records have completed question-specific appraisal.
- Several priority full texts are restricted or lack a verified lawful source.
- No centroid, reference, transformation, technical-error model, or threshold is locked.
- No molecular or outcome data have been accessed for question `0.3.0`.
- No external statistical or pathology review has been completed.
- The current text is an internal working draft and has not undergone peer review.

## Conclusions

Status: `placeholder`

No scientific or clinical conclusion is authorized. This section will remain empty
until the evidence stopping rule, method lock, preregistration, analysis, sensitivity
checks, and internal reviews are complete.

## References

1. Ebbert MTW, et al. Characterization of uncertainty in the classification of
   multivariate assays: application to PAM50 centroid-based genomic predictors for
   breast cancer treatment plans. *J Clin Bioinforma.* 2011;1:37.
   PMID:22196354. DOI:10.1186/2043-9113-1-37.
2. Zhao X, et al. Molecular subtyping for clinically defined breast cancer
   subgroups. *Breast Cancer Res.* 2015;17:29.
   PMID:25849221. DOI:10.1186/s13058-015-0520-4.

## Evidence-to-text ledger

| Manuscript location | Claim type | Supporting artifact | State |
|---|---|---|---|
| Introduction ¶1–2 | External methodological evidence | `revised-appraisals/PMC3275466-v1.0.0.yaml`; `revised-appraisals/PMC4365540-v1.0.0.yaml` | supported, evidence review incomplete |
| Introduction ¶3 | Study objective and boundary | `question/research_question.yaml`; `protocol/reliability_specification.yaml` | supported, method unresolved |
| Methods—governance | Authorization and prohibition | `question/phase_zero_plan_v0.3.0.yaml`; founder authorization | supported |
| Methods—search | Search and counts | `literature/search_receipt_v0.3.1.yaml`; queue receipt | verified |
| Methods—screening | Founder decisions and access | founder progress receipt; `revised_appraisal_progress.yaml` | verified, incomplete |
| Results—measurement error | External evidence appraisal | `revised-appraisals/PMC3275466-v1.0.0.yaml` | context only |
| Results—centering | External evidence appraisal | `revised-appraisals/PMC4365540-v1.0.0.yaml` | context only |
| Results—NaS analysis | NaS-generated result | none | prohibited placeholder |
| Discussion ¶1–2 | Explicit interpretation | two completed appraisals | provisional |
| Conclusions | Scientific conclusion | none | prohibited placeholder |

## Revision log

| Version | Date | Change |
|---|---|---|
| 0.1.0-working | 2026-07-24 | Created governed manuscript; seeded Phase 0 methods and the first two question-specific appraisals. |
