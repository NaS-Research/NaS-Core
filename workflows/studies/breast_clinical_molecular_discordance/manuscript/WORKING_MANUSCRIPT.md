# A Patient-Independent Reliability and Abstention Framework for PAM50 Breast Cancer Subtyping

Working title—subject to revision after the evidence gate.

Manuscript version: `0.4.0-working`

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
samples used for gene centering. RNA-seq implementations have reproduced this
reference sensitivity and shown that calls also depend on matching the reference to
the expression summarization and normalization family. These dependencies complicate
reproducible interpretation when a classifier is expected to operate on one patient
independently. [PMID:22196354; PMID:25849221; PMID:32826944]

Two distinct problems are relevant. First, laboratory measurement uncertainty can
perturb gene-expression values and change a non-archetypal tumor’s assigned subtype.
Second, centering a clinically skewed cohort against its own gene-expression
distribution can produce materially different calls from those obtained in a
representative training population. Existing solutions demonstrate the importance
of both problems, but the reviewed implementations do not yet provide an independently
calibrated, fixed, cross-platform reliability rule that can be executed for one
patient without adapting to a test cohort. A published average-of-within-class-
averages strategy does permit precomputed, single-sample RNA-seq centering, but the
reference must remain matched to the preprocessing family and its validation target
was primarily agreement with prior PAM50 calls rather than biological truth.
[Appraisals: PMC3275466-v1.0.0; PMC4365540-v1.0.0;
PMC7442834-v1.0.0]

Absolute single-sample classifiers also exist. MiniABS uses pairwise expression
ratios among 11 genes to remove dependence on other test samples and was evaluated
across RNA-seq, microarray, NanoString, and qRT-PCR cohorts. It demonstrates
single-sample feasibility but does not provide independently calibrated technical
uncertainty, repeatability, or an explicit abstention state. [PMID:33255759]

Large-scale RNA-seq work has additionally extended single-sample rules to molecular
subtype and recurrence-risk prediction, with independent outcome evaluation and
external comparison against Prosigna. That work supports technical and group-level
prognostic feasibility, but it does not validate patient-level uncertainty or prove
that retrospective changes in emulated treatment recommendations improve outcomes.
[PMID:35974007]

This study is therefore evaluating a narrower methodological question: whether a
fully specified, patient-independent research implementation can report the leading
and runner-up subtype scores, their margin, perturbation repeatability, data-quality
state, and an explicit reliability or abstention state. The intended contribution
is analytical reliability and transparent non-assignment—not a new claim to
single-sample classification, biological truth, clinical validity, treatment
prediction, or clinical utility.
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
Restricted full text was not stored. At this manuscript version, 5 of the 13
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

### RNA-seq reference construction and single-sample classification

Cascianelli and colleagues evaluated standard PAM50 centering across 4,731 tumors from
four public RNA-seq datasets. In TCGA-BRCA, ten randomly constructed references with
a 60:40 ER-positive/ER-negative composition reproduced published calls at a mean
85.52%, whereas reconstructing the reference from the same source sample set used
by the prior analysis reached 99.27%. Their average-of-within-class-averages (AWCA)
procedure reduced dependence on the initially selected reference subset: ten
AWCA-based classifications agreed with one another at a mean 99.13%, and precomputed
RSEM- and FPKM-matched references reproduced published calls above 96% in the
corresponding external datasets. Cross-applying RSEM and FPKM references reduced
concordance to 80–87%, demonstrating that a fixed reference is not automatically
cross-preprocessing portable.

Regularized multiclass logistic-regression models also achieved approximately
87–92% external agreement with published calls, depending on the feature set and
normalization family. These labels were themselves PAM50-derived and the authors
explicitly described them as a benchmark rather than a gold standard. Potential
TCGA/PanCancer sample overlap was not resolved, the model survey was exploratory,
and prognostic comparisons involved very few discordant cases. The evidence is
therefore `supporting`: it directly supports reference sensitivity and the
feasibility of preprocessing-matched single-sample execution, but it does not
establish biological correctness, clinical validity, or clinical utility.
[PMID:32826944; revised appraisal PMC7442834-v1.0.0]

