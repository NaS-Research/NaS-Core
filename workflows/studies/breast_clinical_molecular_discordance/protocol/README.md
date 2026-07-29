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
currently satisfies every criterion, and no calibration source is selected.

The founder selected Route C on 2026-07-28. The checksum-bound decision is stored
at `reviews/FOUNDER_METHOD_ROUTE_DECISION_v1.0.0.yaml`; activation
`method_route_activation_v1.0.0.yaml` preserves question `0.3.0`, stages the
centroid candidate, and activates calibration acquisition while retaining zero
method lock, molecular or outcome access, or execution authority. Accordingly,
no calibration source is selected.

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
artifacts only. The founder authorized both in
`reviews/FOUNDER_CALIBRATION_INQUIRY_AUTHORIZATION_v1.0.0.yaml`, and the two
recipient addresses were verified against authoritative PubMed and NCBI GEO
records. Transmission remains on a credential hold because the authenticated
Gmail sender does not match the approved `dalronj.robertson@gmail.com` sender.
The founder subsequently revoked both inquiries in
`reviews/FOUNDER_CALIBRATION_INQUIRY_REVOCATION_v1.0.0.yaml`. Zero messages were
sent, all external contact is prohibited, and any future contact requires a new
explicit authorization.

The route-neutral precision tool can verify hypothetical technical-replicate
designs without selecting a scientific parameter or source:

```console
uv run nas-core reliability calibration-precision-design \
  workflows/studies/breast_clinical_molecular_discordance/protocol/technical_calibration_precision_scenario_HYPOTHETICAL.yaml \
  --hypothetical-only
```

The checked-in fixture returns 141 independent pair observations for hypothetical
0.90 retention, 95% confidence, and ±0.05 expected Wilson precision. This is
software evidence only, not a NaS sample-size recommendation. See
`reviews/TECHNICAL_CALIBRATION_PRECISION_TOOL_v1.0.0.md`.

Route C's metadata-only calibration-lineage audit executed from frozen revision
`d256342`. It verifies aggregate sample-title and replicate-linkage counts across
GSE60788, GSE96058, and GSE130397 and tests public accession/title overlap while
retaining no identifiers, rows, expression values, outcomes, or raw artifacts:

```console
uv run nas-core reliability calibration-lineage-audit \
  protocol/method_route_activation_v1.0.0.yaml \
  ingestion/calibration_lineage_receipt_v1.0.0.yaml \
  --execute
```

Receipt SHA-256 `ef3cce52…9d2` records zero public accession/title overlap
between GSE60788 and GSE96058. That does not prove biological-specimen
non-overlap, so no source is selected and authoritative lineage confirmation
remains required.

Phase 1 prospective design `0.1.0` is recorded in
`prospective_calibration_experiment_design_v0.1.0.yaml`. It separates an
excluded feasibility pilot, primary post-extraction calibration, and optional
extraction sensitivity; declares technical estimands and firewalls; and leaves
all material parameters for founder and statistical review.

Validate the exact Route C and no-contact bindings with:

```console
uv run nas-core reliability prospective-calibration-validate \
  workflows/studies/breast_clinical_molecular_discordance/protocol/prospective_calibration_experiment_design_v0.1.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance/protocol/method_route_activation_v1.0.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance/protocol/technical_calibration_acquisition_plan_v1.0.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance/reviews/FOUNDER_CALIBRATION_INQUIRY_REVOCATION_v1.0.0.yaml
```

See `PROSPECTIVE_CALIBRATION_DESIGN_REPORT_v0.1.0.md` and the checksum-bound
founder packet. The design authorizes no contact, spending, specimen or data
acquisition, threshold selection, or execution.

The current cross-phase completion state is separately frozen in
`../reviews/RESEARCH_COMPLETION_AUDIT_v1.1.0.yaml` with a human-readable
`RESEARCH_COMPLETION_REPORT_v1.1.0.md`. Version `1.0.0` remains immutable
history. Validate that every cited artifact still
exists with the exact frozen bytes:

```console
uv run nas-core study completion-validate \
  workflows/studies/breast_clinical_molecular_discordance/reviews/RESEARCH_COMPLETION_AUDIT_v1.1.0.yaml \
  workflows/studies/breast_clinical_molecular_discordance \
  workflows/studies/breast_clinical_molecular_discordance/pipeline.yaml
```

The current receipt proves Phase 0 complete and Phase 1 in progress. It explicitly
rejects final-review readiness, scientific conclusions, publication, and
submission in the current state.

The founder approved prospective design `0.1.0` for planning only. Immutable
`prospective_calibration_planning_activation_v1.0.0.yaml` was generated from
revision `00bfa89` and authorizes only internal scientific, statistical,
operational-scenario, and budget-scenario planning.

Three activation-bound multi-objective scenarios are stored under
`calibration-scenarios/`. Recalculate any scenario with:

```console
uv run nas-core reliability calibration-scenario \
  workflows/studies/breast_clinical_molecular_discordance/protocol/calibration-scenarios/HYPOTHETICAL_BALANCED.yaml \
  workflows/studies/breast_clinical_molecular_discordance/protocol/prospective_calibration_planning_activation_v1.0.0.yaml \
  --code-revision 2a51d0b \
  --hypothetical-only
```

The lean, balanced, and high-precision scenarios require 82, 185, and 945
attempted pairs under their hypothetical inputs. These are not approved sample
sizes. See `CALIBRATION_SCENARIO_REPORT_v1.0.0.md` and the combined founder
scientific/statistical planning packet.

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
