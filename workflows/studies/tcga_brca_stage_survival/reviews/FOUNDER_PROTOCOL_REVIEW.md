# Founder Protocol Review — NAS-BRCA-001

Protocol version: `1.1.0`

Review type: `internal_self_review`

Reviewer: Dalron J. Robertson

Conflict disclosure: Founder, study lead, analyst, author, internal reviewer,
and gate approver

## Review checklist

### Scientific and clinical

- [ ] The qualification objective is useful and appropriately narrow.
- [ ] Early stage I/II versus advanced stage III/IV is scientifically defensible.
- [ ] Pathologic stage is not described as causal or as a treatment effect.
- [ ] The TCGA population and overall-survival limitations are adequately stated.
- [ ] AJCC staging-edition heterogeneity is captured and addressed.

### Cohort and endpoint

- [ ] `diagnosis_is_primary_disease` is the correct diagnosis-selection anchor.
- [ ] The deterministic diagnosis tie-breaker is acceptable.
- [ ] Restricting `index_date` to `Diagnosis` preserves a coherent time origin.
- [ ] Death and censoring derivations are unambiguous.
- [ ] The decision to exclude and report zero-day durations is acceptable.
- [ ] Inclusion and exclusion reasons can be made mutually exclusive.

### Statistical

- [ ] The age-adjusted Cox model answers the prespecified qualification question.
- [ ] Age-only adjustment is acceptable for this noncausal reproduction.
- [ ] The 10-deaths-per-group interpretation threshold is acceptable.
- [ ] Proportional-hazards, age-form, influence, and convergence checks are sufficient.
- [ ] Sensitivity analyses S1–S5 are prespecified clearly enough to implement.
- [ ] Multiplicity language prevents confirmatory overstatement.

### Governance and reproducibility

- [ ] Only public/open fields are requested.
- [ ] The exact query, release evidence, raw responses, warnings, and checksums will be frozen.
- [ ] The API status response will not be misrepresented as Data Release verification.
- [ ] No outcome-bearing data has been inspected before this decision.
- [ ] Null, contradictory, failed-diagnostic, and excluded results will be retained.

## Required written decisions

Decision: `pending`

Rationale:

Required changes:

Accepted limitations:

Knowledge or expertise limitations:

Reviewed at:

## Gate consequences

- **Approve:** update the founder review in `analysis_plan.yaml`, change the plan
  to `preregistered`, validate, commit, and tag the protocol before ingestion.
- **Changes requested:** keep `pending_review`, record changes, increment the
  protocol version, and repeat affected checks.
- **On hold:** keep ingestion blocked and state the condition needed to resume.
- **Reject:** retire the plan without retrieving outcome-bearing data.
