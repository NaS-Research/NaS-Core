# Source-Isolated Calibration-Feasibility Pilot Report 1.0.0

Frozen revision `8251aa8` executed the estimands specified before result access
in `calibration_feasibility_pilot_plan_v1.0.0.yaml`. Aggregate receipt
`calibration_feasibility_pilot_receipt_v1.0.0.yaml` has SHA-256
`6dd74a9a9d3efeb0b6a32f10e0259807a7ff9f4b05e3cb33eaeebc300ce8c123`.
The detailed external object independently reproduces SHA-256
`b8863b4fa1b28fd51c0ac012c040938c21853d933c2b4c3a54a8b32a2d845c0d`.

## Prespecified estimands

Every replicate pair was evaluated on the historical 50-gene PAM50 panel using
Spearman correlation, Pearson correlation, mean absolute error, and root mean
square error. All unordered pairs within a replicate group were reduced by the
median. Source summaries were then calculated across independent groups, so
triplicates did not create pseudoreplicated evidence. Median group Spearman and
RMSE uncertainty used 10,000 group-resampling bootstrap replicates with frozen
seed `20260801`.

GSE60788 values were used unchanged because their exact source transformation
cannot be justified from the acquired artifact. GSE130397 used the official
library-specific strand columns—`rev` for Access and `fwd` for Ovation—and
`log2(CPM + 1)` normalization with all 60,675 features in each file as the
library-size denominator.

## Results

| Source | Independent groups | Pairs | Median Spearman (95% interval) | Median Pearson | Median MAE | Median RMSE (95% interval) | Median gene absolute difference |
|---|---:|---:|---:|---:|---:|---:|---:|
| GSE60788 | 6 | 6 | 0.985834 (0.966675–0.990720) | 0.988766 | 0.135111 | 0.195806 (0.146893–0.283179) | 0.076856 |
| GSE130397 | 7 | 15 | 0.983288 (0.969962–0.994454) | 0.987940 | 0.269815 | 0.361678 (0.138683–0.391452) | 0.159238 |

Both sources show high within-source PAM50 rank agreement. GSE130397 also shows
larger typical absolute differences and a wider RMSE interval than GSE60788 on
its own analysis scale. Because the scales differ, these absolute error values
are not a direct cross-source effect-size comparison.

The five highest exploratory gene-level differences were MIA, CCNE1, ACTR3B,
TYMS, and TMEM45B for GSE60788, and NDC80, UBE2T, GPR160, BAG1, and MMP11 for
GSE130397. These rankings are descriptive signals for future QC work; they were
not multiplicity-tested and support no gene-specific biological inference.

## Decision boundary

The pilots establish that the approved public files can support bounded
technical-variation estimation and that high correlation does not imply zero
technical error. They do not establish a patient-level reliability threshold,
analytical validity, subtype-call stability, clinical utility, or a primary
calibration set. The small group counts, library-method heterogeneity, uncertain
same-RNA or same-specimen lineage, and source-specific scales remain material.

The sources were not pooled. No outcome, validation cohort, classifier,
threshold, PHI, controlled data, external contact, export, publication, or
submission was accessed or authorized. Primary calibration remains on hold.
