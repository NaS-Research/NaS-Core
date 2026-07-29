# A Patient-Independent Reliability and Abstention Framework for PAM50 Breast Cancer Subtyping

Working title—subject to revision after the evidence gate.

Manuscript version: `0.55.0-working`

Study: `NAS-BRCA-002`

Question version: `0.3.0`

Last updated: 2026-07-28

Overall status: **working—citation review saturated, evidence synthesis
founder-authorized, metadata input feasibility passed, and Route C activated
under an independent-calibration hold; novelty remains on hold; no molecular
values or outcome dataset used or retained**

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
revised_appraisal_progress_v0.4.0.yaml]

Eleven of the 17 newly included records now have article identity and an approved
CC BY license independently verified through official Europe PMC XML. Four more
were lawfully reviewed through governed ephemeral sessions because their rights do
not authorize durable commercial corpus storage. The IOP article is abstract-only
and subscription-restricted. The IEEE author manuscript was retrieved from the
publisher, verified as CC BY 4.0, and stored immutably through the governed
publisher-PDF import path. All 16 lawfully accessible expanded-set records have
completed appraisal. No failed or restricted retrieval stored article content.

The first citation-chain pass queried backward references and forward citations
for all 30 eligible seeds through the official Europe PMC endpoints. It retrieved
981 backward and 4,639 forward links, deduplicated to 4,628 non-seed source
records. Reconciliation against the completed direct-search inventory and within
the citation set classified 42 records as already screened and 91 as exact
normalized-title duplicates, leaving 4,495 records for advisory triage and founder
screening. These workload classifications contain zero new eligibility decisions
and no scientific conclusion.
[citation-chain/pass-0001-retrieval.yaml;
citation-chain/pass-0001-screening-preparation.yaml]

All 4,495 unscreened citation candidates then received transparent title-based
review priority without an eligibility decision: 80 direct, 400 supporting, and
4,015 context. A full batched Europe PMC enrichment matched every record and
retrieved 4,402 abstracts; 93 records remain metadata-only and cannot be excluded
solely for missing abstracts.
[citation-chain/pass-0001-prioritization.yaml;
citation-chain/pass-0001-full-enrichment.yaml]

Conservative abstract-informed advisory rules then produced 15 include and 4,224
exclude recommendations while holding 256 records for individual adjudication.
These recommendations were frozen in a checksum-bound founder packet and complete
row-level appendix.
[citation-chain/pass-0001-recommendations.yaml;
citation-chain/pass-0001-founder-packet.yaml]

Second-stage title-and-abstract adjudication of the 256 held records recommended 17
additional includes and 239 exclusions. The founder then supplied the exact
statement bound to both packet and appendix checksum pairs. Immutable decision
ledger `1ca4b716…281caf` records all 4,495 unique records exactly once: 32
inclusions, 4,463 exclusions, zero unclear, and zero AI decisions. Identifier-only
reconciliation found no overlap with the active 30-study inventory, three exact
matches to locked prior appraisals (PMIDs 22752290, 27556419, and 16643655), and
29 net-new records. The founder separately approved protocol amendment `0.2.5`,
which activates an uncapped saturation inventory while limiting the later
quality-selected core synthesis to 30 non-duplicate primary studies. Its immutable
queue routes the 29 net-new records to 23 repository checks and six separate
lawful-access checks and reuses three prior appraisals without double-counting.

The repository pass assessed all 23 PMC candidates through the official Europe PMC
full-text endpoint. Thirteen exact-identity articles carried approved CC BY licenses
and were immutably retrieved. Five returned no full text from that endpoint, three
did not carry an approved durable-storage license, and two failed exact identity
matching; none of those ten stored article content. Together with six records
lacking PMC identifiers, 16 records entered a governed access-check queue. A later
bounded identity repair showed that the two apparent mismatches had exact PMCID,
PMID, and DOI agreement and differed only by Unicode dash typography. Both were
CC BY 4.0 and were immutably retrieved, leaving 14 access records unresolved.
Eight of those 14 were subsequently reviewed through the official PMC HTML
interface under a no-storage protocol. Exact page bytes were hashed in memory and
discarded; seven records have explicit durable-storage restrictions and one
declares CC BY 4.0 but lacked repository XML. A version-specific medRxiv preprint
and a public UNC Lineberger author-copy PDF were then verified and hashed through
separate zero-storage routes. Official publisher checks restricted three
abstract-, preview-, or purchase-only records without appraisal. One CC BY 4.0
Lancet Oncology paper also lacks a reproducible checksum-verifiable full-text
route: its publisher PDF returns an access challenge, Unpaywall points only to
that same route, Europe PMC has no repository copy, and the credential-free
Elsevier API returns metadata only. It is now recorded as access-restricted for
governed appraisal despite the permissive license. No challenge was bypassed,
third-party copy retained, or appraisal inferred from its abstract.
The founder authorized all nine checksum-bound citation appraisal batches.
Thirty citation-pass full texts are complete: seven are `supporting`, 23 are
`context_only`, eight are access-restricted, and none remain ready or awaiting
full text. These counts are workflow results, not scientific findings. The locked
appraisals retain the exact proposal, packet, confirmation, access-receipt, and,
where needed, stable appraisal-source checksums. The medRxiv analytical bridge and
UNC genomic-versus-pathology comparison were reviewed through bounded zero-storage
gates that reverified their source checksums and rejected long verbatim passages.
Receipt-derived closures independently reverified the complete lineage for pass 1
(`3f7037ca…d9676`) and pass 2 (`995b8b3f…f6f9a7`). The bound identity-level review
state is 71 eligible, 61 appraisal-complete, 10 access-restricted, and zero
pending. Both passes added evidence and therefore reset rather than advance the
required two-consecutive-zero-pass stopping rule.
[CITATION_PASS_0001_ADJUDICATION_POLICY_v1.0.0.yaml;
citation-chain/pass-0001-adjudication-packet.yaml;
FOUNDER_CITATION_PASS_0001_COMBINED_REVIEW_v1.0.0.md;
FOUNDER_CITATION_PASS_0001_CONFIRMATION_v1.0.0.yaml;
citation-chain/pass-0001-decision-ledger.yaml;
citation-chain/pass-0001-inclusion-reconciliation.yaml;
evidence-cap-amendment-activation-v0.2.5.yaml;
citation-chain/pass-0001-closure.yaml]

Citation pass 2 used all 62 founder-included persistent identities from the
direct search and pass 1. Official Europe PMC retrieval returned 2,053 backward
and 8,163 forward links, yielding 7,135 unique non-seed candidates. Exact
reconciliation against the direct-search inventory, the complete pass-1 founder
ledger, and within-pass duplicates left 2,479 genuinely new records. The founder
confirmed nine inclusions and 2,470 exclusions with zero unclear. Five official
full texts were appraised and locked as `context_only`; four additional inclusions
are access-restricted. Pass-2 closure added all nine identities with no pending
record and no scientific conclusion.
[citation-chain/pass-0002-seeds.yaml;
citation-chain/pass-0002-retrieval.yaml;
citation-chain/pass-0002-screening-preparation.yaml;
citation-chain/pass-0002-recommendations.yaml;
citation-chain/pass-0002-unclear-adjudication.yaml;
FOUNDER_CITATION_PASS_0002_COMBINED_REVIEW_v1.0.0.md]

Citation pass 3 used all 71 founder-included persistent identities from the
direct search and passes 1–2. Official Europe PMC retrieval returned 2,393
backward and 8,617 forward links, yielding 7,728 unique non-seed candidates.
Exact reconciliation against the direct-search inventory and both prior founder
ledgers left 593 genuinely new records. Enrichment matched 592 records and
supplied 575 abstracts; the unresolved metadata identity remains visible.
Checksum-bound advisory screening proposes seven inclusions and 586 exclusions
with zero unclear. These are not founder decisions, and they do not change the
eligible evidence set or support a scientific conclusion.
[citation-chain/pass-0003-seeds.yaml;
citation-chain/pass-0003-retrieval.yaml;
citation-chain/pass-0003-screening-preparation.yaml;
citation-chain/pass-0003-recommendations.yaml;
citation-chain/pass-0003-unclear-adjudication.yaml;
FOUNDER_CITATION_PASS_0003_COMBINED_REVIEW_v1.0.0.md]

