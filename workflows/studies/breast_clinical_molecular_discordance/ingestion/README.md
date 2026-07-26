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

The proposed next boundary is defined in
[`FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md`](../reviews/FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md).
It remains non-authoritative until the founder supplies its exact confirmation.

Completion gate: Governed immutable dataset snapshot is verified.
