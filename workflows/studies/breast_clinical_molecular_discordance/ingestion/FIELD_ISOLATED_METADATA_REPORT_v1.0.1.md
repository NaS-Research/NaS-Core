# Field-Isolated Metadata Audit Report 1.0.1

Study: `NAS-BRCA-002`  
Question: `NAS-RQ-BRCA002`, version `0.3.0`  
Decision: `pass`  
Executed: 2026-07-26  
Frozen code revision: `5d5a5d2de20056324ca0622c750129d962395361`

## Provenance

The execution was authorized by
`FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_CONFIRMATION_v1.0.1.yaml`, bound to
amendment SHA-256
`25b9d1d9c93739c0a9e0921af74f3065d3deea5d88bcf52dc62295f47cc1f356`.
It is also bound to audit 1.0.0 receipt SHA-256
`b5f8c3599219c8b13aa218e9aff3e380cbdf789aa7897b30c5ae6dfd4fea822a`.

The immutable aggregate receipt is
`field_isolated_metadata_receipt_v1.0.1.yaml`, SHA-256
`a974bce9dedf65f2575d66da1728ffa9254db5291d75259371eb401f4803821b`.
All four source-representation SHA-256 values were identical to audit 1.0.0.

## Verified findings

All five bounded input-feasibility checks passed:

1. TCGA-BRCA contains all 50 historical PAM50 genes in the selected STAR-count
   representation, with zero missing or ambiguously duplicated canonical mappings.
2. GSE96058 contains all 50 historical PAM50 genes in its processed-expression
   representation, with zero missing or ambiguously duplicated canonical mappings.
3. Among 1,098 TCGA clinical records, ER, PR, and HER2 were present for 1,049,
   1,048, and 983 records; all three were present for 981.
4. Among 3,409 GSE96058 records, ER, PR, and HER2 were present for 3,189, 3,051,
   and 3,281 records; all three were present for 2,931.
5. The approved sample-title projection classified 3,273 primary records and 136
   technical replicates. All 136 technical replicates linked to a primary record,
   and zero records remained unclassified.

GSE96058's permitted `0`/`1`/`NA` receptor projection yielded 2,935 positive and
254 negative ER records; 2,644 positive and 407 negative PR records; and 438
positive and 2,843 negative HER2 records. Missing counts are the difference from
3,409 and were not represented as observed receptor values.

## Isolation and retention

The audit streamed registered public/open representations through bounded parsers.
It retained only aggregate counts, field names, checksums, parser identifiers,
warnings, and provenance. It retained no patient or sample rows, sample titles,
sample accessions, molecular values, outcomes, treatment fields, published subtype
labels, raw source artifacts, analytical cohort, or classifier result.

## Interpretation boundary

This `pass` closes only the declared input-feasibility checks. It does not establish:

- assay equivalence or cross-platform numerical compatibility;
- a valid or locked expression transformation;
- centroid or external-reference correctness;
- classifier validity, subtype accuracy, or patient-level reliability;
- diagnostic, prognostic, predictive, treatment, or clinical utility; or
- permission to construct a cohort or analyze molecular or outcome data.

The next authorization boundary is method lock and independent review: exact
centroids, external reference, transformations, technical-error model, numerical
tolerances, reliability thresholds, and founder scientific, molecular/pathology,
and statistical review must be resolved before preregistration or molecular
execution.