The pass-2 appraisal set adds convergent but indirect reliability context. NTP
defines per-sample confidence without a receiving-cohort training set; paired
paraffin and frozen breast tissue shows that preservation and normalization alter
expression comparability; ovarian miRNA rank pairs and targeted PurIST validation
show that within-sample rules can be operationally portable while retaining
population, platform, comparator, and clinical-utility limits; and multiregional
colorectal transcriptomics illustrates spatial subtype discordance and
primary-metastasis plasticity. All five reports are `context_only`. They constrain
engineering and validation claims but do not validate PAM50 correctness, a NaS
reliability threshold, or patient treatment benefit.
[FOUNDER_CITATION_APPRAISAL_BATCH_0009_CONFIRMATION_v1.0.0.yaml;
citation-chain/pass-0002-closure.yaml;
citation-appraisals/PMC2990751-v1.0.0.yaml;
citation-appraisals/PMC3037966-v1.0.0.yaml;
citation-appraisals/PMC9378834-v1.0.0.yaml;
citation-appraisals/PMC11524322-v1.0.0.yaml;
citation-appraisals/PPR723583-v1.0.0.yaml]

The first citation appraisal batch adds a deliberately bounded contrast. A paired
triple-negative series reported 92.7% raw RNA-seq/NanoString subtype agreement,
while comparisons in PALOMA-2 and PALLET reported 54% and 69% agreement,
respectively. These percentages are not directly exchangeable: the populations,
platform pairings, normalization, algorithms, and ambiguity rules differed.
An independent 814-patient RT-qPCR study further showed incomplete mapping between
clinical surrogate categories and intrinsic subtypes and systematic call changes
under normal-tissue contamination. The three studies are context-only evidence;
they define reliability mechanisms but do not validate a NaS method or clinical
decision.
[FOUNDER_CITATION_APPRAISAL_BATCH_0001_v1.0.0.md;
FOUNDER_CITATION_APPRAISAL_BATCH_0001_CONFIRMATION_v1.0.0.yaml;
citation-appraisals/PMC11217366-v1.0.0.yaml;
citation-appraisals/PMC6547580-v1.0.0.yaml;
citation-appraisals/PMC3487945-v1.0.0.yaml]

Batch 0002 establishes that cohort-independent execution is feasible but not
sufficient for transport. Singscore provides an auditable within-sample rank
score, while direct classifier comparisons show that single-sample gene-pair and
rule-based methods can still fail when measurement platforms are not represented
in development. The remaining software and rank-ensemble reports are useful prior
art but lack enough external-validation and label-provenance detail for central
performance claims. These studies narrow the contribution: NaS cannot claim
single-sample scoring, gene-pair rules, tie flags, or probability-like outputs as
novel by themselves.
[FOUNDER_CITATION_APPRAISAL_BATCH_0002_CONFIRMATION_v1.0.0.yaml;
citation-appraisals/PMC6219008-v1.0.0.yaml;
citation-appraisals/PMC8796360-v1.0.0.yaml;
citation-appraisals/PMC8479681-v1.0.0.yaml;
citation-appraisals/PMC10848444-v1.0.0.yaml]

Batch 0003 shows that disagreement can enter through specimen selection,
cellularity, peri-surgical timing, platform and preprocessing, incomplete
commercial-assay reconstruction, reference composition, and narrow subtype
margins. A locked commercial assay with separated verification demonstrates the
engineering standard, while paired-biopsy and specimen-preparation studies show
that globally similar expression can still yield clinically adjacent subtype or
risk-category changes. None determines which discordant label is biologically
correct or proves that relabeling improves outcomes.
[FOUNDER_CITATION_APPRAISAL_BATCH_0003_CONFIRMATION_v1.0.0.yaml;
citation-appraisals/PMC1557722-v1.0.0.yaml;
citation-appraisals/PMC4546262-v1.0.0.yaml;
citation-appraisals/PMC4818440-v1.0.0.yaml;
citation-appraisals/PMC7470374-v1.0.0.yaml;
citation-appraisals/PMC8657125-v1.0.0.yaml;
citation-appraisals/PMC10771357-v1.0.0.yaml]

Batch 0004 adds direct but non-anchor analytical evidence for platform bridging:
the Prosigna nCounter-to-NGS preprint used separated bridge and validation cohorts
and prespecified acceptance criteria, but sponsor involvement, preprint status,
and unavailable fitted calibration artifacts constrain inference. Batch 0005
adds context-only paired evidence that pathology surrogates and genomic subtypes
are not interchangeable; its small selected cohort, cohort-level centering,
uncontrolled multiplicity, treatment crossover, and absent external validation
prohibit a patient-independent or treatment-utility conclusion.
[FOUNDER_CITATION_APPRAISAL_BATCH_0004_CONFIRMATION_v1.0.0.yaml;
FOUNDER_CITATION_APPRAISAL_BATCH_0005_CONFIRMATION_v1.0.0.yaml;
citation-appraisals/PPR1259744-v1.0.0.yaml;
citation-appraisals/PMID23907291-v1.0.0.yaml]

Two additional direct comparisons are founder-authorized batch-0006
`context_only` appraisals. A Korean multi-cohort study reported 38.4% IHC/PAM50
discordance, but
its research classifier merged local NanoString expression with TCGA and applied
batch adjustment before subtype assignment. A South African study showed large
differences between clinical-surrogate and PAM50 subtype distributions in 378
quality-passing Black African women, while its explored Ki67 thresholds lacked
held-out calibration and outcome validation. These studies reinforce that
agreement depends on population, assay, preprocessing, reference cohort, mapping,
and threshold choices. They do not identify a universally correct label or show
that relabeling improves outcomes.
[FOUNDER_CITATION_APPRAISAL_BATCH_0006_CONFIRMATION_v1.0.0.yaml;
citation-appraisals/PMC6473265-v1.0.0.yaml;
citation-appraisals/PMC10147771-v1.0.0.yaml]

Three canonical-source appraisals are founder-authorized batch-0007
`context_only` evidence. SCAN demonstrates that within-array normalization
without external reference samples is technically feasible, but its benchmarks
do not validate a PAM50 decision rule. A 5,715-tumor classifier comparison shows
that a simpler three-gene model can be empirically robust while retaining
dataset-level scaling and an unknown biological truth. A two-cohort Swedish
comparison reports only poor-to-moderate four-class IHC/PAM50 agreement, with
substantially better agreement only after Luminal A and B are collapsed.
Collectively, these studies strengthen the rationale for patient-independent
preprocessing, explicit label ambiguity, uncertainty, and abstention. They do not
validate the proposed NaS method or show clinical utility.
[FOUNDER_CITATION_APPRAISAL_BATCH_0007_CONFIRMATION_v1.0.0.yaml;
citation-appraisals/PMC3283537-v1.0.0.yaml;
citation-appraisals/PMC3508193-v1.0.0.yaml;
citation-appraisals/PMC7791620-v1.0.0.yaml]

Five further citation-pass reports are founder-authorized batch-0008
`context_only` appraisals. AMBER directly demonstrates that three-marker IHC
surrogates reproduce basal-like PAM50 labels more reliably than Luminal A,
Luminal B, or HER2-enriched labels, while still leaving PAM50 as an unverified
comparator.
PurIST shows that a fixed eight-pair, within-patient classifier can avoid
receiving-cohort normalization and expose a confidence gradient, but its
pancreatic clustering labels are not breast-subtype truth. A 19-study lung
comparison shows that rank-based classifiers can cross platforms while
performance weakens for a less distinct molecular boundary. A paired-platform
TCGA study isolates technological effects in the same BRCA patients and supports
feature-specific normalization, but trains generic models against pre-existing
PAM50 labels rather than executing a locked PAM50 procedure. The peer-reviewed
mFISHseq report adds external analyses and fuller reporting but remains subject to
adaptive development, correlated comparators, and unvalidated treatment models.
It supersedes its already appraised preprint for citation purposes and is not an
independent replication.
[FOUNDER_CITATION_APPRAISAL_BATCH_0008_CONFIRMATION_v1.0.0.yaml;
citation-appraisals/PMC4779705-v1.0.0.yaml;
citation-appraisals/PMC6942634-v1.0.0.yaml;
citation-appraisals/PMC7299291-v1.0.0.yaml;
citation-appraisals/PMC11265146-v1.0.0.yaml;
citation-appraisals/PMC11696812-v1.0.0.yaml]

### Quality appraisal

Each eligible full text is assessed across population selection, specimen and
measurement, classifier implementation, reference comparator, analysis and
statistics, validation and transportability, and reporting and reproducibility.
High-risk defects cannot be averaged away. Only evidence with low-risk analysis
and transport validation may serve as anchor evidence. AI-assisted extraction is
disclosed, and the founder authorizes each locked appraisal.
[REVISED_FULL_TEXT_APPRAISAL_PROTOCOL.md]

### Publication-version reconciliation

