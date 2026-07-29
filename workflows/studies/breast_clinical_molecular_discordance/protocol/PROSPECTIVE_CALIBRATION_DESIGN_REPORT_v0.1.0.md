# Prospective Calibration Design Report 0.1.0

Study: `NAS-BRCA-002`  
Phase: `phase_1_method_calibration`  
Route: `ROUTE-C`  
Status: founder review required; planning only  
Design SHA-256: `434e6177f2e31e861c213ac58f7eb48be25cc9aeb7640b7ad1f8d26fdda555b1`

## Outcome

NaS now has a machine-validated, no-contact prospective experiment design for
the technical evidence required by Route C. It is bound to the exact Route C
activation, acquisition plan, and founder contact revocation.

The design does not select specimens, a laboratory, an assay vendor, a pair
count, a budget, or a calibration source. It authorizes no contact, spending,
procurement, specimen acquisition, data access, threshold selection, execution,
clinical use, or publication.

## Three-arm architecture

| Arm | Role | Repeated process | Final threshold use |
|---|---|---|---|
| Feasibility pilot | Estimate variance, failures, attrition, and batch structure | Independent libraries and sequencing from the same homogenized RNA | Permanently excluded |
| Primary calibration | Calibrate post-extraction technical reliability | Independent libraries and sequencing from the same homogenized RNA | Yes, after a separate design lock |
| Extraction sensitivity | Estimate additional extraction variation | Independent extraction, libraries, and sequencing from matched homogenized material | Separate sensitivity only |

This architecture prevents pilot optimization from being presented as final
calibration and prevents extraction error from being silently pooled with
post-extraction analytical error.

## Primary and secondary estimands

The proposed single primary estimand is technical PAM50 subtype-label retention
across valid same-RNA replicate pairs. Secondary estimands preserve abstention
state, subtype-score and runner-up-margin error, all 50 gene-level paired errors,
and every assay or classifier failure.

Clinical outcomes are prohibited from every technical-calibration estimand.
TCGA-BRCA outcomes cannot select thresholds, and GSE96058 remains reserved for
unchanged external validation.

## Sample-size boundary

No pair count is locked. The existing 141-pair calculation remains a hypothetical
software fixture based on unapproved 0.90 expected retention and ±0.05 expected
Wilson precision. A real count must incorporate founder-approved precision,
pilot variance, attrition, clustering, coverage across receptor, RNA-quality and
score-margin strata, continuous endpoints, and multiplicity.

## Material decisions still required

1. RNA-seq platform and locked laboratory workflow.
2. Post-extraction-only primary claim versus an additional extraction arm.
3. Scientifically acceptable retention and precision targets.
4. Required receptor, RNA-quality, and score-margin coverage.
5. Pilot size, attrition reserve, clustering, and multiplicity.
6. Whether a future prospective laboratory experiment is financially and
   operationally feasible for NaS.

Approval of this design would authorize only continued planning. Laboratory
scope, pricing, procurement, specimens, data access, and execution would each
remain behind later review gates.
