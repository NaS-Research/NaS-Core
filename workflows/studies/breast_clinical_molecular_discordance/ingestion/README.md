# Ingestion

Required artifacts:

- `ingestion/README.md`
- `ingestion/data_feasibility.yaml`

`data_feasibility.yaml` is a locked Phase 0 requirements and source-assessment
document, not an outcome-ingestion authorization. Founder authorization permits
terms, variable, compatibility, independence, overlap, and non-outcome metadata
assessment. Its outcome-data-access flag remains false.

Metadata audit `1.0.0` executes five source-level requests with no patient rows,
molecular values, or outcome fields. Its immutable
[`metadata_feasibility_receipt_v1.0.0.yaml`](metadata_feasibility_receipt_v1.0.0.yaml)
verifies the open TCGA-BRCA STAR-count file inventory and both declared GSE96058
artifacts. The accompanying
[`METADATA_FEASIBILITY_REPORT_v1.0.0.md`](METADATA_FEASIBILITY_REPORT_v1.0.0.md)
records a `changes_requested` decision because receptor completeness and exact
PAM50 gene coverage cannot be established under the current source-metadata-only
authorization.

The next boundary is defined in
[`FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md`](../reviews/FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md).
The founder supplied its exact confirmation in
[`FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_CONFIRMATION_v1.0.0.yaml`](../reviews/FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_CONFIRMATION_v1.0.0.yaml),
bound to packet SHA-256 `503bdcc6…0d0ff`.

The authorized projection engine:

- queries only registered public/open TCGA-BRCA BCR Biotab supplements and one
  deterministic open STAR-count file;
- streams GSE96058 processed expression and family SOFT representations without
  persisting either source;
- parses only PAM50 gene identifiers, ER/PR/HER2 fields, sample accession, and
  primary-versus-technical-replicate linkage;
- records every permitted and rejected field name, source identifier, checksum,
  parser, count, warning, and code revision;
- retains no patient-level record, molecular value, outcome, treatment, subtype,
  prediction, raw artifact, or analytical cohort; and
- fails closed to `changes_requested` unless all five feasibility checks verify.

Synthetic fixtures must pass before live execution. The implementation must be
committed first so the live receipt can bind the exact executed revision.

Completion gate: Governed immutable dataset snapshot is verified.