Preprints and their versions of record are preserved as separate appraisal
artifacts but cannot be counted as independent studies without a distinct
contribution. A publication-version link requires an independently checksummed
proposal and exact founder confirmation. Materialization verifies the packet,
proposal, earlier and canonical screening identifiers, and inclusion of the
canonical appraisal in the confirmed batch. Reconciliation then requires both
locked appraisals, exact normalized titles, PMIDs, and DOIs; prohibits one record
from participating in multiple links; and emits a family receipt reporting both
the appraisal count and the deduplicated unique-study count. For mFISHseq,
`PMC10723508` is founder-authorized as the preprint of `PMC11696812`. The
reconciliation preserves 53 appraisal reports and counts 52 unique studies.
[citation-version-link-proposals/batch-0008/PMC10723508-to-PMC11696812-v1.0.0.yaml;
FOUNDER_CITATION_APPRAISAL_BATCH_0008_CONFIRMATION_v1.0.0.yaml;
citation-publication-version-reconciliation-v1.0.0.yaml]

### Citation saturation and claim synthesis

Seven sequential bidirectional citation passes are now materially closed. Passes
1–5 added eligible evidence identities. Pass 6 screened 38 genuinely new records
and added zero eligible identities. Pass 7 independently re-queried the same
81-identity seed boundary; all 8,227 non-seed records were already covered by the
direct search or prior founder ledgers, leaving zero new candidates. Passes 6 and
7 are therefore consecutive zero-yield passes. The typed cumulative validator
reports 81 eligible identities, 68 completed appraisals, 13 explicit access
restrictions, zero pending records, `review_status=complete`, and
`stopping_rule_satisfied=true`.
[revised_evidence_review_progress.yaml;
citation-chain/pass-0006-closure.yaml;
citation-chain/pass-0007-closure.yaml]

A founder-authorized working claim-level synthesis reconciles all 68 active
appraisals: 22 supporting and 46 context-only, with no anchor evidence. It
distinguishes supporting, limiting or contradictory, null or negative, and
contextual evidence across eight claims. The authorization is checksum-bound
to the saturated progress receipt and fails validation if an appraisal is omitted,
an unknown identity is cited, or context-only evidence is presented as supporting.
The updated novelty memorandum places question `0.3.0` on hold: broad components
are prior art, while the exact independently calibrated and unchanged externally
validated reliability contract remains unresolved. This working synthesis
authorizes no affirmative novelty, data access, clinical claim, or publication.
[saturated_evidence_synthesis_proposal_v1.0.0.yaml;
FOUNDER_SATURATED_EVIDENCE_SYNTHESIS_CONFIRMATION_v1.0.0.yaml;
saturated_evidence_synthesis_v1.0.0.yaml; novelty_memorandum.yaml]

### Proposed analytical procedure

Status: `placeholder—method dependencies unresolved`

The draft procedure is defined in reliability specification `0.1.0`, but exact
centroids, external reference values, platform transformations, technical-error
calibration, numerical tolerances, and reliability thresholds remain unresolved.
No molecular execution is authorized.

Dependency audit `1.0.0` identifies one verified centroid candidate: official
Bioconductor `genefu` 2.44.0 distributes the historical unscaled PAM50 model
under Artistic-2.0, and both the release archive and embedded model member are
checksummed. This resolves candidate provenance, not method approval.

The exact package member was subsequently imported through frozen revision
`2843a6e`. Import validation reconciled all 250 finite coefficients, five subtype
vectors, 50 canonical genes, and the three prespecified historical aliases. The
canonical candidate SHA-256 is
`51a1b186a32ba02fa61a001ee7dc7e21876b9b09f78cb7eb8f0fdd068b4f8c2b`.
This is coefficient-conformance evidence only; the artifact remains
founder-unapproved and cannot execute on study data.

The historical design still lacks an independently validated platform-matched
centering reference and independent RNA-seq technical-error calibration.
GSE96058's 136 technical replicates are public, but using them for calibration
would adapt the method to the designated external-validation source. A separate
144-pair NanoString study reports aggregate repeatability but does not release
the underlying gene-level data. Molecular execution remains on hold pending the
founder's choice among retaining historical PAM50, changing to MPAM50, or
preserving the question while acquiring independent calibration.
[method_dependency_audit_proposal_v1.0.0.yaml;
FOUNDER_METHOD_DEPENDENCY_DECISION_PACKET_v1.0.0.md]

The founder subsequently selected Route C exactly. Checksum-bound activation
preserves question `0.3.0`, stages the verified centroid candidate, and activates
the independent-calibration acquisition plan. It selects no calibration source
and leaves the fixed reference, technical-error model, thresholds, and numerical
conformance unresolved. It authorizes no molecular or outcome access, classifier
execution, clinical use, or publication.
[FOUNDER_METHOD_ROUTE_DECISION_v1.0.0.yaml;
method_route_activation_v1.0.0.yaml]

A checksum-bound technical-calibration acquisition contract now makes that
dependency executable as a governance gate. A calibration source must be
independent of classifier training and external validation; provide lawful
participant-level technical pairs and stable pair identifiers; distinguish
measurement repeats from biological, spatial, longitudinal, or treatment-related
change; cover the complete classifier panel; and expose sufficient assay,
normalization, preprocessing, missingness, and quality-control metadata to freeze
the measurement bridge. Minimum replicate-pair count and precision targets require
a prospective power analysis.

No assessed path currently meets every requirement. GSE96058 remains reserved for
unchanged external validation. The Hurson et al. resource reports 144 same-RNA
NanoString pairs but does not publicly expose participant-level values. No
independent RNA-seq source has yet passed due diligence, and a prospective NaS
experiment has not been designed or authorized. The contract therefore selects
no source and authorizes no molecular access, outcome access, threshold selection,
method execution, or external contact.
[technical_calibration_acquisition_plan_v1.0.0.yaml;
TECHNICAL_CALIBRATION_READINESS_v1.0.0.md]

A bounded official-metadata scout found two additional small RNA-seq replicate
resources. GSE60788 reports 49 breast tumors and six labeled technical replicates
with public processed expression, but its sample independence from the GSE96058
external-validation cohort is not yet established and statistical adequacy cannot
be assumed from six pairs. GSE130397 reports triplicate FFPE libraries for only
two ER-positive source specimens under Illumina Access and NuGEN Ovation methods;
it may inform within-specimen or library-method variance but cannot represent
patient-level subtype-margin diversity. Neither source was selected, no expression
values were inspected, and no data inquiry was sent.
[technical_calibration_source_scout_v1.0.0.yaml;
UNSENT_CALIBRATION_DATA_INQUIRIES_v1.0.0.md]

A subsequent field-isolated lineage audit streamed the official GEO family SOFT
representations without retaining sample identifiers, titles, rows, expression
values, outcomes, or raw artifacts. It reconciled 55 records and six linked
replicates in GSE60788, 3,409 records and 136 linked replicates in GSE96058, and
21 records and 11 linked replicates in GSE130397. GSE60788 and GSE96058 shared
zero public GEO sample accessions and zero public sample titles. This narrows the
metadata uncertainty but does not establish biological-specimen or RNA-extraction
non-overlap; authoritative lineage confirmation remains required. No calibration
source was selected.
[calibration_lineage_receipt_v1.0.0.yaml;
CALIBRATION_LINEAGE_REPORT_v1.0.0.md]

A deterministic precision-planning component now supports future replicate-study
design. It searches for the smallest observed pair count whose expected Wilson
interval meets a declared half-width and inflates observations by an explicit
cluster design effect. A synthetic fixture returns 141 independent pairs for
hypothetical 0.90 label retention, 95% confidence, and ±0.05 expected precision.
This fixture is algorithm verification, not a sample-size recommendation or PAM50
evidence. Continuous expression error, subtype-specific performance, margin and
abstention calibration, missingness, multiplicity, and clinical utility require
separate design objectives.
[technical_calibration_precision_scenario_HYPOTHETICAL.yaml;
TECHNICAL_CALIBRATION_PRECISION_TOOL_v1.0.0.md]

Phase 1 prospective design `0.1.0` now separates three technical roles. An
excluded feasibility pilot may estimate variance, attrition, failures, and batch
structure; an independent same-RNA arm would calibrate post-extraction technical
reliability; and an optional matched-homogenate arm would estimate extraction
variation separately. The primary proposed estimand is subtype-label retention,
with secondary abstention-state, score-margin, gene-level error, and failure-rate
estimands. Pilot specimens cannot enter final calibration, and GSE96058 remains
external-validation-only.

No assay, specimen, laboratory, pair count, budget, source, or threshold is
selected. The prior 141-pair output remains a hypothetical software fixture, not
a study recommendation. Founder, molecular, statistical, governance, operational,
and budget review remain required before any external contact, procurement,
specimen work, data access, or execution.
[prospective_calibration_experiment_design_v0.1.0.yaml;
PROSPECTIVE_CALIBRATION_DESIGN_REPORT_v0.1.0.md]

