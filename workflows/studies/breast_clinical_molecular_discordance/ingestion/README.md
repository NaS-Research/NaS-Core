# Ingestion

Calibration-feasibility acquisition plan
[`calibration_feasibility_acquisition_plan_v1.0.0.yaml`](calibration_feasibility_acquisition_plan_v1.0.0.yaml)
and its immutable source registry
[`calibration_feasibility_source_registry_v1.0.0.yaml`](calibration_feasibility_source_registry_v1.0.0.yaml)
freeze 24 official NCBI GEO artifacts totaling 14,189,925 bytes: the GSE60788
normalized expression matrix and transcript-to-gene map, plus the GSE130397
official inventory and all 21 public sample files. The two sources are separately
registered as public/open for `calibration-feasibility` only. The atomic staging
service validates every declared size before publishing any immutable object and
records a checksum per artifact. Acquisition does not parse molecular values.
Pooling, outcomes, classifier execution, threshold estimation, external
publication, and generative-model access remain false.

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

Under activated Route C, calibration-lineage audit `1.0.0` streamed the official
GEO family SOFT representations for GSE60788, GSE96058, and GSE130397. Immutable
[`calibration_lineage_receipt_v1.0.0.yaml`](calibration_lineage_receipt_v1.0.0.yaml)
has SHA-256 `ef3cce52…9d2` and is bound to frozen revision `d256342`. It linked
all 6, 136, and 11 replicate-labeled records, respectively, and found zero public
accession/title overlap between GSE60788 and GSE96058.

The audit retained no identifiers, titles, rows, raw artifacts, molecular values,
or outcomes. Public identifier non-overlap does not establish biological-specimen
independence, so no calibration source is selected. See
[`CALIBRATION_LINEAGE_REPORT_v1.0.0.md`](CALIBRATION_LINEAGE_REPORT_v1.0.0.md).

Before GSE81538 acquisition, storage preflight `1.0.0` inspected the configured
Seagate data root without a write probe. Receipt
[`storage_readiness_receipt_v1.0.0.yaml`](storage_readiness_receipt_v1.0.0.yaml)
verifies the marker, required directories, and 4.59 TB available, but returns
`blocked` because the volume is mounted read-only and has no operating-system
write access.

Official NCBI headers freeze the proposed processed artifact at 54,838,076 bytes
with last-modified time `2016-05-17T20:45:49Z`. Candidate manifest
[`gse81538_artifact_manifest_candidate_v1.0.0.yaml`](gse81538_artifact_manifest_candidate_v1.0.0.yaml)
retains the exact URL and proposed object key while leaving SHA-256 pending. No
source bytes, molecular values, or outcomes were accessed. See
[`STORAGE_READINESS_REPORT_v1.0.0.md`](STORAGE_READINESS_REPORT_v1.0.0.md).

After the damaged HFS+ volume was explicitly erased and rebuilt as APFS,
[`storage_readiness_receipt_v1.1.0.yaml`](storage_readiness_receipt_v1.1.0.yaml)
returns `ready` with zero blockers and approximately 6.0 TB available. Acquisition
plan [`gse81538_acquisition_plan_v1.0.0.yaml`](gse81538_acquisition_plan_v1.0.0.yaml)
binds that receipt, the active source registry, standing authorization, and
reference-development protocol to the exact official artifact and immutable
object key. The acquisition implementation streams to governed working storage,
checks exact byte length, calculates SHA-256, and atomically publishes without
overwrite. It does not parse expression or outcome values during acquisition.

Frozen revision `db3c81b` executed that plan and generated immutable metadata
receipt [`gse81538_acquisition_receipt_v1.0.0.yaml`](gse81538_acquisition_receipt_v1.0.0.yaml).
The 54,838,076-byte object has independently reproduced SHA-256
`9da259a9b08ef794890cbf55a738856870d12b6d455da75874e1d6849ed39181`.
See [`GSE81538_ACQUISITION_REPORT_v1.0.0.md`](GSE81538_ACQUISITION_REPORT_v1.0.0.md).

