# Technical Calibration Readiness 1.0.0

Study: `NAS-BRCA-002`  
Question: `NAS-RQ-BRCA002`, version `0.3.0`  
Prepared: 2026-07-28  
Status: route-neutral planning complete; no source selected

## Outcome

NaS now has a machine-validated acquisition contract for the technical evidence
needed to calibrate a fixed patient-level reliability and abstention rule. The
contract is checksum-bound to the method-dependency audit and the verified,
non-executable PAM50 centroid candidate.

No existing source currently passes all hard requirements.

| Source | Current role | Why it cannot calibrate now |
|---|---|---|
| GSE96058, 136 technical pairs | External validation only | Calibrating on it would adapt the rule to the population meant to test the unchanged method. |
| Hurson et al., 144 same-RNA pairs | Permission inquiry candidate | Participant-level molecular replicate values and stable pair identifiers are not publicly available; the platform is NanoString. |
| Independent RNA-seq replicate resource | Due-diligence target | No exact source has yet passed lineage, access, panel, and replicate-design checks. |
| Future NaS replicate experiment | Prospective fallback | It does not yet exist and requires a protocol, power analysis, budget, governance, and laboratory execution. |

## Hard acceptance boundary

A source must be independent of classifier training and external validation;
provide lawful participant-level paired molecular values with stable pair
identifiers; represent true technical repeats rather than biological change;
cover the complete governed classifier panel; and expose enough assay and
preprocessing metadata to freeze an executable bridge.

The minimum number of replicate pairs will not be selected by convenience.
Precision targets and a prospective power analysis must justify it. Outcomes and
external-validation performance are prohibited from threshold calibration.

## What this implementation authorizes

It authorizes validation of the acquisition plan and preparation of source
discovery, an unsent author inquiry, and a prospective experiment design.

It does **not** authorize patient-level or molecular access, outcome access,
threshold selection, method execution, clinical use, publication, contacting an
external party, spending funds, or selecting a founder method route.

## Route decision update

The founder selected Route C exactly on 2026-07-28. The decision and activation
are recorded in `FOUNDER_METHOD_ROUTE_DECISION_v1.0.0.yaml` and
`method_route_activation_v1.0.0.yaml`. Independent-calibration acquisition is
active, but no source, data access, threshold, method lock, or execution is
authorized.
