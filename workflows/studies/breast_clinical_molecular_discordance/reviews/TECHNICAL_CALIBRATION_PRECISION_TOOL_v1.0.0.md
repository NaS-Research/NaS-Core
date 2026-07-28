# Technical Calibration Precision Tool 1.0.0

Study: `NAS-BRCA-002`  
Status: software-qualified with hypothetical inputs only  
Decision authority: none

## Purpose

The tool calculates the number of observed technical-replicate pairs needed to
achieve a declared expected confidence-interval precision for binary label
retention. It uses the expected Wilson score interval and supports a declared
cluster design effect.

This is precision planning, not hypothesis-test power. It does not determine the
number of specimens needed for continuous expression-error distributions,
subtype-specific performance, margin calibration, abstention calibration,
clinical outcomes, or clinical utility.

## Synthetic demonstration

The checked-in scenario assumes, solely for software verification:

- expected technical label retention of 0.90;
- 95% confidence;
- target expected interval half-width of 0.05; and
- design effect of 1.0.

The deterministic result is 141 independent pair observations, with an expected
Wilson half-width of approximately 0.049995. At 140 observations the target is
not met. With a design effect of 2.0, the observation requirement doubles while
preserving the same effective pair count.

These values are not a recommended design and are not evidence about PAM50. They
derive from no NaS molecular or patient data.

## Required scientific review before real use

A real design must separately approve:

1. the reliability estimand and acceptable uncertainty;
2. an expected retention probability justified independently of validation data;
3. confidence level and multiplicity strategy;
4. clustering from multiple pairs per specimen, batch, site, or laboratory;
5. subtype and margin-range representation;
6. missingness, assay failure, and unusable-pair inflation;
7. continuous-expression and threshold-calibration objectives; and
8. the lawful, independent calibration source.

No source is selected and no data collection, molecular access, threshold
selection, or study execution is authorized.
