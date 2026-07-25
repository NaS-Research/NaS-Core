# NAS-BRCA-002 Remaining-Queue Founder Screening Packet

Packet version: `1.0.0`

Question version: `0.3.0`

Queue: `af08a334…8a2a3`

Based on verified progress: `b0c31f7e…00945f`

Status: **Advisory only—founder confirmation required**

## Purpose

This packet applies screening protocol `1.1.0` to the 87 records that remain
pending after the 13 direct-priority inclusions. OpenAI Codex reviewed titles and
complete abstracts from the immutable queue and proposed decisions. It did not
write founder decision events, access molecular or outcome data, appraise full
text, or establish novelty.

The recommended set is intentionally strict:

- 17 `include`;
- 70 `exclude`;
- 0 `unclear`; and
- 5 author-year candidate links rejected as false-positive identity matches.

If confirmed, the 17 recommendations plus the 13 direct-priority records produce
the protocol-capped 30-record evidence set. Inclusion means only that lawful
full-text review is warranted. It is not a quality judgment or scientific
endorsement.

## Author-year candidate-link adjudication

All five links should be **rejected**. Each match is based only on a common first
author surname and publication year; the current and prior records have different
PMIDs and different titles.

| Current record | Candidate prior record(s) | Recommendation |
|---|---|---|
| PPR595721, RAB2A prognostic biomarker | PMID 36910654 | Reject link |
| PMID 31838010, CORALLEEN trial | PMID 31037288; PMID 32962980 | Reject both links |
| PMID 33152285, HER2DX prognostic score | PMID 31037288; PMID 32962980 | Reject both links |
| PMID 33842588, metabolic prognostic signature | PMID 33069665 | Reject link |
| PMID 41977348, subtype-stratified signatures | PMID 42164482 | Reject link |

## Recommended inclusions

| # | Record | Short title | Confidence | Why full text is warranted |
|---:|---|---|---|---|
| 16 | PMID 21718502 | Normal-tissue contamination bias | High | Directly models systematic specimen contamination and PAM50 misclassification. |
| 17 | PMID 23046482 | Prediction consistency in Han Chinese tumors | High | Compares centering, DWD, unclassified states, and external-population consistency. |
| 20 | PMID 24490149 | PLS intrinsic-taxonomy classifier | High | External validation contains explicit unclassified cases and major transport loss. |
| 21 | PMID 24625003 | Multisite Prosigna analytical validation | High | Direct technical replicates, spatial sections, RNA-input limits, interference, and cross-laboratory reproducibility. |
| 29 | PMID 27130929 | OPTIMA multiparameter-test discordance | High | Same-patient commercial assays yield substantial risk and subtype discordance. |
| 37 | PMID 30591591 | PAM50 in Nurses’ Health Study cohorts | High | Directly compares modified-median and subgroup-specific centering in archival tumors. |
| 39 | PMID 30849944 | Luminal-A subtype ambiguity | High | Defines patient-level centroid-distance admixture metrics and externally validates them. |
| 40 | PMID 31138829 | PCA-PAM50 | High | Direct cohort-centering method with executable code and cross-cohort testing. |
| 44 | PMID 32789507 | NanoString normalization and QC | High | Direct technical normalization, site/batch effects, housekeeping selection, and PAM50 probe behavior. |
| 45 | PMID 32997146 | Stable-gene single-sample scoring | High | Directly applicable fixed normalization and single-sample transcriptomic scoring method. |
| 55 | PMID 34387660 | Microarray versus NanoString subtyping | High | Same-patient cross-platform PAM50 comparison shows substantial subtype discordance. |
| 58 | PMID 35361119 | classifieR software | High | Executable single-sample PAM50 software intended to span assay platforms. |
| 64 | PMID 36892725 | PAM50 reproducibility and heterogeneity | High | Direct technical replicates and spatial biological replicates with subtype agreement estimates. |
| 67 | PMID 37209182 | Luminal-A subtype-purity model | High | Patient-level subtype admixture model with independent cohort evidence. |
| 70 | PMID 38105959 | LCM RNA-seq and consensus subtyping | High | Specimen-purity intervention, multiple classifiers, discordance, and consensus assignment. |
| 82 | PMID 41671586 | Selective multimodal subtype classifier | Medium | Uses confidence-aware routing for ambiguous samples; quality and independence require full-text scrutiny. |
| 87 | PMID 42172162 | Cross-cohort latent-simulation classifier | Medium | Explicit uncertainty trajectories and cross-cohort modality-disjoint learning directly challenge the candidate contribution. |

## Recommended exclusions

The primary exclusion reason follows the ordered taxonomy in screening protocol
`1.1.0`.

