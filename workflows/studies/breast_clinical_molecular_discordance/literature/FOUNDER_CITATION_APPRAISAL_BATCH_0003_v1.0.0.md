# Founder Citation Appraisal Batch 0003

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents six AI-assisted full-text appraisal proposals focused on
PAM50 development, specimen effects, technical approximation, and real-world
classifier discordance. It does not contain a founder decision, locked appraisal,
scientific conclusion, novelty finding, or clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC10771357-v1.0.0.yaml` | `458a8c5d2118795b44bea7657167d500757ef0463439c789f01ee8587bd3f1c5` | `context_only` |
| `PMC1557722-v1.0.0.yaml` | `7120eb1c68876306c1819ab3035d423020b7ddf128cc8abfae92debb492816a8` | `context_only` |
| `PMC4546262-v1.0.0.yaml` | `862dce42b6452db123e7df5706b157e4c7208e69b9a862b5217b7b6e220cab0d` | `supporting` |
| `PMC4818440-v1.0.0.yaml` | `9e3aea1758e8d3fabc68b6f3bf314b732a38854b1edc8b61e13b39bfb1928488` | `supporting` |
| `PMC7470374-v1.0.0.yaml` | `11ef4a0667c04194c3185e1a04cc069a2b27e18123b50446688932aab3d56107` | `supporting` |
| `PMC8657125-v1.0.0.yaml` | `23a6a36502300422ee858229ee9eda07229f7d79a18b7cd955dafafde9d3ca83` | `supporting` |

The files are stored under `citation-appraisal-proposals/batch-0003/`. Every
source full text passed exact article-identity, item-license, and checksum
verification before appraisal. Full-text XML remains in governed object storage
outside Git.

## Founder review summary

### PMC1557722 — early compact qRT-PCR classifier

Reported observations:

- Compared a 53-gene qRT-PCR assay with paired microarray measurements.
- Reported 93% cross-platform subtype concordance.
- Used hierarchical clustering and distance-weighted discrimination, making the
  classification cohort dependent.
- Explored recurrence associations in a small, short-follow-up historical series.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Low |
| Classifier implementation | High |
| Reference comparator | Some concerns |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. It is useful historical evidence that
a compact panel can retain subtype signal across paired platforms, but it cannot
validate a fixed, independently transported single-patient artifact.

### PMC4546262 — Prosigna development and verification

Reported observations:

- Trained FFPE subtype centroids on 514 cases, developed ROR in 304 untreated
  cases, and verified the locked model in an independent 232-case tamoxifen cohort.
- Specifies the nCounter controls, fixed training transforms, centroids,
  proliferation score, tumor-size term, and 0–100 ROR calculation.
- Reported independent recurrence associations but sparse Basal-like verification.
- Contains material inventor, consultant, employee, and shareholder disclosures.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Low |
| Classifier implementation | Low |
| Reference comparator | Some concerns |
| Analysis and statistics | Low |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Some concerns |

Review position: retain as `supporting`. This is direct evidence for a locked
single-patient assay and separated verification, but historical cohorts and
commercial dependencies prevent it from serving as independent anchor evidence.

### PMC4818440 — peri-surgical paired-biopsy heterogeneity

Reported observations:

- Evaluated 23 immediate paired specimens and 56 diagnostic-versus-surgical pairs.
- Global expression correlations were generally high, yet roughly 15% of paired
  PAM50 classifications differed.
- Discordant pairs had small margins between their top two subtype centroids.
- Reports FDR-controlled paired analyses and public GEO data.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Some concerns |
| Reference comparator | Some concerns |
| Analysis and statistics | Low |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Low |

Review position: retain as `supporting`. It directly supports the proposition
that sample timing and location can perturb borderline classifications, while
remaining unable to determine which discordant specimen is biologically correct.

### PMC7470374 — modeling versus training commercial tests

Reported observations:

- Used 274 OPTIMA prelim specimens with multiple commercial assay results.
- Compared incomplete published-algorithm reconstruction with models trained on
  true commercial outputs.
- Kept a 50% validation set held out from model selection.
- Training materially improved categorical agreement for several assays; a
  trained Prosigna approximation reached 95.3% binary agreement.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Some concerns |
| Reference comparator | Low |
| Analysis and statistics | Low |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Some concerns |

Review position: retain as `supporting`. It shows why recreating a commercial
test from partial publications can fail and why held-out agreement must be
measured, but it does not establish clinical equivalence or external transport.

### PMC8657125 — specimen preparation changes ROR

Reported observations:

- Compared macrodissected FFPE/nCounter and fresh-frozen bulk/RNA-seq material
  from the same 94 tumors.
- Research FFPE ROR closely tracked approved Prosigna (`r² = 0.958`), whereas
  bulk-tissue ROR agreement was lower (`r² = 0.764`).
- Thirteen of 54 clinically eligible tumors changed risk category; six would
  have changed a guideline-mapped systemic-treatment recommendation and two
  would have changed chemotherapy use.
- Bulk tissue yielded 13 normal-like calls versus one in macrodissected FFPE,
  associated with lower tumor cellularity.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Some concerns |
| Reference comparator | Low |
| Analysis and statistics | Some concerns |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Low |

Review position: retain as `supporting`. This is unusually direct paired evidence
that specimen workflow can alter patient-adjacent risk categories. Because tissue
region, preparation, enrichment, preservation, and platform differ together, it
cannot identify a single causal factor or prove an actual treatment effect.

### PMC10771357 — real-world IHC versus PAM50

Reported observations:

- Analyzed 1,049 centralized PAM50 referrals with Ki67 data from eight countries.
- Three IHC proxy definitions had kappa values of 0.27–0.37 and accuracy of
  0.59–0.70 against PAM50.
- Depending on the proxy, 18–36% of PAM50 Luminal A tumors were classified as
  Luminal B and 5–11% of Luminal B tumors as Luminal A.
- The referral cohort was selected for clinical uncertainty, local IHC methods
  varied, and no long-term outcomes were available.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | High |
| Specimen and measurement | Some concerns |
| Classifier implementation | Low |
| Reference comparator | Some concerns |
| Analysis and statistics | Some concerns |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. It is valuable real-world evidence of
decision-boundary disagreement, but referral selection, decentralized IHC, and
absent outcomes prevent a central correctness or patient-benefit claim.

## Cross-study interpretation boundary

Together, these studies support a sharper engineering target: disagreement is
not confined to one algorithm. It can arise from specimen selection, tumor
cellularity, peri-surgical timing, platform and preprocessing, incomplete
commercial reconstruction, reference composition, and narrow subtype margins.

This evidence does **not** establish that one discordant label is biologically
correct, that a NaS artifact improves outcomes, or that research-derived scores
should direct treatment. A defensible NaS contribution still requires a frozen
single-sample artifact, independently calibrated perturbations, explicit
reliability and abstention thresholds, unchanged external validation, and
transparent failure accounting.

## Exact founder confirmation

If every proposal is acceptable without modification, reply exactly:

`I confirm citation appraisal batch 0003 as written.`

Any requested edit creates a new packet version and new checksums. Exact
confirmation will authorize derivation of six locked appraisals and reconciliation
of the progress ledger.
