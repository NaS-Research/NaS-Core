# Revised Search Feasibility Amendment — Version 0.2.3

Question version: `0.3.0`
Prior candidate strategy: `0.2.0`
Intermediate candidate strategies: `0.2.1`, `0.2.2`
Amended candidate strategy: `0.2.3`

## Count-only result

On 2026-07-23, the authorized candidate queries were sent once to each official
API without storing records or manifests:

- PubMed: 170 records
- Europe PMC: 208 records

## Decision

The counts were below the system safety limit but broader than the intended
high-quality review capped at 30 final studies. The broad
`PAM50 OR intrinsic subtype` concept admitted many general subtype reports that
did not directly address single-sample reliability.

Version `0.2.1` removed the generic `intrinsic subtype` branch and required PAM50
or one of the named direct method families. Its count-only check returned 1,363
PubMed and 1,657 Europe PMC records because the bare acronym `AIMS` was interpreted
as the common English word “aims.”

Version `0.2.2` replaces bare `AIMS` with the full method name `Absolute Intrinsic
Molecular Subtyping`. PAM50, MiniABS, MPAM50, BreastSubtypeR, and PCAPAM50 remain
explicit method terms. Reliability, uncertainty, centering, or related method
concepts remain required. Its corrected preview returned 130 PubMed and 165 Europe
PMC records.

Version `0.2.3` removes broad `normalization`, `confidence`, and `perturbation`
branches already covered by the immutable prior inventory. The supplemental search
now targets single-sample operation, uncertainty, ambiguity, Not Assigned or
abstention, margin, permutation, calibration, centering, test-set bias,
repeatability, and reproducibility. Its final count-only check returned:

- PubMed: 52 records
- Europe PMC: 95 records

The previously identified 13-record priority set is independent of the supplemental
query and remains mandatory for founder adjudication. This amendment changes search
precision, not eligibility, the evidence cap, or the citation-chain stopping rule.

The final counts are bounded for complete human screening and the 30-study evidence
cap. Strategy `0.2.3` is therefore locked and retrieval-authorized under the
question-`0.3.0` founder Phase 0 authorization. Count previews stored no records.
