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
implemented. Live execution requires a valid API contact email; no live search has
yet been captured. Raw responses and normalized abstracts remain in external object
storage, while Git receives only an aggregate receipt after independent verification.
