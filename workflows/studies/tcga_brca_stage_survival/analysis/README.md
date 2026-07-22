# Analysis

Generated cohorts, tables, figures, logs, and model artifacts belong in external
storage. Git contains the deterministic implementation, schemas, synthetic
tests, and metadata receipts only.

## Cohort build

The cohort engine verifies the snapshot manifest and page checksums before
reading records. It then applies this mutually exclusive exclusion order:

1. invalid case index date;
2. no primary-disease diagnosis;
3. non-normalizable pathologic stage;
4. missing diagnosis identifier;
5. missing, invalid, or under-18 age;
6. invalid vital status; and
7. missing, zero, negative, or invalid survival time.

For included cases it selects one primary diagnosis, derives parent stage, age,
vital status, duration, event, and time source, and writes:

- `cohort.csv` — one analysis-ready row per included case;
- `exclusions.csv` — one case ID and one reason per excluded case;
- `qa-summary.json` — every requested field's missingness, cohort flow, stage
  normalization, and included-versus-excluded age/vital summaries; and
- `manifest.json` — source snapshot, protocol, code revision, artifact hashes,
  counts, and build identity.

The QA summary intentionally contains no stage-by-event table, hazard ratio,
survival curve, or fitted model.

The current immutable build is recorded in
[`cohort_build_receipt.yaml`](cohort_build_receipt.yaml). Its AI-assisted QA
review and approved founder gate are stored in the study `reviews/` directory.

Dry run:

```bash
uv run nas-core cohort build \
  workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml \
  workflows/studies/tcga_brca_stage_survival/ingestion/snapshot_receipt.yaml \
  --code-revision <GIT_SHA>
```

Add `--execute` only after the cohort implementation commit has been pushed.

## Survival analysis

The survival engine fails closed unless the cohort receipt and every required
review are approved and all cohort artifacts reverify against their checksums.
It implements the locked primary model, Kaplan–Meier estimates, risk table,
log-rank test, categorical-stage analysis, proportional-hazards tests, and all
five prespecified sensitivity analyses. Secondary and sensitivity coefficient
families receive Benjamini–Hochberg adjusted p-values.

Each immutable run writes:

- `analysis-summary.json` — typed results, diagnostics, abstentions, warnings,
  reproduction classification, and Cortex qualification decision;
- `baseline-table.csv` — early/advanced participant, event, age, and follow-up summaries;
- `model-coefficients.csv` — estimates, hazard ratios, intervals, and p-values;
- `risk-table.csv` and `kaplan-meier.png`; and
- `manifest.json` — cohort identity, protocol, code, dependencies, parameters,
  seed, artifact hashes, and content-addressed run identity.

Dry run only:

```bash
uv run nas-core analysis survival \
  workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml \
  workflows/studies/tcga_brca_stage_survival/analysis/cohort_build_receipt.yaml \
  --code-revision <GIT_SHA>
```

The real run requires `--execute` and must use the pushed implementation commit.
Do not execute during engine development or synthetic validation.
