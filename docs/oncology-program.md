# NaS Oncology Research Program

NaS is a precision-medicine company built like a research institution. The
oncology program exists to turn fit-for-purpose clinical, molecular, treatment,
and outcomes data into validated systems that improve research, therapeutic
development, patient stratification, and eventually clinical decisions and
patient outcomes.

The authoritative machine-readable charter is
[`workflows/oncology/program_charter.yaml`](../workflows/oncology/program_charter.yaml).

## Two tracks

### Platform qualification

Qualification studies prove that Cortex can reproduce an established result
with complete protocol, data, code, result, evidence, and review lineage. They
do not establish a product claim.

`NAS-BRCA-001` is the first qualification study. It tests the known association
between pathologic stage and overall survival in public TCGA-BRCA data.

### Decision-led research

Discovery, validation, and translation studies must begin with an intended user
and decision. They investigate questions that could become a biomarker,
stratification model, evidence product, trial tool, or workflow system.

No decision-led study begins with “find patterns in this dataset.” It begins
with:

1. Who must make a decision?
2. What decision is currently difficult?
3. Which population and context are involved?
4. Which evidence would change the decision?
5. Which meaningful outcome could improve?
6. What data and validation would be required?

## Current boundary

Breast oncology is the initial learning domain because the qualification study
already establishes an end-to-end breast-cancer workflow. The first product
wedge remains unselected. Candidate decision domains include biomarker
stratification, treatment response and resistance, trial intelligence, and
pharmaceutical real-world evidence.

TCGA is public research data, not longitudinal real-world care data. It can
support platform qualification and selected discovery questions, but future
RWD programs will require governed EHR, registry, claims, trial, biobank, or
licensed data partnerships.

## Required artifact sequence

Every decision-led project follows:

```text
program charter
  -> research-question intake
  -> selection review
  -> literature-review protocol
  -> analysis plan
  -> dataset snapshot
  -> analysis run
  -> evidence claims
  -> independent validation
  -> research release
  -> product or workflow evaluation
```

Articles, models, and datasets are inputs to this sequence. None of them define
the program by themselves.
