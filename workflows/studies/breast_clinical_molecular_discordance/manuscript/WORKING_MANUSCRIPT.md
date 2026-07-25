# A Patient-Independent Reliability and Abstention Framework for PAM50 Breast Cancer Subtyping

Working title—subject to revision after the evidence gate.

Manuscript version: `0.12.0-working`

Study: `NAS-BRCA-002`

Question version: `0.3.0`

Last updated: 2026-07-25

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

The foundational PAM50 report defined the 50-gene, five-centroid, Spearman-
correlation classifier and validated group-level prognosis and chemotherapy
response, but it assigns every sample to its nearest centroid without a
patient-level analytical reliability or abstention state. Subsequent test-set-bias
experiments demonstrated that otherwise identical patient data and a locked
classifier can yield different calls when test-set size or ER composition changes
during normalization. [PMID:19204204; PMID:25788628]

MPAM50 is another fixed single-sample alternative. It removes reference subtraction,
uses weighted centroids derived from unnormalized expression, and scores samples
with Pearson correlation. Evaluation across 9,637 samples from 19 datasets further
establishes that cohort-independent subtyping itself is prior art. PCA-PAM50 instead
adapts centering through expression-inferred ER balancing; its packaged
implementation addresses skewed cohorts but remains cohort-dependent and therefore
does not satisfy a patient-independent objective. [PMID:37008073; PMID:41390542]

Large-scale RNA-seq work has additionally extended single-sample rules to molecular
subtype and recurrence-risk prediction, with independent outcome evaluation and
external comparison against Prosigna. That work supports technical and group-level
prognostic feasibility, but it does not validate patient-level uncertainty or prove
that retrospective changes in emulated treatment recommendations improve outcomes.
[PMID:35974007]

Population-scale perturbation work has also examined the difference between the
leading and runner-up PAM50 correlations, systematically removed co-expressed gene
modules, identified stable/prototypical tumors, and derived new single-sample
centroids from perturbation-stable cases. Therefore, neither a score margin nor
perturbation-stability labeling is novel by itself. [PMID:37857634]

Unified research software now executes ten published subtype methods, reports
method-specific calls and inter-method Shannon entropy, and uses cohort composition
to disable methods whose assumptions are likely violated. Thus, multi-method
comparison and discordance quantification also exist, although the published
entropy is not calibrated to patient-level error or abstention. [PMID:41064593]

Patient-level uncertainty and non-assignment are themselves also prior art. PBCMC
uses gene-label permutations to form subtype-specific empirical null distributions,
controls five subtype tests with Benjamini–Hochberg false-discovery rates, and
reports Assigned, Ambiguous, or Not Assigned states for one specimen. Its reported
implementation uses 10,000 permutations, an FDR threshold of 0.01, and a 0.1
leading-versus-runner-up correlation margin. The remaining unresolved problem is
therefore not whether abstention can be implemented, but whether a fixed rule can
be calibrated to independently measured technical error and validated unchanged
in an external cohort. [PMID:28062443]

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

The founder completed title-and-abstract review of all 100 records. The immutable
ledger records 30 inclusions, 70 exclusions, zero pending, zero unclear, and zero
AI decisions. All five fuzzy author-year identity links were rejected. Inclusion
means only that lawful full-text assessment is warranted.

Of the 13 direct-priority inclusions, seven had verified CC-BY full text and five
were lawfully viewable but not approved for durable commercial storage. Those 12
records completed question-specific appraisal. The remaining AIMS article was
identity-verified at the publisher but subscription-restricted; no full text was
stored or appraised. Read-only receipts retain source identity, rights observations,
and ephemeral checksums rather than article content.
[revised-screening-progress/batch-0002.yaml;
FOUNDER_REMAINING_SCREENING_CONFIRMATION_v1.0.0.md;
revised_appraisal_progress_v0.3.5.yaml]

