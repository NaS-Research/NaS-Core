# Analysis

Required artifacts:

- `analysis/README.md`
- `tests/README.md`

The current executable method component is the synthetic-only single-sample
reliability kernel in `nas_core.analysis.reliability`. It performs fixed
five-centroid Spearman scoring and the deterministic 50-run leave-one-gene-out
panel while preserving explicit failure and abstention states. Its input contract
rejects any sample identifier that does not begin with `SYNTHETIC-`.

It is a method-validation component, not a real cohort analysis. Real molecular
execution remains prohibited until the evidence review closes, all governed
method dependencies are resolved, the specification and analysis plan are
approved and preregistered, and molecular access is explicitly authorized.

Completion gate: Deterministic pipeline and synthetic tests pass; run artifacts are frozen.
