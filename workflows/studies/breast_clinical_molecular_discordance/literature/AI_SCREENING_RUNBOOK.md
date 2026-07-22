# AI Advisory Screening Runbook

Policy: `AI_SCREENING_POLICY.yaml` version `1.0.1`

AI screening is advisory. It cannot create, change, or supersede a founder
decision. All requests, recommendation records, and model manifests remain in
the external object store; Git receives aggregate receipts only.

## Credential setup

Create or edit the repository-local `.env` file and set:

```text
OPENAI_API_KEY=your-local-key
```

`.env` is ignored by Git. Never place the key in a command, YAML policy, prompt,
receipt, log, or research artifact.

## Provider-retention authorization

The Responses request sets `store: false`, and OpenAI states that API inputs and
outputs are not used for model training by default. Standard abuse-monitoring logs
may nevertheless retain customer content for up to 30 days unless the API
organization has Zero Data Retention. See OpenAI's
[API data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint)
and [business-data commitments](https://openai.com/business-data/).

Before the first live run, record one prospective choice in a new policy version:

- acknowledge standard abuse-monitoring retention for this exact public/open
  abstract queue; or
- require and verify Zero Data Retention for the API organization.

The founder selected the standard abuse-monitoring path for this exact public/open
title-and-abstract queue on 2026-07-22. Policy `1.0.1` records that authorization
and keeps provider application storage disabled. The authorization does not cover
licensed full text, controlled data, PHI, patient-level data, autonomous decisions,
or use outside this queue. Live execution still requires a local API credential.

## Network-free preview

```bash
uv run nas-core literature screening-ai \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt.yaml \
  workflows/studies/breast_clinical_molecular_discordance/literature/AI_SCREENING_POLICY.yaml \
  --progress-receipt workflows/studies/breast_clinical_molecular_discordance/literature/screening-progress/batch-0001.yaml \
  --code-revision "$(git rev-parse HEAD)"
```

This validates configuration without reading abstracts or contacting a provider.

## Calibration execution

After provider-retention authorization, the first live run should omit
`--progress-receipt`. That intentionally presents
the first ten queue records, including five records already labeled by the founder,
so recommendations can be compared without exposing the labels to the model.

```bash
uv run nas-core literature screening-ai \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt.yaml \
  workflows/studies/breast_clinical_molecular_discordance/literature/AI_SCREENING_POLICY.yaml \
  --code-revision "$(git rev-parse HEAD)" \
  --receipt-output workflows/studies/breast_clinical_molecular_discordance/literature/ai-screening/calibration-0001.yaml \
  --execute
```

The receipt must report zero final decisions and `calibration_status: required`.
No recommendation may be used for routing until the evaluation workflow is built
and its acceptance rules are locked.

## Pending-record execution

After calibration authorization, pass the latest founder progress receipt so the
model receives pending records only. Each provider call handles at most ten records.
Every run writes a new receipt; never overwrite or renumber one.

## Required review display

The future review view must show title, concise advisory rationale, recommendation,
confidence, matched criteria, evidence sentence IDs, and any proposed exclusion
reason. It must visually distinguish AI advice from the founder decision and
require an explicit founder action before adding a human event.
