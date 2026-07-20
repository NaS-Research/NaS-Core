# NAS-BRCA-001

This canonical study workspace contains the versioned definitions, protocol,
and future deterministic implementation for the first NaS Cortex pilot: an
open-data reproduction of the association between pathologic stage and overall
survival in TCGA-BRCA.

Large or generated artifacts use the external object namespace
`studies/NAS-BRCA-001`; they do not belong in Git.

The protocol is intentionally marked `pending_review`. Do not download the study
dataset or inspect final outcome results until an independent scientific reviewer
approves the plan and its status is changed to `preregistered`.

Validate the plan from the repository root:

```bash
uv run nas-core study validate workflows/studies/tcga_brca_stage_survival
uv run nas-core plan validate workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml
```

Regenerate its machine-readable schema after changing the typed protocol model:

```bash
uv run nas-core plan schema workflows/analysis_plan.schema.json
```
