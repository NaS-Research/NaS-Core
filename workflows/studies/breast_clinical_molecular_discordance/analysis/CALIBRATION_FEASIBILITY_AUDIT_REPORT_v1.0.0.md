# Calibration-feasibility audit report 1.0.0

Frozen revision `0bf1255` executed the source-isolated audit. Receipt
`calibration_feasibility_audit_receipt_v1.0.0.yaml` has SHA-256
`0d642c61ffe434bbd9f03d323f5bc530d4e0c6dbec72e42224dc15d370c378ac`.

## GSE60788

- 55 expression columns: 49 primary/unlabeled and six replicate-labeled records.
- 27,979 feature rows and 1,538,845 finite numeric values.
- All 50 historical PAM50 genes resolve directly after only the three declared
  historical aliases; no panel gene is missing.
- Values are continuous, range from -13.9364263 to 26.89753752, and include
  552,858 negative observations. The exact source transformation is therefore
  not inferred from the values.
- The source is usable for a bounded source-specific replicate-feasibility pilot,
  but six pairs cannot establish a population reliability threshold.

## GSE130397

- 21 count files: 10 primary/library groups and 11 linked replicate records.
- Every file has the same ordered 60,675-feature schema.
- The three numeric columns contain 3,822,525 finite, nonnegative integer values,
  ranging from 0 to 3,383,949.
- Features use unmapped Ensembl gene identifiers. Direct PAM50 symbol coverage is
  therefore zero and panel coverage remains unresolved—not absent.
- The source header exposes unstranded, forward, and reverse count columns. The
  scientifically appropriate strandedness column is not selected by this audit.

## Decision

The audit is complete, but primary calibration remains not ready. GSE60788 may
support an excluded source-specific technical-replicate pilot after its estimands
are frozen. GSE130397 requires a versioned, lawful gene-annotation mapping and a
source-supported strandedness decision before panel-level analysis. The sources
must not be pooled. No identifier or molecular value was retained; no outcome,
classifier, threshold, AI, clinical, publication, or submission action occurred.
