# Literature

## Question 0.3.0 revised evidence review

The current reliability-focused review is governed by:

- [`REVISED_EVIDENCE_REVIEW_PROTOCOL.md`](REVISED_EVIDENCE_REVIEW_PROTOCOL.md)
- [`search_strategy_v0.3.0.yaml`](search_strategy_v0.3.0.yaml)
- [`revised_priority_evidence.yaml`](revised_priority_evidence.yaml)
- [`revised_evidence_review_progress.yaml`](revised_evidence_review_progress.yaml)
- [`REVISED_SCREENING_WORKFLOW.md`](REVISED_SCREENING_WORKFLOW.md)
- [`REVISED_SCREENING_PROTOCOL.md`](REVISED_SCREENING_PROTOCOL.md)
- [`FOUNDER_PRIORITY_SCREENING_PACKET_v1.0.0.md`](FOUNDER_PRIORITY_SCREENING_PACKET_v1.0.0.md)
- [`FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md`](FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md)
- [`FOUNDER_REMAINING_SCREENING_CONFIRMATION_v1.0.0.md`](FOUNDER_REMAINING_SCREENING_CONFIRMATION_v1.0.0.md)

Search strategy `0.2.4` is locked after coverage QA repaired a pre-screening gap in
version `0.2.3`. Count-only feasibility returned 56 PubMed and 99 Europe PMC hits.
The replacement execution `a2500aba…f1ea9f` contains 100 unique records, 55
cross-source duplicates, complete abstracts, and all 13 mandatory priority papers.
Its search and queue objects, hashes, sizes, schemas, identifiers, pending states,
and count invariants were independently verified.

Reconciliation `075aa083…397891` classified all 100 records against the immutable
prior inventory: 55 exact matches, 5 author-year-only candidates, and 40 new
candidates. No prior decision was transferred. The founder rejected all five fuzzy
author-year links and confirmed the exact remaining-record packet under SHA-256
`210a4d8e…4304aa`. Raw records and detailed reconciliation mappings remain outside
Git. The progress ledger cannot claim completion until appraisal accounting and two
consecutive zero-yield backward-plus-forward citation passes reconcile.

Screening protocol `1.1.0` is locked to the replacement queue. Verified progress
`7b90c37a…63218c` records complete founder review of all 100 records: 30 inclusions,
70 exclusions, zero pending, zero unclear, and zero AI decisions. Inclusion
authorizes lawful full-text assessment; it is not a quality designation or
scientific endorsement.

The 30-record access inventory contains 26 repository candidates and four records
requiring separate lawful-access checks. Reconciled progress now records 19
independently verified CC-BY full texts, nine governed read-only reviews, and two
access restrictions. No restricted full text was stored. All 28 lawfully accessible
records are appraised: 15 are `supporting`, 13 are `context_only`, and none is
anchor evidence.

Citation pass 1 queried both official Europe PMC directions for every eligible
seed. The verified receipt records 981 backward and 4,639 forward links and 4,628
unique non-seed records. Its separate screening-preparation inventory reconciles
all 4,628: 42 were already present in the completed direct-search inventory, 91
are normalized-title duplicates within the citation set, and 4,495 require
screening. These are workload dispositions, not autonomous eligibility decisions.
Raw responses, candidate metadata, and the full deduplication ledger remain in
checksummed external object storage; aggregate receipts are in `citation-chain/`.
Transparent title prioritization version `1.0.1` ranks—but does not decide—all
4,495 candidates: 80 direct, 400 supporting, and 4,015 context. Full official
Europe PMC enrichment matched every candidate and returned 4,402 abstracts through
90 batched requests. Ninety-three metadata-only records remain explicitly visible.
The next artifact is an abstract-informed advisory packet covering every record.

Abstract advisory version `1.0.2` covers all 4,495 records and remains nondecisional:
15 high-confidence include recommendations, 4,224 exclusion recommendations, and
256 held for individual adjudication. The frozen founder packet has SHA-256
`a6ebe1f9…8e9f0a`; its complete 4,495-row CSV appendix has SHA-256
`a1f378c4…7e062c`. Founder confirmation can authorize only the 4,239 proposed
decisions. The 256 unclear records require a separate adjudication packet.

