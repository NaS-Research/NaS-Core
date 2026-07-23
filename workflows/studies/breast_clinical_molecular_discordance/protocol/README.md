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

Validate it with:

```console
uv run nas-core reliability validate \
  workflows/studies/breast_clinical_molecular_discordance/protocol/reliability_specification.yaml
```

Completion gate: the reliability specification and analysis plan have documented
founder approval, are preregistered, and are Git-tagged. Until then, molecular and
outcome execution remain prohibited.
