# AI-Assisted Cohort QA Review — NAS-BRCA-001

Build ID: `73bfc98672e03ca3da427fda5de63ccf804674783a21ddcbf5563955290d2e53`

Code revision: `912e281`

Reviewed at: 2026-07-21T19:19:43-05:00

Authority: Advisory only; cannot authorize survival modeling

## Disposition

The cohort build is internally consistent and suitable for founder review. No
stage-by-outcome table, survival curve, hazard ratio, hypothesis test, or fitted
model was produced or inspected.

## Integrity findings

- All three generated artifact hashes match the immutable manifest.
- The manifest payload checksum was independently recomputed and matched.
- The cohort contains 1,037 unique cases.
- The exclusion log contains 61 unique cases.
- The two partitions do not overlap and together contain all 1,098 input cases.
- Missingness is reported for all 15 source fields requested by protocol `1.1.0`.
- Every excluded case has exactly one reason under the declared precedence.

## Cohort flow

| Reason | Cases |
| --- | ---: |
| Invalid index date | 2 |
| Non-normalizable pathologic stage | 24 |
| Invalid survival time | 20 |
| Missing or invalid age | 15 |
| Included | 1,037 |
| Input | 1,098 |

## Material QA observations

- AJCC staging-system edition is absent at the case level for 142 input cases;
  the preregistered stage-edition sensitivity analysis remains necessary.
- The excluded group is older in the available aggregate data: mean age 67.28
  years versus 58.75 among included cases.
- Vital status is Dead for 13 of 61 excluded cases and 139 of 1,037 included
  cases. This does not test the primary question, but it indicates that
  complete-case selection may affect generalizability and survival estimates.
- Twenty cases lack a valid positive survival duration under the locked rules.
- Twenty-four cases have missing or non-normalizable pathologic stage.

## Recommendation

Approve the cohort for prespecified modeling with the following mandatory
conditions:

1. retain the complete exclusion and missingness tables in the research release;
2. carry the included-versus-excluded differences into the limitations;
3. execute the staging-edition and five-year-censoring sensitivities;
4. do not reinterpret excluded records after seeing the primary estimate; and
5. keep the cohort build immutable if modeling produces an unexpected result.
