# Question 0.3.0 Founder Screening Workflow

This runbook governs the replacement queue for the single-sample reliability and
abstention question. It supersedes the interim 96-record queue before screening
began; no records or decisions were deleted.

## Bound artifacts

- Search execution: `a2500aba…f1ea9f`
- Search receipt: `search_receipt_v0.3.1.yaml`
- Screening queue: `af08a334…8a2a3`
- Queue receipt: `screening_queue_receipt_v0.3.1.yaml`
- Prior-inventory reconciliation: `075aa083…397891`
- Reconciliation receipt: `inventory_reconciliation_v0.3.1.yaml`

The queue contains 100 unique records with abstracts and all 13 mandatory direct
priority papers. Every record is pending. Reconciliation against the prior
457-record inventory found 55 exact prior matches, 5 author-year-only candidates,
and 40 new candidates. Prior decisions were not transferred.

## Screening order

1. Adjudicate all 13 records in `revised_priority_evidence.yaml`.
2. Confirm or reject the five author-year-only prior-inventory links.
3. Screen the remaining records using protocol `0.2.4`.
4. Appraise or record lawful-access restriction for every inclusion.
5. Begin backward and forward citation chaining only after primary screening.

Display the next records:

```bash
uv run nas-core literature screening-next \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt_v0.3.1.yaml \
  --batch-size 20
```

Final include, exclude, or unclear decisions require Dalron J. Robertson. Use the
append-only batch format in `SCREENING_WORKFLOW.md`, substituting the revised queue
receipt and queue ID. AI may prioritize and advise but cannot submit decisions.

The title/abstract rules are locked in
[`REVISED_SCREENING_PROTOCOL.md`](REVISED_SCREENING_PROTOCOL.md). The first
advisory packet is
[`FOUNDER_PRIORITY_SCREENING_PACKET_v1.0.0.md`](FOUNDER_PRIORITY_SCREENING_PACKET_v1.0.0.md).
It recommends including all 13 direct-priority records for full-text review. The
founder confirmed the packet, and verified progress receipt
[`revised-screening-progress/batch-0001.yaml`](revised-screening-progress/batch-0001.yaml)
records the append-only decisions.

The remaining 87 recommendations are in
[`FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md`](FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md).
The founder confirmed that exact packet on 2026-07-25. The confirmation audit is
[`FOUNDER_REMAINING_SCREENING_CONFIRMATION_v1.0.0.md`](FOUNDER_REMAINING_SCREENING_CONFIRMATION_v1.0.0.md),
and verified progress receipt
[`revised-screening-progress/batch-0002.yaml`](revised-screening-progress/batch-0002.yaml)
records 30 inclusions, 70 exclusions, zero pending, zero unclear, and zero AI
decisions. The reviewed packet remains byte-for-byte unchanged so its recorded
SHA-256 remains reproducible.

For a future packet, record a temporary confirmation YAML outside Git whose
`packet_sha256` is the SHA-256 of the reviewed Markdown and whose
`confirmation_statement` is exactly `I confirm the screening packet as written.`
The confirmation must also bind the queue ID, current progress ID, founder identity,
confirmation time, and rejection or acceptance of every candidate identity link.

Generate the typed decision batch without storing decisions:

```bash
uv run nas-core literature screening-confirm \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt_v0.3.1.yaml \
  workflows/studies/breast_clinical_molecular_discordance/literature/revised-screening-progress/batch-0001.yaml \
  workflows/studies/breast_clinical_molecular_discordance/literature/FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md \
  /path/to/temporary/founder-confirmation.yaml \
  /path/to/temporary/decision-batch.yaml
```

The command fails closed if the packet checksum, queue, progress state, record
ordering, displayed identifiers, coverage, or founder authority differs. Use the
existing `screening-record` dry run and execute steps only after this command
succeeds.

Before any future founder confirmation, validate packet coverage and immutable
record identities without creating a decision batch:

```bash
uv run nas-core literature screening-confirm-preview \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt_v0.3.1.yaml \
  workflows/studies/breast_clinical_molecular_discordance/literature/revised-screening-progress/batch-0001.yaml \
  workflows/studies/breast_clinical_molecular_discordance/literature/FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md
```

The derived access inventory is
[`revised-full-text/inventory/access_inventory_v0.3.2.yaml`](revised-full-text/inventory/access_inventory_v0.3.2.yaml).
It contains all 30 founder inclusions: 26 have repository identifiers and four
require separate lawful-access checks. The current reconciled ledger is
[`revised_appraisal_progress_v0.3.4.yaml`](revised_appraisal_progress_v0.3.4.yaml):
12 appraisals are complete, 15 accessible papers are ready for appraisal, two
records are access-restricted, and one open-access IEEE paper awaits retrieval
after scheduled publisher maintenance.

## Boundaries

This phase selects methodological evidence. It does not establish novelty, produce
a scientific result, authorize molecular or outcome data, or permit clinical use.