Second-stage advisory policy `1.0.0` reviews those 256 held records and recommends
17 additional includes and 239 exclusions. Its packet SHA-256 is
`ba8560a7…c1f29fe`; its appendix SHA-256 is `1e41f1f1…56e9e81`. Combined tests
prove exact, non-overlapping coverage of all 4,495 records: 32 proposed includes,
4,463 proposed excludes, zero unclear, and zero founder decisions. The combined
review artifact allows one exact founder confirmation while retaining both packet
boundaries.

The founder supplied the exact checksum-bound confirmation statement. Decision
ledger `1ca4b716…281caf` now freezes all 4,495 records: 32 inclusions, 4,463
exclusions, zero unclear, and zero AI decisions. The stored 2,391,610-byte ledger
has SHA-256 `e9779f63…fefd`; confirmation changed no packet or appendix bytes.

Exact-identifier reconciliation `0a6d4893…580b4` compared all 32 inclusions with
the active 30-record inventory and 36 unique prior appraisals. No inclusion was
already in the active inventory. Three have reusable locked appraisals (PMIDs
22752290, 27556419, and 16643655), leaving 29 net-new records. Reconciliation
used only PMID, PMCID, and normalized DOI equality; it made no founder decision
and drew no scientific conclusion.

The founder separately approved evidence-cap amendment `0.2.5` under exact source
SHA-256 `4aeb5ef4…d507`. Activation `6769d900…ab2f33` verified the amendment,
reconciliation receipt, and external reconciliation object before creating the
immutable appraisal queue: 23 repository candidates, six lawful-access checks,
and three prior-appraisal reuses. The saturation inventory is now uncapped; the
quality-selected core synthesis remains limited to 30 non-duplicate primary
studies. Molecular and outcome access remain prohibited.

Citation access inventory `1.0.0` contains the 29 net-new studies with stable
screening IDs: 23 repository candidates and six initial access checks. Repository
batch `95f35d80…15ef9b` contacted the official Europe PMC full-text endpoint for
all 23. Thirteen articles passed exact PMCID, PMID, DOI, title, and item-level CC BY
verification and have immutable receipts in `citation-full-text/retrievals/`.
Five returned 404, three lacked an approved durable-storage license, and two failed
exact identity matching. Those ten stored no article content.

Access-check queue `de76e254…46ad93` combines the ten repository failures with six
records having no PMCID. It records zero final access decisions: all 16 remain
pending lawful read-only, publisher-license, identity-correction, or restriction
review in that immutable initial queue. A bounded dash-typography repair later
resolved `PMC7299291` and `PMC11265146` under exact PMCID, PMID, and DOI agreement;
both CC BY 4.0 articles were retrieved and verified. Current reconciled
`citation_appraisal_progress_v1.0.0.yaml` records three completed appraisals,
22 ready for appraisal, three access restrictions, and one record awaiting full
text. Ten verified ephemeral reviews now include eight official PMC pages, one
version-specific medRxiv representation, and one institutional author-copy PDF;
every exact content representation was hashed in memory and no article content was
stored. The UNC Lineberger copy for PMID 23907291 is bound to SHA-256
`5ffda151…805a` and remains outside the reusable corpus because no redistribution
license was verified. Official publisher checks separately restrict PMIDs 28069519,
30040052, and 31435878 without inferring an appraisal from abstracts or previews.
The sole unresolved record is the 2010 Lancet Oncology paper PMID 20181526: the
publisher declares it CC BY 4.0, but the approved client does not yet have a
reproducible checksum-verifiable full-text route. The version-2 `PPR1259744`
medRxiv preprint remains restricted from the reusable corpus under CC BY-NC 4.0.

