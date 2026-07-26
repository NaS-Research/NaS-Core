# Founder Citation Appraisal Batch 0002

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents four AI-assisted full-text appraisal proposals focused on
single-sample scoring and classifier construction. It does not contain a founder
decision, locked appraisal, scientific conclusion, novelty finding, or clinical
recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC10848444-v1.0.0.yaml` | `6f262f2ce657a955726d6a0a8d99b5a2c81decfe75f13024acbc5cb05e32d23d` | `context_only` |
| `PMC6219008-v1.0.0.yaml` | `58b8caa3091953606f7eb1c5884c19742f4797ff7e3a72fbbe57f3583b584c01` | `supporting` |
| `PMC8479681-v1.0.0.yaml` | `44f729d21a9ba282d7d56f3c8ca6b8bf3385a84195dc2dda0fe6cd0b199a443f` | `context_only` |
| `PMC8796360-v1.0.0.yaml` | `6b8e10e786475308155c56b50fe5792d38ed8ddf342ff32cdf4b33122738f05c` | `supporting` |

The files are stored under `citation-appraisal-proposals/batch-0002/`. All source
full texts were exact-identity, item-license, and checksum verified before
appraisal. Full-text XML remains in governed object storage outside Git.

## Founder review summary

### PMC6219008 — singscore

Reported observations:

- Implements a genuinely one-sample rank score with theoretical within-sample
  normalization and no comparison cohort.
- Tested stability in 500 paired TCGA breast-tumor microarray/RNA-seq profiles.
- Cohort-dependent GSVA, z-score, PLAGE, and normalized ssGSEA became less stable
  in small datasets; unnormalized ssGSEA and singscore remained stable.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Low |
| Reference comparator | Some concerns |
| Analysis and statistics | Some concerns |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Low |

Review position: retain as `supporting`. It strongly establishes the feasibility
and auditability of cohort-independent within-sample scoring, but it evaluates
gene-set activity rather than PAM50 subtype correctness or patient utility.

### PMC8796360 — rule-based versus centroid predictors

Reported observations:

- Directly compared raw/centered centroids, AIMS, k-TSP, and a rule-based random
  forest over breast, bladder, lung, and pan-cancer datasets.
- SCAN-B breast prediction accuracy was `0.78–0.85` for k-TSP and `0.86–0.89`
  for the rule-based random forest in a 50/50 split.
- An older unrepresented microarray platform caused substantial external failures;
  mixed-platform training improved—but did not guarantee—transport.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Low |
| Reference comparator | Some concerns |
| Analysis and statistics | Some concerns |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Low |

Review position: retain as `supporting`. It is direct evidence that single-sample
execution does not eliminate platform risk and that compatibility must be verified
for each new measurement context. Reference labels remain technical targets, and
the breast validation is not an independent cohort.

### PMC8479681 — multiclassPairs package article

Reported observations:

- Provides public random-forest and one-versus-rest k-TSP workflows.
- Supports platform-wise selection, class imbalance, missing-gene imputation, and
  explicit tie flags.
- States superior breast-cancer performance over Rgtsp but omits main-text metric,
  split, label-provenance, and external-validation detail.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Unclear |
| Specimen and measurement | Unclear |
| Classifier implementation | Low |
| Reference comparator | Unclear |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. The package is useful implementation
prior art, but this short software paper cannot support a central performance or
transport claim.

### PMC10848444 — rank-based tree ensembles

Reported observations:

- Compared random rank forests and boosting with k-TSP and nearest-template
  prediction across 12 public cancer datasets.
- Repeated class-balanced 70/15/15 train/validation/test splits 50 times.
- Reported aggregate TNBC accuracy of `0.91` and `0.90` for boosting and random
  rank forest, but did not report the claimed microarray-to-RNA-seq transport by
  train/test direction.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Some concerns |
| Reference comparator | Some concerns |
| Analysis and statistics | Some concerns |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. It is relevant method prior art, but
aggregate accuracy does not verify unchanged cross-platform transport, calibrated
uncertainty, or a fixed breast-cancer artifact.

## Cross-study interpretation boundary

The batch narrows the candidate NaS contribution. Cohort-independent scoring,
gene-pair rules, multiclass single-sample prediction, rank-tree ensembles,
probability-like outputs, tie flags, and cross-platform training already exist.
NaS cannot claim those components alone as novel. A defensible contribution still
requires a fixed artifact, independently calibrated technical perturbations,
predeclared reliability/abstention thresholds, unchanged external transport, and
transparent failure accounting.

The papers do **not** establish that a NaS implementation is accurate, clinically
useful, or ready for patient-level decisions.

## Exact founder confirmation

If every proposal is acceptable without modification, reply exactly:

`I confirm citation appraisal batch 0002 as written.`

Any requested edit creates a new packet version and new checksums. Exact
confirmation will authorize derivation of four locked appraisals and reconciliation
of the progress ledger.
