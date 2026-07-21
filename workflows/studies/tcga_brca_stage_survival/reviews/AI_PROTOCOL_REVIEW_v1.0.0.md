# AI-Assisted Protocol Review — NAS-BRCA-001

Reviewed protocol: `1.0.0`

Resulting protocol: `1.1.0`

Review type: `ai_assisted_internal_review`

Reviewer: OpenAI Codex

Reviewed at: 2026-07-21T07:26:50-05:00

Authority: Advisory only; cannot authorize preregistration

## Disposition

Advisory review complete after revisions. The protocol remains
`pending_review`. Dalron J. Robertson must personally complete the founder
self-review record and make the gate decision.

No GDC case data, outcome-bearing data, or final study results were retrieved or
inspected during this review.

## Primary-source checks

- GDC states that expanded TCGA clinical data can contain multiple diagnoses and
  recommends using `diagnosis_is_primary_disease = true` to identify the
  diagnosis associated with the molecular data:
  <https://gdc.cancer.gov/why-does-tcgabiolinks-no-longer-work-when-retrieving-diagnosis>.
- The current GDC API available-fields reference includes `index_date`,
  `diagnoses.diagnosis_id`, `diagnoses.diagnosis_is_primary_disease`,
  `diagnoses.ajcc_staging_system_edition`, and follow-up identifiers:
  <https://docs.gdc.cancer.gov/API/Users_Guide/Appendix_A_Available_Fields/>.
- GDC API release notes document recent changes to survival handling, including
  use of `follow_ups.days_to_follow_up` and exclusion of unknown vital status:
  <https://docs.gdc.cancer.gov/API/Release_Notes/API_Release_Notes/>.
- GDC documentation defines `days_to_last_follow_up` relative to the initial
  pathologic diagnosis:
  <https://docs.gdc.cancer.gov/Data_Submission_Portal/Users_Guide/Data_Submission_Walkthrough/>.

## Findings and resolutions

### AR-001 — Primary diagnosis selection was not reliable

Severity: Critical

Resolution: Resolved in protocol `1.1.0`

The draft requested `classification_of_tumor` but not the explicit
`diagnosis_is_primary_disease` field now recommended by GDC for expanded TCGA
clinical data. The revised protocol requests the primary-disease flag and
requires it for diagnosis selection.

### AR-002 — API array order was an unstable tie-breaker

Severity: Critical

Resolution: Resolved in protocol `1.1.0`

“Stable source order” is not a defensible invariant for nested API results. The
revised protocol selects the eligible primary diagnosis closest to the case
index date and then uses lexical `diagnosis_id` as the final deterministic
tie-breaker.

### AR-003 — Survival time origins could be mixed

Severity: Critical

Resolution: Resolved in protocol `1.1.0`

The draft described diagnosis as the common time origin but did not request or
restrict `case.index_date`. The revision requests `index_date`, restricts the
cohort to `Diagnosis`, uses `demographic.days_to_death` for deaths, and uses the
maximum positive follow-up time plus the selected diagnosis's last-follow-up
time for living cases.

### AR-004 — Zero-day durations lacked an analysis rule

Severity: Major

Resolution: Resolved in protocol `1.1.0`

Zero-day durations can create ambiguous survival ordering and implementation
differences. The revision excludes them, requires an explicit count, and records
the possible selection limitation.

### AR-005 — Stage-edition heterogeneity was not captured

Severity: Major

Resolution: Resolved in protocol `1.1.0`

The revision requests and preserves the AJCC staging-system edition, reports its
distribution, and adds a gated sensitivity analysis within the predominant
edition.

### AR-006 — Model failure and age-form assumptions lacked explicit handling

Severity: Major

Resolution: Resolved in protocol `1.1.0`

The revision adds an interpretation threshold of at least 10 deaths in each
binary stage group, blocks interpretation when the Cox coefficient is not
estimable or convergence fails, defines the logarithm used for a time-varying
effect, and adds a restricted-cubic-spline age sensitivity analysis.

### AR-007 — Data Release provenance could be overstated

Severity: Major

Resolution: Protocol requirement added; ingestion implementation still required

The existing ingestion service records an operator-supplied Data Release and
the API `/status` response, but the latter does not itself verify the declared
Data Release. Before ingestion, the implementation must archive an official
release-note reference and checksum and must not label the release as
API-verified without supporting evidence.

## Remaining founder decisions

The founder review must decide whether:

1. restricting to `index_date = Diagnosis` is acceptable for this qualification study;
2. excluding zero-day records is preferable to applying a small positive offset;
3. 10 deaths per stage group is an acceptable minimum interpretation threshold;
4. age-only adjustment is sufficient for the deliberately narrow reproduction;
5. the proposed pass, conditional-pass, and fail criteria are adequate; and
6. protocol `1.1.0` should be approved, revised, held, or rejected.
