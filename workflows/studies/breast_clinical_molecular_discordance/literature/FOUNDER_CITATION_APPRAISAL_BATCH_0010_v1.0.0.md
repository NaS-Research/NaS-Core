# Founder Citation Appraisal Batch 0010

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents five AI-assisted, checksum-bound full-text appraisal
proposals created from citation pass 3. Two additional founder-included records
are documented as access restricted and are not appraised from abstracts. This
packet contains no founder decision, locked appraisal, scientific conclusion,
novelty finding, causal treatment claim, or clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC12764145-v1.0.0.yaml` | `babe487f294fd817865b32c805fe9d5b92aa37de6236a7f6d771f4d40c2cdb44` | `context_only` |
| `PMC3273349-v1.0.0.yaml` | `a9ffc2f079f20c53eb1466eca1b75c4a06ccaa8407b5757f9443f57e947585a1` | `context_only` |
| `PMC3733243-v1.0.0.yaml` | `40ec1ef98400c3c99a25be45102c0cff2f481652d2742a3abe1448e5bc7a5e10` | `context_only` |
| `PMC7746197-v1.0.0.yaml` | `02f67b940a3c8182512982927fa592246082cf52764538df00eac19d9bc6b1ce` | `context_only` |
| `PMC7873419-v1.0.0.yaml` | `7bbedad60858dd07289a482df450368192c3410deff9b1f636fda02161206a40` | `context_only` |

The proposals are stored under `citation-appraisal-proposals/batch-0010/`.
Every proposal passed the typed non-authoritative schema. Both no-storage
proposals were additionally re-verified against canonical official PMC OAI
article XML, including identity, content checksum, bounded derivative narrative,
and verbatim-leakage checks. Zero bytes from those two articles were retained.

## Source reconciliation

| Article | Source representation | Canonical bytes | Content SHA-256 | Receipt SHA-256 |
|---|---|---:|---|---|
| `PMC3273349` | licensed Europe PMC article XML | 124,434 | `f1350e6a7eafa5780b69251834dc5b80aebe557a16117d71c71878654541e552` | `9d2e1af209d208a184d5b7bc128db40d20e47ff9ccacc4e88bb64896495e58f7` |
| `PMC7746197` | licensed Europe PMC article XML | 160,442 | `7b51ea838f5ec71a0b6795c0c86f2e8b5ad572c69b7a773f7b6d22341f9ecb9f` | `9fe1aaf22d0220b5b042e558300914cee3bb0b81ed5e7135f0da782b3dc397b8` |
| `PMC7873419` | licensed Europe PMC article XML | 130,160 | `66b2036b2daea46845162daff36deb1c956bef59d2c59073fb077a9225cf2890` | `54eb9d3c4ef2b9b36c85f8fe9561a3988ac5218de336e2d63fd44dd164215f86` |
| `PMC3733243` | canonical PMC OAI article XML, ephemeral | 72,783 | `89ee9f6da46ff3068c7d0cbef35c5368e8729b407a47b6e85acf97faba654232` | `41b5b9eca79096c7db935cb351122e121067166b4043debef0a0c5192a2c5db1` |
| `PMC12764145` | canonical PMC OAI article XML, ephemeral | 93,417 | `c26e305c216896ee459293540061fc51bca77205312ff128209d2f11a045fc4c` | `79eec5b9350fc0c81fa0ef70816ce5aee367bdf456fb3c95a4cb9bd68628bf4b` |

The first three articles are retained only in governed external object storage
under verified CC BY 4.0 licenses. `PMC3733243` is an author manuscript available
for lawful read-only review without a redistribution license. `PMC12764145` is
CC BY-NC-ND 4.0 and was also reviewed without durable article retention.

## Founder review summary

### PMC3273349 — preserved and frozen glioma expression

Reported observations:

- Compares 55 paired fresh-frozen and paraffin glioma specimens, including old,
  degraded archival material.
- Reports broad recovery of group-level differential expression and many
  historical cluster assignments after feature filtering.
- Uses different assay platforms and assay years for the two preservation states.

Review position: retain as `context_only`. The paired design is useful
preanalytic evidence, but preservation, platform, and year are confounded; the
small single-source glioma series has no independent validation or clinical-use
assessment.

### PMC3733243 — ovarian signature transport to paraffin tissue

Reported observations:

- Includes 30 paired ovarian frozen and paraffin samples and evaluates survival
  and subtype signatures.
- Reports quality failures and batch effects rather than presenting only
  successful specimens.
- Learns cross-platform weights from the paired data before evaluating transport.

Review position: retain as `context_only`. It shows that preservation and
platform transitions require explicit validation, but adaptation and assessment
are not independently separated and the retrospective ovarian evidence cannot
validate the NaS breast classifier.

### PMC7873419 — image-based colorectal molecular subtype prediction

Reported observations:

- Trains on one retrospective colorectal collection and tests in two external
  cohorts.
- Uses domain-adversarial deep learning to reduce image-source effects.
- Predicts spatial labels and labels for tumors that molecular algorithms did
  not classify.

Review position: retain as `context_only`. It is meaningful external
prediction-model prior art, but its comparator is an imperfect transcriptomic
surrogate, individual calibration and clinical utility are absent, and image
classification does not validate a breast expression method.

### PMC7746197 — multiregional colorectal heterogeneity

Reported observations:

- Uses multiple spatial biopsies and three colorectal transcriptomic
  classification systems.
- Reports location-dependent within-tumor discordance and protein heterogeneity.
- The central multiregional RNA analysis contains fourteen tumors.

Review position: retain as `context_only`. It supports the risk that one biopsy
may not represent the whole tumor, but the exploratory small-sample colorectal
study lacks an independent multiregional validation cohort.

### PMC12764145 — robust intrinsic colorectal single-sample classifier

Reported observations:

- Defines a 201-gene single-sample method with synthetic centroids, explicit
  quality filtering, and an open R implementation.
- Tests multiple public cohorts and simulated noise, missing genes, and mixture
  perturbations.
- Evaluates agreement against subtype references reconstructed from expression
  data rather than independent biological truth.

Review position: retain as `context_only`. This is strong recent methodological
prior art for single-sample classification and abstention, but simulated
perturbations do not calibrate empirical assay error and retrospective colorectal
results do not establish breast-method or treatment utility.

## Access-restricted founder inclusions

| Record | Reason | Decision SHA-256 |
|---|---|---|
| PMID `31678167` | Official Elsevier routes expose metadata but no credential-free, checksum-verifiable article body | `ea5c4ead240224bcc8637006b755a2ec1d6eb79ba35ac6ef70f861ec6a5d5973` |
| PMID `35982221` | Official Nature full text requires subscription, purchase, or institutional access | `3a1036746f66433f38d725ea652515407977cf67bf904a668a854f86c5071f0e` |

No access control was bypassed, no third-party copy was retained, and no
abstract-only appraisal was substituted.

## Decision requested

Confirming this packet will convert the five proposals into founder-authorized,
AI-assisted locked appraisals. It will not make them scientific conclusions or
clinical recommendations. The two access-restricted inclusions remain formally
accounted for without an evidence role.

Exact confirmation statement:

`I confirm citation appraisal batch 0010 as written.`
