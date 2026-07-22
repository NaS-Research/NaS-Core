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
implemented. Locked strategy `0.1.1` produced immutable execution `9eec1656…c185`:
391 PubMed records and 123 Europe PMC records became 457 unique records after 57
cross-source duplicates. All eight objects, hashes, sizes, and count invariants were
independently verified. Raw responses and normalized abstracts remain in external
object storage; [`search_receipt.yaml`](search_receipt.yaml) contains aggregates only.

Screening has not started, the evidence matrix is still empty, and no novelty or
scientific conclusion has been drawn.
