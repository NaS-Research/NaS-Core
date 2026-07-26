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

Completion gate: Deterministic pipeline and synthetic tests pass; run artifacts are frozen.