Eleven of the 17 newly included records now have article identity and an approved
CC BY license independently verified through official Europe PMC XML. Four more
were lawfully reviewed through governed ephemeral sessions because their rights do
not authorize durable commercial corpus storage. The IOP article is abstract-only
and subscription-restricted. The remaining IEEE article is confirmed open access
under CC BY but awaits full-text retrieval after scheduled publisher maintenance.
Three of those 15 records have completed appraisal and 12 remain ready. No failed
or restricted retrieval stored article content.

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

### Foundational PAM50 classifier

Parker and colleagues reduced 161 qRT-PCR-performing genes to a 50-gene classifier
using repeated ten-percent leave-out cross-validation in 189 prototype tumors.
Each tumor was assigned to the nearest of five PAM-derived centroids using Spearman
rank correlation. Prognostic testing included 761 patients who received no systemic
therapy, and a separate 133-patient cohort evaluated pathologic complete response
to taxane-anthracycline chemotherapy. Intrinsic subtype added group-level
prognostic information to standard variables, and the subtype-based model had high
negative predictive value for pathologic complete response.

This report supplies the foundational research centroids and classifier structure,
but not a reliability reference standard. Prototype selection emphasizes
archetypal tumors; Normal-like calls may reflect normal-tissue contamination; and
every specimen receives a nearest-centroid label regardless of score separation,
measurement error, or reproducibility. The evidence is `supporting` for exact
method provenance and population-level validation, not anchor evidence for
patient-level reliability or abstention. [PMID:19204204; revised appraisal
PMC2667820-v1.0.0]

### Test-set bias and patient independence

Patil and colleagues assembled 6,297 tumors from 28 studies spanning 15 microarray
platform types. In a 198-patient Affymetrix cohort, they repeatedly changed the
number and ER composition of samples normalized with a given patient while holding
that patient's expression data and the PAM50 classifier fixed. Calls changed when
the surrounding normalization cohort changed, with greatest agreement when subset
composition resembled the full cohort. Unnormalized prediction using Spearman
gene ranks removed this induced dependency in the tested setting, and a separate
grade classifier showed similar within- and cross-platform accuracy with and
without scaling.

The design isolates an important technical failure: a classification can change
without any biological change in the patient. Full-cohort PAM50 calls remain a
self-consistency reference rather than biological truth, and the proposed
rank-based workaround is not a calibrated modern RNA-seq reliability system. The
evidence is nevertheless `supporting` and makes patient independence a required
property rather than a novel observation. [PMID:25788628; revised appraisal
PMC4495301-v1.0.0]

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

### Modified fixed-centroid single-sample classification

Hamaneh and Yu developed MPAM50 using weighted subtype-average centroids,
log-transformed within-sample expression, no test-cohort reference subtraction,
and Pearson correlation. The centroids were trained from TCGA-BRCA and GSE115577
after removing samples with discordant PAM50 calls. Testing included 9,637 samples
from 19 independent datasets. Median agreement with reported PAM50 labels was
0.792, with substantial Luminal-A/Luminal-B/Normal confusion. Comparisons included
AIMS, MiniABS, three other PAM50 modifications, clinical receptor-defined groups,
and survival curves.

MPAM50 provides another reproducible fixed classifier and broad technical
replication, further removing generic fixed single-sample classification as a NaS
contribution. Primary labels remain varying research PAM50 calls, discordant
training samples were excluded, only one paired-platform dataset assessed the
same patients, and no technical-repeat reliability or abstention calibration was
performed. The evidence is `supporting`, not anchor evidence. [PMID:37008073;
revised appraisal PMC10052604-v1.0.0]

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

### Population-scale margin and perturbation stability

Veerla and colleagues analyzed 6,233 population-based SCAN-B tumors using a
repeated-reference PAM50 nearest-centroid implementation. They retained the
second-best subtype and calculated the correlation difference between the leading
and runner-up centroids. Basal-like tumors generally had the greatest separation,
Normal-like tumors the least, and Luminal A versus Luminal B formed a continuum
rather than two cleanly separated classes.

