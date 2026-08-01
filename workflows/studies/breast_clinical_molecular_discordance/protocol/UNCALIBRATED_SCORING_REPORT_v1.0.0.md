# Uncalibrated Scoring Boundary Report 1.0.0

The checksum-bound receipt
`uncalibrated_scoring_receipt_v1.0.0.yaml` has SHA-256
`0c0111ea298862e0cbb536694b4c1224e3fea25266aaa9bc572328dfa8a825c8`.
It was frozen from implementation revision `1792e8f` without accessing TCGA,
GSE96058, or outcome values and without executing the classifier on a study
profile.

The implementation joins the frozen processed-input QC states to the fixed
five-centroid Spearman arithmetic. A QC failure bypasses scoring and abstains.
A numerical failure after valid QC records `score_failed` and abstains. A
successful numerical score records the best score, runner-up score, and margin,
but its only permitted state is `uncalibrated`, its only permitted action is
`abstain`, and its reason is `technical_calibration_incomplete`. No threshold
can convert that score into a reportable label.

Attempted-denominator accounting is exact and fail-closed:

- attempted = QC-valid + QC-failed;
- QC-valid = scored + score-failed;
- scored = uncalibrated;
- abstained = attempted; and
- reported labels = 0.

These equations prevent invalid profiles and scoring failures from disappearing
from later reporting. Synthetic fixtures prove the software behavior, including
tie failure and denominator rejection, but do not establish analytical or
clinical reliability. The prospective primary-calibration assay, compatible
technical-error distribution, pair count, and reliability thresholds remain
unresolved.
