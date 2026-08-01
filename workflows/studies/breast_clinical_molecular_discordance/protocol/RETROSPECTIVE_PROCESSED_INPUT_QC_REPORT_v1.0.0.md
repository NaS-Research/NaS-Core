# Retrospective Processed-Input QC Report 1.0.0

Frozen revision `eb2eebc` verified the bridge lineage and immutable external
reference, then froze the executable QC contract. Receipt
`retrospective_processed_input_qc_receipt_v1.0.0.yaml` has SHA-256
`393119cdcb2541b38b0b2634959343c0ba81a591a0ff86105e70e95265ad49e4`.

## Frozen states

An exact, unique, finite 50-gene panel is required. The three historical aliases
may resolve only to their declared canonical genes. Any alias/canonical collision
is a duplicate mapping and abstains.

| Failure state | Trigger | Action |
|---|---|---|
| `schema_mismatch` | Any unexpected non-PAM50 field in the extracted profile | Abstain |
| `duplicate_mapping` | Two supplied identifiers resolve to one canonical gene | Abstain |
| `insufficient_gene_coverage` | Fewer than all 50 canonical genes | Abstain; no imputation |
| `nonfinite_input` | NaN or infinite value | Abstain |
| `negative_fpkm` | TCGA discovery FPKM below zero | Abstain |
| `below_declared_floor` | GSE96058 value below `log2(0.1)` beyond `1e-12` tolerance | Abstain |
| `constant_centered_profile` | Fewer than two distinct values after fixed-reference centering | Abstain |

Valid TCGA values receive only the frozen `log2(FPKM + 0.1)` transformation.
Valid GSE96058 values remain unchanged. Both subtract the immutable fixed
reference in canonical gene order. A valid profile may continue to locked
scoring, but cannot be described as reliable until the technical-error and
reliability thresholds are independently calibrated.

## Rerun boundary

Reacquisition is allowed only for checksum or file-schema delivery failure. A
scientific QC failure cannot be rerun, imputed, cohort-centered, or adapted until
it passes. Every attempted profile and failure remains in the relevant
denominator.

These rules govern processed input; they do not replace laboratory RNA,
library-complexity, mapping, depth, or instrument QC. No molecular value,
validation value, classifier, outcome, publication, or submission was accessed
or authorized.
