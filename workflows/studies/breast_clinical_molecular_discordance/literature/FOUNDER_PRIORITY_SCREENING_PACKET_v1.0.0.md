# Founder Priority Screening Packet

Packet version: `1.0.0`

Question version: `0.3.0`

Protocol: `REVISED_SCREENING_PROTOCOL.md` version `1.1.0`

Queue: `af08a334…8a2a3`

Status: **Awaiting founder decisions**

## Advisory recommendation

The title and abstract of each mandatory priority record plausibly satisfies at
least one locked inclusion criterion. The AI advisory recommendation is therefore
`include` for all 13 at title/abstract screening. This is intentionally sensitive:
inclusion advances a paper to full-text appraisal and is not an endorsement of its
methods, claims, quality, or clinical utility.

| PMID | Short label | Recommendation | Confidence | Screening rationale |
|---|---|---|---|---|
| 19204204 | Original PAM50/ROR predictor | Include | High | Foundational 50-gene centroid method and training assumptions |
| 28062443 | Single-subject PAM50 uncertainty | Include | High | Direct ambiguity, Not Assigned, permutation, and abstention method |
| 22196354 | PAM50 measurement-error uncertainty | Include | High | Direct repeated-measure error model and classification reproducibility |
| 25479802 | AIMS | Include | High | Absolute cohort-independent classifier with robustness testing |
| 33255759 | MiniABS | Include | High | Platform-agnostic absolute single-sample alternative with external testing |
| 35974007 | RNA-seq SSP | Include | High | Single-sample RNA-seq subtype predictor with external test comparison |
| 37008073 | MPAM50 | Include | High | Reference-free single-sample PAM50 alternative across 19 datasets |
| 32826944 | AWCA and RNA-seq classifiers | Include | High | Reference sensitivity, fixed single-sample adaptation, and portability |
| 37857634 | SCAN-B perturbation/stability | Include | High | Nearest/runner-up structure and gene-set perturbation in 6,233 tumors |
| 41064593 | BreastSubtypeR | Include | High | Reproducible multi-classifier implementation, mapping, and assumptions |
| 41390542 | PCAPAM50 | Include | High | Executable centering implementation and ER-imbalance robustness |
| 25788628 | Test-set bias | Include | High | Direct evidence that cross-sample normalization changes patient predictions |
| 25849221 | Subgroup-specific centering | Include | High | Direct centering method for clinically skewed PAM50 cohorts |

## Founder action

Dalron J. Robertson must either:

- confirm `include` for all 13;
- identify any PMID that should be `exclude` and select one protocol reason; or
- identify any PMID that should be `unclear`.

No immutable decisions have been recorded from this packet.

## Boundary

These recommendations use bibliographic metadata and abstracts only. They do not
replace full-text eligibility review, risk-of-bias appraisal, source verification,
or founder scientific judgment.