The founder approved that design for planning only. A checksum-bound activation
authorizes internal scientific, statistical, operational-scenario, and
budget-scenario planning while preserving zero authority for contact, quotations,
spending, specimens, data access, source selection, thresholds, or execution.

Three provenance-bound hypothetical scenarios jointly evaluate binary
label-retention precision and multiplicity-adjusted continuous paired-error
precision. After their declared attrition and clustering assumptions, the lean,
balanced, and high-precision scenarios require 82, 185, and 945 attempted pairs
and twice as many measurements. The balanced scenario is governed by continuous
precision at 166 effective pairs rather than binary retention at 141. These
figures are planning outputs from assumed probabilities, variance, precision,
multiplicity, attrition, and clustering; they are not NaS data, approved sample
sizes, laboratory commitments, budgets, or study results.
[prospective_calibration_planning_activation_v1.0.0.yaml;
CALIBRATION_SCENARIO_REPORT_v1.0.0.md]

Standing founder autonomy now permits reasonable, reversible internal method
decisions without serial approval packets while preserving final human review
and hard stops for external, paid, controlled, irreversible, clinical, or
publication actions. Under that authority, Phase 1 planning freezes bulk RNA
sequencing as the platform family, same-RNA independent library preparation and
sequencing as the primary repeat architecture, and repeated extraction as a
separate sensitivity arm. A 30-pair, 30-source feasibility pilot is provisionally
specified to estimate nuisance parameters only and is permanently excluded from
primary calibration and external validation. Marginal receptor, RNA-quality,
blinded-margin, and processing-position quotas guard against convenience
sampling. One primary label-retention estimand is separated from a
Holm-controlled confirmatory continuous family, descriptive failure measures,
and exploratory gene-level FDR analyses. These are internal protocol decisions,
not executed evidence, an approved final pair count, or an analytical-validity
claim.
[phase_one_internal_planning_bundle_v1.0.0.yaml;
PHASE_ONE_INTERNAL_PLANNING_REPORT_v1.0.0.md]

A repository-evidence-only platform audit verifies complete governed PAM50 gene
mapping in GSE96058 and agreement with the candidate centroid panel. Seven of
eight broader compatibility criteria remain partial or pending: the assay
transformation and normalization bridge, platform-matched fixed reference,
performance-blind GSE96058 input bridge, assay-specific QC cutoffs, prospective
batch/run lineage, independent numerical conformance, and calibration-artifact
storage receipt. The audit therefore returns `changes_required`. No molecular
values or outcomes were parsed, and gene presence is not interpreted as assay
equivalence or analytical validity.
[platform_compatibility_audit_receipt_v1.0.0.yaml;
PLATFORM_COMPATIBILITY_AUDIT_REPORT_v1.0.0.md]

A synthetic-only deterministic kernel now tests the proposed state machine without
patient data. It requires exactly the historical 50-gene panel, resolves only the
three declared historical aliases, fails closed on incomplete, ambiguous, or
nonfinite inputs, calculates Spearman correlations against five supplied synthetic
centroids, preserves the best and runner-up scores and margin, and performs exactly
50 leave-one-gene-out sensitivity runs. Caller-supplied synthetic thresholds map
valid results to `reliable` or `unstable`; invalid scores or perturbations map to
`unclassifiable`, and input failures map to `insufficient_data`. Every state other
than `reliable` abstains. The kernel accepts only identifiers beginning
`SYNTHETIC-` and labels its output `synthetic_method_validation_only`. These are
software-verification capabilities, not an approved analytical method or scientific
result.

The kernel can also apply an explicit synthetic technical-error panel. Each panel
declares its gene order, generator seed, and generation description; output
provenance binds its complete contents by SHA-256. Leave-one-gene-out and
technical-error totals, valid runs, and retained-label counts are reported
separately and must reconcile to aggregate repeatability. A nonfinite or otherwise
invalid technical perturbation remains in the denominator and makes the result
unclassifiable rather than disappearing. These vectors test execution and failure
logic only; they are not an empirical model of laboratory error and cannot select
the real reliability threshold.

Synthetic batch execution is defined as repeated independent single-sample calls;
the scoring function receives no batch statistic or companion expression. The
batch contract rejects duplicate identifiers and binds ordered inputs by SHA-256
while leaving each sample result bound only to its own input. Automated tests show
that the complete target result is unchanged when processed alone, before or after
an unrelated synthetic companion, or after batch-order reversal. This establishes
software-level companion invariance, not analytical performance or transport in a
real cohort.

### Data sources, cohort, and statistical analysis

Status: `placeholder—data access not authorized`

TCGA-BRCA is the proposed discovery source and processed SCAN-B GSE96058 is the
candidate external-validation source. Cohort construction, estimands, statistical
models, sensitivity analyses, multiplicity handling, and figure specifications will
be inserted only after the evidence gate and preregistration.

A governed source-level metadata audit queried the current GDC service status and
case-field mapping, ran a zero-row aggregate file query, and issued HEAD-only checks
for the declared GSE96058 annotation and processed-expression artifacts. GDC Data
Release 45.0 exposed 1,231 open TCGA-BRCA STAR-count files, and both GEO artifacts
were available. None of the 770 indexed GDC case-field names identified receptor
status, and source-level metadata could not enumerate expression-table genes.

During pre-gate endpoint characterization, a public GEO family response was found
to co-mingle receptor and replicate annotations with treatment, survival,
published subtype, and prediction fields. That response was not retained and no
outcome analysis was performed. This disclosure remains part of the audit trail.

The founder subsequently authorized a fail-closed field-isolation procedure.
Executed code revision `2f0b15f…74d0c` streamed one registered BCR patient table,
one deterministic STAR-count file, the GSE96058 processed-expression
representation, and its family SOFT representation. The parser retained only
aggregate derivatives and discarded all raw representations. It parsed no
expression or outcome values and retained no patient/sample record. Both source
representations contained all 50 historical PAM50 genes without ambiguous panel
mappings. In TCGA, ER, PR, and HER2 were present for 1,049, 1,048, and 983 of
1,098 records, respectively; all three were present for 981. In GSE96058, the
corresponding counts were 3,189, 3,051, and 3,281 of 3,409, with all three present
for 2,931.

Audit `1.0.0` could not classify replicate state under its original field
allowlist. The founder separately authorized audit amendment `1.0.1`, which
accepted only sample titles matching the declared `F<number>` or
`F<number>repl` grammar, reduced them transiently to aggregate linkage counts,
and normalized only the declared `0`/`1`/`NA` receptor categories. All four
source-representation checksums matched audit `1.0.0`. The amended audit
classified 3,273 primary records and 136 technical replicates, linked every
technical replicate to a primary, left zero records unclassified, and returned
`pass`. No title or sample accession was retained. These are input-feasibility
findings, not cohort, molecular, diagnostic, prognostic, or treatment results.
[metadata_feasibility_receipt_v1.0.0.yaml;
METADATA_FEASIBILITY_REPORT_v1.0.0.md;
field_isolated_metadata_receipt_v1.0.0.yaml;
FIELD_ISOLATED_METADATA_REPORT_v1.0.0.md;
field_isolated_metadata_receipt_v1.0.1.yaml;
FIELD_ISOLATED_METADATA_REPORT_v1.0.1.md]

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

### Non-neoplastic tissue contamination

Paired tumor and adjacent benign tissue from 55 patients showed that increasing
non-neoplastic contribution changed classifications across three published
genomic predictors. In the studied PAM50 implementation, contamination shifted
calls toward less aggressive subtypes and lower ROR-S categories. Correction
changed subtype in five of 24 tumors with measured cellularity and raised risk
category in eight; directionally similar patterns appeared in public cohorts.

This supports tumor purity as a distinct pre-analytic reliability input. The
mixtures were largely simulated from expression profiles, commercial assays were
not reproduced exactly, and cohort-wide correction amounts were selected partly
by outcome performance because individual purity was unavailable. It does not
justify an outcome-tuned or one-size-fits-all correction. [PMID:21718502; revised
appraisal PMC3151208-v1.0.0]

### Population and preprocessing consistency

Three intrinsic gene sets and three adjustment choices were compared in 169 Han
Chinese tumors. PAM50 was less sensitive than the older signatures to systematic
microarray correction, but its agreement between unadjusted, gene-centered, and
DWD implementations ranged from kappa 0.66 to 0.80. Hu 306 versus PAM50 agreement
fell from 0.85 with gene centering to 0.67 with DWD.

