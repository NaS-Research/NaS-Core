# Protocol

Required artifacts:

- `protocol/analysis_plan.yaml`
- `protocol/reliability_specification.yaml`

The reliability specification is the pre-analysis method contract for question
`0.3.0`. Version `0.1.0` fixes:

- the historical 50-gene PAM50 input and current-symbol alias mapping;
- the five-centroid, Spearman nearest-centroid score, runner-up, and margin formulas;
- a deterministic 50-run leave-one-gene-out sensitivity panel;
- the governed boundary for an independent technical measurement-error panel;
- every data-quality, reliability, unclassifiable, and abstention state; and
- the exact patient-level output fields and report-versus-abstain actions.

It is intentionally `draft` and nonexecuting. The centroid and reference artifacts,
platform transformations, technical-error model, numerical tolerances, margin threshold,
and label-retention threshold must be evidence-backed, lawfully reusable, checksummed,
and approved before the contract can be locked. Neither outcomes nor external-validation
performance may select those values.

The deterministic scoring contract now has a synthetic-only execution kernel. It
normalizes the three historical gene aliases, fails closed on missing, duplicate,
ambiguous, or nonfinite inputs, computes five Spearman centroid scores, preserves
top and runner-up scores and their margin, executes all 50 leave-one-gene-out
runs, and can additionally execute an explicit synthetic technical-error panel.
Family-level totals, valid runs, and retained-label counts reconcile exactly to
the aggregate repeatability output. Caller-supplied synthetic thresholds map
results to `reliable`, `unstable`, `unclassifiable`, or `insufficient_data`
states. Every non-reliable state abstains.
The input model accepts only `SYNTHETIC-*` sample identifiers and every output is
marked `synthetic_method_validation_only`.

This implementation validates algorithms and state transitions. Synthetic
technical-error vectors must be explicit, complete, seed-bound, and checksummed
in output provenance; invalid vectors remain counted and force abstention. It
does **not** resolve or approve the real centroid matrix, external reference,
transformation, empirically calibrated technical-error model, numerical
tolerance, or scientific thresholds. It cannot read patient identifiers,
authorize molecular access, or produce a NaS research result.

Exercise the kernel with explicitly synthetic method and sample YAML files:

```console
uv run nas-core reliability synthetic-score \
  workflows/studies/breast_clinical_molecular_discordance/protocol/reliability_specification.yaml \
  /path/to/synthetic-method.yaml \
  /path/to/SYNTHETIC-sample.yaml \
  --technical-error-panel /path/to/synthetic-technical-panel.yaml \
  --synthetic-only
```

Validate it with:

```console
uv run nas-core reliability validate \
  workflows/studies/breast_clinical_molecular_discordance/protocol/reliability_specification.yaml
```

Completion gate: the reliability specification and analysis plan have documented
founder approval, are preregistered, and are Git-tagged. Until then, molecular and
outcome execution remain prohibited.
