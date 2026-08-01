# Technical Calibration Readiness Report 1.0.0

## Decision

`public_feasibility_only_primary_calibration_not_ready`

Frozen revision `63708b6` reconciled the active standing authorization,
technical-calibration acquisition contract, source scout, lineage audit,
prospective design, internal Phase 1 plan, contact revocation, fixed reference,
and reference sensitivity. Receipt SHA-256 is
`c1da22e2cc9034380f7a4ee0ce748000a120bb4639956ffecdb7aebb90e1a784`.

## Path decisions

- **GSE60788:** public/open feasibility acquisition is authorized. Its six
  replicate-labeled records can test panel mapping, pair lineage, missingness,
  and preliminary variance components. They cannot calibrate thresholds.
- **GSE130397:** public/open feasibility acquisition is authorized. Its small
  FFPE library-method replicate structure can test processing and gene-level
  feasibility. It cannot represent the intended population or calibrate thresholds.
- **GSE96058:** remains external-validation-only. Molecular access is prohibited
  until the method and thresholds are locked.
- **Hurson/PMC10147733:** participant-level paired values are controlled or
  unavailable. The founder's external-contact revocation remains active.
- **Prospective NaS experiment:** scientifically planned but cannot execute
  without separate review for laboratory contact, spending, and specimens.

## Permitted feasibility estimands

- PAM50 panel completeness and identifier mapping.
- Declared replicate-pair lineage and denominator reconciliation.
- Gene-level paired differences as feasibility variance components.
- Assay missingness, invalidity, and processing-metadata completeness.

These public pilot estimates are permanently excluded from final threshold
calibration and external validation.

## Prohibited uses

No pooling of the small heterogeneous sources into a technical-error
distribution; no reliability, margin, retention, or abstention threshold; no
GSE96058 molecular access; no clinical outcome; no classifier execution; no
external contact, spending, specimen acquisition, clinical use, or publication.

## Next gate

Register and checksum the exact official public artifacts, then perform
source-specific panel, scale, pair-lineage, and denominator audits before any
feasibility molecular statistic is calculated.
