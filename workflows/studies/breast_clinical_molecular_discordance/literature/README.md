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

Sequential pass retrieval uses a typed cumulative-seed boundary. Pass 2 combined
the 30 direct founder inclusions with all 32 pass-1 founder inclusions
from the checksum-verified evidence-cap activation queue. Exact persistent-
identifier deduplication is permitted across 61 `MED` PMIDs and one Europe PMC
`PPR` preprint identity, but no founder inclusion may be dropped because of
appraisal role, access restriction, result direction, or core-synthesis limits.
Screening preparation bound the complete pass-1 founder decision ledger in addition
to the locked direct-search inventory, preventing previously screened citation
records from being presented as new.

Pass 2 retrieved 2,053 backward and 8,163 forward links and deduplicated them to
7,135 unique non-seed candidates. Prior-screening and within-pass reconciliation
left 2,479 genuinely new records. Official enrichment matched 2,478 records and
supplied 2,410 abstracts; the single unresolved metadata record remains visible.
The founder confirmed both checksum-bound packets. The resulting ledger contains
nine inclusions, 2,470 exclusions, zero unclear, and zero AI decisions.

Exact-identifier reconciliation against the active inventory and all locked
appraisals classified the nine inclusions as net new. Access review accounts for
all nine: five official sources were reviewed ephemerally with canonical
checksums and zero retained article bytes, and four publisher-only records have
typed restriction decisions. The founder confirmed checksum-bound appraisal
batch `0009`; all five accessible studies are locked as `context_only`.
Receipt-derived closure `995b8b3f…f6f9a7` adds all nine eligible identities and
proves complete appraisal accounting.

Citation pass 3 used all 71 founder-included persistent identities. Official
Europe PMC retrieval returned 2,393 backward and 8,617 forward links, yielding
7,728 unique non-seed candidates. Prior-screening and within-pass reconciliation
left 593 genuinely new records. Enrichment matched 592 records and supplied 575
abstracts while preserving one unresolved identity. The founder confirmed both
checksum-bound packets, producing seven inclusions, 586 exclusions, zero unclear,
and zero AI decisions.

All seven inclusions are lawfully accounted for. Three CC BY 4.0 Europe PMC
articles are retained in governed external object storage, two official PMC OAI
articles were reviewed ephemerally with zero article bytes retained, and two
publisher records have explicit restricted-access decisions. The founder
confirmed appraisal batch `0010`; all five accessible studies are now locked as
`context_only`. Receipt-derived closure `08fcf9c6…4a33d9` adds all seven
eligible identities and proves complete appraisal accounting. The cumulative
review now contains 78 eligible identities: 66 appraisal-complete and 12
access-restricted, with zero pending. Pass 3 added evidence, so citation pass 4
must execute and the two-consecutive-zero stopping rule is not yet satisfied.

Citation pass 4 preserved all 78 cumulative identities. Official Europe PMC
retrieval returned 2,617 backward and 8,873 forward links, yielding 8,092 unique
non-seed candidates. Prior-screening and within-pass reconciliation left 367
genuinely new records. Complete enrichment matched 366 records and supplied 359
abstracts while preserving one unresolved identity. Two checksum-bound advisory
packets propose two inclusions and 365 exclusions with zero unclear. The current
founder confirmation produced two inclusions, 365 exclusions, zero unclear, and
zero AI decisions. Both inclusions are net new and lawfully readable: one
licensed durable full text and one canonical official PMC OAI no-storage review.
The founder confirmed appraisal batch `0011`, but post-confirmation
reconciliation failed closed on one DOI mismatch. `PMC5947827` is correctly
locked. Corrective batch `0012` binds `PMC9604175` to the official DOI
`10.3390/ijms232012707` while changing no scientific judgment, source checksum,
or proposed `context_only` role. The current gate is the exact founder statement
`I confirm citation appraisal batch 0012 as written.` The founder confirmed the
correction, both appraisals are locked as `context_only`, and receipt-derived
closure `7880f29b…d5a1ff` adds two eligible identities. The cumulative review
now contains 80 eligible identities: 68 appraisal-complete and 12
access-restricted, with zero pending. Pass 5 is required because pass 4 yielded
new evidence.

