# NAS-BRCA-002 Research Completion Report 1.16.0

Phase 0 is complete. Phase 1 remains in progress; Phases 2–6 have not started.
The study is not ready for final human review, and no scientific conclusion,
publication, or submission is authorized.

The retrospective expression bridge is frozen. TCGA-BRCA discovery will use
GDC `fpkm_unstranded` transformed as `log2(FPKM + 0.1)`. GSE96058 will be
consumed unchanged on its officially declared `log2(FPKM + 0.1)` scale. Both
will subtract the immutable GSE81538 gene-wise reference and use the checksummed
genefu centroids with Spearman scoring. Cohort-specific centering, validation
adaptation, imputation, and outcome-guided tuning are prohibited.

The next Phase 1 action is to freeze processed-input QC, failure, and abstention
rules. The retrospective bridge does not select the prospective laboratory
assay, and primary calibration remains on hold. External contact, spending,
specimens, controlled data, validation molecular values, outcomes, classifier
execution, publication, and submission remain prohibited. Final human review
remains preserved.
