# Abstract Coverage Remediation

Recorded at: `2026-07-22T13:58:53-05:00`

## Finding

The first verified search execution (`9eec1656…c185`) contained 457 unique
records but only 123 abstracts. PubMed ESummary provides citation metadata, not
abstract text. The first screening queue (`32753def…ad01`) therefore had 334
title-only records and was not accepted as ready for title/abstract screening.
It remains immutable on external storage as a diagnostic attempt and has no
approved Git-tracked receipt.

## Correction

Retrieval revision `fca4644` adds batched PubMed EFetch XML capture, preserves
the raw responses, binds every abstract to its PMID, and retains the existing
copyright and external-storage restrictions. The locked scientific query and
eligibility criteria did not change.

Replacement execution `83d33fb2…4434` contains the same 457 unique citation
records and 57 duplicates with abstracts present for all 457 records. Its manifest
and all 12 stored objects were independently verified. Only the replacement
execution is authorized as input to the next screening queue.

No record was screened, included, excluded, or interpreted during remediation.
