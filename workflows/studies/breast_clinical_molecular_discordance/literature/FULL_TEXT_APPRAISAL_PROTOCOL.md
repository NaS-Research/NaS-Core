# Full-Text Eligibility and Quality-Appraisal Protocol

Version: `1.0.0`

This gate applies to the 27 provisional title/abstract inclusions. Relevance rank,
journal name, citation count, novelty, and favorable results are not measures of
methodological quality.

## Framework

Every appraisal records the exact full-text source, access basis, content checksum,
study design, full-text eligibility, evidence locations, reviewer, limitations,
funding and conflicts. Seven domains are judged independently:

1. population selection;
2. specimen and measurement;
3. classifier implementation;
4. reference or comparator definition;
5. analysis and statistics;
6. validation and transportability; and
7. reporting and reproducibility.

The domains adapt concepts from PROBAST+AI for prediction/classification models and
QUADAS-2 for selection, index-method, comparator, and flow concerns. STROBE and
design-specific EQUATOR guidance inform reporting completeness, but reporting
completeness is not treated as proof of low risk of bias.

- [PROBAST+AI](https://www.bmj.com/content/388/bmj-2024-082505)
- [QUADAS-2](https://www.bristol.ac.uk/population-health-sciences/projects/quadas/history/quadas-2/)
- [STROBE](https://www.equator-network.org/reporting-guidelines/strobe/)

## Evidence roles

- `anchor`: eligible; no high or unclear domain; analysis/statistics and external
  validation/transportability must both be low risk.
- `supporting`: eligible; limitations exist, but no domain is high risk.
- `context_only`: eligible for background, contradiction, method history, or gap
  definition, but not strong enough to support a central effectiveness or clinical
  claim.
- `excluded`: fails a full-text eligibility criterion with one explicit reason.

The framework intentionally has no additive quality score. A severe defect cannot
be averaged away by strong reporting elsewhere. Contradictory and null findings are
appraised under the same rules as favorable findings.

## Operational sequence

1. Resolve a lawful source and record its access basis; do not bypass paywalls.
2. Hash the exact reviewed full-text file or normalized open-text representation.
3. Confirm eligibility from the complete paper before quality designation.
4. Select the study design and evaluate all seven domains with page/section evidence.
5. Validate the YAML with `nas-core literature appraisal-validate`.
6. Founder reviews and locks the appraisal; later evidence claims cite the locked
   appraisal and exact source artifact.
