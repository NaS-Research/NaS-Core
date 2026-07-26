# NaS Core Project Status

Last updated: 2026-07-26

This is the living implementation record for NaS Core. It should answer three
questions at a glance: what are we building now, what proves it is finished,
and what comes next?

## Current focus

### Continue sequential citation chaining after closing input feasibility

Citation pass 2 has executed from frozen revision `5d7a6d9…7520e0`. Its 62
unique persistent seeds comprise 61 `MED` PMIDs and one `PPR` preprint from the
30 direct inclusions and all 32 pass-1 inclusions. Official Europe PMC retrieval
returned 2,053 backward and 8,163 forward links, yielding 7,135 unique non-seed
candidates. Reconciliation against the direct-search inventory, complete pass-1
founder ledger, and within-pass duplicates removed 4,656 previously screened or
duplicate records and left 2,479 genuinely new candidates.

All 2,479 records were prioritized and enriched; 2,478 matched official metadata,
2,410 supplied abstracts, and one unresolved metadata record remains visible.
The two checksum-bound advisory packets cover every new candidate exactly once:
9 proposed inclusions, 2,470 proposed exclusions, zero unclear, zero founder
decisions, and zero scientific conclusions. The current gate is exact founder
review of `FOUNDER_CITATION_PASS_0002_COMBINED_REVIEW_v1.0.0.md`. Molecular and
outcome access remain prohibited.

A no-persistence production-path preflight proves that exact confirmation would
materialize 2,479 decisions and that identifier-only reconciliation against the
30-record active inventory and all 53 locked appraisal reports would route all
nine proposed inclusions as net new. The later-pass queue boundary is now typed,
checksum-bound to the decision, reconciliation, and active amendment receipts,
and preserves protocol `0.2.5`. If confirmed, four records have repository
identifiers and five require separate lawful-access checks. These are anticipated
workflow routes, not founder decisions or access authorizations.

The sequential stopping-rule boundary is generalized beyond pass 2. Each next
seed receipt requires the original 30-record inventory, the complete pass-1
activation queue, and exactly one ordered founder-authorized queue for every later
prior pass. Screening preparation independently requires one founder decision
ledger for every prior pass. Empty eligible sets remain checksum-bound as empty
queues, contribute no new seeds, and do not create access inventories; this allows
the system to prove two consecutive zero-yield passes without losing lineage.

Citation-pass completion is no longer a free-standing count assertion. A typed
closure service re-verifies retrieval and screening objects, founder decision and
reconciliation ledgers, appraisal queues, exact reused appraisals, access inventory,
and appraisal progress before deriving new eligible evidence IDs. Pass 1 is now
materially closed from frozen revision `8c94614` under immutable closure
`3f7037ca…d9676`. It reconciles 4,628 unique citation records, 4,495 founder
decisions, 32 inclusions, three exact appraisal reuses, 25 completed appraisals,
four access restrictions, and 32 new eligible evidence records. The bound
identity-level evidence state is 62 eligible, 56 appraisal-complete, six
access-restricted, and zero pending. Because pass 1 added evidence, the
consecutive-zero stopping count remains zero.

The proposed analytical contract now has an executable synthetic-only kernel.
It accepts only `SYNTHETIC-*` identifiers; validates the exact historical
50-gene panel and declared aliases; fails closed on missing, ambiguous, nonfinite,
or invalid method inputs; computes five-centroid Spearman scores, runner-up
margin, all 50 leave-one-gene-out runs, and optional explicit synthetic
technical-error vectors; and makes every non-reliable state abstain. Family-level
counts reconcile to aggregate repeatability, label-changing vectors expose
instability, and invalid vectors remain counted and force abstention. It does not
resolve the real centroid/reference artifacts, platform transforms, empirical
technical-error calibration, numerical tolerance, or scientific thresholds and
cannot authorize or execute patient-level molecular analysis.

The patient-independence claim is now executable at the software boundary.
Synthetic batch scoring is only a list of independent single-sample calls: it
accepts no cohort statistic, rejects duplicate identities, retains sample-only
result hashes, and separately hashes ordered batch provenance. Tests prove that
the same target result is unchanged alone, before or after an unrelated
companion, and under reversed batch order. This is not patient validation.

Founder-authorized field-isolated audit `1.0.0` executed from frozen code revision
`2f0b15f…74d0c` and produced receipt SHA-256 `b5f8c359…822a`. It verified all
50 historical PAM50 genes without ambiguous mappings in both frozen source
representations. It quantified TCGA receptor completeness across 1,098 records
and GSE96058 receptor completeness across 3,409 records while retaining no
patient/sample rows, molecular values, outcomes, raw artifacts, cohort, or
classifier result.

Four of five checks passed. The approved GEO characteristic fields contained no
primary-versus-technical-replicate linkage, so all 3,409 sample records remained
unclassified and the receipt correctly returned `changes_requested`. The official
GEO description states that `!Sample_title` distinguishes titles such as `F30`
and `F30repl`, but that field is outside audit `1.0.0`'s allowlist. The founder
authorized amendment `1.0.1` exactly on 2026-07-26. Audit `1.0.1` then executed
from frozen revision `5d5a5d2…95361` and produced receipt SHA-256
`a974bce9…3821b`. All four source representations matched audit `1.0.0`; the
strict title projection classified 3,273 primary records and 136 technical
replicates, linked all 136 replicates, and left zero records unclassified. All
five feasibility checks passed. No transient title, accession, patient/sample
row, molecular value, outcome, raw artifact, cohort, or classifier result was
retained. Input feasibility is closed; method compatibility and scientific review
remain unresolved.

The completed citation-appraisal state remains:

Primary title-and-abstract screening is complete. Founder-confirmed progress
`7b90c37a…63218c` records 30 inclusions, 70 exclusions, zero pending, zero unclear,
and zero AI decisions. All five fuzzy author-year identity links were rejected.
The expanded access inventory is complete: 26 of the 30 inclusions have repository
identifiers and four required separate lawful-access checks. Reconciliation now
records 19 durable CC BY retrievals, nine governed read-only reviews, 28 completed
appraisals, zero records ready for appraisal, and two access restrictions. No
restricted text was stored. All lawfully accessible records are appraised. Citation
pass 1 now has a
checksum-bound founder ledger containing 32 inclusions and 4,463 exclusions, with
zero unclear and zero AI decisions. Exact-identifier reconciliation found no overlap
with the active 30-record inventory, three previously appraised studies, and 29
net-new records. Founder-approved amendment `0.2.5` is active. Official Europe PMC
assessment retrieved 13 exact-identity CC BY full texts and failed closed on ten
repository candidates. Bounded title normalization subsequently resolved two
exact-ID, CC BY 4.0 records. Eight additional PMC-hosted articles, one
version-specific medRxiv preprint, and one institutional author-copy PDF have
verified ephemeral-review receipts with zero article bytes stored. The founder
has confirmed all eight checksum-bound citation appraisal batches. Citation
progress now records 25 completed appraisals—seven `supporting` and 18
`context_only`—four explicit publisher-access restrictions, zero records ready
for appraisal, and zero records awaiting full text.

