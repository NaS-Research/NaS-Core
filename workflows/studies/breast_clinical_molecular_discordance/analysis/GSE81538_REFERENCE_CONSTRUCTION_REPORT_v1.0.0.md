# GSE81538 Fixed Reference Construction Report 1.0.0

## Decision

`pass`

Frozen revision `1b7b2f5e63b5710154ac3d655031aadbc2c0ba53` constructed
the prespecified GSE81538 fixed reference. Receipt SHA-256 is
`c71ad6af37d9eeecd6b567e0abba959233a460a945ecf9d89ca25be408457f3c`.

## Executed method

The service independently verified the governed matrix and external participant-
manifest checksums. It read exactly 5,000 finite values: the 50 PAM50 rows across
the 100 prespecified samples, balanced as 50 ER-negative and 50 ER-positive
records. It consumed the stored `log2(FPKM + 0.1)` values unchanged and calculated
the gene-wise median.

The resulting 50-gene vector is stored only in governed external object storage:

`derived/nas-brca-002/reference-development/gse81538_pam50_median_reference_v1.0.0.json`

Independent verification reproduced SHA-256
`72bd804f9f4540ecbf9eadbc42feb6dee5b6618a775caff4965e92ae866f40e9`.
Neither its values nor participant identifiers are retained in Git.

## Aggregate diagnostics

- Selected samples: 100 (50 per ER stratum)
- Retained genes: 50
- Parsed and finite measurements: 5,000
- Reference minimum: -1.07501738803508
- Reference maximum: 7.65613042047944
- Reference mean: 3.5832184383530477

These are construction-integrity diagnostics, not biological or clinical findings.

## Boundaries and limitations

No outcome, treatment, subtype, validation-cohort, classifier, reliability, or
clinical-association value was accessed or produced. No participant molecular
data was supplied to generative AI. The reference remains candidate and is not
locked. It inherits the conservative ER-code inference, unverified identifier-
level independence, and potential source-representativeness limitations.

## Next gate

Execute the prespecified outcome-blind sensitivities: alternative eligible
deterministic samples where available, 20% trimmed-mean comparison, and
reference-vector/score stability without GSE96058 or outcomes.