The investigators then grouped PAM50 genes into seven co-expression modules and
reclassified every tumor after removing one module at a time. Classification
stability varied strongly by subtype, receptor-defined subgroup, and removed
module. More than 80% of prototypical Basal-like triple-negative and HER2-enriched
ER-negative/HER2-positive tumors remained unchanged across all perturbations,
whereas Normal-like and luminal assignments were substantially less stable. Among
Luminal-B tumors, removing the proliferation or basal-keratin module caused more
than 40% to switch subtype. When a switch occurred, it often moved to the original
runner-up label.

The paper also defined 1,934 perturbation-stable ER-positive/HER2-negative tumors,
derived new subtype centroids from them, and used those centroids for uncentered
single-sample classification. Outcome and metagene analyses were exploratory and
the refined method was developed and evaluated in the same SCAN-B population.
Gene-module deletion is a structural sensitivity analysis rather than a calibrated
model of laboratory measurement error. No independently validated reliability
probability or prespecified abstention threshold was provided. The evidence is
`supporting`, but it removes best-runner-up margin, perturbation testing, stable-case
labeling, and refined single-sample centroids as standalone NaS novelty claims.
[PMID:37857634; revised appraisal PMC10587090-v1.0.0]

### Unified multi-method software and inter-method discordance

Yang and colleagues introduced BreastSubtypeR, an R/Bioconductor package that
harmonizes ten published nearest-centroid and single-sample subtype methods. Its
wrapper outputs reproduced the original implementations with kappa 1.00 in 4,606
SCAN-B cases. The package preserves separate method calls, calculates Shannon
entropy to describe inter-method concordance, and deliberately does not force a
consensus label.

BreastSubtypeR also implements AUTO, which examines cohort ER/HER2 prevalence,
subtype composition, and subgroup size to disable methods whose assumptions are
likely violated. In simulated SCAN-B cohorts with extreme ER-positive prevalence,
selected-method accuracy exceeded excluded-method accuracy by approximately
18–19 percentage points. Across subtype-specific SCAN-B, ABiM100, and OSLO2-EMIT0
scenarios, improvements ranged from approximately 14 to 36 percentage points,
depending on comparator and cohort.

The package is a strong reproducible research implementation, distributed under
GPL-3 through Bioconductor with source, tests, vignettes, and a Shiny interface.
It remains `supporting` evidence rather than clinical or reliability validation:
AUTO thresholds were developed and substantially evaluated in SCAN-B, selection
depends on cohort composition rather than patient-only state, primary comparators
were research PAM50 or IHC labels, no direct Prosigna or outcome validation was
performed, and entropy was not calibrated to error probability or abstention.
[PMID:41064593; revised appraisal PMC12501779-v1.0.0]

### Cohort-adaptive PCA-PAM50 software

The PCAPAM50 package reengineers PCA-PAM50 into documented CRAN functions. It
infers an expression-guided ER-balanced subset, refines centering using confidently
classified Basal-like and Luminal-A cases, and compares final calls with
conventional PAM50. The report states improved IHC concordance and more stable
behavior in ER-imbalanced subsets, building substantially on prior evaluation in
TCGA, METABRIC, and an in-house cohort.

This is relevant implementation evidence but not a patient-independent solution:
the reference adapts to the composition of the test cohort, IHC concordance is not
intrinsic-subtype truth, and the package paper does not supply a new independent
technical or clinical validation cohort. With high concern for transport validation,
the evidence is retained as `context_only`. [PMID:41390542; revised appraisal
PMC12789466-v1.0.0]

### Single-subject uncertainty and non-assignment

Fresno and colleagues developed Permutation-Based Confidence for Molecular
Classification (PBCMC), a single-subject uncertainty procedure for correlation-
based PAM50. For each specimen, gene labels are permuted to generate empirical
null correlation distributions for the five centroids. The method applies
upper-tail tests, controls the five subtype tests using Benjamini–Hochberg, and
combines significance with a leading-versus-runner-up correlation margin to
produce Assigned, Ambiguous, and Not Assigned states.

The study evaluated 5,228 tumors across six training and 27 test datasets. Its
recommended configuration used 10,000 permutations, an FDR threshold of 0.01,
and a 0.1 correlation-difference threshold. Across all datasets, 61.17% of tumors
were Assigned, 6.15% Ambiguous, and 32.68% Not Assigned. The pbcmc Bioconductor
package provides executable code.

