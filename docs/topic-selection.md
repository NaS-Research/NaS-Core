# Oncology Topic Selection

This process prevents NaS from collecting interesting papers or datasets
without a decision-led research purpose.

## Step 1: Write candidate intakes

Copy
[`workflows/templates/research_question_intake.yaml`](../workflows/templates/research_question_intake.yaml)
for each serious candidate. Give it the next durable question ID and replace
every instructional value.

Each intake must define:

- intended user and decision;
- current workflow and unmet need;
- population, exposure or intervention, comparator, outcomes, time horizon,
  and estimand;
- precision-medicine rationale;
- evidence and data modalities required;
- available and missing sources;
- statistical, causal, machine-learning, or mechanistic analysis family;
- internal, external, biological or clinical, and deployment validation;
- proposed system output;
- scientific, decision, and product success criteria.

## Step 2: Score each candidate

Score each dimension from 0 to 5 using evidence, not enthusiasm.

| Dimension | 0 | 3 | 5 |
| --- | --- | --- | --- |
| Decision impact | No identifiable action | Could influence research | Clear high-value decision |
| Unmet need | Existing workflow sufficient | Material friction or uncertainty | Serious unresolved need |
| Scientific testability | Not falsifiable | Testable with assumptions | Precise falsifiable question |
| Data feasibility | No credible data path | Partial or licensable path | Fit-for-purpose data available |
| Validation feasibility | No independent test | Plausible future validation | Independent validation available |
| Differentiation | Commodity analysis | Some distinct value | Defensible NaS advantage |
| Translation path | Paper only | Possible workflow | Clear deployable system |
| Governance feasibility | Prohibited or unclear | Review required | Permitted and operationally feasible |

The maximum score is 40. Scores do not automatically select a topic; they make
tradeoffs reviewable.

## Step 3: Apply hard gates

A candidate cannot be selected when:

- there is no identifiable user or decision;
- the primary outcome cannot be measured credibly;
- the required data have no lawful access path;
- the design cannot distinguish the intended claim from major confounding;
- there is no plausible independent validation path;
- success would still not produce an actionable research or workflow output.

## Step 4: Review and select

At least one scientific/product reviewer records an approval or requested
changes. Only an approved intake may change to `selected`, and only a selected
intake may change `literature_status` to `ready`.

Validate an intake with:

```bash
uv run nas-core question validate path/to/research_question.yaml
```

## Step 5: Begin the formal literature review

Once selected, copy the literature-review protocol template into the question's
workflow directory. Record searches before screening results so the review can
be reproduced and updated.