Citation pass 5 preserved all 80 cumulative identities. Official retrieval
returned 2,696 backward and 8,927 forward links and 8,190 unique non-seed
candidates. Prior-screening reconciliation left 99 new records; all matched
official metadata and 96 have abstracts. The founder confirmed the two
checksum-bound packets, freezing one inclusion, 98 exclusions, zero unclear,
and zero AI decisions. The included Oxford article has no PMCID, and its
official HTML and PDF endpoints returned an automated-access challenge. No
control was bypassed, no article text was retained, and no abstract-only
appraisal was substituted. Receipt-derived closure `efb35a2c…cf9dc` adds PMID
`28376187` as access-restricted. The cumulative review now contains 81 eligible
identities: 68 appraisal-complete and 13 access-restricted, with zero pending.
Because pass 5 added evidence, pass 6 is required and the consecutive-zero
stopping count remains zero.

Citation pass 6 preserves all 81 cumulative identities. Official retrieval
returned 2,733 backward and 8,954 forward links, yielding 8,227 unique non-seed
candidates. Reconciliation against the direct search and all five prior founder
decision ledgers left 38 genuinely new records with no within-pass duplicates.
Official enrichment matched all 38 records and supplied every abstract.
Conservative advisory screening proposes zero inclusions and 38 exclusions with
zero unclear. The current gate is the exact statement `I confirm the proposed
citation pass 6 decisions in the checksum-bound packet.` Confirmation would
freeze the first zero-yield pass; one additional consecutive fully screened
zero-yield pass would still be required for saturation.

For pass 3 and later, cumulative seeds are not reconstructed from memory or only
the immediately preceding pass. The typed seed receipt binds the direct-search
inventory, the pass-1 activation queue, and one ordered founder-authorized queue
for every later prior pass. Screening preparation independently requires one
founder decision ledger for every prior pass. A fully screened pass with zero
inclusions still receives a checksum-bound empty queue, adds no seeds, and creates
no access inventory. This preserves auditable lineage through the locked requirement
for two consecutive fully screened zero-yield passes.

Pass completion is derived through a separate checksum-bound closure gate. It
re-verifies retrieval and deduplication objects, founder decision and inclusion
ledgers, the pass appraisal queue, exact prior-appraisal reuses, the access
inventory, and final appraisal progress. Unresolved full-text or appraisal work
prevents closure. Pass 1 was materially closed from frozen revision `8c94614`
under closure `3f7037ca…d9676`. It reconciles 4,628 unique records, 4,495
founder-screened records, 32 inclusions, three prior-appraisal reuses, 25 completed
appraisals, four access restrictions, and 32 new eligible identities. After pass
3, the bound review state contains 78 eligible identities, 66 appraisal-complete
identities, 12 access-restricted identities, and zero pending. Because all three
completed passes added evidence, the consecutive-zero stopping count remains
zero.

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
`citation_appraisal_progress_v1.0.0.yaml` records 25 completed appraisals, zero
ready for appraisal, four access restrictions, and zero records awaiting full
text. The completed set contains seven `supporting` and 18 `context_only`
appraisals. Ten verified ephemeral reviews include eight official PMC pages, one
version-specific medRxiv representation, and one institutional author-copy PDF;
every exact content representation was hashed in memory and no article content was
stored. The UNC Lineberger copy for PMID 23907291 is bound to SHA-256
`5ffda151…805a` and remains outside the reusable corpus because no redistribution
license was verified. Official publisher checks separately restrict PMIDs 28069519,
30040052, and 31435878 without inferring an appraisal from abstracts or previews.
The final access decision covers the 2010 Lancet Oncology paper PMID 20181526.
ScienceDirect and Crossref declare the version of record CC BY 4.0, but
Unpaywall identifies only the same publisher PDF, Europe PMC has no repository
copy, publisher PDF delivery returns an access challenge, and the
credential-free Elsevier API returns metadata only. The permissive license does
not substitute for a reproducible checksum-verifiable article body; no challenge
was bypassed, no third-party copy was retained, and no appraisal was inferred
from the abstract. The version-2 `PPR1259744`
medRxiv preprint remains restricted from the reusable corpus under CC BY-NC 4.0.

