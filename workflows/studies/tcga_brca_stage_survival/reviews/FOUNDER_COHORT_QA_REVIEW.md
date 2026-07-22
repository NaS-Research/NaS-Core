# Founder Cohort QA Review — NAS-BRCA-001

Build ID: `73bfc98672e03ca3da427fda5de63ccf804674783a21ddcbf5563955290d2e53`

Review type: `internal_self_review`

Reviewer: Dalron J. Robertson

Conflict: Founder, study lead, analyst, author, internal reviewer, and gate approver

## Checklist

- [x] Snapshot, protocol, algorithm, and code identities match the receipt.
- [x] Artifact and manifest checksum verification is accepted.
- [x] The 1,037 included and 61 excluded cases form a complete, disjoint partition.
- [x] Exclusion precedence implements protocol `1.1.0` without outcome-based changes.
- [x] Missingness is reported for every requested source field.
- [x] Stage normalization covers all included cases without viewing survival by stage.
- [x] Included-versus-excluded age and vital-status differences are accepted as limitations.
- [x] The AJCC-edition sensitivity analysis remains mandatory.
- [x] No stage-by-outcome result has been viewed before this decision.
- [x] The immutable cohort may not be changed in response to later model results.

## Decision

Status: `approved`

Rationale: The founder explicitly approved build `73bfc986…d2e53` for the
prespecified modeling phase after reviewing its aggregate QA summary and
AI-assisted integrity review. The verified partition and provenance satisfy the
cohort gate, with the limitations below retained.

Required changes: None before prespecified modeling. Any later correction must
preserve this build and create a new algorithm version; it cannot overwrite or
silently redefine this cohort after outcomes are inspected.

Accepted limitations:

- AJCC staging-system edition is absent for 142 input cases.
- Complete-case selection may affect generalizability and survival estimates;
  excluded cases were older in aggregate and differed in vital-status counts.
- Twenty cases lacked a valid positive survival duration, 24 lacked a usable
  pathologic stage, and 15 lacked valid age under the locked rules.
- The AJCC-edition and five-year-censoring sensitivity analyses remain mandatory.
- This qualification analysis cannot support patient-level treatment,
  diagnostic, clinical-utility, or deployment claims.

Reviewed at: `2026-07-21T20:28:27-05:00`

## Consequences

- **Approve:** update the typed cohort receipt, tag the frozen cohort gate, and
  implement the prespecified statistical pipeline.
- **Changes requested:** preserve this build, document the defect, change the
  algorithm version, and create a new build without inspecting model results.
- **On hold:** keep modeling blocked and record the condition required to resume.
- **Reject:** preserve the build and stop the qualification analysis.