This is direct `supporting` prior art and materially narrows the NaS contribution:
single-subject uncertainty, false-discovery control, explicit ambiguity, and
abstention cannot be claimed as novel. Gene-label permutations test whether
centroid correlation exceeds a randomized null; they do not estimate repeatability
under independently measured assay error. The thresholds were selected using the
study collections, and no independent technical-repeat, prospective clinical,
probability-calibration, or decision-impact validation was performed. A surviving
NaS contribution must therefore connect a frozen patient-independent classifier
to an independently estimated technical-error model, prespecified reliability
estimand, and unchanged external validation. [PMID:28062443; revised appraisal
PMID28062443-v1.0.0]

### Direct commercial-assay discordance

OPTIMA Prelim applied actual commercial and laboratory assays to the same 302
ER-positive/HER2-negative early breast cancers. Although each of three subtype
tests assigned a similar population proportion to Luminal A, only 121 tumors
(40.1%) received a unanimous Luminal A call and 123 (40.7%) had discordant subtype
assignments. Across five risk tests, 183 tumors (60.6%) were placed in different
risk categories. This eliminates in-silico reconstruction as a sufficient
explanation for patient-level disagreement.

The study has no outcome data and no independent reference that identifies which
discordant assay is correct. Its result supports non-interchangeability and the
need to disclose assay dependence; it cannot calibrate technical reliability or
authorize a treatment decision. [PMID:27130929; revised appraisal
PMC5939629-v1.0.0]

### Technical repeatability and spatial heterogeneity

A replicate study separated duplicate NanoString runs on the same RNA from
pathologist-selected spatial sampling. PAM50 subtype agreed in 127 of 144
same-RNA pairs (90%) and in 29 of 40 spatial pairs (76%); approximately half of
the technical discordance was Luminal A versus Luminal B. ROR-P group agreement
was 93% and 81%, respectively. Discordant spatial pairs had larger continuous
distances, especially for ROR-P, but distributions overlapped.

This is the most direct reviewed evidence so far that a reliability layer should
distinguish assay repeatability from tumor sampling heterogeneity. The spatial
set is small and intentionally enriched for histologic difference, agreement
confidence intervals and acceptance thresholds were not prespecified, and no
external laboratory or clinical decision validation was performed. [PMID:36892725;
revised appraisal PMC10147733-v1.0.0]

### Cohort-adaptive Luminal A ambiguity

An analysis of 674 METABRIC and 509 TCGA Luminal A tumors quantified distance to
assigned and competing subtype centroids. Luminal A/Luminal B overlap predominated,
and the most admixed groups had worse clinicopathologic features and survival.
The report also retained important null findings for mutation load and MATH score.

The categorical threshold was selected using METABRIC survival and changed in
TCGA; the continuous ratio still depends on cohort-derived centroids, covariance,
and tertiles. METABRIC lacked three PAM50 genes and used random value replacement.
The method is therefore `context_only`: it reinforces ambiguity as a biological
and prognostic signal but cannot serve as a fixed patient-independent reliability
algorithm or unchanged external validation. [PMID:30849944; revised appraisal
PMC6408846-v1.0.0]

### NaS analytical results

Status: `placeholder—no molecular or outcome data accessed`

No NaS-generated subtype, reliability, survival, concordance, calibration, or
clinical-association result exists for question `0.3.0`.

## Discussion

Status: `working interpretation—must not be cited as a result`

The 15 completed appraisals show that the broad problem is established: PAM50
calls can be sensitive to technical error, cohort-dependent centering, and
preprocessing-specific RNA-seq references. They also show that fixed external
references, pairwise-ratio classifiers, and supervised models already support
single-sample execution, recurrence-risk stratification, group-level prognostic
separation, runner-up margins, perturbation-stability labeling, multi-method
comparison, discordance entropy, empirical permutation confidence, explicit
Ambiguous or Not Assigned states, direct commercial-assay discordance, and
technical-versus-spatial repeatability differences. A defensible NaS contribution cannot therefore
be merely a classifier, risk predictor, margin, perturbation experiment,
ensemble-disagreement score, uncertainty test, or abstention label. It would need
to reproduce a fixed classifier unchanged, calibrate perturbations from independent
technical evidence, define a reliability estimand and thresholds without outcome
tuning, validate transport in an independent cohort, and abstain prospectively when
the assignment is not analytically reliable.