Citation appraisal batch 0001 covers three direct studies: `PMC11217366`,
`PMC6547580`, and `PMC3487945`. The founder supplied the exact confirmation bound
to packet SHA-256 `4704eba6…0516e` and all three proposal checksums. The typed
authorization service independently verifies those bytes before deriving locked
founder-authorized appraisals; modified or incomplete inputs fail closed. All three
are locked as `context_only`. The original proposal files correctly retain
`founder_decision_recorded=false` because authority resides in the separate,
append-only confirmation artifact.

Citation appraisal batch 0002 covers four single-sample method papers under
packet SHA-256 `f45518a3…f92e2`. `PMC6219008` and `PMC8796360` are locked as
`supporting`; `PMC8479681` and `PMC10848444` are locked as `context_only`.

Citation appraisal batch 0003 covers six checksum-verified full texts.
`PMC4546262`, `PMC4818440`, `PMC7470374`, and `PMC8657125` are locked as
`supporting`; `PMC1557722` and `PMC10771357` are locked as `context_only`. The
batch adds direct evidence about fixed commercial
assay development, paired specimen perturbations, peri-surgical variation,
commercial-test reconstruction, and real-world IHC/PAM50 disagreement.

The typed appraisal-confirmation contract is no longer batch-0001-specific. It
derives the exact statement from the four-digit batch number, binds that number to
the packet filename, verifies the packet and every proposal checksum, rejects
missing or substituted proposal sets, verifies screening and study identities,
and then derives founder-authorized appraisals in memory. Separate append-only
confirmation artifacts crossed this gate for batches 0001 through 0008. All 25
locked appraisals are materialized in `citation-appraisals/`; the proposal files
remain unchanged and non-authoritative.

Citation appraisal batch 0004 locks the `PPR1259744` Prosigna
nCounter-to-whole-transcriptome-NGS analytical bridge as `supporting`. The packet
is bound to SHA-256 `b03ea215…d7eda` and the proposal to
`2bc1b32d…c93f3`. The proposal records the separated bridge and validation
cohorts, paired comparator, prespecified analytical criteria, archival testing,
preprint status, Veracyte funding, proprietary data, and incomplete public
calibration artifact.

Citation appraisal batch 0005 locks the PMID 23907291 genomic-versus-pathology
comparison as `context_only`. Its institutional author copy was reverified against
the prior 518,968-byte receipt and SHA-256 `5ffda151…805a` through a structured
no-storage proposal gate. That gate limits derivative narrative sizes, rejects
long verbatim source sequences, and retains no article text. Packet SHA-256
`990c74c2…b8117` binds proposal SHA-256 `e10db278…a8cd6`. The proposal records
moderate overall agreement alongside cohort-level centering, selected population,
small subgroup analyses, crossover treatment sequence, absent multiplicity
control, and no external validation.

