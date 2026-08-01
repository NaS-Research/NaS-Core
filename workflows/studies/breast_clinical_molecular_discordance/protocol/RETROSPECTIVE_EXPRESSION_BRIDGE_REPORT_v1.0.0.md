# Retrospective Expression Bridge Report 1.0.0

Frozen revision `6a45c2b` verified every declared evidence hash and the immutable
external GSE81538 reference object. Receipt
`retrospective_expression_bridge_receipt_v1.0.0.yaml` has SHA-256
`86a8521b65d033c1815d5c23436c55f187049a80016f3ce5b8b10be1782e0638`.

## Frozen bridge

| Component | Frozen operation |
|---|---|
| TCGA-BRCA discovery input | GDC augmented STAR Counts `fpkm_unstranded` |
| TCGA-BRCA transformation | `log2(FPKM + 0.1)` in IEEE-754 binary64 |
| GSE96058 validation input | Source-supplied `log2(FPKM + 0.1)` |
| GSE96058 transformation | Consume unchanged |
| Gene panel | Exact historical PAM50 50; no imputation or ambiguous duplicates |
| Centering | Subtract the immutable GSE81538 50-gene median reference gene-wise |
| Scoring artifact | Checksummed genefu 2.44.0 five-by-fifty centroids |
| Scoring operation | Spearman correlation to each fixed centroid |

The GDC mRNA pipeline documentation states that augmented STAR count files
include unstranded FPKM, while official GSE96058 GEO sample metadata states that
FPKM values were collapsed to gene symbols, offset by 0.1, and log2 transformed.
The bridge was selected from those metadata and existing checksum-bound NaS
artifacts without accessing molecular values, outcomes, or validation
performance.

- GDC pipeline: <https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/Expression_mRNA_Pipeline/>
- GSE96058 metadata example: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM2528463>

## Interpretation and boundary

The bridge is frozen for the retrospective research study. It forbids cohort-
specific centering, validation adaptation, imputation, outcome-guided tuning,
and performance-guided revision. It does not establish that GDC STAR/GENCODE-36
FPKM and SCAN-B Cufflinks FPKM are analytically interchangeable. Their upstream
difference is an explicit transport limitation that unchanged external
validation must quantify.

The fixed reference and centroids are locked for this retrospective bridge only.
The future prospective primary-calibration assay, laboratory QC thresholds,
technical-error model, and reliability thresholds remain unresolved. No
classifier, validation matrix, outcome, clinical use, publication, or submission
was authorized.
