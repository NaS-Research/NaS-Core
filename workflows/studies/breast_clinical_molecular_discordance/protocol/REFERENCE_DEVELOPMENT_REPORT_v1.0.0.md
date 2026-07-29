# Reference-development protocol 1.0.0

## Decision

GSE81538 is registered as an active public/open source for a single bounded role:
outcome-blind development of a fixed PAM50 platform reference. It is not a
discovery cohort and is not an external-validation cohort.

The source remains a **candidate**, not a locked method component. No expression
values, outcomes, or participant rows were accessed, no source bytes were stored,
and no classifier was run.

## Frozen candidate method

Before molecular parsing, public metadata will be used to select exactly 50
ER-positive and 50 ER-negative primary tumors by lexicographic GEO accession
order. Expression cannot influence membership. After a field-isolated unit audit,
the 50 PAM50 genes will be represented as `log2(FPKM + 1)` only if the official
matrix is proven to contain untransformed FPKM. A gene-wise median across the
frozen 100-sample set is the proposed fixed reference; that vector is subtracted
before Spearman scoring.

The rule follows the historical need for a platform-matched, receptor-balanced
reference while preventing discovery outcomes or validation performance from
choosing the reference.

## Required work before lock

1. Restore a writable marker-validated object store.
2. Freeze the official artifact manifest and checksum.
3. Verify GSE81538–GSE96058 participant non-overlap using public provenance.
4. Audit the matrix scale and exact gene mapping without outcomes.
5. Freeze the 100-sample accession manifest before expression parsing.
6. Execute the primary and prespecified reference-sensitivity calculations.

The shared SCAN-B program and laboratory context must remain disclosed. GSE96058
molecular and outcome data stay firewalled until the bridge and reference are
locked.