This interpretation may change after appraisal of the 12 remaining accessible
records, resolution of the open IEEE retrieval, and sequential citation chaining.
AIMS and the IOP article remain identified but unappraised access-restricted
sources. This is not an authorized novelty conclusion.

## Limitations

Status: `working`

- Primary title-and-abstract screening is complete; 12 accessible appraisals, one
  open IEEE retrieval, and citation chaining are incomplete.
- Twelve of 13 priority records have completed question-specific appraisal: seven
  from verified CC-BY retrieval and five through governed read-only review.
- AIMS is identity-verified but subscription-restricted. It remains unappraised,
  and no absence-of-prior-art claim may be inferred from that access boundary.
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
6. Veerla S, et al. Perturbation and stability of PAM50 subtyping in
   population-based primary invasive breast cancer. *NPJ Breast Cancer.*
   2023;9:83. PMID:37857634. DOI:10.1038/s41523-023-00589-0.
7. Yang Q, Hartman J, Sifakis EG. BreastSubtypeR: a unified R/Bioconductor
   package for intrinsic molecular subtyping in breast cancer research.
   *NAR Genom Bioinform.* 2025;7(4):lqaf131.
   PMID:41064593. DOI:10.1093/nargab/lqaf131.
8. Parker JS, et al. Supervised risk predictor of breast cancer based on
   intrinsic subtypes. *J Clin Oncol.* 2009;27(8):1160–1167.
   PMID:19204204. DOI:10.1200/JCO.2008.18.1370.
9. Patil P, et al. Test set bias affects reproducibility of gene signatures.
   *Bioinformatics.* 2015;31(14):2318–2323.
   PMID:25788628. DOI:10.1093/bioinformatics/btv157.
10. Hamaneh MB, Yu YK. A simple method for robust and accurate intrinsic
    subtyping of breast cancer. *Cancer Inform.* 2023;22:11769351231159893.
    PMID:37008073. DOI:10.1177/11769351231159893.
11. Raj-Kumar PK, et al. Enhanced PAM50 subtyping of breast cancer implemented
    in the PCAPAM50 R package. *Sci Rep.* 2025;15.
    PMID:41390542. DOI:10.1038/s41598-025-30752-5.
12. Fresno C, et al. A novel non-parametric method for uncertainty evaluation
    of correlation-based molecular signatures: its application on PAM50
    algorithm. *Bioinformatics.* 2017;33(5):693–700.
    PMID:28062443. DOI:10.1093/bioinformatics/btw704.

## Evidence-to-text ledger