The final access decision concerns the CC BY 4.0 Lancet Oncology record PMID
20181526. Publisher, Unpaywall, Europe PMC, Crossref, and credential-free Elsevier
API checks confirmed its identity and license but exposed no reproducible,
checksum-verifiable article body. No challenge was bypassed, no third-party copy
was retained, and no appraisal was inferred from its abstract. A live re-fetch
also showed that PMC HTML can retain the same byte count while changing its
SHA-256. Delayed appraisals therefore use fail-closed publisher-PDF, PMC OAI, or
allowlisted publisher-HTML routes that verify article identity and exact or
canonical bytes, bound derivative narrative and verbatim leakage, and retain no
article bytes.

The historical review index
`FOUNDER_PENDING_CITATION_APPRAISAL_REVIEW_v1.0.0.md` records all seven
batch-specific confirmations and links to their append-only confirmation
artifacts. Exact authorization materialized 22 derived appraisals in
`literature/citation-appraisals/`; the immutable proposal files remain unchanged
as provenance. A separately checksummed, founder-authorized version link binds
the peer-reviewed `PMC11696812` report to the already appraised `PMC10723508`
preprint. Mechanical reconciliation preserves 53 appraisal reports while
counting 52 unique studies.

Delayed canonical appraisals carry explicit appraisal-source receipt IDs and
checksums in addition to their original access receipts. This preserves the
lawful-access decision while proving which stable, reverified representation
supports each appraisal.

The earlier source-level audit and the new field-isolated receipt together prove
source availability, exact PAM50 row coverage, and receptor completeness. They do
not prove assay equivalence, lock a transformation, validate a classifier, or
authorize molecular or outcome analysis.

Definition of done:

- Question version `0.3.0` defines a fixed single-sample method and a specific
  contribution not already answered by the SCAN-B perturbation study.
- The minimum implementation set and all margin, stability, uncertainty,
  unclassifiable, and abstention rules are declared without outcome inspection.
- Exact centroids, reference vector, platform transformations, technical-error
  model, numerical tolerances, and reliability thresholds are lawfully sourced,
  checksummed, evidence-backed, and locked before molecular access.
- The revised evidence review satisfies its locked stopping rule and retains
  contradictory and null evidence.
- Every read-only appraisal reconciles to an identity-verified source URL and
  ephemeral-content checksum; no restricted full text enters Git or object storage.
- Metadata-only checks verify receptor fields and PAM50 gene coverage in TCGA and
  GSE96058 without accessing outcomes.
- Separate founder scientific/product, molecular/pathology, and statistical review
  passes record conflicts and knowledge limitations.
- A new `go`, `change`, `hold`, or `reject` decision is recorded; only `go` may
  authorize a versioned preregistration.

Current gate state:

- Question version `0.2.0` and its founder-authorized `change` decision are
  preserved. Version `0.3.0` is the active proposed revision; preregistration and
  outcome access remain prohibited.
- Draft method specification `0.1.0` is typed and mechanically validated. It cannot
  authorize molecular execution while any scientific dependency remains unresolved.
- Revised evidence protocol `0.2.4` and priority set `1.0.0` are typed. All 13
  direct candidates have founder `include` decisions for full-text review; no prior
  question-`0.2.0` decision was silently carried forward.
- Typed Phase 0 plan, literature-search strategy, evidence matrix, and data-
  feasibility specification are implemented.
- AI-assisted question review is advisory; the founder Phase 0 decision is recorded,
  while the revised scientific, molecular, and statistical reviews remain pending.
- The search and source-feasibility specifications are locked. Literature retrieval
  and non-outcome source assessment are authorized; outcome access is disabled.
- Coverage QA stopped the interim 96-record queue before screening because four
  mandatory priority papers were absent. Replacement execution `a2500aba…f1ea9f`
  contains 100 unique records and 55 cross-source duplicates from 56 PubMed and 99
  Europe PMC hits. Its verified all-pending queue contains complete abstracts and
  all 13 priority papers.
- Reconciliation `075aa083…397891` classifies all 100 records against the prior
  inventory: 55 exact matches, 5 author-year-only candidates, and 40 new candidates.
  No previous screening decision was transferred.
- Question-`0.3.0` title/abstract protocol `1.1.0` is locked. Verified founder
  progress records all 100 decisions: 30 inclusions, 70 exclusions, zero pending,
  zero unclear, and zero AI decisions.
- The priority access inventory reconciles all 13 inclusions: 7 verified CC-BY
  full texts, 5 governed read-only reviews, and 1 subscription restriction. No
  restricted text was retained or redistributed.
- The question-specific `PMC3275466` appraisal is complete as `context_only`.
  Its technical-error framework directly challenges the novelty boundary, but sparse
  calibration, unvalidated independence assumptions, inconsistent simulation counts,
  and no external repeat-measure validation prevent it from supplying a transportable
  NaS error model.
- The subgroup-centering paper `PMC4365540` is also `context_only`. It demonstrates
  that cohort composition can radically change PAM50 calls, but its proposed fix
  uses the study cohort's clinical composition and explicitly cannot classify one
  patient independently. It supports—not resolves—the fixed-reference requirement.
- The RNA-seq reference-sensitivity paper `PMC7442834` is `supporting`. Across
  4,731 tumors, it demonstrates reference-subset sensitivity, materially improves
  within-method stability with AWCA, and tests preprocessing-matched external
  references and regularized classifiers. Published PAM50 calls remain a technical
  target rather than biological truth, transport is normalization-specific, and
  clinical validity is unproven, so it is not anchor evidence.
- MiniABS paper `PMC7761033` is `supporting`. It establishes that an 11-gene,
  pairwise-ratio classifier can operate on a single sample across RNA-seq,
  microarray, NanoString, and qRT-PCR datasets. Its PAM50-derived target labels,
  feature-selection sequence, Normal-like sensitivity, and absence of calibrated
  uncertainty or abstention prevent an anchor role. NaS cannot claim single-sample
  execution alone as novel.
- SCAN-B SSP paper `PMC9381586` is `supporting` and is the strongest reviewed
  validation so far. It uses a non-overlapping 2,412-patient test set, long
  follow-up, adjusted outcome models, external Prosigna comparisons, public data,
  and executable code. It also establishes that subtype and recurrence-risk
  prediction already exist; retrospective treatment emulation and absent
  patient-level uncertainty prevent anchor or clinical-utility claims.
- Population-scale stability paper `PMC10587090` is `supporting` and directly
  overlaps the proposed contribution: it evaluates runner-up correlation margins,
  leave-one-gene-cluster-out stability, stable/prototypical labels, and refined
  single-sample centroids in 6,233 tumors. Its perturbations are biological-module
  deletions rather than calibrated technical error, and the method lacks independent
  validation and a prespecified abstention rule.
