# Metadata Feasibility Report

Version: `1.0.0`

Study: `NAS-BRCA-002`

Question: `NAS-RQ-BRCA002` version `0.3.0`

Decision: **Changes requested**

## What was executed

The governed audit made exactly five source-level requests:

1. GDC service status;
2. GDC case-field mapping;
3. a zero-row, aggregate-only TCGA-BRCA file query;
4. an HTTP `HEAD` request for the GSE96058 hg38 annotation; and
5. an HTTP `HEAD` request for the GSE96058 processed expression artifact.

The executable audit requested no case, sample, expression, treatment, or outcome
rows. It stored no remote response body. The immutable derivative receipt records
only request/representation hashes, source-level schema findings, aggregate file
counts, and file headers:

- [`metadata_feasibility_receipt_v1.0.0.yaml`](metadata_feasibility_receipt_v1.0.0.yaml)

## Verified findings

- The GDC API reported Data Release 45.0 and API tag 8.5.0 at execution.
- A zero-row GDC aggregation reported 1,231 open TCGA-BRCA
  `Gene Expression Quantification` files produced by `STAR - Counts`, in TSV
  format.
- The current GDC case mapping contained 770 indexed fields.
- NCBI GEO served the declared GSE96058 hg38 annotation artifact at 20,808,999
  bytes.
- NCBI GEO served the declared GSE96058 processed gene-expression artifact at
  591,676,211 bytes.

These findings establish source and workflow availability. They do not establish
cohort eligibility, gene-level coverage, classifier compatibility, or permission
to analyze molecular values.

## Unresolved findings

- No current GDC case-mapping field name contains `estrogen`, `progesterone`,
  `HER2`, or `receptor`. Therefore, indexed GDC case metadata cannot establish
  ER/PR/HER2 completeness.
- The GDC zero-row file aggregation does not enumerate expression-table genes.
  Exact PAM50 coverage remains unverified.
- `HEAD` metadata proves that the two GEO artifacts exist, but it cannot establish
  PAM50 row coverage or alias resolution.
- GEO family metadata co-mingles receptor and technical-replicate annotations with
  patient-level treatment and survival fields. It cannot be retrieved under the
  current no-patient-level-data authorization.

The Phase 0 feasibility requirement is therefore not satisfied. Molecular
retrieval, outcome retrieval, classifier execution, threshold selection, and
preregistration remain prohibited.

## Endpoint-characterization disclosure

Before the five-request gate was implemented, development characterization made a
bounded read-only request to the public GSE96058 family SOFT endpoint. Inspection
revealed that the bundle includes sample-level receptor, PAM50, treatment, and
survival attributes. The response was not written to Git, object storage, or a
local research dataset; no counts, associations, model fitting, or outcome
analysis were performed. Work stopped and the endpoint was excluded from the
governed audit.

This disclosure prevents the final study record from incorrectly implying that
the unsafe endpoint was never touched. It does not authorize future use of that
bundle.

## Required next decision

Continuing the feasibility audit requires a narrowly bounded authorization for
transient field/schema isolation:

- aggregate-only ER/PR/HER2 completeness from TCGA clinical supplements;
- gene-identifier-only projection from one frozen open GDC STAR-count file;
- gene-identifier-only projection from the GSE96058 processed matrix; and
- receptor and replicate-field projection from GSE96058 while mechanically
  rejecting treatment, survival, published subtype, and prediction fields.

The proposed authorization is
[`FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md`](../reviews/FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md).
It does not authorize cohort construction, molecular analysis, outcome analysis,
threshold tuning, clinical inference, or publication claims.
