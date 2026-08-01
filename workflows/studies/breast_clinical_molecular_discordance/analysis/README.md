# Analysis

Required artifacts:

- `analysis/README.md`
- `tests/README.md`

The current executable method component is the synthetic-only single-sample
reliability kernel in `nas_core.analysis.reliability`. It performs fixed
five-centroid Spearman scoring and the deterministic 50-run leave-one-gene-out
panel, plus optional explicit synthetic technical-error vectors, while preserving
per-family counts and explicit failure and abstention states. Its input contract
rejects any sample identifier that does not begin with `SYNTHETIC-`. Synthetic
technical-error panels bind their declared generator seed and receive a stable
SHA-256 in output provenance; they are software fixtures, not error calibration.

The batch wrapper is deliberately non-analytical: it applies the same kernel to
each unique synthetic identity independently and exposes no cohort-level
statistics to scoring. Companion-sample and input-order invariance are tested
directly. Batch hashes retain ordered execution provenance while individual
results remain byte-equivalent across batch contexts.

It is a method-validation component, not a real cohort analysis. Real molecular
execution remains prohibited until the evidence review closes, all governed
method dependencies are resolved, the specification and analysis plan are
approved and preregistered, and molecular access is explicitly authorized.

Reference construction is a distinct, bounded Phase 1 operation rather than a
cohort analysis. Plan
[`gse81538_reference_construction_plan_v1.0.0.yaml`](gse81538_reference_construction_plan_v1.0.0.yaml)
binds the audited matrix, external 100-record manifest, amended protocol, and
50-gene candidate by SHA-256. The service reads only those selected columns from
the 50 PAM50 rows, applies no additional transformation to the verified
`log2(FPKM + 0.1)` values, and computes a gene-wise median. The value-bearing
reference is written immutably outside Git; the repository receipt contains only
aggregate diagnostics, provenance, and artifact hashes. Outcomes, GSE96058,
classifier execution, and generative-AI processing remain prohibited.

Dry-run validation:

```console
uv run nas-core ingest reference-construct \
  analysis/gse81538_reference_construction_plan_v1.0.0.yaml \
  ingestion/gse81538_matrix_audit_receipt_v1.0.0.yaml \
  ingestion/gse81538_reference_metadata_receipt_v1.0.0.yaml \
  protocol/reference_development_protocol_v1.1.0.yaml \
  protocol/artifact-candidates/genefu_2.44.0_pam50_candidate_v1.0.0.yaml \
  --data-root "$NAS_DATA_ROOT" --code-revision REVISION
```

Completion gate: Deterministic pipeline and synthetic tests pass; run artifacts are frozen.

Frozen revision `1b7b2f5` executed the reference plan. Receipt
[`gse81538_reference_construction_receipt_v1.0.0.yaml`](gse81538_reference_construction_receipt_v1.0.0.yaml)
has SHA-256 `c71ad6af…57f3c`. Exactly 5,000 finite selected measurements
produced a 50-gene external reference with independently reproduced SHA-256
`72bd804f…f40e9`. No additional transform, outcome or validation access,
classifier execution, participant-data AI processing, or method lock occurred.
See
[`GSE81538_REFERENCE_CONSTRUCTION_REPORT_v1.0.0.md`](GSE81538_REFERENCE_CONSTRUCTION_REPORT_v1.0.0.md).

Sensitivity plan
[`gse81538_reference_sensitivity_plan_v1.0.0.yaml`](gse81538_reference_sensitivity_plan_v1.0.0.yaml)
binds the matrix, family metadata, participant manifest, primary reference, all
receipts, amended protocol, and PAM50 gene order. It compares the primary median
with a 20%-per-tail trimmed mean and summarizes vector agreement plus centered-
profile rank stability. It separately audits whether 50 new records remain in
each ER stratum; an underfilled stratum is reported as non-estimable and is not
silently replaced by a smaller cohort. No centroid classifier, threshold,
outcome, or validation data is used.

Frozen revision `5c1eba8` executed the panel. Receipt
[`gse81538_reference_sensitivity_receipt_v1.0.0.yaml`](gse81538_reference_sensitivity_receipt_v1.0.0.yaml)
has SHA-256 `be2322e4…613ff`. Median and 20%-trimmed-mean vectors show Pearson
`0.993438` and Spearman `0.991164`; centered-profile rank correlations have mean
`0.985411`, median `0.987995`, and minimum `0.938824`. The exact alternative
50+50 sensitivity is non-estimable because only 32 unselected ER-negative
records remain; no post hoc substitute was used. See
[`GSE81538_REFERENCE_SENSITIVITY_REPORT_v1.0.0.md`](GSE81538_REFERENCE_SENSITIVITY_REPORT_v1.0.0.md).
