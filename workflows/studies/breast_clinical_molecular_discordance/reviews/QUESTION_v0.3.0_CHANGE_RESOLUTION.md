# NAS-BRCA-002 Question v0.3.0 Change Resolution

Resolution version: `1.0.0`

Source decision:
[`FOUNDER_PHASE_ZERO_GATE_DECISION_v0.2.0.yaml`](FOUNDER_PHASE_ZERO_GATE_DECISION_v0.2.0.yaml)

Active revision:
[`../question/research_question.yaml`](../question/research_question.yaml)

Historical question:
[`../question/versions/research_question_v0.2.0.yaml`](../question/versions/research_question_v0.2.0.yaml)

## Outcome

Question `0.3.0` is drafted and remains `proposed` and `not_ready`. This revision
does not approve the question, establish novelty, authorize preregistration, or
permit molecular or outcome data access.

The revision changes the primary object of study. Version `0.2.0` broadly asked
which PAM50 classifications remain stable across implementations. Version `0.3.0`
asks whether a frozen, patient-independent procedure can decide when a research
PAM50 label may enter downstream analysis and when the system must warn, fail, or
abstain.

## Required-change trace

| Phase 0 required change | v0.3.0 resolution | State |
| --- | --- | --- |
| Center the question on single-sample reliability, calibration, and abstention | The scientific question now requires one-sample operation and a reliability result contract; calibration is limited to declared analytical targets because biological truth is unavailable | Resolved in question |
| Define the minimum implementation set without outcome-guided selection | The question requires a frozen fixed-centroid method and prohibits cohort or outcome dependence; the exact implementation inventory remains the next governed specification | Pending specification |
| Define margins, stability, uncertainty, and abstention before data access | Required outputs and estimands are named; exact formulas and thresholds remain intentionally unset until the specification and evidence review | Pending specification |
| Complete the revised evidence review and two-pass citation-chain stopping rule | The evidence needs are narrowed to single-sample operation, margins, repeatability, calibration targets, abstention, and frozen external validation | Pending execution |
| Verify TCGA and GSE96058 receptor fields and PAM50 gene coverage | Both sources and their unresolved field/gene checks are explicit in the question | Pending metadata-only verification |
| Complete founder scientific, molecular, and statistical review | The founder review is reset to `pending` for v0.3.0; the v0.2.0 decision is not carried forward as approval | Pending founder review |

## Locked boundaries

- No test-cohort-dependent centering or classification may be represented as
  patient-independent.
- Reliability means repeatability and rule satisfaction under declared technical
  conditions; it is not the probability that a subtype is biologically correct.
- The system must preserve missing-gene, mapping, transformation, and numerical
  failures rather than force a subtype.
- Thresholds may not be chosen using molecular enrichment, survival, treatment,
  or validation outcomes.
- External validation must run the frozen method unchanged and retain transport
  failure and abstention.
- No output is a clinical assay, diagnosis, prognosis, treatment recommendation,
  or evidence of clinical utility.

## Next gate

The next implementation must create the versioned minimum-method and output
specification. Question `0.3.0` returns to founder review only after that
specification, the revised evidence stopping rule, and metadata-only source checks
are complete.