Because centering and DWD use the study collection, detailed clinical analysis
selected only consistently classified cases, and survival included only ten
events, this record is `context_only`. It reinforces preprocessing dependence and
population transport concerns without supplying a fixed reference or truth label.
[PMID:23046482; revised appraisal PMC3445863-v1.0.0]

### Clinical-grade Prosigna analytical validation

A CLSI-guided Prosigna study used prespecified SOPs and acceptance criteria across
three sites, six operators, reagent lots, runs, independent pathology review, and
serial FFPE sections. RNA-level SD was below one ROR unit; the full tissue workflow
had total SD 2.9 ROR units. Cross-site subtype concordance averaged 97%, and risk
category concordance was 90% to 93%.

The interferent experiment is equally important: when required macrodissection
was omitted, adjacent non-tumor tissue lowered ROR by as much as 19 units and
changed five of 23 subtype calls. The study supports a locked assay's analytical
repeatability while showing that pre-analytic failure can dominate instrument
noise. Manufacturer employment, ownership, patents, only three sites, and lack of
independent postmarket replication prevent an anchor role. [PMID:24625003;
revised appraisal PMC4008304-v1.0.0]

### Explicit ambiguous and unclassifiable classifier states

A four-model PLS/logistic classifier was developed in 139 PAM50 prototype arrays
and evaluated in 535 tumors from three Han Chinese microarray studies. With its
prespecified probability threshold of 0.5, the method preserved both ambiguous
and unclassifiable states rather than forcing every tumor into a subtype.
Agreement with PAM50 in the pooled validation data was kappa 0.541, with 125
tumors—approximately one quarter—unclassified and 55 ambiguous. Excluding
unclassified tumors raised kappa to 0.829; lowering the threshold post hoc to 0.1
reduced the unclassified rate to 2% and yielded kappa 0.704.

This is `context_only` prior art for explicit classifier abstention. It shows why
coverage, ambiguity, and conditional agreement must be reported together:
discarding hard cases can make agreement appear substantially stronger. PAM50 was
treated as the reference rather than biological truth, preprocessing remained
study-dependent, and the revised threshold was not calibrated in a further
independent cohort. [PMID:24490149; revised appraisal PMC3893734-v1.0.0]

### Cohort-adaptive clinical-concordance optimization

PCA-PAM50 was evaluated in an in-house 118-tumor laser-microdissected RNA-seq
cohort, 1,097 TCGA tumors, and approximately 1,000 METABRIC tumors. Compared with
conventional PAM50, clinical/intrinsic concordance increased by 6.0, 9.3, and
8.7 percentage points, respectively. In TCGA, 107 conventionally classified
Luminal A tumors switched to Luminal B and had higher MKI67 expression and worse
progression-related outcomes. The corresponding METABRIC switched-case survival
contrast was not consistently significant.

The method is `context_only`: it infers expression-based ER status, repeatedly
selects ER-positive cases to balance each cohort, and then recenters genes
iteratively. Its output can therefore change with the accompanying test cohort.
Moreover, the clinical Luminal A/B comparator partly uses an expression-derived
MKI67 cutoff calibrated across the studied data. Greater agreement with that
surrogate cannot establish a patient-independent or biologically correct subtype
call. [PMID:31138829; revised appraisal PMC6538748-v1.0.0]

### Whole-transcriptome subtype-purity modeling

A semi-supervised NMF study merged TCGA and METABRIC and modeled 1,178 PAM50
Luminal A tumors using 11,379 common transcripts. The lowest versus highest
quartile of Luminal A adherence had more adverse clinicopathologic features,
approximately threefold greater TP53 mutation prevalence, and adjusted overall-
mortality hazard ratio 2.08. The report also retained an important negative
finding: tumors with predominant basal-like admixture did not have shorter
survival than Luminal B- or HER2-admixed groups.

This analysis is `context_only`. The complete patient matrix and existing PAM50
labels jointly train the factorization; hyperparameters and quartiles are selected
within the evaluated cohorts. Bulk transcriptomes also cannot establish whether
the apparent mixture arises within cells, between spatial regions, from tumor
purity, or from processing. The authors explicitly identify single-cell or
spatial profiling as necessary to resolve that construct. The prognostic
association is hypothesis-generating and does not establish treatment utility.
[PMID:37209182; revised appraisal PMC10241706-v1.0.0]

### Population-cohort centering sensitivity

The Nurses’ Health Study and NHSII evaluated modified-median and subgroup-specific
gene centering in 882 archival tumors. Calls agreed in 86% of tumors (kappa 0.81),
but modified-median centering changed 44 tumors from Luminal B to Luminal A and
produced 36 additional Normal-like calls relative to subgroup-specific centering.
Four-class agreement with IHC surrogates was poor (kappa 0.32), improving only
after Luminal A and B were collapsed.

This large epidemiologic application is `context_only` for the NaS method.
Both centering strategies depend on the study cohort, the IHC comparator is not
intrinsic-subtype truth, and Ki-67 was missing for 545 tumors and replaced by
histologic grade. Recurrences were self-reported, ROR-PT was prognostic only in
crude analyses, and population transport beyond predominantly White US nurses
remains untested. [PMID:30591591; revised appraisal PMC6449178-v1.0.0]

### NanoString normalization and low-margin discordance

A four-dataset NanoString study compared an iterative RUVSeq workflow with
nSolver, NanoStringDiff, and RCRnorm. In the 1,649-sample Carolina Breast Cancer
Study, RUVSeq removed more study-phase structure while retaining ER-associated
biology. PAM50 calls from RUVSeq and nSolver agreed in 91% of tumors
(kappa 0.87; 95% CI 0.85–0.90). Approximately half of discordant calls had low
algorithm confidence, and half had competing-centroid correlation differences
below 0.1.

This is `supporting` evidence that preprocessing error and classifier-margin
uncertainty interact. It also supplies explicit below-limit-of-detection and
housekeeping-gene QC, public code, and cross-dataset checks. The normalization
workflow is intentionally retuned using each dataset’s technical and biological
structure, so it cannot itself be the frozen patient-independent preprocessing
contract. [PMID:32789507; revised appraisal PMC8138885-v1.0.0]

### Fixed stable-reference single-sample scoring

The stingscore method derives a stable-gene reference from TCGA carcinomas and
CCLE carcinoma cell lines and computes rank-based signature scores for one sample
without an accompanying cohort. Stable-gene behavior was evaluated across 14
datasets with approximately 13,000 samples, and reduced-panel accuracy was tested
for 3,009 signatures across 75,012 perturbation measurements. The implementation
and fixed stable-gene list are available in Bioconductor.

This is `supporting` prior art for true single-sample, fixed-reference scoring.
It materially supports the feasibility of the NaS architecture while preventing
single-sample rank scoring from being claimed as novel. Stability was poor in
blood, most targeted-panel checks were down-sampled from transcriptomes, targeted
and whole-transcriptome scores retained offsets, and a docetaxel example had only
24 patients without an independent holdout. It does not calibrate PAM50 call
reliability or abstention. [PMID:32997146; revised appraisal
PMC7641762-v1.0.0]

### Confounded microarray–NanoString platform discordance

A Taiwanese study compared PAM50 calls for 64 patients profiled by both Affymetrix
microarray and NanoString nCounter workflows. Only 41 patients (65%) received the
same subtype (kappa 0.60); agreement relative to nCounter was 25% for Luminal A,
43% for basal-like, 81% for HER2-enriched, and 100% for Luminal B.

This is `context_only`, not a clean platform-accuracy estimate. Microarray used
fresh-frozen tissue and NanoString used later archived FFPE tumor-enriched
sections; each platform was centered within a different cohort, and DWD,
housekeeping genes, probe regions, and preprocessing also differed. Treating
nCounter as a gold standard cannot identify which discordant call is correct.
The result demonstrates workflow non-equivalence while leaving assay, specimen,
spatial, and algorithmic effects inseparable. [PMID:34387660; revised appraisal
PMC8385191-v1.0.0]

### Integrated annotation software without breast validation

classifieR wraps PAM50, inferred OncotypeDX, cell-composition, pathway, and
transcription-factor tools in an R/Shiny interface accepting several expression
platforms. The report shows a 78% speed improvement and 46% lower memory use for
one 156-sample example.

The software is `context_only` for the research question. It does not report a
defined breast validation population, PAM50 agreement, calibration, uncertainty,
abstention, or clinical outcomes. Backend packages were modified, many settings
are hidden, hosted versions update automatically, and the web server is
research-use-only without a pinned source release. It establishes that integrated
annotation interfaces exist, not that their breast predictions are reliable.
[PMID:35361119; revised appraisal PMC8974006-v1.0.0]

### Spatially guided mFISHseq and consensus subtyping

