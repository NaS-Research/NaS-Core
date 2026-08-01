# GSE81538 processed-expression matrix audit 1.0.0

## Decision

The checksum-bound, outcome-blind matrix audit **passed**. The governed
GSE81538 processed-expression artifact is structurally complete and suitable for
the next bounded reference-development step. This decision does not validate a
classifier, establish a biological result, or authorize outcome analysis.

## Provenance

- Frozen implementation revision: `cf8d7f6`
- Audit-plan SHA-256: `a1b996dd8c8b54a05a10fafa1e97034001450c1f23b141627578bfddfef1012d`
- Acquisition-receipt SHA-256: `f22b690b4dae2d5029d97fd646a1a1d2baa468f3cc723d95f2d03e74bcca0735`
- Compressed source bytes: `54,838,076`
- Independently reproduced source SHA-256: `9da259a9b08ef794890cbf55a738856870d12b6d455da75874e1d6849ed39181`
- Audit-receipt SHA-256: `98bfb62ad4ba1247feb0ba6c1487341517bb59049c2ad22b4e51fe2ed2773b4c`

## Executed checks

The audit streamed the stored compressed object and parsed all numeric cells. It
verified:

- exactly 18,802 gene rows and 18,802 unique gene identifiers;
- zero duplicate gene identifiers;
- exactly 405 sample columns in the ordered header `T1` through `T405`;
- exactly 7,614,810 measurements;
- 7,614,810 finite measurements, zero missing values, and zero nonfinite values;
- a minimum of `-3.32192809488736` and maximum of `16.2706822322647`;
- 969,918 values at the expected `log2(0.1)` floor and zero values below it; and
- all 50 governed PAM50 genes, with zero missing or ambiguous mappings.

The matrix contains the modern canonical names `NUF2`, `NDC80`, and `ORC6`, so
the permitted historical aliases `CDCA1`, `KNTC2`, and `ORC6L` were not needed.

## Interpretation

The observed floor and official GEO processing statement agree that this artifact
is already represented as `log2(FPKM + 0.1)`. It must not receive the candidate
protocol's conditional `log2(FPKM + 1)` transformation. The preprocessing bridge
must be amended prospectively before reference construction.

This audit establishes matrix integrity, declared input scale, and PAM50 panel
coverage. It does not independently validate the submitter's FPKM calculation,
prove participant identity or ER labels, establish GSE81538–GSE96058 participant
non-overlap, select the 100-sample reference subset, construct a reference vector,
execute PAM50, inspect outcomes, or estimate clinical performance.

## Data-minimization boundary

Molecular values were parsed by deterministic code only to calculate aggregate
integrity statistics. No participant row or matrix subset was written to Git or
retained by the audit. No outcome, treatment, subtype, score, reference vector,
or classifier result was accessed or produced. No participant-level matrix was
provided to a generative model.
