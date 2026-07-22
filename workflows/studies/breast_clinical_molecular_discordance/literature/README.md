# Literature

Required artifacts:

- `literature/protocol.md`
- `literature/search_strategy.yaml`

Completion gate: Search protocol is locked before evidence retrieval.

Current state: the founder authorized the bounded Phase 0 audit on 2026-07-22,
and the search strategy is locked for execution. The empty evidence matrix defines
the required extraction structure but contains no screening decisions or scientific
evidence yet. No novelty conclusion may be drawn from an empty or partially
screened matrix.

The governed PubMed/Europe PMC retrieval runner and both source registrations are
implemented. Locked strategy `0.1.1` produced replacement execution `83d33fb2…4434`:
391 PubMed records and 123 Europe PMC records became 457 unique records after 57
cross-source duplicates. All 12 objects, hashes, sizes, count invariants, and
abstract coverage for all 457 records were
independently verified. Raw responses and normalized abstracts remain in external
object storage; [`search_receipt.yaml`](search_receipt.yaml) contains aggregates only.

The earlier execution and queue were retained but not approved for screening after
the queue QA exposed 334 missing PubMed abstracts. See
[`ABSTRACT_COVERAGE_REMEDIATION.md`](ABSTRACT_COVERAGE_REMEDIATION.md).

Screening has not started, the evidence matrix is still empty, and no novelty or
scientific conclusion has been drawn.

The screening-queue engine is implemented with typed pending/include/exclude/unclear
states and mandatory human provenance for every decision. Verified queue
`b02c2abf…f042` contains all 457 titles and abstracts as pending, with zero human
and zero AI decisions. It remains outside Git; the aggregate
[`screening_queue_receipt.yaml`](screening_queue_receipt.yaml) records provenance.