- BreastSubtypeR paper `PMC12501779` is `supporting`. It unifies ten classifiers,
  reproduces original outputs, computes inter-method entropy, and performs
  cohort-aware method selection. AUTO is not patient-independent, and entropy is
  not calibrated to classification error or abstention.
- All seven retrieved CC-BY priority papers are now appraised: five supporting,
  two context-only, and zero anchor studies.
- A governed read-only review receipt is implemented for lawfully viewable content
  that may not be durably stored. It records identity, access terms, checksum,
  access time, and verification state while mechanically prohibiting storage and
  redistribution claims. Appraisal progress distinguishes durable retrieval from
  read-only review and allows a storage restriction to coexist with completed
  ephemeral appraisal.
- Five governed read-only reviews are complete. PBCMC directly establishes
  single-subject empirical permutation confidence, false-discovery control, a
  runner-up margin, and Assigned/Ambiguous/Not Assigned states as prior art. Its
  gene-label null does not estimate repeatability under independently measured
  technical error, and its thresholds lack unchanged external validation.
- The AIMS publisher record is identity-verified and subscription-restricted.
  No paywall was bypassed, no full text was stored, and no appraisal was inferred
  from the abstract. All 13 priority records therefore reconcile to 12 completed
  appraisals and one explicit access restriction: nine supporting, three
  context-only, and zero anchor studies.
- Living manuscript `0.8.0-working` contains traceable Phase 0 methods,
  all 12 completed appraisals, an evidence-to-text ledger, explicit interpretation
  labels, and prohibited placeholders for NaS results and conclusions.
- The founder confirmed the exact 87-record packet under SHA-256
  `210a4d8ef80fc90aeee194ad3d3c299c4e70570a9a0bb1804f2ac385224304aa`.
  The append-only batch records 17 additional inclusions and 70 exclusions and
  rejects all five author-year-only candidate links. The final evidence set reaches
  the locked 30-record cap.
- The checksum-bound confirmation workflow rejected no invariants: packet bytes,
  queue state, record ordering, identities, coverage, authority, and author-year
  adjudication all verified. The packet remains byte-for-byte unchanged, and a
  separate confirmation audit records the authorization boundary.
- Expanded inventory `access_inventory_v0.3.2.yaml` is bound to completed progress
  `7b90c37a…63218c` and contains all 30 current inclusions: 26 repository
  candidates and four separate access checks. Prior verified receipts remain valid
  only for records that retain exact identity and inclusion in the current queue.
- Reconciled appraisal progress `revised_appraisal_progress_v0.4.0.yaml` records
  19 durable CC BY retrievals, nine governed read-only reviews, 28 completed
  appraisals, zero records ready for appraisal, and two access restrictions.
- The IEEE CC-BY-4.0 author manuscript is durably registered and appraised as
  `context_only`. Its internal held-out accuracy arithmetic and zero-shot
  METABRIC estimates do not reconcile, its external evaluation is fine-tuned,
  and its modality-disjoint cohorts lack patient-level multimodal correspondence.
- Citation pass 1 queried both official Europe PMC directions for all 30 eligible
  seeds. It retrieved 981 backward and 4,639 forward links, yielding 4,628 unique
  non-seed source records. Verified preparation reconciles every record: 42 match
  the completed direct-search inventory, 91 are exact normalized-title duplicates
  within the citation set, and 4,495 require screening. No citation candidate has
  received an autonomous inclusion or exclusion.
- Transparent title prioritization retains all 4,495 candidates while routing 80
  to `direct`, 400 to `supporting`, and 4,015 to `context` review priority. A
  pre-decision calibration lowered the supporting threshold so known single-sample
  scoring methods were not buried. Full official Europe PMC enrichment matched all
  4,495 records and supplied 4,402 abstracts; the remaining 93 stay metadata-only.
- Abstract-informed advisory version `1.0.2` covers all 4,495 candidates: 15
  high-confidence includes, 4,224 exclusions, and 256 records held for individual
  adjudication. Packet `a6ebe1f9…8e9f0a` and its complete 4,495-row appendix
  `a1f378c4…7e062c` are frozen. Zero final founder decisions are recorded.
- Versioned second-stage policy `1.0.0` adjudicates all 256 held records as 17
  additional includes and 239 exclusions. Combined coverage is exactly 4,495
  unique records: 32 proposed includes, 4,463 proposed exclusions, and zero
  unclear. Both packet pairs remain advisory and record zero founder decisions.
- Exact founder confirmation froze decision ledger `1ca4b716…281caf` across all
  4,495 citation candidates: 32 include, 4,463 exclude, zero unclear, and zero AI
  decisions. Packet bytes, appendix bytes, coverage, authority, and the stored
  2,391,610-byte ledger checksum all verified.
- Inclusion reconciliation `0a6d4893…580b4` verified the founder ledger against
  the active 30-record inventory and 36 unique prior appraisals. It found zero
  active-inventory matches, three exact prior-appraisal matches (PMIDs 22752290,
  27556419, and 16643655), and 29 net-new records. No founder decision changed and
  no title-only or fuzzy identity match was used.
- Founder-approved protocol amendment `0.2.5` activates an uncapped saturation
  inventory and retains a maximum 30-study quality-selected core synthesis.
  Activation `6769d900…ab2f33` verified the approved amendment and reconciliation
  checksums and created a 32-record governed queue: 23 repository candidates, six
  access checks, and three prior-appraisal reuses. It authorized no molecular or
  outcome access.
- Citation access inventory `1.0.0` assigns stable screening IDs to all 29 net-new
  records. Repository batch `95f35d80…15ef9b` assessed all 23 PMC candidates:
  13 exact-identity CC BY articles were verified and stored, five returned 404,
  three lacked an approved durable-storage license, and two failed exact identity
  matching. Failed records stored no article content.
- Access-check queue `de76e254…46ad93` combines those ten fail-closed repository
  results with six records lacking repository identifiers. Two title-only dash
  mismatches were later resolved under exact PMCID, PMID, and DOI agreement and
  retrieved as CC BY 4.0. Fourteen remain pending access resolution, not scientific
  exclusion. Citation progress records 12 ready for appraisal, 14 awaiting full
  text, and three founder-authorized appraisals completed.
- Citation appraisal batch 0001 covers `PMC11217366`, `PMC6547580`, and
  `PMC3487945`. Exact founder confirmation is bound to the packet and proposal
  checksums. The authorization service derives three locked `context_only`
  appraisals, and the governing progress ledger records the completed state.
- Eleven newly included repository records now have immutable, independently
  verified CC BY receipts. Four more were lawfully reviewed without storage under
  rights that do not authorize a NaS commercial corpus. One IOP article is
  abstract-only and paywalled; no appraisal was inferred from its abstract.
- PubMed and Europe PMC are registered for bounded evidence synthesis. Replacement
  execution `83d33fb2…4434` contains 457 unique records with complete abstracts.
