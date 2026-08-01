# Pilot-Informed Pair-Count Reestimation Report 1.0.0

Frozen revision `d4e0dca` evaluated whether the two completed excluded public
pilots could support the required blinded final pair-count reestimation. Receipt
`calibration_pair_count_reestimation_receipt_v1.0.0.yaml` has SHA-256
`f5b6229489182d36f94dd47e066e59a9dc869146d57d2b1e1662d9d56e3e4892`.

## Result

The 13 independent replicate groups and 21 within-group pairs estimate
source-specific PAM50 rank agreement and expression-scale variation. They do
not estimate the locked primary-calibration inputs:

- subtype-label retention under a locked classifier;
- subtype-score and runner-up-margin paired standard deviations;
- target-assay attrition, rerun, batch, or clustering parameters; or
- receptor, RNA-quality, margin, and processing-placement coverage.

Neither source used the still-unselected target assay workflow, no classifier
was executed, and the two expression scales are noncommensurate. Substituting a
source RMSE for subtype-score variation would therefore create false precision.

The final attempted-pair count is formally non-estimable from these pilots. The
previous balanced result of 185 attempted pairs remains a hypothetical internal
feasibility reference, not an approved sample size. The 30-pair excluded
prospective pilot remains a planning target only.

## Decision boundary

No proxy was substituted and no source was pooled. No threshold, classifier,
outcome, specimen, procurement, spending, or execution was authorized. Primary
calibration remains on hold until the intended assay and preprocessing bridge
are frozen and a target-matched excluded pilot supplies the missing nuisance
parameters.
