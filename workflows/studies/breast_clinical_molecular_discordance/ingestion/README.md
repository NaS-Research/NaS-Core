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

Synthetic fixtures passed before live execution, and the implementation was
committed before contact with remote sources. Immutable
[`field_isolated_metadata_receipt_v1.0.0.yaml`](field_isolated_metadata_receipt_v1.0.0.yaml)
is bound to code revision `2f0b15f…74d0c` and receipt SHA-256
`b5f8c359…822a`.

Audit `1.0.0` verified all 50 historical PAM50 genes without ambiguous panel
mappings in both source representations. It quantified receptor completeness as:

- TCGA-BRCA: 1,049 ER, 1,048 PR, 983 HER2, and 981 all-three-complete among
  1,098 records;
- GSE96058: 3,189 ER, 3,051 PR, 3,281 HER2, and 2,931 all-three-complete among
  3,409 records.

The audit returned `changes_requested` because no approved GEO characteristic
encoded the primary-versus-technical-replicate linkage; all 3,409 samples
remained unclassified for replicate state. The complete interpretation boundary
is recorded in
[`FIELD_ISOLATED_METADATA_REPORT_v1.0.0.md`](FIELD_ISOLATED_METADATA_REPORT_v1.0.0.md).

The official GEO description documents titles such as `F30` and `F30repl`.
Reading `!Sample_title` would expand the permitted field list, so it is not
silently added. The separately reviewable
[`FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_v1.0.1.md`](../reviews/FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_v1.0.1.md)
defines the exact no-retention correction. The founder supplied its checksum-bound
exact authorization in
[`FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_CONFIRMATION_v1.0.1.yaml`](../reviews/FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_CONFIRMATION_v1.0.1.yaml).
Audit `1.0.1` must verify that every source representation is checksum-identical
to audit `1.0.0`, accept only the declared `F<number>`/`F<number>repl` title
grammar and `0`/`1`/`NA` receptor categories, and retain only aggregate counts.
Molecular and outcome execution remain prohibited.

Audit `1.0.1` executed from frozen revision `5d5a5d2…95361`. Immutable
[`field_isolated_metadata_receipt_v1.0.1.yaml`](field_isolated_metadata_receipt_v1.0.1.yaml)
has SHA-256 `a974bce9…3821b` and returned `pass`: it classified 3,273 primary
records and 136 technical replicates, linked all 136 replicates, and left zero
records unclassified. The full boundary and aggregate interpretation are recorded
in
[`FIELD_ISOLATED_METADATA_REPORT_v1.0.1.md`](FIELD_ISOLATED_METADATA_REPORT_v1.0.1.md).

Completion gate: Governed immutable dataset snapshot is verified.