- Verified queue `b02c2abf…f042` has progress state `dd27a686…ac21`: 27 founder-
  included records, 7 excluded, 423 pending, zero unclear, and zero AI decisions.
- The append-only founder-review workflow is implemented with resumable batches,
  immutable decision events, explicit supersession, and verified progress receipts.
  The first founder decision batch has been submitted and independently verified.
- The governed AI advisory screener, OpenAI gateway, locked structured prompt, and
  immutable provenance contracts are implemented and validated without live model
  use. The founder selected zero-API Phase 0 screening, so policy `1.0.2` disables
  live provider execution. No API credential is required for the active workflow.
- Deterministic prioritization `1.0.0` ranked all 452 initially pending records
  locally. The 29-record core tier is fully founder-reviewed. Supporting/context
  safety screening and full-text eligibility and quality appraisal remain required.
- TCGA/GDC is approved as the proposed discovery source. Processed SCAN-B GSE96058
  is now registered and approved as the external-validation candidate; PAM50 gene
  coverage and cross-platform transformations still require metadata verification.
- Full-text progress is now mechanically reconciled: 8 of 27 founder inclusions have
  verified full text and completed appraisals. Roles are 3 supporting and 5 context-only;
  4 additional papers are access-restricted or non-open-access. No anchor
  study or scientific conclusion exists yet. One Research Square preprint is
  durably linked to its already-appraised peer-reviewed version and is not double-counted.
- The structured evidence matrix, novelty/no-go memorandum, field-level source
  feasibility assessment, governed GSE96058 registration, and Phase 0 gate decision
  are complete. The locked evidence stopping rule was not claimed as satisfied:
  review terminated through an explicit no-go trigger.
- NAS-BRCA-001 remains an immutable conditional platform-qualification pass with
  a pending founder results/remediation decision.

## Next implementation queue

1. Confirm or revise the two checksum-bound citation pass-2 packets, materialize
   the append-only founder decision ledger, and appraise all lawfully accessible
   inclusions.
2. Execute later sequential citation passes until two consecutive fully screened
   passes add zero eligible evidence.
3. Update the living manuscript and its evidence-to-text ledger after every material
   appraisal, protocol decision, executed analysis, figure, and review decision.
4. Resolve and approve the exact centroid and external-reference artifacts,
   redistribution rights, expression transformations, and numerical tolerances.
5. Define an independently calibrated technical-error model and lock the margin
   and canonical-label-retention thresholds without molecular or outcome inspection.
6. Complete the founder scientific/product, molecular/pathology, and statistical
   reviews for question `0.3.0`, then record a new gate decision.
7. Complete the NAS-BRCA-001 founder results review and authorize, hold, or reject
   a transparent versioned remediation.
8. If authorized, remediate only declared NAS-BRCA-001 technical defects and
   preserve the original immutable run.
9. Implement persisted evidence claims, citations, provenance, contradictory
   evidence, null findings, limitations, and review state.
10. Add license-aware permitted passage ingestion and hybrid keyword and semantic
   retrieval after the Phase 0 evidence inventory is screened.
11. Expand the screening model gateway into general evidence reasoning with
   minimum-necessary context, citations, uncertainty, abstention, and governance.
12. Build evaluation suites for retrieval, citation validity, numerical
   fidelity, unsupported claims, and appropriate abstention.
13. Generate an immutable research release containing the protocol, dataset
   manifest, code revision, environment, results, figures, literature,
   limitations, approvals, and disclosures.
14. Generate a reviewable white-paper draft whose substantive claims trace to
   executed artifacts, external sources, or labeled interpretation.
15. Build the internal workbench for projects, protocols, datasets, runs,
   evidence review, and publication releases.
16. Complete repeated internal oncology pilots before selecting the first
    external commercial product surface.

## Recently completed

### 2026-07-26 — Project-to-publication completion audit reconciled

Reconciled every phase in `NAS-BRCA-002/PROJECT_PLAN.md` against current immutable
receipts, typed state, synthetic method evidence, and manuscript placeholders.
Phase 0 is the only fully closed project-to-publication phase. Phases 1, 2, 3,
7, and 12 contain partial work but have not met their exit gates; all remaining
outcome-bearing, release, review, website, and publication phases remain
unstarted or blocked. The audit replaces stale claims that evidence retrieval,
metadata verification, synthetic method execution, and manuscript work had not
begun. It records the exact pass-2 founder statement as the next human action and
explicitly rejects a misleading percent-complete estimate.

### 2026-07-26 — Citation pass 2 prepared for founder confirmation

Executed the cumulative-seed, bidirectional Europe PMC retrieval, prior-decision
deduplication, prioritization, enrichment, conservative advisory, and field-isolated
second-stage adjudication workflow. Pass 2 reduced 7,135 non-seed records to 2,479
genuinely new candidates. Two checksum-bound packets now propose nine inclusions
and 2,470 exclusions with zero unclear. Mechanical tests prove complete,
non-overlapping coverage. No founder or AI decision and no scientific conclusion
has been recorded.

Implemented the post-confirmation later-pass routing boundary without materializing
pass-2 decisions. The real-artifact in-memory preflight found zero active-inventory
matches, zero prior-appraisal matches, and nine net-new candidates. Under the
already active uncapped amendment, those candidates route to four repository
checks and five separate access checks. Receipt, object, count, founder-authority,
and no-molecular/no-outcome invariants fail closed.

Generalized the cumulative seed contract and CLI for pass 3 and later. Synthetic
pass-3 and pass-4 tests prove that direct, pass-1, and all later founder inclusions
remain present; duplicates are exact-identifier reconciled; every prior decision
ledger is used for screening deduplication; and a zero-inclusion pass remains in
the checksum lineage without creating a meaningless access inventory.

Implemented receipt-derived citation-pass closure with fail-closed source-object,
receipt-byte, identity, count, founder-authority, and appraisal-accounting checks.
Synthetic tests cover a completed eligible record, unresolved appraisal rejection,
and a zero-yield pass with no access artifacts. The real pass-1 no-write preflight
reconciles all 32 inclusions and proves that pass 1 resets the consecutive-zero
counter.

### 2026-07-26 — Citation pass 1 materially closed

Executed the frozen receipt-derived closure path and wrote immutable closure
`3f7037ca…d9676`. The gate independently reverified all retrieval, screening,
founder-decision, reconciliation, queue, access, prior-appraisal, and appraisal-
progress artifacts before closing the pass. The evidence-review progress record
now reports 62 eligible identities, 56 appraisal-complete identities, six
access-restricted identities, and zero pending. Pass 1 contributed 32 eligible
identities, so it does not count toward the required two consecutive zero-yield
passes. No molecular or outcome access and no scientific conclusion were
authorized.

### 2026-07-26 — Synthetic single-sample reliability kernel implemented

