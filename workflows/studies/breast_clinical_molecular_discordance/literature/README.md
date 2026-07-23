# Literature

## Question 0.3.0 revised evidence review

The current reliability-focused review is governed by:

- [`REVISED_EVIDENCE_REVIEW_PROTOCOL.md`](REVISED_EVIDENCE_REVIEW_PROTOCOL.md)
- [`search_strategy_v0.3.0.yaml`](search_strategy_v0.3.0.yaml)
- [`revised_priority_evidence.yaml`](revised_priority_evidence.yaml)
- [`revised_evidence_review_progress.yaml`](revised_evidence_review_progress.yaml)

The revised search remains a nonexecuting draft. Its 13-record direct priority set
contains candidate evidence, not automatic inclusion decisions or scientific
conclusions. The progress ledger cannot claim completion until the locked search,
deduplication, founder screening, appraisal accounting, and two consecutive
zero-yield backward-plus-forward citation passes all reconcile.

Required artifacts:

- `literature/protocol.md`
- `literature/search_strategy.yaml`

Completion gate: Search protocol is locked before evidence retrieval.

Current state: the founder authorized the bounded Phase 0 audit on 2026-07-22,
and the search strategy is locked for execution. The evidence matrix now contains
the eight completed appraisals. It supports an early `change` decision because a
direct prior study substantially overlaps the broad thesis; it does not support an
affirmative novelty claim because the locked stopping rule was not satisfied.

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

Core-priority screening and eight full-text appraisals are complete. The broader
queue remains partially screened, so the evidence review is explicitly marked
`terminated_by_no_go`, not saturated. No novelty claim or outcome-bearing
scientific analysis has been authorized.

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
[`appraisal_progress.yaml`](appraisal_progress.yaml) records 8 of 27 appraisals
complete, 8 verified full texts retrieved, 4 access-restricted records, and fails
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
`PMC4166472` is supporting evidence: it provides large-scale, multi-study external
validation and direct PAM50 comparisons, but evaluates an adaptable IntClust research
classifier across heterogeneous retrospective cohorts rather than a fixed modern
PAM50 assay or patient-decision workflow.
`PMC7442834` is direct supporting evidence that PAM50 RNA-seq calls depend on
reference-cohort construction and that preprocessing-matched AWCA references can
improve stability. It is not anchor evidence because published PAM50 calls are not
a gold standard, TCGA/PanCA independence is unresolved, and clinical validation is
exploratory.
`PMC3283537` is officially non-open-access and was not stored. Its related lawful
comparison `PMC3413822` is context-only evidence: it shows moderate classifier
agreement and comparative prognostic differences but does not establish the correct
patient-level subtype or directly test reference stability.
`PMC8138885` is officially non-open-access and was not stored. `PMC5001207`
(CrossLink) is context-only: it recognizes cross-condition transportability, but its
cohort-level k-means procedure cannot classify an individual patient independently
and its strongest cross-platform PAM50 evaluation lacks true subtype labels.
`PMC7376512` is context-only measurement evidence: in its limited PAM50 subset,
IHC surrogate Luminal A/B labels agreed with PAM50 for 55.8% of tumors using the
selected hotspot score and 66.3% using global Ki67. The study does not identify the
correct discordant label, evaluates 22 hotspot methods without a prespecified
multiplicity strategy, and has no external validation; these results support the
measurement-variability rationale but not a clinical-reliability claim.
The apparent next stability record was the Research Square preprint of
`PMC10587090`, not a distinct study. A founder-authorized duplicate/version
decision links it to the peer-reviewed record so it is not retrieved or counted
twice. The Phase 0 [`novelty_memorandum.yaml`](novelty_memorandum.yaml) therefore
recommends `change`: question `0.2.0` is too broadly framed around work already
performed in 6,233 SCAN-B tumors. The candidate revision must focus on a fixed
single-sample reliability, calibration, and abstention layer.

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
