# GSE81538 Reference Metadata Selection Report 1.0.0

## Decision

`pass`

Frozen revision `76ace2be2c71449a5bc16fcfb7d59b55fc0ae140` executed the
founder-approved, field-isolated GSE81538 metadata selection. Receipt SHA-256 is
`b8b43884ed751b9ac78ee3a73dbea9c20cb8d20f5cd6be7c602bc9f261666423`.

## Executed boundary

The parser streamed the checksum-verified 51,036-byte family SOFT object and
read only `!Sample_title`, `!Sample_geo_accession`, and the exact `er consensus`
characteristic. It did not read expression, outcome, treatment, validation,
subtype, score, or classifier values. No participant data was sent to generative
AI.

All 405 records had unique accessions and unique ordered titles `T1` through
`T405`, establishing exact linkage to the already-audited expression columns.
The aggregate ER-consensus distribution was 82 code-0, 8 code-1, 11 code-2,
and 304 code-3 records.

## Frozen selection

Per founder decision `1.1`, code 0 was eligible for the ER-negative stratum,
code 3 for the ER-positive stratum, and codes 1/2 were excluded. Lexicographic
GEO-accession ordering selected 50 records per eligible stratum. The resulting
100-record manifest is stored only in governed external object storage at:

`derived/nas-brca-002/reference-development/gse81538_er_balanced_manifest_v1.0.0.json`

Its independently reproduced SHA-256 is
`4f36124c02dbe733dd7ffaf630c327715a19e3152e920db47249cecb8884a9fe`.
Participant identifiers are absent from Git.

## Limitations

- The public metadata contains no explicit inline codebook for ER consensus
  codes 0–3; using extreme codes 0 and 3 is a founder-approved conservative
  inference.
- The primary publication describes GSE81538 and GSE96058 as training and
  independent validation cohorts, but this is not an identifier-level or
  biological-specimen non-overlap audit.
- Deterministic balanced sampling does not guarantee that the subset represents
  all source-cohort variation.
- This milestone freezes participant selection only. It is not a classifier,
  subtype, reliability, validation, outcome, or clinical result.

## Next gate

Read only the 50 PAM50 rows and the 100 manifest-selected columns from the
governed GSE81538 matrix, construct the prespecified gene-wise median reference,
and run outcome-blind reference sensitivity diagnostics. GSE96058 molecular and
outcome data remain firewalled.