The mFISHseq preprint combines four-marker RNA-FISH, annotated laser-capture
microdissection, and total RNA sequencing in 1,082 archival tumors. Its IHC
biomarker thresholds were evaluated with a 70:30 split. Among 1,013 tumors used
for subtype analysis, single-sample agreement between multigene classifiers was
substantial but imperfect; a three-classifier vote reclassified 305 tumors (30%)
relative to IHC surrogates and produced outcome-separated groups.

This is promising preanalytic and spatial `context_only` evidence. The 293-gene
classifier, consensus scheme, extensive survival analyses, and treatment-response
exploration used the full cohort rather than an unchanged external subtype holdout.
Majority voting among correlated classifiers is not a truth standard. A reported
T-DM1 model with AUC 0.96 used only 52 trial patients and awaits independent
prespecified validation. The work is a non-peer-reviewed preprint; numerous
authors are employees, inventors, or advisers of the company developing the test,
and code and patient-level data are available only by request. [PMID:38105959;
revised appraisal PMC10723508-v1.0.0]

### Modality-disjoint latent simulation

The IEEE CDLS report combines non-overlapping TCGA-BRCA, BCSC, and METABRIC
cohorts in a shared latent space and applies five PPO-guided refinement steps with
kNN feedback. It reports calibration, multi-seed stability, five-fold
cross-validation, and transparent warnings that the representation-space
trajectories are non-causal and not clinical digital twins.

This evidence is `context_only`. No patient has the complete multimodal feature
set, the METABRIC transfer evaluation reinitializes and fine-tunes part of the
model, and BCSC cohort construction is incompletely reported. Several central
numbers also fail internal consistency checks: the four listed held-out
accuracies average approximately 0.891 rather than the reported 0.876, and
BCSC-assisted zero-shot METABRIC accuracy is reported as 0.840, 0.810, and 0.818
in different locations. The paper establishes that uncertainty trajectories,
latent refinement, modality-absence encoding, and research interfaces are active
prior art, but it does not validate a fixed patient-level reliability or
abstention rule. [PMID:42172162; revised appraisal
PMID42172162-v1.0.0]

### NaS analytical results

Status: `placeholder—no molecular or outcome data accessed`

No NaS-generated subtype, reliability, survival, concordance, calibration, or
clinical-association result exists for question `0.3.0`.

## Discussion

Status: `working interpretation—must not be cited as a result`

The saturated evidence set contains 81 eligible identities: 68 completed
appraisals, 13 explicit access restrictions, and zero pending records. The
completed appraisals comprise 22 supporting and 46 context-only studies. They
show that the broad problem is established:
PAM50 calls can be sensitive to technical error, cohort-dependent centering, and
preprocessing-specific RNA-seq references. They also show that fixed external
references, pairwise-ratio classifiers, and supervised models already support
single-sample execution, recurrence-risk stratification, group-level prognostic
separation, runner-up margins, perturbation-stability labeling, multi-method
comparison, discordance entropy, empirical permutation confidence, explicit
Ambiguous or Not Assigned states, direct commercial-assay discordance, and
technical-versus-spatial repeatability differences. The latest batch additionally
adds permutation confidence, preservation-dependent expression comparability,
rank-pair portability, targeted assay bridging, and spatial subtype heterogeneity
as prior art. A defensible NaS contribution cannot therefore be merely a
classifier, risk predictor, margin, perturbation experiment, ensemble-disagreement
score, uncertainty test, abstention label, or cohort-derived purity score. It
would need to reproduce a fixed classifier unchanged, calibrate perturbations
from independent technical evidence, define a reliability estimand and thresholds
without outcome tuning, validate transport in an independent cohort, and abstain
prospectively when the assignment is not analytically reliable.

Sequential citation chaining is complete under the locked stopping rule: passes
6 and 7 were consecutive zero-yield passes. The founder-authorized saturated
synthesis preserves eight claim-level dispositions and the novelty memorandum
retains a hold. Thirteen eligible identities, including AIMS and the IOP article,
remain explicitly access-restricted and were not inferred from abstracts. Evidence
saturation does not itself authorize a novelty or scientific conclusion.

## Limitations

Status: `working`

- Primary screening and citation passes 1–7 are complete. The saturated evidence
  state contains 81 eligible identities, 68 completed appraisals, 13 access
  restrictions, and zero pending records. Passes 6 and 7 were consecutive
  zero-yield passes, satisfying the locked stopping rule.
- Twelve of 13 priority records have completed question-specific appraisal: seven
  from verified CC-BY retrieval and five through governed read-only review.
- AIMS is identity-verified but subscription-restricted. It remains unappraised,
  and no absence-of-prior-art claim may be inferred from that access boundary.
- Field-isolated audit `1.0.1` closed PAM50 gene presence, receptor completeness,
  and GSE96058 primary/technical-replicate linkage. It did not establish assay
  equivalence, numerical compatibility, a valid transformation, or classifier
  validity.
- No centroid, reference, transformation, technical-error model, or threshold is locked.
- Public representations containing molecular and prohibited metadata fields were
  transiently transferred through the authorized projection gate. No molecular or
  outcome value was parsed, retained, or analyzed for question `0.3.0`.
- No external statistical or pathology review has been completed.
- The current text is an internal working draft and has not undergone peer review.

## Conclusions

Status: `placeholder`

No scientific or clinical conclusion is authorized. This section will remain empty
until method lock, preregistration, analysis, sensitivity checks, and internal
reviews are complete.

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
13. Tan AC, et al. Multiclass prediction with partial least square regression
    for gene expression data: applications in breast cancer intrinsic taxonomy.
    *Biomed Res Int.* 2013;2013:248648.
    PMID:24490149. DOI:10.1155/2013/248648.
14. Raj-Kumar PK, et al. PCA-PAM50 improves consistency between breast cancer
    intrinsic and clinical subtyping reclassifying a subset of luminal A tumors
    as luminal B. *Sci Rep.* 2019;9:7956.
    PMID:31138829. DOI:10.1038/s41598-019-44339-4.
15. Kannan N, et al. Quantification of subtype purity in Luminal A breast cancer
    predicts clinical characteristics and survival. *Breast Cancer Res Treat.*
    2023;200:239–253. PMID:37209182. DOI:10.1007/s10549-023-06961-9.
16. Kensler KH, et al. PAM50 molecular intrinsic subtypes in the Nurses' Health
    Study cohorts. *Cancer Epidemiol Biomarkers Prev.* 2019.
    PMID:30591591. DOI:10.1158/1055-9965.EPI-18-0863.
17. Bhattacharya A, et al. An approach for normalization and quality control for
    NanoString RNA expression data. *Brief Bioinform.* 2021.
    PMID:32789507. DOI:10.1093/bib/bbaa163.
18. Foroutan M, et al. Stable gene expression for normalisation and single-sample
    scoring. *Nucleic Acids Res.* 2020.
    PMID:32997146. DOI:10.1093/nar/gkaa802.
19. Horng CC, et al. Molecular subtyping of breast cancer intrinsic taxonomy with
    oligonucleotide microarray and NanoString nCounter. *Biosci Rep.* 2021.
    PMID:34387660. DOI:10.1042/BSR20211428.
20. Quinn GP, et al. classifieR: a flexible interactive cloud-application for
    functional annotation of cancer transcriptomes. *BMC Bioinformatics.*
    2022;23:114. PMID:35361119. DOI:10.1186/s12859-022-04641-x.
21. Paul ED, et al. Multiplexed RNA-FISH-guided laser capture microdissection RNA
    sequencing improves breast cancer molecular subtyping, prognostic
    classification, and predicts response to antibody drug conjugates.
    *medRxiv* [preprint]. 2023. PMID:38105959.
    DOI:10.1101/2023.12.05.23299341.
22. Hezil N, et al. A digital twin-inspired closed-loop latent simulation framework
    for cross-cohort breast cancer subtype classification under modality-disjoint
    learning. *IEEE J Biomed Health Inform.* 2026. PMID:42172162.
    DOI:10.1109/JBHI.2026.3696086.

## Evidence-to-text ledger

