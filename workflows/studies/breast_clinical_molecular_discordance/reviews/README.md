# Reviews

Record review decisions and resolved comments; never store credentials or PHI.

The active Phase 1 review instrument is
[`QUESTION_REVIEW_PACKET.md`](QUESTION_REVIEW_PACKET.md).

Field-isolated metadata audit `1.0.0` is founder-authorized through
[`FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_CONFIRMATION_v1.0.0.yaml`](FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_CONFIRMATION_v1.0.0.yaml).
It permits only the transient, no-retention projection defined in
[`FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md`](FOUNDER_FIELD_ISOLATED_METADATA_AUTHORIZATION_v1.0.0.md);
it does not authorize molecular analysis, outcome access, cohort construction,
classifier execution, or scientific conclusions.

Executed audit `1.0.0` returned `changes_requested` because its approved GEO
characteristic fields did not contain primary-versus-technical-replicate
linkage. The
[`FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_v1.0.1.md`](FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_v1.0.1.md)
permits only a validated, no-retention `!Sample_title` projection and
source-specific `0`/`1`/`NA` receptor category normalization. The founder supplied
the exact checksum-bound authorization in
[`FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_CONFIRMATION_v1.0.1.yaml`](FOUNDER_FIELD_ISOLATED_METADATA_AMENDMENT_CONFIRMATION_v1.0.1.yaml)
on 2026-07-26. It does not authorize patient-level retention, molecular analysis,
outcome access, cohort construction, classifier execution, or scientific conclusions.

The authorized amendment executed from frozen revision `5d5a5d2…95361` and
returned `pass`. Its immutable aggregate-only receipt is
[`../ingestion/field_isolated_metadata_receipt_v1.0.1.yaml`](../ingestion/field_isolated_metadata_receipt_v1.0.1.yaml);
the interpretive boundary is documented in
[`../ingestion/FIELD_ISOLATED_METADATA_REPORT_v1.0.1.md`](../ingestion/FIELD_ISOLATED_METADATA_REPORT_v1.0.1.md).

Reference-input decision packet
[`REFERENCE_INPUT_DECISION_PACKET_v1.0.0.md`](REFERENCE_INPUT_DECISION_PACKET_v1.0.0.md)
binds the executed matrix and metadata evidence to two explicit founder choices:
the corrected no-additional-transform bridge and the conservative ER-consensus
stratification rule. It is a proposal only and authorizes no parser execution,
reference construction, classifier execution, outcome access, or publication.

The founder subsequently approved the bounded choices exactly as recorded in
[`FOUNDER_REFERENCE_INPUT_DECISION_v1.1.0.yaml`](FOUNDER_REFERENCE_INPUT_DECISION_v1.1.0.yaml).
The decision consumes GSE81538 unchanged as `log2(FPKM + 0.1)`, defines
ER-negative as consensus code 0 and ER-positive as code 3, excludes codes 1/2,
and preserves the documented codebook and independence limitations. It authorizes
only the checksum-bound reference-input implementation; it does not authorize
outcome access, GSE96058 molecular access, classifier execution, clinical use,
publication, or submission.