| Manuscript location | Claim type | Supporting artifact | State |
|---|---|---|---|
| Introduction ¶1–9 | External methodological evidence | 12 records in `literature/revised-appraisals/` | supported, evidence review incomplete |
| Introduction ¶10 | Study objective and boundary | `question/research_question.yaml`; `protocol/reliability_specification.yaml` | supported, method unresolved |
| Methods—governance | Authorization and prohibition | `question/phase_zero_plan_v0.3.0.yaml`; founder authorization | supported |
| Methods—search | Search and counts | `literature/search_receipt_v0.3.1.yaml`; queue receipt | verified |
| Methods—screening | Founder decisions | `revised-screening-progress/batch-0002.yaml`; founder confirmation | verified, complete |
| Methods—full-text access | Access and appraisal state | `revised_appraisal_progress_v0.3.5.yaml` | verified, incomplete |
| Results—measurement error | External evidence appraisal | `revised-appraisals/PMC3275466-v1.0.0.yaml` | context only |
| Results—foundational PAM50 | External evidence appraisal | `revised-appraisals/PMC2667820-v1.0.0.yaml` | supporting |
| Results—test-set bias | External evidence appraisal | `revised-appraisals/PMC4495301-v1.0.0.yaml` | supporting |
| Results—centering | External evidence appraisal | `revised-appraisals/PMC4365540-v1.0.0.yaml` | context only |
| Results—RNA-seq reference | External evidence appraisal | `revised-appraisals/PMC7442834-v1.0.0.yaml` | supporting |
| Results—absolute single sample | External evidence appraisal | `revised-appraisals/PMC7761033-v1.0.0.yaml` | supporting |
| Results—modified fixed centroid | External evidence appraisal | `revised-appraisals/PMC10052604-v1.0.0.yaml` | supporting |
| Results—subtype and recurrence risk | External evidence appraisal | `revised-appraisals/PMC9381586-v1.0.0.yaml` | supporting |
| Results—margin and perturbation | External evidence appraisal | `revised-appraisals/PMC10587090-v1.0.0.yaml` | supporting |
| Results—multi-method software | External evidence appraisal | `revised-appraisals/PMC12501779-v1.0.0.yaml` | supporting |
| Results—PCA-PAM50 software | External evidence appraisal | `revised-appraisals/PMC12789466-v1.0.0.yaml` | context only |
| Results—single-subject uncertainty | External evidence appraisal | `revised-appraisals/PMID28062443-v1.0.0.yaml` | supporting |
| Results—commercial-assay discordance | External evidence appraisal | `revised-appraisals/PMC5939629-v1.0.0.yaml` | supporting |
| Results—technical and spatial reproducibility | External evidence appraisal | `revised-appraisals/PMC10147733-v1.0.0.yaml` | supporting |
| Results—Luminal A ambiguity | External evidence appraisal | `revised-appraisals/PMC6408846-v1.0.0.yaml` | context only |
| Results—NaS analysis | NaS-generated result | none | prohibited placeholder |
| Discussion ¶1–2 | Explicit interpretation | 12 completed appraisals plus one access-restricted priority record | provisional |
| Conclusions | Scientific conclusion | none | prohibited placeholder |

## Revision log

| Version | Date | Change |
|---|---|---|
| 0.12.0-working | 2026-07-25 | Added OPTIMA commercial-assay discordance, PAM50 technical/spatial reproducibility, and cohort-adaptive Luminal A ambiguity appraisals; 15 of 30 records are now appraised. |
| 0.11.0-working | 2026-07-25 | Reconciled expanded lawful-access review: 27 full texts are verified, 15 expanded-set papers are ready for appraisal, two records are restricted, and one open IEEE retrieval remains. |
| 0.8.0-working | 2026-07-24 | Added the PBCMC single-subject uncertainty appraisal, recorded AIMS as subscription-restricted, and narrowed the candidate contribution beyond uncertainty and abstention alone. |
| 0.7.0-working | 2026-07-24 | Added four governed read-only appraisals: foundational PAM50, test-set bias, MPAM50, and PCAPAM50; priority appraisal is now 11 of 13. |
| 0.6.0-working | 2026-07-24 | Completed all seven accessible priority appraisals; added BreastSubtypeR and excluded generic multi-method discordance from the candidate novelty claim. |
| 0.5.0-working | 2026-07-24 | Added population-scale margin and perturbation evidence; restricted the candidate contribution to independently calibrated and externally validated reliability and abstention. |
| 0.4.0-working | 2026-07-24 | Added SCAN-B subtype and recurrence-risk evidence; excluded generic RNA-seq risk prediction from the candidate novelty claim. |
| 0.3.0-working | 2026-07-24 | Added MiniABS appraisal; removed any implied novelty claim for single-sample classification and isolated reliability and abstention as the candidate contribution. |
| 0.2.0-working | 2026-07-24 | Added the supporting RNA-seq reference-sensitivity appraisal and narrowed the fixed-reference contribution. |
| 0.1.0-working | 2026-07-24 | Created governed manuscript; seeded Phase 0 methods and the first two question-specific appraisals. |
