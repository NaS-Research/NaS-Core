# Calibration Scenario Report 1.0.0

Study: `NAS-BRCA-002`  
Phase: `phase_1_method_calibration`  
Status: hypothetical internal planning only  
Planning activation SHA-256:
`f92d0558811d8ecb066d8dae96386c10582588093da737df3460c879aa393dbc`

## Purpose

Three deterministic scenarios quantify how binary label-retention precision,
continuous paired-error precision, multiplicity, clustering, and attrition can
change the operational scale of a future calibration experiment. They are
scenario analyses, not power calculations based on NaS data and not approved
sample sizes.

## Results

| Scenario | Binary effective pairs | Continuous effective pairs | Governing objective | Attempted pairs | Measurements |
|---|---:|---:|---|---:|---:|
| Lean | 73 | 49 | Label retention | 82 | 164 |
| Balanced | 141 | 166 | Continuous mean precision | 185 | 370 |
| High precision | 669 | 664 | Label retention | 945 | 1,890 |

The attempted-pair totals incorporate each scenario's hypothetical attrition and
design effect. Each pair requires two independently processed measurements.
Pilot specimens, extraction-sensitivity specimens, controls, reruns, and
reference materials are not included in these totals.

## Interpretation

The prior 141-pair figure addressed only a hypothetical binary label-retention
interval. It is not sufficient to define a complete experiment. In the balanced
scenario, multiplicity-adjusted continuous error precision governs instead,
raising the effective requirement to 166 and the attrition-inflated operational
requirement to 185 attempted pairs.

The lean scenario may be more operationally approachable but cannot be assumed
adequate for subtype, margin, batch, continuous-error, or multiplicity
objectives. The high-precision scenario demonstrates how quickly stringent
confidence, clustering, and attrition assumptions can make the experiment
impractical.

## NaS review position

Use the balanced scenario only as the internal feasibility reference. It is the
most informative middle case and exposes the fact that continuous error—not
binary agreement alone—may govern the design. Do not approve 185 pairs as the
final sample size.

Before any sample-size recommendation, NaS should:

1. freeze the assay and primary repeat architecture;
2. define which continuous objectives are confirmatory;
3. design an excluded feasibility pilot;
4. obtain pilot estimates of variance, attrition, batch structure, and missingness;
5. specify subtype and score-margin coverage;
6. rerun the prospective calculation with approved inputs; and
7. obtain founder, molecular, statistical, governance, operational, and budget
   review.

No scenario authorizes contact, laboratory quotations, spending, procurement,
specimens, data access, threshold selection, or execution.