Citation appraisal batch 0006 contains two locked `context_only` appraisals for
direct IHC/PAM50 comparisons in Korean and South African cohorts.
Packet SHA-256 `a1bbada9…c002` binds proposal SHA-256 values
`6e918cf4…84d2` and `7effc650…a917`.
Their official publisher PDFs passed the delayed exact-byte, article-identity,
bounded-narrative, and verbatim-leakage gates while zero article bytes were
retained. Re-fetching the prior PMC HTML pages demonstrated that dynamic
page bytes can change without a byte-count change, so those receipts remain
access-provenance records but are not sufficient for a delayed exact-byte appraisal
gate. The new allowlisted publisher/repository PDF route verifies the DOI-to-source
binding, complete PDF boundaries, title and DOI identity, exact SHA-256, proposal
provenance, bounded derivative text, and absence of copied 12-word passages. It
retains no article bytes. `PMC3283537` failed the delayed checksum gate because
its repository PDF changed bytes; `PMC3508193` and `PMC7791620` also remain
outside batch 0006 until separate stable-source routes are governed.

For dynamic delivery envelopes, Cortex provides two additional fail-closed
routes. The PMC OAI route isolates and canonicalizes the single JATS `article`
subtree, excluding the changing OAI response timestamp before hashing. The
publisher-HTML route is restricted to an explicit DOI-to-URL allowlist, removes
non-article script/style/template content, and hashes canonical citation metadata
plus visible text. Both routes re-fetch and re-canonicalize the source during
proposal validation, verify PMID/PMCID/DOI/title identity, enforce narrative and
verbatim limits, and retain no source content. A canonical checksum is not a
license grant; durable storage and redistribution remain prohibited unless
separately authorized.

Citation appraisal batch 0007 uses those canonical routes for `PMC3283537`,
`PMC3508193`, and `PMC7791620`. All three are locked as `context_only` under
packet SHA-256 `43410b02…21d5`. Together they show that
single-sample microarray normalization is feasible, that simplified classifier
robustness does not remove cohort-level fitting or establish biological truth,
and that IHC surrogates show only poor-to-moderate four-class agreement with
PAM50 in two Swedish cohorts. These observations do not validate a NaS method,
patient-level subtype adjudication, or treatment utility.

Citation appraisal batch 0008 completes review of the remaining five verified
citation-pass full texts. Three canonical PMC OAI representations
were re-fetched and verified with zero article bytes retained; two CC BY 4.0
sources were reverified against the external object store. All five proposals are
`context_only`. The set contributes direct evidence about IHC/PAM50 mismatch and
paired-platform TCGA-BRCA normalization, plus indirect evidence about rank-based
patient-independent classification and difficult molecular boundaries. It does
not establish a correct biological label, validate a NaS classifier, or support a
clinical decision. `PMC11696812` is the peer-reviewed successor to the already
appraised `PMC10723508` preprint and must replace it as the canonical synthesis
citation rather than count as an independent study.

Publication-version control is mechanically enforced. The link proposal has its
own checksum and was authorized through the batch-0008 founder confirmation
contract. Authorization required the canonical publication to have an appraisal
in that same confirmed batch. The reconciliation service then
verifies both appraisals against exact screening IDs, normalized titles, PMIDs,
and DOIs; rejects missing, overlapping, or cross-study links; and emits an
immutable family receipt whose unique-study count is the appraisal count minus
authorized version links. The materialized receipt records 53 appraisal reports,
one authorized version link, and 52 unique studies. The CLI commands are
`citation-appraisal-authorize --version-link-proposal-dir ... --version-link-output-dir ...`
and `citation-publication-version-reconcile`.

Delayed appraisals may bind a stable canonical source separately from the
original access receipt. The progress command accepts repeatable
`--appraisal-source-receipt-dir` arguments and records both the alternate receipt
ID and checksum. It verifies inventory identity, title, PMCID, checksum, lawful
read permission, and completed-appraisal status while preserving the original
access receipt and decision.

The historical filename
`FOUNDER_PENDING_CITATION_APPRAISAL_REVIEW_v1.0.0.md` is retained for immutable
links. Its current contents index the seven completed confirmations, exact packet
hashes, proposal counts, evidence-role totals, and append-only confirmation
artifacts. It is a convenience index, not a combined authorization.

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