Implemented the first executable component of the proposed NaS method without
accessing patient or observed molecular data. Typed method, sample, and result
contracts enforce the exact panel, five subtype centroids, deterministic
provenance, explicit quality and reliability states, and synthetic-only identity
scope. The engine computes canonical and runner-up scores, margins, 50
leave-one-gene-out runs, label retention, failure reasons, and report-versus-
abstain action. A CLI exposes only explicitly acknowledged synthetic execution.
Focused tests cover deterministic output, order-invariant hashing, aliases,
collisions, missingness, nonfinite values, ties, thresholds, and rejection of
non-synthetic identifiers. Real method selection and molecular execution remain
prohibited.

### 2026-07-26 — Synthetic technical-error family implemented

Extended synthetic method validation across the second perturbation family
required by specification `0.1.0`. Typed panels require the exact 50-gene order,
an explicit generator seed and description, complete perturbation vectors, and
stable provenance hashing. Each family reports total, valid, and retained-label
counts that reconcile to the aggregate result. Synthetic stable vectors preserve
the label, label-changing vectors trigger threshold-based instability, and
nonfinite vectors remain in the denominator and force `unclassifiable` abstention.
This validates execution logic only; no empirical technical-error distribution,
real threshold, molecular access, or scientific result was approved.

### 2026-07-26 — Synthetic companion and order invariance proved

Added typed synthetic batch input and result contracts plus a CLI that composes
independent single-sample calls without cohort statistics. Duplicate identities
fail before execution; each result retains sample-only provenance; and the batch
receives a separate ordered-input SHA-256. Tests demonstrate byte-equivalent
target results when run alone, after a companion, before a companion, and after
batch-order reversal. This satisfies a software prerequisite for patient-
independent execution but does not validate real molecular performance.

### 2026-07-26 — Field-isolated metadata audit amendment 1.0.1 passed

Recorded the founder's exact checksum-bound amendment authorization, implemented
the no-retention title projection and source-continuity gate, froze the code, and
executed the live audit. All four source representations matched audit `1.0.0`.
The audit classified 3,273 GSE96058 primary records and 136 technical replicates,
linked all 136 replicates, and left zero records unclassified. All five input-
feasibility checks passed. No title, accession, patient/sample row, molecular
value, outcome, raw artifact, cohort, or classifier output was retained.

### 2026-07-26 — Field-isolated metadata audit 1.0.0 executed

Recorded the founder's exact checksum-bound authorization, implemented a
synthetic-tested no-retention projection engine, froze it before source access,
and executed the live audit. Both TCGA and GSE96058 contain all 50 historical
PAM50 genes without ambiguous canonical mappings. TCGA has 981 of 1,098 records
with all three receptor fields present; GSE96058 has 2,931 of 3,409. The approved
GEO characteristics did not encode primary/technical linkage, so the audit
returned `changes_requested`. No patient-level row, molecular value, outcome,
raw source, cohort, or classifier output was retained.

### 2026-07-26 — Citation appraisal batches 0002–0008 authorized

Recorded seven append-only founder confirmations, independently reverified every
packet and proposal checksum, and materialized 22 locked citation appraisals.
Citation pass 1 now has 25 completed appraisals—seven supporting and 18
context-only—plus four explicit access restrictions and no review backlog.
Appraisal-source receipts now preserve the exact stable representation used for
eight delayed appraisals without replacing the original lawful-access receipt.
The founder-authorized mFISHseq publication-version link and reconciliation
receipt preserve 53 appraisal reports while counting 52 unique studies.

### 2026-07-25 — Source-level metadata feasibility audit completed

Implemented a typed, immutable feasibility receipt and a five-request execution
gate. The gate allowlists exact official GDC and NCBI URLs; requests zero GDC
rows; uses HEAD-only GEO artifact checks; rejects patient and outcome fields; and
stores only hashes, aggregate counts, schema findings, and file headers. Seven
synthetic tests cover authorization, zero-row enforcement, derivative isolation,
immutable writing, and schema parity.

The live audit verified GDC Data Release 45.0, API tag 8.5.0, 770 current case
mapping fields, 1,231 open TCGA-BRCA STAR-count files, and both declared
GSE96058 artifacts. It found no indexed receptor-named GDC case field and could
not establish PAM50 row coverage from source-level metadata. The immutable receipt
therefore records `changes_requested`. The development record also discloses a
transient GEO endpoint-characterization exposure; no response was stored and no
outcome analysis was performed.

### 2026-07-25 — Structured no-storage appraisal proposal path completed

Implemented a purpose-built institutional-PDF appraisal proposal gate. It
re-fetches only an approved source, requires exact receipt byte count and SHA-256,
reconciles inventory and proposal identities, constrains derivative-summary sizes,
rejects long verbatim source sequences, and writes only a typed non-authoritative
proposal. No article bytes or extracted text are retained.

The gate produced batch 0005 for PMID 23907291. The proposal is `context_only`
because the paired genomic/pathology comparison is directly relevant but uses
cohort-level centering, a selected 94-patient cohort, exploratory treatment
subgroups, no declared multiplicity control, treatment crossover, and no external
validation. The founder-confirmation filename contract now supports `PMC`, `PMID`,
and `PPR` records, repairing the latent authorization failure for batch 0004.

### 2026-07-26 — Citation full-text access queue resolved

Closed the last citation-pass access check for PMID 20181526 without weakening
the evidence boundary. The official ScienceDirect page and Crossref record
declare the version of record CC BY 4.0; Unpaywall points only to the same
publisher PDF, Europe PMC has no repository copy, automated publisher PDF
delivery returns an access challenge, and the credential-free Elsevier
text-mining endpoint returns metadata only. The final decision therefore records
the article as access-restricted for governed appraisal despite its permissive
license. No access control was bypassed, no third-party copy was retained, and no
scientific conclusion was drawn from the abstract.

Reconciled citation progress is now three completed, 22 ready for appraisal,
four restricted, and zero awaiting full text. All 29 net-new citation-pass
inclusions have a terminal access route or a verified review source.

## Historical implementation log

### 2026-07-25 — Publisher access queue reduced to one unresolved record

Implemented an exact-allowlist institutional-PDF no-storage route with HTTPS
host/path validation, complete-PDF checks, in-memory parsing, exact title and DOI
verification, byte hashing, and a mechanically zero-storage receipt.

The public UNC Lineberger author copy for PMID 23907291 was verified at 518,968
bytes with SHA-256 `5ffda151…805a`; no article bytes were retained. Separate
decisions record its publisher copyright and prohibit durable corpus reuse.
Official publisher checks classified PMIDs 28069519, 30040052, and 31435878 as
access-restricted without appraisal or inference from abstracts. Reconciled
citation progress is three completed, 22 ready for appraisal, three restricted,
and one awaiting a reproducible CC BY full-text route.

### 2026-07-25 — medRxiv preprint access and appraisal packet verified

Implemented a source-specific medRxiv no-storage verifier with exact HTTPS host,
DOI-in-path, version, title, rights, and content checks. The verifier uses the
official `.full.txt` representation because repeated tests proved its checksum is
stable; dynamic HTML was explicitly rejected as an appraisal-binding artifact.

