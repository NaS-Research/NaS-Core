# Founder Citation Appraisal Batch 0009

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents five AI-assisted, checksum-bound full-text appraisal
proposals created from citation pass 2. Four additional founder-included records
are documented as access restricted and are not appraised from abstracts. This
packet contains no founder decision, locked appraisal, scientific conclusion,
novelty finding, causal treatment claim, or clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC11524322-v1.0.0.yaml` | `9dc05ba2384ceb29dfbc2bf206692fa37eb0ab88777594e593c3959c317556c8` | `context_only` |
| `PMC2990751-v1.0.0.yaml` | `a23f871a12e80ced6230caf21278a86385ca9a8fd53c848491396016adcf9e83` | `context_only` |
| `PMC3037966-v1.0.0.yaml` | `b14cc2bce37c322eb3125144a899715477dc444f4e4191720a685060f7c8eb75` | `context_only` |
| `PMC9378834-v1.0.0.yaml` | `589fc41799c75f43e6b3ff61df7e9ecc6ddf49ce9155189de1279a0e1bd9280a` | `context_only` |
| `PPR723583-v1.0.0.yaml` | `5dec16d48290e9824dfce46a6bf885ba02cb9fc18eabdb0c5f811a881e087cef` | `context_only` |

The proposals are stored under `citation-appraisal-proposals/batch-0009/`.
Every proposal was re-verified against its exact official source receipt.
Validation enforces source identity, source checksum, bounded derivative
narrative, and rejection of copied source sequences of twelve words or more.
Zero article bytes were retained in Git or the durable research corpus.

## Source reconciliation

| Article | Source representation | Canonical bytes | Content SHA-256 | Receipt SHA-256 |
|---|---|---:|---|---|
| `PMC2990751` | canonical PMC OAI article XML | 95,916 | `c442e380aaf798bed1465f42aee9004afdf3e60bc2d9afc9b018cf41d4ab065e` | `7f649b5b2bfbe32bd6adea39d80092706c714c6c32bba912df6ebcb3259ef8a4` |
| `PMC3037966` | canonical PMC OAI article XML | 167,121 | `3a6cd17a156109c96a25f4a534b5562e09f527334207b0c95b03fb8dbdc77857` | `f72d1e332185ce75fbf5eddac0da817f036b59b5ce4f395ae2c2c2277f2c552f` |
| `PMC9378834` | canonical PMC OAI article XML | 118,266 | `3e2018b49d75102d08b406a869b8e3b803ee57bab6de22458566d2ba92ffba85` | `5b76b4e3272cd5d7714b32fe692084df34a4343dcfa220a2e0bcd30e923a12e6` |
| `PMC11524322` | canonical PMC HTML | 41,131 | `4cb21562b2db0eb37df34012e057fdb060770d9932b4617643953760512287b4` | `67d75658e2f746d0927395b6557f7e33a8147bb97c785c51e717b0f2f1af0c06` |
| `PPR723583` | canonical Research Square HTML | 65,444 | `e016fae9277b87b575fc7793138b6d42c60988ab8ddf16aabfed49b9009e8c6d` | `4ba2872a8a87cd5e924ca163e2c90c8e84a406e030ac386c571b3298f49e8927` |

The PMC HTML fallback initially detected a dynamic-wrapper checksum change and
failed closed. Its receipt was replaced with the stable canonical visible-text
representation only after the canonicalization implementation and tests were
committed.

## Founder review summary

### PMC2990751 — nearest template prediction

Reported observations:

- Defines a patient-independent template classifier with a permutation-derived
  confidence value for each sample.
- Exercises binary, multiclass, cross-platform, and cross-species tasks.
- Uses three independent breast cohorts but evaluates breast subtype agreement
  against an earlier predictor rather than independent biological truth.

Review position: retain as `context_only`. This is strong algorithmic prior art
for single-sample classification and abstention, but its heterogeneous benchmark
demonstrations do not validate breast-subtype correctness or treatment utility.

### PMC3037966 — matched paraffin and frozen breast tissue

Reported observations:

- Compares paired paraffin and frozen tissue from twenty evaluable breast tumors.
- Includes pathology review, tumor-content thresholds, biological replicates,
  technical replicates, and several established expression signatures.
- Reports strong within-protocol reproducibility and broadly similar signature
  outputs after preservation-specific normalization.

Review position: retain as `context_only`. The paired design directly informs
preanalytic robustness, but the small single-center sample, recent blocks,
legacy DASL platform, exploratory analyses, and commercial assay interests
prevent a stronger role.

### PMC9378834 — ovarian serum miRNA pair classifiers

Reported observations:

- Develops within-sample relative-order classifiers in large public serum
  microarray datasets.
- Tests a selected rule in held-out and separate GEO data and separately examines
  ovarian-versus-other-cancer discrimination.
- Uses Japanese cohorts on the same assay platform and computes predictive values
  in artificial case-control mixtures.

Review position: retain as `context_only`. It supports the engineering value of
rank-pair rules but has important spectrum, prevalence, platform, population,
model-selection, and prospective-validation limitations.

### PMC11524322 — rapid PurIST analytical validation

Reported observations:

- Bridges the fixed pancreatic PurIST concept from RNA sequencing to a targeted
  NanoString workflow in 74 archived tumors.
- Includes large specimens, core biopsies, separate-day duplicates, internal
  controls, external controls, and detailed investigation of two discordant calls.
- Reports high cross-platform agreement and a three-day laboratory workflow while
  stating that clinical-outcome validation remains underway.

Review position: retain as `context_only`. This is useful analytical-validation
prior art, but both platforms use the same classifier, the cohort and laboratory
are single-center, patent interests exist, and patient benefit is not established.

### PPR723583 — multiregional colorectal transcriptomics

Reported observations:

- Connects 1,093 primary and metastatic samples from 692 patients with
  multiregional heterogeneity, molecular classifications, and survival analyses.
- Reports frequent within-tumor CMS discordance, data-derived low-heterogeneity
  features, novel congruent classes, and phenotype changes between primary and
  metastatic samples.
- Uses extensive model checks and public data accessions, but novel class
  construction and evaluation overlap within one institutional series.

Review position: retain as `context_only`. The study is highly relevant to the
claim that a single biopsy may not fully represent tumor state, but it is
indirect colorectal evidence, its novel classifier is not externally locked and
validated, and this source is a non-peer-reviewed preprint.

## Access-restricted founder inclusions

The following records remain inclusions but cannot receive full-text quality
appraisal from the available governed routes:

| Record | Reason | Decision SHA-256 |
|---|---|---|
| PMID `28825136` | Springer article requires purchase or institutional access | `deabbb2b79970de4bed16de6198adad01bbc54e26c06bcb0ee993912e8be4357` |
| PMID `31812633` | Elsevier version is not openly licensed and its API requires credentials | `cc418689299a80f0719f7dbf355d82a94ebd04ccb63347ffc282c734cdc796e4` |
| PMID `39326668` | CC BY version exists, but official checksum-verifiable delivery requires credentials or returns an access challenge | `22de7efa8432ab2857d77a5d5548ee18a6cc5a31b7c73421692123be3527eaff` |
| PMID `41936844` | CC BY version exists, but official checksum-verifiable delivery requires credentials or returns an access challenge | `e960a69eadd75654dc9507c775c33ab39fe1387018076e3af0dbbfb89d228e7b` |

No abstract-only appraisal was substituted. These records can be reopened later
if the founder supplies lawful institutional access or an approved publisher API
credential.

## Decision requested

Confirming this packet will convert the five proposals into founder-authorized,
AI-assisted locked appraisals. It will not make them scientific conclusions or
clinical recommendations. The four access-restricted inclusions remain formally
accounted for without an evidence role.

Exact confirmation statement:

`I confirm citation appraisal batch 0009 as written.`