Citation appraisal batch 0001 covers three direct studies: `PMC11217366`,
`PMC6547580`, and `PMC3487945`. The founder supplied the exact confirmation bound
to packet SHA-256 `4704eba6…0516e` and all three proposal checksums. The typed
authorization service independently verifies those bytes before deriving locked
founder-authorized appraisals; modified or incomplete inputs fail closed. All three
are locked as `context_only`. The original proposal files correctly retain
`founder_decision_recorded=false` because authority resides in the separate,
append-only confirmation artifact.

Citation appraisal batch 0002 now proposes judgments for four single-sample
method papers under packet SHA-256 `f45518a3…f92e2`. `PMC6219008` and
`PMC8796360` are proposed as `supporting`; `PMC8479681` and `PMC10848444` are
proposed as `context_only`. The proposals remain non-authoritative and the live
progress ledger remains at three completed, 20 ready, and six awaiting access
until the founder confirms the exact packet.

Citation appraisal batch 0003 now proposes judgments for the six remaining
checksum-verified full texts. `PMC4546262`, `PMC4818440`, `PMC7470374`, and
`PMC8657125` are proposed as `supporting`; `PMC1557722` and `PMC10771357` are
proposed as `context_only`. The batch adds direct evidence about fixed commercial
assay development, paired specimen perturbations, peri-surgical variation,
commercial-test reconstruction, and real-world IHC/PAM50 disagreement. It remains
non-authoritative pending its own exact founder confirmation and does not alter
the live progress counts.

The typed appraisal-confirmation contract is no longer batch-0001-specific. It
derives the exact statement from the four-digit batch number, binds that number to
the packet filename, verifies the packet and every proposal checksum, rejects
missing or substituted proposal sets, verifies screening and study identities,
and then derives founder-authorized appraisals in memory. Authorization-readiness
tests cover the real batch-0002 and batch-0003 bytes without recording a founder
decision. Only a separate exact founder confirmation artifact can cross this gate.
The three batch-0001 locked appraisals are materialized in
`citation-appraisals/`; the proposal files remain unchanged and non-authoritative.

Citation appraisal batch 0004 proposes the `PPR1259744` Prosigna
nCounter-to-whole-transcriptome-NGS analytical bridge as `supporting`. The packet
is bound to SHA-256 `b03ea215…d7eda` and the proposal to
`2bc1b32d…c93f3`. The proposal records the separated bridge and validation
cohorts, paired comparator, prespecified analytical criteria, archival testing,
preprint status, Veracyte funding, proprietary data, and incomplete public
calibration artifact. It remains non-authoritative until the founder separately
confirms batch 0004 exactly.

Citation appraisal batch 0005 proposes the PMID 23907291 genomic-versus-pathology
comparison as `context_only`. Its institutional author copy was reverified against
the prior 518,968-byte receipt and SHA-256 `5ffda151…805a` through a structured
no-storage proposal gate. That gate limits derivative narrative sizes, rejects
long verbatim source sequences, and retains no article text. Packet SHA-256
`990c74c2…b8117` binds proposal SHA-256 `e10db278…a8cd6`. The proposal records
moderate overall agreement alongside cohort-level centering, selected population,
small subgroup analyses, crossover treatment sequence, absent multiplicity
control, and no external validation. It remains non-authoritative until the
founder separately confirms batch 0005 exactly.

Citation appraisal batch 0006 is being prepared from stable official file
representations. Re-fetching the prior PMC HTML pages demonstrated that dynamic
page bytes can change without a byte-count change, so those receipts remain
access-provenance records but are not sufficient for a delayed exact-byte appraisal
gate. The new allowlisted publisher/repository PDF route verifies the DOI-to-source
binding, complete PDF boundaries, title and DOI identity, exact SHA-256, proposal
provenance, bounded derivative text, and absence of copied 12-word passages. It
retains no article bytes. Official stable PDFs are verified as available for
`PMC3283537`, `PMC6473265`, and `PMC10147771`; `PMC3508193` and `PMC7791620`
remain outside batch 0006 until their separate stable-source routes are governed.

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
