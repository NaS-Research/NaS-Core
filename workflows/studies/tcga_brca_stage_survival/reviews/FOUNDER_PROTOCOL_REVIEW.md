# Founder Protocol Review — NAS-BRCA-001

Protocol version: `1.1.0`

Review type: `internal_self_review`

Reviewer: Dalron J. Robertson

Conflict disclosure: Founder, study lead, analyst, author, internal reviewer,
and gate approver

## Review checklist

### Scientific and clinical

- [x] The qualification objective is useful and appropriately narrow.
- [x] Early stage I/II versus advanced stage III/IV is scientifically defensible.
- [x] Pathologic stage is not described as causal or as a treatment effect.
- [x] The TCGA population and overall-survival limitations are adequately stated.
- [x] AJCC staging-edition heterogeneity is captured and addressed.

### Cohort and endpoint

- [x] `diagnosis_is_primary_disease` is the correct diagnosis-selection anchor.
- [x] The deterministic diagnosis tie-breaker is acceptable.
- [x] Restricting `index_date` to `Diagnosis` preserves a coherent time origin.
- [x] Death and censoring derivations are unambiguous.
- [x] The decision to exclude and report zero-day durations is acceptable.
- [x] Inclusion and exclusion reasons can be made mutually exclusive.

### Statistical

- [x] The age-adjusted Cox model answers the prespecified qualification question.
- [x] Age-only adjustment is acceptable for this noncausal reproduction.
- [x] The 10-deaths-per-group interpretation threshold is acceptable.
- [x] Proportional-hazards, age-form, influence, and convergence checks are sufficient.
- [x] Sensitivity analyses S1–S5 are prespecified clearly enough to implement.
- [x] Multiplicity language prevents confirmatory overstatement.

### Governance and reproducibility

- [x] Only public/open fields are requested.
- [x] The exact query, release evidence, raw responses, warnings, and checksums will be frozen.
- [x] The API status response will not be misrepresented as Data Release verification.
- [x] No outcome-bearing data has been inspected before this decision.
- [x] Null, contradictory, failed-diagnostic, and excluded results will be retained.

## Required written decisions

Decision: `approved`

Rationale: Protocol `1.1.0` is sufficiently narrow, deterministic, governed, and
falsifiable for the first Cortex qualification study. The founder accepted the
five explicit recommendations presented after the AI-assisted review and
authorized preregistration.

Required changes: None before preregistration. Data Release reference capture
must be implemented and validated before the first real snapshot.

Accepted limitations: Founder self-review is not independent human review;
TCGA is not representative of routine care; age-only adjustment is noncausal;
AJCC editions and follow-up completeness may vary; zero-day records will be
excluded and reported; overall survival is not disease-specific survival.

Knowledge or expertise limitations: NaS is currently a one-person organization.
No external breast-oncology or biostatistical expert reviewed this protocol.
External expert critique is planned near manuscript completion.

Reviewed at: 2026-07-21T14:13:33-05:00

## Gate consequences

- **Approve:** update the founder review in `analysis_plan.yaml`, change the plan
  to `preregistered`, validate, commit, and tag the protocol before ingestion.
- **Changes requested:** keep `pending_review`, record changes, increment the
  protocol version, and repeat affected checks.
- **On hold:** keep ingestion blocked and state the condition needed to resume.
- **Reject:** retire the plan without retrieving outcome-bearing data.