Version 2 of `PPR1259744` produced reproducible content SHA-256
`47b4a207…7576`, with 70,291 bytes reviewed in memory and zero article bytes
stored. A CC BY-NC durable-storage restriction is recorded. Batch 0004 proposes
the preprint as `supporting` analytical-bridging evidence while preserving its
preprint status, sponsor interest, proprietary data, and incomplete artifact
availability as limitations. Reconciled citation progress is three completed,
21 ready for appraisal, and five awaiting publisher resolution.

### 2026-07-25 — Eight PMC records cleared for no-storage appraisal

Implemented an official-PMC-only ephemeral review service. It enforces HTTPS host
and path allowlists, minimum complete-page size, exact PMID and DOI, bounded title
normalization, the page's canonical full-text URL, raw-byte hashing, and a receipt
that forbids durable storage and redistribution.

Eight complete PMC pages passed. Seven publisher-reserved, CC BY-NC, or CC
BY-NC-ND items received explicit durable-storage restrictions; `PMC10147771`
declares CC BY 4.0 but was reviewed ephemerally because repository XML was
unavailable. Citation progress now records 15 durable retrievals, eight read-only
reviews, three completed appraisals, 20 ready for appraisal, and six awaiting
publisher or preprint resolution.

### 2026-07-25 — Two citation identity failures repaired and retrieved

The official Europe PMC XML for `PMC7299291` and `PMC11265146` matched the
inventory PMCID, PMID, and DOI exactly; only Unicode dash typography differed in
the titles. A bounded normalizer now equates six dash code points while preserving
all lexical content and exact primary-identifier requirements.

Both articles carry CC BY 4.0. The pushed retrieval engine stored and independently
verified 120,129 and 134,490 bytes, respectively, in governed external object
storage. Aggregate receipts are in Git. Batch 0001's three derived locked
appraisals are now materialized by an exclusive checksum-verifying authorization
command. Reconciled progress is 15 durable full texts, three completed appraisals,
12 ready for appraisal, and 14 awaiting access.

### 2026-07-25 — Appraisal authorization generalized across batches

Replaced the batch-0001-only confirmation constraint with a batch-derived exact
statement for batches `0001` through `9999`. The contract now requires the packet
filename and statement to agree with the same four-digit batch number, rejects
duplicate proposal checksums, and the authorization service rejects cross-study
proposal substitution.

Real batch-0002 and batch-0003 packet/proposal bytes now pass authorization-readiness
tests without creating a founder decision or locked appraisal artifact. Exact
founder confirmation remains mandatory and independently scoped to each batch.

### 2026-07-25 — Citation appraisal batch 0003 frozen for review

Completed seven-domain proposals for all six remaining checksum-verified citation
full texts. Four are proposed as supporting evidence and two as context-only.
The batch covers early compact qRT-PCR classification, locked Prosigna development,
paired peri-surgical sampling, commercial-test approximation, paired
specimen-preparation effects, and real-world IHC/PAM50 discordance.

The packet binds six proposal checksums and requires the exact statement
`I confirm citation appraisal batch 0003 as written.` No founder decision,
completion-ledger change, scientific conclusion, novelty claim, or patient-level
recommendation was recorded. Batches 0002 and 0003 remain independently pending.

### 2026-07-25 — Citation appraisal batch 0002 frozen for review

Completed seven-domain appraisal proposals for four direct single-sample method
papers. Two are proposed as supporting evidence and two as context-only. The packet
retains platform failures, label circularity, absent uncertainty calibration,
incomplete external transport, and sparse performance reporting rather than
promoting algorithm availability into clinical evidence.

Packet SHA-256 `f45518a3…f92e2` binds all four proposal checksums. No founder
decision, ledger completion, scientific conclusion, novelty claim, or patient-level
recommendation was recorded.

### 2026-07-25 — Citation appraisal batch 0001 founder-authorized

Bound the founder's exact confirmation to packet SHA-256 `4704eba6…0516e` and
three immutable proposal checksums. A typed authorization service now fails closed
on altered packet bytes, altered proposals, missing records, identity changes,
non-exact language, undisclosed reviewer conflict, or absent founder authority.

The live citation ledger now records three completed `context_only` appraisals,
ten verified full texts ready for appraisal, and 16 unresolved access records.
The batch supports a bounded synthesis that PAM50 agreement depends on population,
specimen, platform, preprocessing, implementation, and ambiguity handling; it does
not establish NaS accuracy, novelty, clinical utility, or patient-level readiness.

### 2026-07-25 — Citation appraisal proposal boundary implemented

Implemented a typed, fail-closed appraisal-proposal contract that cannot record a
founder decision or be loaded as locked evidence. The first three checksum-verified
papers were extracted against all seven domains and frozen in a checksum-bound
founder packet.

The proposals expose a coherent but bounded pattern: reported agreement changes
substantially with population, platform, preprocessing, classifier implementation,
and ambiguity handling. All three are proposed as `context_only`; no scientific
conclusion, clinical claim, or progress-ledger completion was recorded.

### 2026-07-25 — Citation lawful-access inventory and repository pass completed

Implemented a typed access inventory, fail-closed batch repository assessor,
pending access-check queue, and citation appraisal-progress command. All 29 net-new
records received stable screening IDs.

The official Europe PMC full-text endpoint was queried for all 23 repository
candidates. Thirteen exact-identity articles carried approved CC BY licenses and
were stored outside Git with verified receipts. Ten stored nothing: five endpoint
404s, three licenses outside the approved durable-storage set, and two identity
mismatches. Queue `de76e254…46ad93` governs those ten plus six no-PMCID records.
Thirteen studies are ready for appraisal and 16 await access resolution. No
eligibility decision or scientific conclusion changed.

### 2026-07-25 — Evidence-cap amendment 0.2.5 activated

The founder approved the exact amendment text under SHA-256
`4aeb5ef4…d507`. The typed activation engine independently verified that file,
reconciliation receipt `6d7f34e3…f61d`, and external reconciliation object before
changing protocol state.

Activation `6769d900…ab2f33` replaces the arbitrary 30-record evidence cap with an
uncapped saturation inventory while preserving a maximum 30-study core synthesis.
The immutable queue covers all 32 pass-1 inclusions: 23 repository candidates, six
lawful-access checks, and three prior-appraisal reuses. That activation-time
snapshot recorded 62 eligible identities, 31 completed, two restricted, and 29
pending; subsequent lawful-access appraisal and immutable pass closure now
supersede those workflow counts. No screening decision, scientific conclusion,
molecular permission, or outcome permission changed.

### 2026-07-25 — Citation pass 1 founder ledger frozen and reconciled

The founder supplied the exact statement bound to both packet and appendix checksum
pairs. Immutable decision ledger `1ca4b716…281caf` records complete, unique coverage
of 4,495 candidates: 32 inclusions, 4,463 exclusions, zero unclear records, and zero
AI decisions. The external ledger checksum is `e9779f63…fefd`.