### Absolute single-sample classification

Seo and colleagues developed MiniABS, a random-forest classifier based on pairwise
expression ratios among 11 genes. Because each feature is calculated entirely
within one specimen, execution does not require a contemporaneous reference cohort.
The model was developed from 432 TCGA-BRCA tumors and evaluated in 5,816 samples
from ten additional studies spanning RNA-seq, microarray, NanoString, and qRT-PCR.
Across the validation datasets, the authors reported a mean accuracy of 86.54%
against prior PAM50 calls after excluding Normal-like tumors. In GSE96058, agreement
with author-provided PAM50 calls was 76.7% with a kappa of 0.613; MiniABS reassigned
404 of 767 PAM50 Luminal-B tumors and 208 of 225 Normal-like tumors to Luminal A.

The study demonstrates that cross-platform, cohort-independent single-sample
classification is technically feasible. It does not establish that discordant
MiniABS labels are biologically correct: PAM50-derived calls supplied the training
and validation targets, feature selection appears to have preceded the TCGA
train-test split, and the key retrospective Luminal-B survival contrast was
nonsignificant (HR 1.5, 95% CI 0.9–2.4; P=0.126). The downloadable model also lacks
an independently calibrated measurement-error, repeatability, confidence, or
abstention rule. The evidence is therefore `supporting`, not anchor evidence.
[PMID:33255759; revised appraisal PMC7761033-v1.0.0]

### Single-sample subtype and recurrence-risk prediction

Staaf and colleagues trained AIMS-derived single-sample predictors for breast
cancer subtype and recurrence risk in SCAN-B. The development cohort contained
5,250 patients, while a completely non-overlapping population-based test set
contained 2,412 patients with median distant-recurrence follow-up of 8.1 years.
Four-class subtype agreement with the extended nearest-centroid target was 90%
(kappa 0.84). Three-category recurrence-risk agreement was 84% (weighted kappa
0.90), although exact agreement across the underlying 20 risk-score bins was only
17%. Group-level prognostic separation was similar between the single-sample and
nearest-centroid methods, including covariate-adjusted analyses in 772
ER-positive/HER2-negative, node-negative patients treated with endocrine therapy.

External comparisons included 103 clinical Prosigna cases and 100 cases with
non-clinical NanoString-derived Prosigna results. Pooled agreement was 81% for
subtype, 76% for three-category recurrence risk, and 85% for binary recurrence-risk
classification. A retrospective guideline emulation estimated that strict use of
the single-sample recommendation could change chemotherapy assignment for 17% of
an age-restricted ER-positive/HER2-negative, node-negative subgroup, but the authors
explicitly described this analysis as naive and called for prospective evaluation.

This is the strongest reviewed evidence for technically executable, prognostically
informative single-sample RNA-seq classification. It remains `supporting` rather
than anchor evidence because its primary target reproduces a research
nearest-centroid method, external clinical series are small, exact continuous-risk
agreement is limited, and no prospective decision impact, patient-level
uncertainty, repeatability, or abstention rule was validated.
[PMID:35974007; revised appraisal PMC9381586-v1.0.0]

### NaS analytical results

Status: `placeholder—no molecular or outcome data accessed`

No NaS-generated subtype, reliability, survival, concordance, calibration, or
clinical-association result exists for question `0.3.0`.

## Discussion

Status: `working interpretation—must not be cited as a result`

The first five appraisals suggest that the broad problem is established: PAM50
calls can be sensitive to technical error, cohort-dependent centering, and
preprocessing-specific RNA-seq references. They also show that fixed external
references, pairwise-ratio classifiers, and supervised models already support
single-sample execution, recurrence-risk stratification, and group-level prognostic
separation. A defensible NaS contribution cannot therefore be merely “a
single-sample classifier” or “an RNA-seq risk predictor.” It would need to predefine
every artifact and transformation, reproduce a fixed classifier unchanged,
calibrate perturbations from independent technical evidence, distinguish
analytical reliability from label agreement, expose ambiguity rather than conceal
it in a hard label, and abstain when the assignment is not analytically reliable.