| Manuscript location | Claim type | Supporting artifact | State |
|---|---|---|---|
| Introduction ¶1–9 | External methodological evidence | `literature/saturated_evidence_synthesis_v1.0.0.yaml`; 68 completed appraisals | supported; evidence review saturated |
| Introduction ¶10 | Study objective and boundary | `question/research_question.yaml`; `protocol/reliability_specification.yaml` | supported, method unresolved |
| Methods—governance | Authorization and prohibition | `question/phase_zero_plan_v0.3.0.yaml`; founder authorization | supported |
| Methods—metadata feasibility | Source-level and field-isolated input audits | `ingestion/metadata_feasibility_receipt_v1.0.0.yaml`; `ingestion/field_isolated_metadata_receipt_v1.0.0.yaml`; `ingestion/field_isolated_metadata_receipt_v1.0.1.yaml`; all audit reports | all five input-feasibility checks verified; method compatibility unresolved |
| Methods—search | Search and counts | `literature/search_receipt_v0.3.1.yaml`; queue receipt | verified |
| Methods—screening | Founder decisions | `revised-screening-progress/batch-0002.yaml`; founder confirmation | verified, complete |
| Methods—citation pass 1 | Founder decisions, identity routing, lawful-access appraisal, and closure | `citation-chain/pass-0001-decision-ledger.yaml`; `citation-chain/pass-0001-inclusion-reconciliation.yaml`; `citation-chain/pass-0001-closure.yaml` | pass closed; 32 eligible identities added; stopping count reset |
| Methods—citation pass 2 | Cumulative retrieval, founder screening, lawful access, appraisal, and closure | `citation-chain/pass-0002-decision-ledger.yaml`; `citation-pass-0002-full-text/appraisal-progress-v1.0.0.yaml`; `citation-chain/pass-0002-closure.yaml` | pass closed; 9 eligible identities added; 5 context only, 4 restricted |
| Methods—citation pass 3 | Cumulative retrieval, founder screening, lawful access, appraisal, and closure | `citation-chain/pass-0003-decision-ledger.yaml`; `citation-chain/pass-0003-closure.yaml` | pass closed; 7 eligible identities added; 5 appraised and 2 restricted |
| Methods—citation passes 4–5 | Cumulative retrieval, founder screening, lawful access, appraisal, and closure | `citation-chain/pass-0004-closure.yaml`; `citation-chain/pass-0005-closure.yaml` | passes closed; 3 eligible identities added; 2 appraised and 1 restricted |
| Methods—citation passes 6–7 | Zero-yield stopping-rule verification | `citation-chain/pass-0006-closure.yaml`; `citation-chain/pass-0007-closure.yaml`; `revised_evidence_review_progress.yaml` | two consecutive zero-yield passes; stopping rule satisfied |
| Methods—saturated synthesis | Founder-authorized claim-level evidence synthesis | `saturated_evidence_synthesis_v1.0.0.yaml`; `novelty_memorandum.yaml` | 81 eligible; 68 appraised; 13 restricted; novelty held |
| Methods—evidence-cap amendment | Founder authorization and appraisal routing | `FOUNDER_EVIDENCE_CAP_AMENDMENT_APPROVAL_v0.2.5.yaml`; `evidence-cap-amendment-activation-v0.2.5.yaml` | verified, active |
| Methods—citation lawful access | Repository retrieval and access routing | `citation-full-text/repository-access-batch-v1.0.0.yaml`; `citation-full-text/access-check-queue-v1.0.0.yaml`; `citation_appraisal_progress_v1.0.0.yaml` | 25 materialized, 0 ready, 4 restricted, 0 unresolved full texts |
| Results—citation appraisal batch 0001 | External evidence appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0001_CONFIRMATION_v1.0.0.yaml`; three files in `citation-appraisals/` | context only |
| Results—citation appraisal batch 0002 | Founder-authorized AI-assisted appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0002_CONFIRMATION_v1.0.0.yaml`; four files in `citation-appraisals/` | 2 supporting, 2 context only |
| Results—citation appraisal batch 0003 | Founder-authorized AI-assisted appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0003_CONFIRMATION_v1.0.0.yaml`; six files in `citation-appraisals/` | 4 supporting, 2 context only |
| Results—citation appraisal batch 0004 | Founder-authorized AI-assisted preprint appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0004_CONFIRMATION_v1.0.0.yaml`; `citation-appraisals/PPR1259744-v1.0.0.yaml` | supporting |
| Results—citation appraisal batch 0005 | Founder-authorized AI-assisted ephemeral appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0005_CONFIRMATION_v1.0.0.yaml`; `citation-appraisals/PMID23907291-v1.0.0.yaml` | context only |
| Results—citation appraisal batch 0006 | Founder-authorized AI-assisted publisher-PDF appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0006_CONFIRMATION_v1.0.0.yaml`; two files in `citation-appraisals/` | 2 context only |
| Results—citation appraisal batch 0007 | Founder-authorized AI-assisted canonical-source appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0007_CONFIRMATION_v1.0.0.yaml`; three files in `citation-appraisals/` | 3 context only |
| Results—citation appraisal batch 0008 | Founder-authorized AI-assisted canonical and durable-source appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0008_CONFIRMATION_v1.0.0.yaml`; five files in `citation-appraisals/` | 5 context only; mFISHseq pair counts once |
| Results—citation appraisal batch 0009 | Founder-authorized AI-assisted canonical-source appraisal | `FOUNDER_CITATION_APPRAISAL_BATCH_0009_CONFIRMATION_v1.0.0.yaml`; five files in `citation-appraisals/` | 5 context only |
| Results—mFISHseq publication-version link | Founder-authorized same-study decision | `citation-version-links/PMC10723508-to-PMC11696812-v1.0.0.yaml`; `citation-publication-version-reconciliation-v1.0.0.yaml` | materialized; the linked pair counts as one study |
| Methods—full-text access | Access and appraisal state | `revised_appraisal_progress_v0.4.0.yaml` | verified, accessible-set appraisal complete |
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
| Results—non-neoplastic contamination | External evidence appraisal | `revised-appraisals/PMC3151208-v1.0.0.yaml` | supporting |
| Results—population/preprocessing consistency | External evidence appraisal | `revised-appraisals/PMC3445863-v1.0.0.yaml` | context only |
| Results—Prosigna analytical validation | External evidence appraisal | `revised-appraisals/PMC4008304-v1.0.0.yaml` | supporting |
| Results—ambiguous/unclassifiable states | External evidence appraisal | `revised-appraisals/PMC3893734-v1.0.0.yaml` | context only |
| Results—clinical-concordance optimization | External evidence appraisal | `revised-appraisals/PMC6538748-v1.0.0.yaml` | context only |
| Results—whole-transcriptome purity | External evidence appraisal | `revised-appraisals/PMC10241706-v1.0.0.yaml` | context only |
| Results—population-cohort centering | External evidence appraisal | `revised-appraisals/PMC6449178-v1.0.0.yaml` | context only |
| Results—NanoString normalization | External evidence appraisal | `revised-appraisals/PMC8138885-v1.0.0.yaml` | supporting |
| Results—stable-reference scoring | External evidence appraisal | `revised-appraisals/PMC7641762-v1.0.0.yaml` | supporting |
| Results—cross-platform discordance | External evidence appraisal | `revised-appraisals/PMC8385191-v1.0.0.yaml` | context only |
| Results—integrated annotation software | External evidence appraisal | `revised-appraisals/PMC8974006-v1.0.0.yaml` | context only |
| Results—spatially guided mFISHseq | External evidence appraisal | `revised-appraisals/PMC10723508-v1.0.0.yaml` | context only |
| Results—modality-disjoint latent simulation | External evidence appraisal | `revised-appraisals/PMID42172162-v1.0.0.yaml` | context only |
| Results—NaS analysis | NaS-generated result | none | prohibited placeholder |
| Discussion ¶1–2 | Explicit interpretation | `saturated_evidence_synthesis_v1.0.0.yaml`; 68 completed appraisals and 13 access-restricted identities | founder-authorized working synthesis; novelty held |
| Conclusions | Scientific conclusion | none | prohibited placeholder |

## Revision log

