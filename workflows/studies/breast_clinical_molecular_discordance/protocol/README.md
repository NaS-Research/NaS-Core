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

The synthetic batch boundary composes only independent calls to this single-sample
kernel. It accepts no batch statistics, rejects duplicate synthetic identities,
retains each result's sample-only input hash, and records
`sample_execution: independent_single_sample_calls`. Tests prove that adding a
companion fixture or reversing batch order changes the batch hash but cannot
change either sample's reliability result. This is software evidence for
patient-independent execution, not validation on patients.

Method-dependency audit `1.0.0` is now bound to the founder-authorized saturated
synthesis and this exact draft specification. It verifies Bioconductor `genefu`
2.44.0 as a lawful, checksummed historical PAM50 centroid candidate while
showing that the fixed reference, independent RNA-seq technical-error
calibration, thresholds, and numerical conformance remain unresolved. The audit
recommends holding molecular execution and acquiring independent calibration.
The material choice is frozen in
`reviews/FOUNDER_METHOD_DEPENDENCY_DECISION_PACKET_v1.0.0.md`.

The route-neutral candidate import is complete. Frozen importer revision
`2843a6e` verified both official source hashes, canonicalized only `CDCA1` to
`NUF2`, `KNTC2` to `NDC80`, and `ORC6L` to `ORC6`, and materialized exactly 250
finite coefficients. The candidate SHA-256 is
`51a1b186a32ba02fa61a001ee7dc7e21876b9b09f78cb7eb8f0fdd068b4f8c2b`.
Its receipt remains candidate-only, founder-unapproved, and non-executable.

The route-neutral technical-calibration acquisition plan is now frozen at
`technical_calibration_acquisition_plan_v1.0.0.yaml`. It rejects validation
leakage, requires participant-level technical pairs with lawful access and stable
pair identities, requires full classifier-panel and assay-process coverage, and
defers any minimum pair count to a prospective power analysis. No listed source
currently satisfies every criterion, and no source or founder route is selected.

Validate the acquisition contract with:

```console
uv run nas-core reliability calibration-plan-validate \
  workflows/studies/breast_clinical_molecular_discordance/protocol/technical_calibration_acquisition_plan_v1.0.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance/protocol/method_dependency_audit_proposal_v1.0.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance/protocol/artifact-candidates/genefu_2.44.0_pam50_candidate_v1.0.0.yaml
```

Metadata-only source scouting is recorded in
`technical_calibration_source_scout_v1.0.0.yaml`. It identifies GSE60788 and
GSE130397 as relevant but currently ineligible small replicate resources and
records zero molecular access, outcome access, source selection, or external
contact. Validate it with:

```console
uv run nas-core reliability calibration-scout-validate \
  workflows/studies/breast_clinical_molecular_discordance/protocol/technical_calibration_source_scout_v1.0.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance/protocol/technical_calibration_acquisition_plan_v1.0.0.yaml
```

Two correspondence drafts are stored in
`reviews/UNSENT_CALIBRATION_DATA_INQUIRIES_v1.0.0.md`. They are preparation
artifacts only and have not been sent.

Exercise the kernel with explicitly synthetic method and sample YAML files:

```console
uv run nas-core reliability synthetic-score \
  workflows/studies/breast_clinical_molecular_discordance/protocol/reliability_specification.yaml \
  /path/to/synthetic-method.yaml \
  /path/to/SYNTHETIC-sample.yaml \
  --technical-error-panel /path/to/synthetic-technical-panel.yaml \
  --synthetic-only
```

The corresponding batch command accepts a `SyntheticExpressionBatch` YAML:

```console
uv run nas-core reliability synthetic-batch-score \
  workflows/studies/breast_clinical_molecular_discordance/protocol/reliability_specification.yaml \
  /path/to/synthetic-method.yaml \
  /path/to/SYNTHETIC-batch.yaml \
  --synthetic-only
```

Validate it with:

```console
uv run nas-core reliability validate \
  workflows/studies/breast_clinical_molecular_discordance/protocol/reliability_specification.yaml

uv run nas-core reliability audit-validate \
  workflows/studies/breast_clinical_molecular_discordance/protocol/method_dependency_audit_proposal_v1.0.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance/literature/saturated_evidence_synthesis_v1.0.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance/protocol/reliability_specification.yaml
```

Completion gate: the reliability specification and analysis plan have documented
founder approval, are preregistered, and are Git-tagged. Until then, molecular and
outcome execution remain prohibited.
