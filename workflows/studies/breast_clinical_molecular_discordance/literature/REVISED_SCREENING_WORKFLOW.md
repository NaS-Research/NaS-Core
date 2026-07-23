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

## Boundaries

This phase selects methodological evidence. It does not establish novelty, produce
a scientific result, authorize molecular or outcome data, or permit clinical use.