| Version | Date | Change |
|---|---|---|
| 0.55.0-working | 2026-07-29 | Added the repository-evidence-only platform audit: complete 50-gene mapping is verified, while seven transformation, reference, QC, lineage, numerical-conformance, and storage criteria remain partial or pending. |
| 0.54.0-working | 2026-07-29 | Bound standing founder autonomy and froze the internal Phase 1 platform, excluded 30-pair pilot, marginal coverage, multiplicity, and symbolic-budget plans while preserving all execution and external-action stops. |
| 0.53.0-working | 2026-07-29 | Recorded founder-approved internal Phase 1 planning and three provenance-bound hypothetical multi-objective scenarios requiring 82, 185, or 945 attempted pairs; none is an approved sample size, budget, or result. |
| 0.52.0-working | 2026-07-29 | Reconciled stale pre-saturation prose and evidence-ledger rows to the frozen final state: 81 eligible identities, 68 appraisals, 13 restrictions, zero pending, seven closed passes, and the two-zero-yield stopping rule satisfied. |
| 0.51.0-working | 2026-07-29 | Entered Phase 1 with a typed, nonexecuting prospective calibration design: excluded pilot, primary same-RNA calibration, optional extraction sensitivity, five technical estimands, validation firewalls, and zero contact, spending, data access, or execution authority. |
| 0.50.0-working | 2026-07-28 | Recorded the frozen calibration-lineage audit: all declared GEO replicate labels reconcile and GSE60788/GSE96058 have zero public identifier overlap, but biological non-overlap remains unproven; no source or data access was authorized. |
| 0.49.0-working | 2026-07-28 | Recorded the founder's exact Route C decision and activated the independent-calibration hold under frozen revision `74b3f2a`; no source, method lock, data access, execution, clinical use, or publication is authorized. |
| 0.48.0-working | 2026-07-28 | Added a nondecisional technical-replicate precision calculator with expected Wilson intervals, design-effect inflation, fail-closed targets, and an explicitly hypothetical 141-pair software fixture. |
| 0.47.0-working | 2026-07-28 | Added a typed metadata-only calibration-source scout: GSE60788 and GSE130397 are relevant but ineligible small RNA-seq replicate resources; two narrowly scoped inquiry drafts remain unsent. |
| 0.46.0-working | 2026-07-28 | Added the checksum-bound technical-calibration acquisition contract: eight hard source requirements, four candidate paths, validation-leakage prohibitions, and a prospective power-analysis requirement; no source or route is selected and no data access or execution is authorized. |
| 0.45.0-working | 2026-07-28 | Materialized the route-neutral historical PAM50 candidate with 250 verified coefficients, exact source hashes, and zero execution authorization. |
| 0.44.0-working | 2026-07-28 | Added the checksum-bound method-dependency audit, verified the official `genefu` 2.44.0 centroid candidate, documented the unresolved fixed-reference and independent technical-error dependencies, and froze Routes A–C for founder review without authorizing molecular execution. |
| 0.43.0-working | 2026-07-28 | Materialized the founder-authorized saturated synthesis, updated the 81/68/13 evidence state and novelty hold, and preserved zero authorization for molecular access, outcomes, clinical claims, or publication. |
| 0.42.0-working | 2026-07-26 | Executed cumulative citation pass 3 from all 71 governed seeds, reduced 7,728 non-seed records to 593 new candidates, and froze advisory packets proposing seven inclusions and 586 exclusions with zero unclear; no founder decision or scientific conclusion was recorded. |
| 0.41.0-working | 2026-07-26 | Founder-authorized citation appraisal batch 0009, locked five context-only appraisals, formally accounted for four restrictions, closed citation pass 2, and updated the evidence state to 71 eligible, 61 appraisal-complete, 10 restricted, and zero pending. |
| 0.40.0-working | 2026-07-26 | Added synthetic batch execution as independent single-sample composition, with duplicate-identity rejection, ordered batch provenance, and tests proving that companion fixtures and batch order cannot change an individual result. |
| 0.39.0-working | 2026-07-26 | Extended synthetic-only method validation to explicit seed-bound technical-error panels with stable provenance hashes, family-level accounting, label-changing instability tests, and fail-closed invalid-run abstention; no empirical error model was approved. |
| 0.38.0-working | 2026-07-26 | Added the synthetic-only single-sample reliability kernel: exact-panel validation, alias handling, five-centroid Spearman scoring, top/runner-up margin, 50 leave-one-gene-out runs, explicit failure states, and abstention; no real method artifact, threshold, molecular access, or result was authorized. |
| 0.37.0-working | 2026-07-26 | Materially closed citation pass 1 from frozen receipt lineage; the bound review state is 62 eligible identities, 56 appraisal-complete, six access-restricted, zero pending, and zero consecutive zero-yield passes. |
| 0.36.0-working | 2026-07-26 | Added citation pass-2 cumulative retrieval and nondecisional screening: 7,135 non-seed records reduced to 2,479 genuinely new candidates, with nine proposed inclusions, 2,470 proposed exclusions, zero unclear, and exact founder confirmation pending. |
| 0.35.0-working | 2026-07-26 | Added founder-authorized field-isolated audit `1.0.1`: unchanged sources classified 3,273 primary records and 136 linked technical replicates with zero unclassified; all five input-feasibility checks pass while molecular/outcome execution remains prohibited. |
| 0.34.0-working | 2026-07-26 | Added founder-authorized field-isolated audit `1.0.0`: both sources contain all 50 PAM50 genes; receptor completeness is quantified for 1,098 TCGA and 3,409 GSE96058 records; replicate linkage remains unresolved and molecular/outcome execution remains prohibited. |
| 0.33.0-working | 2026-07-26 | Materialized founder-confirmed citation appraisal batches 0002–0008, closed citation pass 1 at 25 appraised and 4 restricted records, bound delayed appraisals to stable source receipts, and reconciled 53 appraisal reports to 52 unique studies. |
| 0.32.0-working | 2026-07-26 | Closed the final citation full-text access check for CC BY PMID 20181526 after official publisher, Unpaywall, Europe PMC, Crossref, and Elsevier API routes failed to provide a reproducible article body; citation state is 3 appraised, 22 ready, 4 restricted, and 0 awaiting full text. |
| 0.31.0-working | 2026-07-26 | Added checksum-bound publication-version authorization and unique-study reconciliation so the mFISHseq preprint and version of record cannot be double-counted. |
| 0.30.0-working | 2026-07-25 | Added five checksum-bound batch-0008 proposals and the explicit mFISHseq preprint/version-of-record non-duplication boundary. |
| 0.29.0-working | 2026-07-25 | Added the five-request source-level metadata audit, its `changes_requested` feasibility finding, and the transparent pre-gate endpoint-characterization disclosure. |
| 0.28.0-working | 2026-07-25 | Added three checksum-bound, non-authoritative batch-0007 proposals covering SCAN normalization, simplified subtype robustness, and Swedish IHC/PAM50 concordance. |
| 0.27.0-working | 2026-07-25 | Added two checksum-bound, non-authoritative batch-0006 IHC/PAM50 comparison proposals and recorded fail-closed rejection of an unstable repository PDF. |
| 0.26.0-working | 2026-07-25 | Added the bounded no-storage proposal validator, generalized `PMC`/`PMID`/`PPR` founder references, and non-authoritative batch-0005 genomic-versus-pathology appraisal proposal. |
| 0.25.0-working | 2026-07-25 | Added the checksum-bound UNC institutional-PDF review receipt and explicit publisher decisions for three restricted records; citation state is 3 appraised, 22 ready, 3 restricted, and 1 pending access. |
| 0.22.0-working | 2026-07-25 | Added a reproducible medRxiv version-2 no-storage receipt, CC BY-NC durable-storage restriction, and non-authoritative batch-0004 appraisal proposal; citation state is 3 appraised, 21 ready, and 5 pending access. |
| 0.21.0-working | 2026-07-25 | Added eight verified PMC no-storage review receipts and seven durable-storage restrictions; citation state is 3 appraised, 20 ready, and 6 pending access. |
| 0.20.0-working | 2026-07-25 | Repaired two exact-ID Unicode-dash title mismatches, retrieved both CC BY 4.0 full texts, and materialized batch-0001 locked appraisals; citation state is 3 appraised, 12 ready, and 14 pending access. |
| 0.19.0-working | 2026-07-25 | Recorded non-authoritative batch 0002 and batch 0003 appraisal proposals; evidence synthesis and completed-appraisal counts remain unchanged pending exact founder authorization. |
| 0.18.0-working | 2026-07-25 | Added founder-authorized citation appraisal batch 0001 and the bounded cross-study platform, population, implementation, and ambiguity synthesis; 31 total appraisals are complete. |
| 0.17.0-working | 2026-07-25 | Added the governed IEEE publisher-PDF receipt and CDLS appraisal; all 28 lawfully accessible records are appraised, with two access restrictions retained. |
| 0.16.0-working | 2026-07-25 | Added cross-platform microarray/nCounter discordance, classifieR, and spatially guided mFISHseq appraisals; all 27 lawfully accessible records are now appraised. |
| 0.15.0-working | 2026-07-25 | Added NHS cohort-centering, NanoString QC/normalization, and fixed stable-reference single-sample scoring appraisals; 24 of 30 records are now appraised. |
| 0.14.0-working | 2026-07-25 | Added explicit ambiguous/unclassifiable PLS states, cohort-adaptive PCA-PAM50, and whole-transcriptome ssNMF subtype-purity appraisals; 21 of 30 records are now appraised. |
| 0.13.0-working | 2026-07-25 | Added non-neoplastic contamination, Han Chinese preprocessing consistency, and clinical-grade Prosigna analytical-validation appraisals; 18 of 30 records are now appraised. |
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