A new typed reconciliation engine independently reloads and verifies that ledger,
normalizes only PMID, PMCID, and DOI identifiers, and routes every inclusion without
changing its decision. Production reconciliation `0a6d4893…580b4` found 29 net-new
records, three exact prior-appraisal matches, and no match to the active 30-paper
inventory. Versioned appraisal histories resolve deterministically to the latest
locked appraisal. Evidence-cap amendment `0.2.5` was subsequently approved through
its separate founder decision.

### 2026-07-25 — Citation confirmation and cap-amendment paths prepared

Implemented the typed combined founder-confirmation service and final citation
decision-ledger receipt. Integration tests reproduce the two real packet appendices,
prove exact 4,495-record coverage, and verify the expected 32/4,463 disposition.
The service fails closed on absent exact authority, tampered packet bytes, mismatched
hashes, incomplete second-stage coverage, duplicates, or unclear records.

The founder confirmation template remains intentionally invalid while authorization
is absent. Draft amendment `0.2.5` proposes an uncapped saturation inventory and a
quality-selected core synthesis set so the 30-study target cannot suppress eligible
contradictory evidence. Neither artifact changes current governance.

### 2026-07-25 — Citation pass 1 unresolved set fully adjudicated

Implemented a versioned, policy-bound second-stage advisory workflow for all 256
records held by the first packet. Abstract review retained 17 direct assay,
classifier, platform, specimen, normalization, or implementation-comparison
records and recommended exclusion of 239 outcome, treatment, biomarker, taxonomy,
secondary, nonhuman, or otherwise indirect records.

The second packet has SHA-256 `ba8560a7…c1f29fe`; its complete appendix has
SHA-256 `1e41f1f1…56e9e81`. Mechanical combined coverage proves 4,495 unique
records exactly once, with 32 proposed includes, 4,463 proposed excludes, zero
unclear, and zero founder decisions. A single combined review statement now binds
both packet and appendix pairs.

### 2026-07-25 — Citation pass 1 founder packet frozen

Implemented a conservative abstract-informed advisory engine and checksum-bound
founder packet generator. Two pre-decision calibration reviews repaired outcome-
only routing and added explicit microarray vocabulary. Superseded external advisory
objects remain immutable; no recommendation became a decision.

The final packet proposes 15 includes and 4,224 exclusions and holds 256 records
for individual adjudication, including all 93 records without abstracts. Its
complete CSV appendix contains every title, identifier, rationale, confidence,
protocol reason, signal, and `founder_decision_recorded=false` flag.

### 2026-07-25 — Full citation metadata enrichment completed

Implemented transparent, zero-cost title prioritization and batched Europe PMC
metadata enrichment. The ranking writes no eligibility decision and retains every
candidate. Calibration occurred before screening and is versioned as
`citation-title-priority-1.0.1`.

The final ranking contains 80 direct-, 400 supporting-, and 4,015 context-priority
records. Ninety bounded official API requests matched all 4,495 identities and
returned 4,402 abstracts. The 93 abstract-unavailable records remain in the
screening inventory; none was excluded because an abstract was missing.

### 2026-07-25 — Citation pass 1 retrieved and prepared for screening

Implemented immutable backward-plus-forward citation retrieval from the official
Europe PMC endpoints and a separate verified screening-preparation boundary. The
pass covers all 30 eligible seeds, persists raw responses and normalized candidates
outside Git, and emits concise checksum-bound receipts.

Pass 1 contains 4,628 unique non-seed records from 981 backward and 4,639 forward
links. Exact PMID and normalized-title reconciliation found 42 records already
screened in the completed direct inventory and 91 duplicate candidate identities,
leaving 4,495 for advisory triage and founder screening. The preparation layer
records zero final decisions and draws no scientific conclusion.

### 2026-07-25 — Publisher-PDF evidence path and IEEE appraisal completed

Implemented a reusable CLI path for governed import of explicitly licensed
publisher PDFs without a PMCID. The service verifies PDF integrity, article title,
DOI, printed CC BY license, manifest identity, and object checksums before issuing
a receipt. The IEEE author manuscript was stored immutably and appraised.

Progress is now 28 of 30: 15 `supporting`, 13 `context_only`, zero anchor, and two
access-restricted records. The IEEE model is retained as context because its
modality-disjoint design cannot establish patient-level multimodal concordance,
external validation is not unchanged, and central reported metrics conflict.

### 2026-07-25 — All accessible evidence appraised

Completed the microarray-versus-NanoString, classifieR, and mFISHseq appraisals.
At this checkpoint, 27 records were complete: 15 `supporting`, 12 `context_only`,
and zero anchor records. Two sources were explicitly restricted, and the
confirmed-open IEEE paper remained for the next milestone.

The last batch prevents three overclaims. Cross-platform disagreement cannot be
attributed to the assay when specimen and preprocessing also differ; an integrated
interface does not establish predictive validity; and spatially guided tumor
enrichment plus consensus voting does not validate a classifier when development
and outcome interpretation share the same cohort.

### 2026-07-25 — Population transport and stable-reference scoring appraised

Completed the NHS PAM50, NanoString normalization/QC, and stable-gene scoring
appraisals. Progress is now 24 of 30: 15 `supporting`, nine `context_only`, and
zero anchor records.

The batch connects three layers of the future reliability pipeline. Cohort-dependent
centering changed 14% of NHS tumor calls; NanoString normalization agreed on 91%
of calls and localized many disagreements to low margins; stingscore demonstrates
that a fixed external reference can execute on one patient without a comparison
cohort. None independently calibrates PAM50 repeatability or a clinical abstention
threshold.

### 2026-07-25 — Cohort-adaptive classifier methods appraised

Completed three question-specific appraisals. The PLS/logistic classifier,
PCA-PAM50, and ssNMF subtype-purity studies are all `context_only`; progress is
now 21 of 30, with 13 supporting and eight context-only records.

The batch establishes that explicit Ambiguous/Unclassifiable states and continuous
subtype-purity scores are prior art. It also exposes the central methodological
problem: apparent performance can rise by excluding hard cases, changing thresholds
after validation, or adapting normalization and latent factors to the test cohort.
None supplies a frozen, independently calibrated patient-level reliability rule.

### 2026-07-25 — Pre-analytic and assay reproducibility appraised

Completed three additional appraisals. The paired-tissue contamination study and
the CLSI-guided Prosigna analytical validation are `supporting`; the cohort-adaptive
Han Chinese gene-set comparison is `context_only`. Progress is now 18 of 30.

The evidence separates three mechanisms that must not be collapsed: benign-tissue
contamination can systematically lower PAM50 risk, cohort-level centering can
change subtype calls, and the locked commercial workflow itself can be highly
repeatable across sites. Prosigna reported total SD 2.9 ROR units and 97% subtype
concordance, but omitting macrodissection produced ROR bias as large as -19 units.

## Current blockers

- Docker is not currently available in the development environment, so the
  Compose services have been syntax-validated but not started locally.