Matrix-audit plan
[`gse81538_matrix_audit_plan_v1.0.0.yaml`](gse81538_matrix_audit_plan_v1.0.0.yaml)
binds that exact acquisition receipt, the staged PAM50 centroid candidate, and
reference-development protocol. The audit streams the compressed object twice:
once to independently reproduce its byte length and SHA-256 and once to parse
the CSV through gzip without materializing sample rows. It verifies the exact
`T1`–`T405` header, 18,802 unique gene rows, every numeric cell, the declared
`log2(FPKM + 0.1)` floor, and all 50 PAM50 genes including governed historical
aliases. It cannot read outcomes, execute a classifier, or materialize a
reference vector. Synthetic pass and fail-closed tests cover changed provenance,
header sequence, and panel completeness before live execution.

The separate family-SOFT acquisition plan
[`gse81538_family_soft_acquisition_plan_v1.0.0.yaml`](gse81538_family_soft_acquisition_plan_v1.0.0.yaml)
freezes the official 51,036-byte NCBI sample-metadata artifact. The typed
acquisition contract distinguishes `sample_metadata` from a
`processed_expression_matrix`, so its receipt must record source bytes without
claiming that molecular bytes were stored. The exact HTTPS path is allowlisted,
the object write is immutable, and no field is parsed during acquisition.

Frozen revision `8e105f1` acquired the object. Receipt
[`gse81538_family_soft_acquisition_receipt_v1.0.0.yaml`](gse81538_family_soft_acquisition_receipt_v1.0.0.yaml)
records exactly 51,036 bytes and independently reproduced SHA-256
`8d7bab685bb6ed135f64da10273e9b159e761e813a100a057829f5159957332c`.
See
[`GSE81538_FAMILY_SOFT_ACQUISITION_REPORT_v1.0.0.md`](GSE81538_FAMILY_SOFT_ACQUISITION_REPORT_v1.0.0.md).

Founder decision `1.1` and protocol amendment `1.1.0` authorize a strictly
field-isolated selection. Plan
[`gse81538_reference_metadata_plan_v1.0.0.yaml`](gse81538_reference_metadata_plan_v1.0.0.yaml)
permits only sample title, GEO accession, and the exact `er consensus` field.
It selects the first 50 code-0 and first 50 code-3 records in lexicographic GEO
accession order, excludes codes 1/2, and writes the identifier-bearing manifest
only to governed external storage. The Git receipt contains aggregate counts,
checksums, provenance, limitations, and explicit zero-access attestations for
expression, outcomes, validation data, classifier execution, and generative AI.

Frozen revision `76ace2b` executed the plan. Receipt
[`gse81538_reference_metadata_receipt_v1.0.0.yaml`](gse81538_reference_metadata_receipt_v1.0.0.yaml)
has SHA-256 `b8b43884…66423` and records 405 unique linked records: 82 code-0,
8 code-1, 11 code-2, and 304 code-3. The external manifest contains exactly 50
ER-negative and 50 ER-positive records and independently reproduces SHA-256
`4f36124c…a9fe`. See
[`GSE81538_REFERENCE_METADATA_REPORT_v1.0.0.md`](GSE81538_REFERENCE_METADATA_REPORT_v1.0.0.md).

Execute only from the frozen implementation revision:

```console
uv run nas-core ingest reference-metadata \
  ingestion/gse81538_reference_metadata_plan_v1.0.0.yaml \
  ingestion/gse81538_family_soft_acquisition_receipt_v1.0.0.yaml \
  ingestion/gse81538_matrix_audit_receipt_v1.0.0.yaml \
  reviews/FOUNDER_REFERENCE_INPUT_DECISION_v1.1.0.yaml \
  protocol/reference_development_protocol_v1.1.0.yaml \
  --data-root "$NAS_DATA_ROOT" --code-revision REVISION \
  --output-path ingestion/gse81538_reference_metadata_receipt_v1.0.0.yaml \
  --execute
```

Completion gate: Governed immutable dataset snapshot is verified.
