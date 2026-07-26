# Founder Citation Appraisal Batch 0008

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents five AI-assisted, checksum-bound full-text appraisal
proposals and one checksum-bound publication-version link proposal. The
appraisals cover IHC/PAM50 agreement, rank-pair single-sample classification,
cross-cohort classifier transport, cross-platform normalization, and spatially
informed breast-cancer profiling. It does not contain a founder decision, locked
appraisal, scientific conclusion, novelty finding, causal treatment claim, or
clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC11265146-v1.0.0.yaml` | `30202c4290f0c40c8372f326249751f92f218cf05d7700c11df3b27ece685fd4` | `context_only` |
| `PMC11696812-v1.0.0.yaml` | `391eb32e0ad4992383d32efa0851ee0033a2626382fb999ee8ea94d038c5bf8a` | `context_only` |
| `PMC4779705-v1.0.0.yaml` | `96c7e010209ad01709e8bd16923318995d1e569e5c3b3b52e014c087fd38a10c` | `context_only` |
| `PMC6942634-v1.0.0.yaml` | `078148c946c1b8673822fcf865ace3f0d5b36b41b829f8e53dc558f14a4115d8` | `context_only` |
| `PMC7299291-v1.0.0.yaml` | `15e7a823fdc0c06485678e983d373cdf4dddaefbcf74bc052cc1bfcdfa11ba4b` | `context_only` |

The proposals are stored under `citation-appraisal-proposals/batch-0008/`.

## Immutable publication-version proposal

| Proposed relationship | Proposal SHA-256 | Effect after confirmation |
|---|---|---|
| `PMC10723508` `preprint_of` `PMC11696812` | `009718e17fbf432e5d085dcd71a77301e788f9e84bf77eec5b9295856b187d68` | Preserve both reports; cite the version of record and count the pair once |

The proposal is stored under
`citation-version-link-proposals/batch-0008/PMC10723508-to-PMC11696812-v1.0.0.yaml`.
It is non-authoritative and mechanically cannot enter synthesis reconciliation
without this packet's exact founder confirmation.

Three articles were re-fetched through official PMC OAI, reduced to their
canonical JATS article subtree, identity-checked, and verified against immutable
receipts. Proposal validation constrained derivative narrative length, rejected
copied source sequences of 12 words or more, and retained zero article bytes.

| Article | Canonical bytes | Content SHA-256 | Receipt SHA-256 |
|---|---:|---|---|
| `PMC4779705` | 154,310 | `c4799ecf859a94dc7230ccc37eec5759d85cd8da0dd7ca058272def5bd962d9f` | `83ae21f53f809811dc85ccf2311fe7365f1f1655e5c515a72a1790c7ba1b3f18` |
| `PMC6942634` | 100,049 | `220610032adfa252093635223e9e0e2395ceadf704a1b086a03e58f02ee1e2cf` | `4381b2ea5997d40153cbe9cd14cfef0286dfaaebb369b12c8fbe806d2d02e0b2` |
| `PMC11696812` | 253,781 | `5b5e30f693880dfcaf0efb16444bf5807fc5a7f42d45dc68a9f334ed693e07a0` | `24643e2655373bef89a73cc8b00bbab4b02849d178452fc3f1fce329b1a4bf8e` |

Two CC BY 4.0 articles were appraised from the already registered external object
store. Their raw source bytes remain outside Git and were independently
checksum-verified before appraisal.

| Article | Stored bytes | Content SHA-256 | Retrieval receipt SHA-256 |
|---|---:|---|---|
| `PMC7299291` | 120,129 | `b7c5ee0550a0f8597a28786f2298bd97349cb8671cfb4c66b1d4fbdf48c69ec7` | `f406197c9c451c12b844a2300cc80ac503f4f94a484448babdc9cb2d4fd0b644` |
| `PMC11265146` | 134,490 | `542412c6ba9b8253f799c9b8e1cecdd959536721cc8e9f26e060e0e408cdd425` | `a63b485bf6c68d79bbf8e6529e202995e34265aedc9e5858360e31d6fe17bc0d` |

## Founder review summary

### PMC4779705 — three-biomarker IHC in AMBER

Reported observations:

- Included 1,920 archival cases from three epidemiologic cohorts and compared
  RNA-based PAM50 with IHC surrogates in a selected 447-case subset.
- Used centralized tissue-microarray staining, automated digital scoring,
  cellularity exclusions, and alternative core-to-case collapsing rules.
- Found that triple-negative IHC identified basal-like tumors substantially better
  than the three-marker panel separated Luminal A, Luminal B, or HER2-enriched
  tumors.
- Showed that ER/PR positivity thresholds and tissue characteristics materially
  change agreement.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | High |
| Reference comparator | High |
| Analysis and statistics | Some concerns |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. This is direct evidence that routine
IHC surrogates are not interchangeable with PAM50, especially at Luminal and
HER2-enriched boundaries. PAM50 remains a comparator rather than biological
truth, the RNA subset is selected, several rules were explored, and no frozen
patient-level reliability or treatment rule was validated.

### PMC6942634 — PurIST pancreatic single-sample classifier

Reported observations:

- Uses eight fixed within-patient gene-pair comparisons, published coefficients,
  a basal-like probability, and a fixed `0.5` decision threshold.
- Evaluates multiple independent datasets and platforms without receiving-cohort
  normalization.
- Reports internal leave-one-out error of `3.1%`, a pooled validation AUC of
  `0.993`, and reduced accuracy among lower-confidence calls.
- Tests matched bulk/FNA specimens and a platform-specific NanoString variant,
  but treatment-response findings remain retrospective.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Low |
| Reference comparator | High |
| Analysis and statistics | Some concerns |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. PurIST is strong engineering prior art
for patient-independent rank-based prediction and confidence reporting. It is
indirect pancreatic-cancer evidence, and its clustering-derived target labels are
not independent biological truth. It cannot validate breast PAM50 correctness or
patient treatment benefit.

### PMC7299291 — cross-platform lung single-sample predictors

Reported observations:

- Uses 19 studies containing 3,213 unique lung-cancer samples across RNA
  sequencing and several microarray platforms.
- Assigns entire cohorts to training or test sets and compares open kTSP and AIMS
  within-sample classifiers.
- Achieves strong performance for the biologically distinct histology task, but
  molecular-subtype balanced accuracy ranges broadly across external cohorts.
- Finds that gene-rule stability is weaker where the underlying expression
  boundary behaves more like a continuum.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Some concerns |
| Reference comparator | High |
| Analysis and statistics | Some concerns |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Low |

Review position: retain as `context_only`. The work is valuable evidence that
single-sample rules can cross platforms while still becoming unstable for a
difficult molecular boundary. The lung endpoint is indirect, its molecular target
is reconstructed through cohort-level centering, and it lacks calibrated
uncertainty or clinical utility.

### PMC11265146 — feature-specific cross-platform normalization

Reported observations:

- Uses paired Agilent and RNA-sequencing measurements from the same 431 TCGA-BRCA
  and 187 TCGA-COAD patients.
- Tests microarray-to-RNA-seq and RNA-seq-to-microarray transfer with identical
  nested cross-validation folds.
- Compares feature-specific quantile normalization and mean-variance normalization
  using balanced accuracy, kappa, and expression reconstruction error.
- Reports that normalization can recover within-platform classification
  performance under favorable settings, while warning that results depend on the
  classification problem and matching gene distributions.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | High |
| Reference comparator | High |
| Analysis and statistics | Low |
| Validation and transportability | High |
| Reporting and reproducibility | Low |

Review position: retain as `context_only`. The paired-patient design is unusually
clean evidence about platform effects and is directly relevant to TCGA-BRCA. The
study trains generic learners against existing PAM50 labels rather than executing
a locked PAM50 classifier, and its distribution matching is not patient
independent.

### PMC11696812 — peer-reviewed mFISHseq version of record

Reported observations:

- Develops a spatial RNA-FISH, laser-capture microdissection, and RNA-sequencing
  workflow in 1,082 archived specimens, with 1,013 invasive tumors used in most
  analyses.
- Reports discordance across IHC, mFISHseq, PAM50, and AIMS and uses a majority
  consensus to reassign subtypes.
- Adds external METABRIC and TCGA analyses plus a 48-patient research-use
  deployment.
- Develops a 19-feature T-DM1 response model from only 52 treated patients and
  states that prospective validation is needed.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | High |
| Reference comparator | High |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. Peer review and external analyses make
this the canonical report to cite, but they do not remove adaptive development,
correlated-comparator, treatment-model, or commercial reproducibility concerns.

## Publication-version boundary

`PMC11696812` is the peer-reviewed version of record for the study previously
appraised as preprint `PMC10723508`:

- preprint DOI: `10.1101/2023.12.05.23299341`;
- version-of-record DOI: `10.1038/s41467-024-55583-2`;
- same 1,082-specimen development cohort;
- same mFISHseq platform, 293-gene classifier, consensus framework, and core
  treatment-response analyses.

If this packet is confirmed, the peer-reviewed paper will replace the preprint as
the canonical citation in later synthesis. The preprint remains preserved as
provenance, but the pair must count as one study and cannot be treated as
replication. The founder-authorized link will be stored separately from both
appraisals; it will not silently erase or rewrite the earlier appraisal.

## Cross-study interpretation boundary

These reports jointly support four bounded propositions:

1. A fixed within-sample rank-pair classifier can avoid receiving-cohort
   normalization and can expose a useful confidence gradient.
2. Cross-platform portability is achievable under controlled conditions but
   depends on the endpoint, shared features, and normalization design.
3. Molecular-subtype disagreement increases near continuous or weakly separated
   biological boundaries.
4. IHC, PAM50, and other expression classifiers are comparators, not independent
   truth sources; consensus voting does not create truth.

They do not validate a NaS classifier, establish a correct subtype for a
discordant patient, prove prospective treatment benefit, establish novelty, or
authorize molecular-data execution.

## Founder decision

To authorize the five exact appraisals and the exact publication-version link,
reply with:

`I confirm citation appraisal batch 0008 as written.`

Any edit to the packet or proposal changes its checksum and requires a new
version and a new exact confirmation.
