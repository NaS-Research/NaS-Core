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

The append-only founder-review engine is implemented. It produces deterministic
pending batches, rejects stale or duplicate submissions, locks exclusions to the
protocol taxonomy, supports explicit supersession for correction and unclear-record
adjudication, verifies the full cumulative event chain, and writes only aggregate
progress receipts to Git. Screening remains unstarted. Follow
[`SCREENING_WORKFLOW.md`](SCREENING_WORKFLOW.md) for each small review batch.

Founder batch 4 produced verified progress state `dd27a686…ac21`: 27 included,
7 excluded, 423 pending, zero unclear, and zero AI decisions. The latest aggregate
receipt is [`screening-progress/batch-0004.yaml`](screening-progress/batch-0004.yaml).
The locked core-priority tier is fully reviewed. These 27 inclusions are provisional
until full-text eligibility and quality appraisal; they are not yet the final
evidence set.
The active workflow presents deterministic core-priority batches for explicit
founder decisions.

Full-text appraisal protocol `1.0.1`, a typed validation contract, and a founder
template are implemented. Seven evidence-located domains govern eligibility and the
`anchor`, `supporting`, `context_only`, or `excluded` role. High-risk domains cannot
be averaged away, and only studies with low-risk analysis and validation can become
anchor evidence. AI assistance must be disclosed and every locked record requires
explicit founder authorization.

The verified access inventory derives directly from founder progress state
`dd27a686…ac21` and reconciles all 27 provisional inclusions. Sixteen have PMC
repository identifiers and 11 require separate lawful-access checks. A PMCID is
treated only as a repository candidate, not proof of reuse rights. The first
candidate (`PMC10587090`) was checked against official Europe PMC XML and declares
CC BY 4.0 and has been durably retrieved and appraised.

Immutable full-text retrieval `1.0.0` is implemented for one current founder-
included record at a time through the official Europe PMC endpoint. It verifies
PMCID, PMID, DOI, exact title, and an allowlisted item-level CC BY 2.0, 2.5, 3.0,
or 4.0 declaration;
stores raw XML and its manifest outside Git; independently reloads and revalidates
both artifacts; and emits only a concise receipt to Git. Missing, ambiguous, or
unapproved licenses fail closed. Real retrieval awaits the pushed engine revision.

Identity normalization permits only XML whitespace normalization and one terminal
period difference in titles; PMCID, PMID, and DOI must match exactly. This bounded
rule addresses punctuation differences between bibliographic and repository records
without permitting fuzzy article matching.

The first durable retrieval and appraisal are complete. `PMC10587090` was fetched by pushed engine
revision `42d9752`, stored as 137,087 bytes of official Europe PMC XML outside Git,
and independently verified against SHA-256 `2ca3db6f…0e2a`, article identity, and
CC BY 4.0 metadata. The aggregate receipt is
[`full-text/PMC10587090.yaml`](full-text/PMC10587090.yaml). Its section-located
appraisal is eligible with a `supporting` role: it is useful evidence about PAM50
stability, but is not independent anchor evidence. This is a methodological evidence
designation, not a scientific conclusion. The reconciled
[`appraisal_progress.yaml`](appraisal_progress.yaml) records 3 of 27 appraisals
complete, 3 verified full texts retrieved, 2 access-restricted records, and fails
closed on identity, checksum, license, or provenance mismatches. `PMC3275466` is
eligible as `context_only` evidence because
its sample-level uncertainty is simulated from a sparse, laboratory-specific error
model rather than validated with repeated measurements of the independent tumors.
This role informs problem definition but cannot support a clinical-reliability claim.
`PMC1468408` is also context-only: it is foundational cross-platform evidence, but
its validation set contributed to SSP centroid construction and its legacy DWD-based
microarray workflow does not directly validate modern PAM50. `PMC10052604` and
`PMC12789466` are recorded as restricted under CC BY-NC and CC BY-NC-ND respectively;
their full texts were not durably stored.

AI advisory policy `1.0.2` and its prompt remain available but live provider use is
disabled following the founder's zero-API Phase 0 decision. The
provider-neutral gateway records structured recommendations, confidence, matched
criteria, sentence-level evidence references, model/prompt/input provenance, and
zero final decisions. No API credential is required for the active workflow.

Deterministic prioritization version `1.0.0` ranked all 452 pending records locally
with no model call, network call, screening decision, or scientific conclusion. The
locked thresholds produced 29 core-priority, 158 supporting-priority, and 265
context-priority records. Priority is not eligibility or methodological quality;
the founder must screen records against the protocol, and quality appraisal follows
full-text eligibility. See
[`DETERMINISTIC_PRIORITIZATION.md`](DETERMINISTIC_PRIORITIZATION.md).