- Paid AI advisory screening is intentionally inactive under founder policy `1.0.2`;
  the active deterministic Phase 0 workflow requires no API credential.
- `NAS-BRCA-002` version `0.3.0` is proposed. Method specification `0.1.0` is
  nonexecuting until its exact artifacts, transforms, technical-error calibration,
  numerical tolerances, and thresholds are resolved. The complete evidence stopping
  rule and founder scientific/product, molecular/pathology, and statistical reviews
  are also required before selection.
- Revised search strategy `0.2.4`, its queue, prior-inventory reconciliation,
  founder screening, and all 28 accessible appraisals are complete. The citation-
  chain stopping rule remains incomplete.
- AIMS is identity-verified at the publisher but subscription-restricted. Its
  full text cannot be appraised unless the founder supplies lawful access; the
  evidence review must retain this limitation and cannot infer novelty from it.
- GSE96058 is approved only as a processed-data validation candidate. All 50
  historical PAM50 genes, receptor completeness, and primary-versus-technical-
  replicate linkage are verified. The cross-platform transformation, assay
  compatibility, and classifier validity remain unresolved.
- The Seagate volume currently reports approximately 4.2 TiB available. It is
  primary local storage, not an independent backup.
- NAS-BRCA-001 public release is blocked by pending founder results review, a
  failed S4 nonlinear-age sensitivity, nonconvergent S3, a material exposure PH
  violation, and Kaplan–Meier figure-layout failure.

## Durable decisions and boundaries

- `nas-website` and `NaS-Core` remain separate repositories.
- NaS Core begins as a modular monolith.
- OpenAI is a replaceable reasoning provider, not the NaS product or knowledge
  store.
- Numerical research results come from deterministic executed code.
- Survival analysis uses pinned, replaceable statistical libraries behind NaS
  typed result contracts; library output is not accepted until serialized,
  checksummed, and independently verified.
- Outcome-bearing runs are immutable. Post-result defect corrections require a
  written amendment, new algorithm version, new run ID, and retained provenance
  for both the original and replacement runs.
- Cohort construction is frozen before outcome modeling. An unexpected result
  cannot justify silently changing eligibility, normalization, or exclusions;
  any correction requires a preserved prior build and a new algorithm version.
- The first pilot is a reproduction of the association between pathologic
  stage and overall survival in TCGA-BRCA, not a clinical validation study.
- NaS research begins with an intended user and decision. Datasets, articles,
  models, and interesting patterns do not define a research program by
  themselves.
- Every approved research question receives a permanent study ID and canonical
  workspace. Multiple prespecified hypotheses may share one study; a material
  change in decision, population, principal exposure, primary outcome, or
  validation claim requires a new study.
- Study manifests define stable external artifact namespaces. Git contains
  definitions, deterministic code, synthetic tests, and review records; data
  snapshots, run artifacts, and frozen releases remain in external storage.
- The oncology program separates platform qualification, discovery, external
  validation, translation, and deployment claims.
- The qualification study ends in a pass, conditional pass, or fail judgment
  about Cortex; its hazard ratios and figures are not patient-level decision
  support or evidence of clinical utility.
- A decision-support study must define the user, choice, patient context,
  alternatives, outcome, evidence, uncertainty, validation path, abstention
  conditions, and real-world impact evaluation before translation.
- `NAS-BRCA-002` is a proposed discovery and external-validation study of PAM50
  classification stability in clinically HR-positive/HER2-negative disease. No
  implementation is assumed to be a universal gold standard, and the work cannot
  support patient-level testing or treatment claims.
- Phase 0 discovery artifacts may define searches, source requirements, falsification
  criteria, and no-go rules before question selection, but retrieval remains disabled
  until the founder explicitly authorizes the bounded audit.
- Novelty is an evidence-backed conclusion, not an assumption. NAS-BRCA-002 cannot
  claim novelty until the reproducible evidence matrix and novelty memo are reviewed.
- An external validation source must be independently assessed, registered, legally
  usable, sufficiently independent, and analytically compatible before it enters a
  preregistered validation plan.
- Public website publication must derive from an approved frozen research
  release. The version-of-record PDF, web edition, tables, figures, citations,
  and displayed numbers must agree and follow visible versioning and correction
  procedures.
- Study plans must be typed, governance-validated, reviewed with explicit
  provenance, and locked before outcome-bearing data ingestion.
- A research question cannot become selected or literature-ready until every
  gate-required review is approved. Founder self-review may authorize the
  current internal gate when conflicts and knowledge limits are disclosed.
- AI-assisted review is advisory: it cannot be gate-required, approve a study,
  authorize ingestion, or be represented as human review.
- AI literature recommendations remain separate from the append-only founder
  decision ledger. NAS-BRCA-002 prohibits autonomous exclusions; calibration and
  locked routing rules are required before AI output may prioritize human review.
- External expert feedback is recorded separately from founder self-review.
  Public NaS reports remain labeled founder-led, internally reviewed, and not
  peer reviewed until a journal completes formal peer review.
- Bibliographic API exports and normalized records remain in external object
  storage. Git may contain only aggregate receipts, screening decisions, and
  concise evidence extraction; copyrighted abstracts and full text are not
  redistributed, embedded, or used for model training without item-level rights.
- Lawfully viewable articles without durable-storage authorization may be appraised
  only through an ephemeral read-only receipt. The content is not retained; the
  receipt records source identity, access basis, rights observation, checksum, and
  verification state, and never grants redistribution rights.
- GDC ingestion is fail-closed unless the plan is `preregistered`; every
  snapshot records the exact request, API provenance, explicitly supplied data
  release, raw response checksums, and immutable object locations.
- Public/open and explicitly approved licensed data are the only v0 data
  classes; controlled data and PHI remain prohibited.
- The data-source landscape is an informational candidate catalog, not an
  authorization list. A project selects the minimum necessary sources for its
  approved question, and only entries approved in `data/source-registry.yaml`
  may be ingested.
- Data confined to a provider's secure workspace must remain there unless its
  agreement explicitly permits export; it cannot automatically be copied to
  the Seagate data root.
- Raw datasets, credentials, embeddings, and generated research artifacts do
  not belong in Git.
- Local v0 snapshots use the path-safe filesystem object-store adapter rooted at
  the marker-validated Seagate `NAS_DATA_ROOT`; S3 remains a replaceable future
  deployment backend.
- Public/open v0 data and research artifacts use the configurable external
  `NAS_DATA_ROOT`; storage layout integrity is marker-validated before use.

## Update procedure

For every completed implementation:

1. Verify the implementation against its definition of done.
2. Move the completed current focus into **Recently completed**.
3. Keep the five most recent completion entries and remove older ones.
4. Promote the first unfinished queue item into **Current focus**.
5. Rewrite its definition of done so it is objectively testable.
6. Add newly discovered future work in dependency order.
7. Update blockers and durable decisions.
8. Update the date and commit the status change with the implementation.
