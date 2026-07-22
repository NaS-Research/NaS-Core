# AI-Assisted Statistical Review — NAS-BRCA-001 Run 1.0.0

Run ID: `f41f944078a2b08c4a3348c55709a9dcb1302e0fb565239c446e4a1a8583a2ec`

Authority: Advisory only; cannot approve a results gate or scientific release

## Disposition

The immutable run is internally traceable and reproduces the expected direction,
but it is not release-ready. The recorded Cortex decision of **conditional pass**
is consistent with the prespecified rules because governance and the primary
association succeeded while material diagnostic and sensitivity problems remain.

## Verified result

- Participants: 1,037; deaths: 139.
- Early stage: 777 participants and 80 deaths.
- Advanced stage: 260 participants and 59 deaths.
- Age-adjusted advanced-versus-early HR: 2.81 (95% CI 2.00–3.94;
  p=2.03×10^-9).
- Unadjusted log-rank p=3.66×10^-9.
- Five-year-censoring HR: 3.57 (95% CI 2.39–5.34).
- The most common reported AJCC edition was 6th; its restricted result remained
  directionally consistent (HR 3.71, 95% CI 2.04–6.75).

These estimates are associations in a retrospective public research dataset.
They are not causal effects and do not support individual prognosis or treatment.

## Material findings

1. The advanced-stage proportional-hazards test failed (p=0.000426). A single
   constant hazard ratio therefore compresses a time-varying relationship and
   must not be presented as fully satisfying the primary model assumptions.
2. S3 produced a time-interaction estimate but emitted a Newton–Raphson
   nonconvergence warning. Its coefficients are not interpretable as validated
   sensitivity results.
3. S4 failed with a singular matrix. The prespecified nonlinear-age sensitivity
   is incomplete and must remain recorded as failed.
4. The Kaplan–Meier curves render, but the risk annotation overlaps the x-axis
   label. The figure fails release-layout QA even though its checksum is valid.
5. AJCC edition was missing for 137 included cases and varied from 3rd through
   7th among reported records, reinforcing the planned staging-edition limitation.

## Integrity review

- All five artifact sizes and SHA-256 checksums matched the run manifest.
- The independently recomputed manifest checksum matched
  `49aa35b…c7cb9`.
- Group counts sum to 1,037 participants and 139 events.
- All S1–S5 branches are present, including failed and non-interpretable results.
- The result contract retains warnings rather than converting them into success.

## Recommendation

Record **changes requested** or **on hold** for public release. Preserve this run
unchanged. Before a replacement run:

1. document a post-result technical amendment that is limited to the S4 spline
   parameterization and figure layout;
2. obtain targeted statistical review of the S3 time-varying-effect method;
3. increment the analysis algorithm version;
4. rerun from the same frozen cohort under a new content-addressed run ID; and
5. report both this original run and the amended run in the final provenance.

The primary result may be described internally as reproduced with a material PH
limitation, but no public scientific claim should be frozen yet.