| # | Record | Short title | Reason | Rationale |
|---:|---|---|---:|---|
| 1 | PPR1032191 | Expression clustering and ancestry | 3 | Reports ambiguous PAM50 calls but does not test a relevant classifier or reliability method. |
| 2 | PPR1136080 | Core-PAM50 prognosis model | 3 | Primary object is a survival score; subtype-centroid comparison does not evaluate patient-level assignment reliability. |
| 3 | PPR1175189 | Pathway risk stratification | 3 | Outcome prediction beyond PAM50, not intrinsic-subtype reliability. |
| 4 | PPR1271381 | MHCII immune activation score | 3 | Prognostic and treatment-effect biomarker; subtype is only a stratum. |
| 5 | PPR148720 | NanoString normalization preprint | 5 | Superseded by included peer-reviewed PMID 32789507. |
| 6 | PPR158449 | Stable-gene scoring preprint | 5 | Superseded by included peer-reviewed PMID 32997146. |
| 7 | PPR35627 | Rank-based test-set-bias preprint | 5 | Superseded by already appraised PMID 25788628. |
| 8 | PPR428650 | SCAN-B SSP preprint | 5 | Superseded by already appraised PMID 35974007. |
| 9 | PPR595721 | RAB2A prognostic biomarker | 3 | Single-gene outcome association; PAM50 is only a covariate. |
| 10 | PPR627342 | Luminal-A subtype purity preprint | 5 | Superseded by included peer-reviewed PMID 37209182. |
| 11 | PPR668423 | RGCC prognostic biomarker | 3 | Single-gene outcome association; PAM50 is only a correlate. |
| 12 | PPR705217 | Patient-specific co-expression | 3 | General network/outcome score, not an intrinsic-subtype classifier or reliability method. |
| 13 | PPR896786 | IRSN-23 preprint | 5 | Superseded by PMID 40128415 and remains primarily a chemotherapy-response signature. |
| 14 | PMID 20837693 | PAM50 prognosis in ER-positive tumors | 3 | Clinical validity association without relevant classifier reliability analysis. |
| 15 | PMID 21555689 | ACOSOG Z1031 | 3 | Treatment-response study; PAM50 is a baseline biomarker. |
| 18 | PMID 24088296 | Gene-test systematic review | 4 | Review/economic assessment retained only for citation chaining. |
| 19 | PMID 24359601 | Gemcitabine effect by subtype | 3 | Treatment-effect association without classifier-method analysis. |
| 22 | PMID 26021444 | Serial tumors during chemotherapy | 3 | Biological and treatment-induced change, not technical repeatability or classifier reliability. |
| 23 | PMID 26132585 | METABRIC ensemble biomarkers | 3 | Cohort-trained label refinement without fixed single-sample reliability or transport validation. |
| 24 | PMID 26375671 | Subtypes across progression | 3 | Biological progression and outcome association, not analytical reliability. |
| 25 | PMID 26566278 | BRCA mutation and claudin-low | 3 | Biological subtype comparison without relevant method evaluation. |
| 26 | PMID 26770261 | Iterative METABRIC subtype refinement | 3 | Same-cohort iterative relabeling without a patient-independent reliability method. |
| 27 | PMID 26846986 | Weak ER-positive tumors | 3 | Clinical subgroup profiling without classifier reliability analysis. |
| 28 | PMID 26909792 | EndoPredict versus ROR | 3 | Prognostic score comparison rather than subtype-assignment reliability. |
| 30 | PMID 27144536 | MRI radiomics versus gene assays | 2 | Image-based recurrence prediction, not gene-expression intrinsic-subtype methodology. |
| 31 | PMID 27402148 | IHC basal biomarkers | 2 | IHC surrogate classifier rather than gene-expression reliability method. |
| 32 | PMID 27903675 | Chemoendocrine score | 3 | Treatment-response signature; subtype is a component. |
| 33 | PMID 29220095 | Digital Ki67 hot spots | 2 | Image-based proliferation measurement, not molecular-subtype reliability. |
| 34 | PMID 29241890 | Value-of-information analysis | 3 | Economic trial-design analysis without classifier-method evidence. |
| 35 | PMID 29386247 | AR/ER ratio | 3 | Biomarker prognosis study; Prosigna is descriptive. |
| 36 | PMID 30411790 | Basal biomarkers and gemcitabine | 3 | Treatment-effect biomarker study without relevant classifier analysis. |
| 38 | PMID 30778520 | PerELISA trial | 3 | Treatment trial using ROR response, not classifier reliability. |
| 41 | PMID 31838010 | CORALLEEN trial | 3 | Treatment trial; PAM50/ROR are response endpoints. |
| 42 | PMID 31992350 | Image-based subtype classifier | 2 | Histopathology approximation of PAM50, outside the gene-expression analytical method. |
| 43 | PMID 32572716 | Automated Ki67 | 2 | Image-based proliferation score, not intrinsic-subtype reliability. |
| 46 | PMID 33152285 | HER2DX prognostic score | 3 | Outcome model using subtype as one feature. |
| 47 | PMID 33396205 | Pan-cancer PAM50 patterns | 3 | Biological pan-cancer reuse of an already appraised uncertainty method. |
| 48 | PMID 33397968 | HER2-low PAM50 features | 3 | Descriptive biology without a classifier reliability method. |
| 49 | PMID 33531653 | PAM50 in prostate cancer | 6 | Outside breast cancer scope. |
| 50 | PMID 33575114 | TNBC single-cell heterogeneity | 3 | Cell-level biological network study, not bulk patient-assignment reliability. |
| 51 | PMID 33842588 | Metabolic prognostic nomogram | 3 | Outcome signature; PAM50 is only a comparator. |
| 52 | PMID 33971670 | Pan-cancer prognostic SSP | 3 | Organ-agnostic proliferation/outcome classifier, not breast intrinsic-subtype reliability. |
| 53 | PMID 34026336 | Immune environment and gemcitabine | 3 | Treatment-effect biomarker analysis. |
| 54 | PMID 34092112 | EA1131 trial | 3 | Treatment trial stratified by basal subtype. |
| 56 | PMID 34615722 | Basal IHC panel | 2 | IHC treatment-predictive surrogate rather than gene-expression method. |
| 57 | PMID 35295953 | MCTS1 prognostic biomarker | 3 | Single-gene outcome association. |
| 59 | PMID 35432381 | Fatty-acid prognostic signature | 3 | Outcome signature; PAM50 is descriptive. |
| 60 | PMID 35456196 | Non-coding RNA subtype networks | 3 | Biological discovery method without fixed patient-level classification or reliability. |
| 61 | PMID 36524129 | Pyrimidine prognostic signature | 3 | Outcome signature; PAM50 is a covariate. |
| 62 | PMID 36602784 | Immune signatures versus TILs | 3 | Response/outcome biomarker comparison. |
| 63 | PMID 36809046 | WSG-ADAPT-TP | 3 | Treatment de-escalation trial using subtype as a biomarker. |
| 65 | PMID 36915811 | Macrophage prognostic index | 3 | Outcome signature; PAM50 defines a subgroup. |
| 66 | PMID 37096121 | Survival gene signature | 3 | Prognostic model comparison without subtype reliability. |
| 68 | PMID 37977656 | Patient-specific co-expression | 3 | General network rewiring/outcome method, not an intrinsic-subtype classifier. |
| 69 | PMID 38038766 | Positive surgical margins | 3 | Surgical-margin outcome; “margin” is not a classifier score margin. |
| 71 | PMID 38448600 | Ribociclib cell-cycle study | 3 | Treatment-induced biology, not analytical reliability. |
| 72 | PMID 38838499 | EMIT-1 decision impact | 3 | Clinical decision-impact study without classifier-method evaluation. |
| 73 | PMID 39740059 | Image-based subtype heterogeneity | 2 | Histopathology model outside the gene-expression reliability method. |
| 74 | PMID 39979291 | HER2-low breast classifier | 3 | New biological taxonomy without patient-independent uncertainty or transport detail in the abstract. |
| 75 | PMID 39980051 | Letrozole-treated DCIS | 3 | Biological treatment-induced subtype change. |
| 76 | PMID 39990808 | Glasgow prognostic score | 3 | Clinical outcome score; PAM50 is a covariate. |
| 77 | PMID 40128415 | IRSN-23 validation | 3 | Chemotherapy-response signature rather than intrinsic-subtype reliability. |
| 78 | PMID 40227228 | ER-low SCAN-B biology | 3 | Biological subgroup characterization without classifier-method analysis. |
| 79 | PMID 41106018 | Ki67 endocrine sensitivity | 3 | Treatment-response biomarker study. |
| 80 | PMID 41109527 | TOUCH trial | 3 | Treatment trial using AIMS subtype as a biomarker. |
| 81 | PMID 41335375 | PATRICIA trial | 3 | Treatment trial restricted by PAM50 subtype. |
| 83 | PMID 41937807 | Shortcut learning audit | 2 | Clinical-only proxy model does not execute or validate a gene-expression subtype classifier. |
| 84 | PMID 41977348 | Subtype-stratified prognosis | 3 | Prognostic signatures stratified by PAM50, not subtype reliability. |
| 85 | PMID 42132950 | GEDO in Sjögren’s disease | 6 | Primary method and cohort are outside breast cancer; TCGA is only a benchmark. |
| 86 | PMID 42169063 | CorePAM prognostic score | 3 | Cross-platform survival score, not an intrinsic-subtype assignment method. |

## Founder confirmation

Before immutable submission, the founder should confirm:

1. all five author-year links are rejected;
2. all 17 inclusion recommendations;
3. all 70 exclusions and their primary reasons; and
4. whether any record should be changed to `unclear`.

No decision in this packet may be represented as founder-confirmed until that
review occurs.