This interpretation may change after appraisal of absolute single-sample
classifiers, RNA-seq implementations, uncertainty methods, and software packages.
It is not an authorized novelty conclusion.

## Limitations

Status: `working`

- The primary evidence review and citation chaining are incomplete.
- Only 5 of 13 priority records have completed question-specific appraisal.
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
3. Cascianelli S, et al. Machine learning for RNA sequencing-based intrinsic
   subtyping of breast cancer. *Sci Rep.* 2020;10:14071.
   PMID:32826944. DOI:10.1038/s41598-020-70832-2.
4. Seo MK, Paik S, Kim S. An improved, assay platform agnostic, absolute single
   sample breast cancer subtype classifier. *Cancers (Basel).* 2020;12(12):3506.
   PMID:33255759. DOI:10.3390/cancers12123506.
5. Staaf J, et al. RNA sequencing-based single sample predictors of molecular
   subtype and risk of recurrence for clinical assessment of early-stage breast
   cancer. *NPJ Breast Cancer.* 2022;8:94.
   PMID:35974007. DOI:10.1038/s41523-022-00465-3.

## Evidence-to-text ledger

| Manuscript location | Claim type | Supporting artifact | State |
|---|---|---|---|
| Introduction ¶1–4 | External methodological evidence | `revised-appraisals/PMC3275466-v1.0.0.yaml`; `revised-appraisals/PMC4365540-v1.0.0.yaml`; `revised-appraisals/PMC7442834-v1.0.0.yaml`; `revised-appraisals/PMC7761033-v1.0.0.yaml`; `revised-appraisals/PMC9381586-v1.0.0.yaml` | supported, evidence review incomplete |
| Introduction ¶5 | Study objective and boundary | `question/research_question.yaml`; `protocol/reliability_specification.yaml` | supported, method unresolved |
| Methods—governance | Authorization and prohibition | `question/phase_zero_plan_v0.3.0.yaml`; founder authorization | supported |
| Methods—search | Search and counts | `literature/search_receipt_v0.3.1.yaml`; queue receipt | verified |
| Methods—screening | Founder decisions and access | founder progress receipt; `revised_appraisal_progress.yaml` | verified, incomplete |
| Results—measurement error | External evidence appraisal | `revised-appraisals/PMC3275466-v1.0.0.yaml` | context only |
| Results—centering | External evidence appraisal | `revised-appraisals/PMC4365540-v1.0.0.yaml` | context only |
| Results—RNA-seq reference | External evidence appraisal | `revised-appraisals/PMC7442834-v1.0.0.yaml` | supporting |
| Results—absolute single sample | External evidence appraisal | `revised-appraisals/PMC7761033-v1.0.0.yaml` | supporting |
| Results—subtype and recurrence risk | External evidence appraisal | `revised-appraisals/PMC9381586-v1.0.0.yaml` | supporting |
| Results—NaS analysis | NaS-generated result | none | prohibited placeholder |
| Discussion ¶1–2 | Explicit interpretation | five completed appraisals | provisional |
| Conclusions | Scientific conclusion | none | prohibited placeholder |

## Revision log

| Version | Date | Change |
|---|---|---|
| 0.4.0-working | 2026-07-24 | Added SCAN-B subtype and recurrence-risk evidence; excluded generic RNA-seq risk prediction from the candidate novelty claim. |
| 0.3.0-working | 2026-07-24 | Added MiniABS appraisal; removed any implied novelty claim for single-sample classification and isolated reliability and abstention as the candidate contribution. |
| 0.2.0-working | 2026-07-24 | Added the supporting RNA-seq reference-sensitivity appraisal and narrowed the fixed-reference contribution. |
| 0.1.0-working | 2026-07-24 | Created governed manuscript; seeded Phase 0 methods and the first two question-specific appraisals. |
