# Founder Screening Workflow

This runbook applies locked screening protocol `1.0.0` to verified queue
`b02c2abf…f042`. It records evidence-selection decisions only. It does not
perform evidence synthesis, establish novelty, or authorize outcome analysis.

## Review unit

Work in batches of 10–20 records. The queue and copyrighted abstracts remain in
the external object store. Git receives only typed aggregate progress receipts;
decision-event ledgers remain immutable outside Git.

Display the next 20 pending records:

```bash
uv run nas-core literature screening-next \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt.yaml \
  --batch-size 20
```

After the first batch, add the latest receipt so completed records are skipped:

```bash
uv run nas-core literature screening-next \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt.yaml \
  --progress-receipt workflows/studies/breast_clinical_molecular_discordance/literature/screening-progress/batch-0001.yaml \
  --batch-size 20
```

## Decision batch

Create a temporary YAML file outside Git. Bind it to the queue and, after the
first batch, to the exact latest `progress_id`:

```yaml
schema_version: 1.0.0
queue_id: b02c2abfab2276f6042889bd8e5d0c65b5c01469dd39f2df2222a53e36b5f042
expected_previous_progress_id: null
reviewer_id: dalron-j-robertson
reviewer_name: Dalron J. Robertson
reviewer_role: founder_internal_reviewer
decisions:
  - screening_id: REPLACE_WITH_64_CHARACTER_ID_FROM_SCREENING_NEXT
    decision: include
  - screening_id: REPLACE_WITH_ANOTHER_SCREENING_ID
    decision: exclude
    exclusion_reason: outside_breast_cancer_scope
  - screening_id: REPLACE_WITH_ANOTHER_SCREENING_ID
    decision: unclear
```

Allowed decisions and exclusion reasons are defined in
[`SCREENING_PROTOCOL.md`](SCREENING_PROTOCOL.md). `pending` is not a submitted
decision. AI output cannot populate this file.

Validate without reading the queue or storing decisions:

```bash
uv run nas-core literature screening-record \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt.yaml \
  /path/to/temporary/decision-batch.yaml \
  --code-revision "$(git rev-parse HEAD)"
```

After review, execute once and write a new, never-overwritten aggregate receipt:

```bash
uv run nas-core literature screening-record \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt.yaml \
  /path/to/temporary/decision-batch.yaml \
  --code-revision "$(git rev-parse HEAD)" \
  --receipt-output workflows/studies/breast_clinical_molecular_discordance/literature/screening-progress/batch-0001.yaml \
  --execute
```

For later batches, pass both `--previous-progress-receipt` and a decision batch
whose `expected_previous_progress_id` matches it. Stale submissions fail closed.

## Corrections and unclear adjudication

Never edit or delete a prior event. A replacement decision must provide the
current event's `event_id` as `supersedes_event_id` and a nonempty
`change_reason`. Use `screening-next --include-unclear` with the latest progress
receipt to retrieve unresolved records.

## Verification gate

Each successful execution independently reloads the queue, manifest, cumulative
event ledger, and progress summary; checks hashes, sizes, event identities,
supersession chains, queue membership, and reconciled counts; and only then writes
the aggregate receipt. Screening is complete only when both `pending` and
`unclear` counts are zero.
