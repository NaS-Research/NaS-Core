# Search Strategy Amendment 0.1.1

Recorded at: `2026-07-22T13:42:03-05:00`

Stage: pre-retrieval count feasibility; no bibliographic snapshot or screening
decisions existed when this amendment was made.

## Trigger

The authorized count-only preview returned:

- PubMed: 391 records
- Europe PMC: 79,501 records

Europe PMC searches both metadata and available full text, and its unfielded,
unquoted multiword syntax expanded the intended concepts far beyond the review
question. Two attempted full captures were stopped by transport errors; the
subsequent hardened attempt was manually stopped before storage after its runtime
and memory demonstrated that the corpus was not screenable. No search snapshot,
normalized record inventory, evidence row, or scientific conclusion was produced.

## Change

The Europe PMC query now applies `TITLE_ABS:` to every concept and quotes the
multiword phrases `"breast cancer"`, `"breast carcinoma"`, and
`"intrinsic subtype"`. The PubMed query, review questions, eligibility criteria,
date range, extraction fields, and stopping rule are unchanged.

## Rationale and boundary

This is a source-syntax correction based only on result-count feasibility, not
on article relevance, direction, authors, journals, or study findings. It does
not tune the review to support novelty and does not authorize molecular or outcome
data access. Strategy `0.1.1` remains locked under the existing bounded founder
authorization and must pass another count-only preview before full execution.
