# Founder Citation Appraisal Batch 0007

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents three AI-assisted, checksum-bound full-text appraisal
proposals covering single-sample microarray normalization, simplified molecular
subtyping, and IHC/PAM50 concordance. It does not contain a founder decision,
locked appraisal, scientific conclusion, novelty finding, causal treatment claim,
or clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC3283537-v1.0.0.yaml` | `3d12f771baa40fbfce6db36668c1353da6b4a4ff5b19df405222e2f1328395d7` | `context_only` |
| `PMC3508193-v1.0.0.yaml` | `86da301798e793d19564ee11a5abdd7b79ecde7355b1d6bc8213d83ab4160b9b` | `context_only` |
| `PMC7791620-v1.0.0.yaml` | `7016575c7bf6be472a413881ed955cc1bda5a31de19faaa704fe6bbd45e69b50` | `context_only` |

The proposals are stored under `citation-appraisal-proposals/batch-0007/`.
The source workflows re-fetched each official source, isolated its canonical
article representation, verified identity and checksum, constrained derivative
narrative lengths, rejected copied source sequences of 12 words or more, retained
only the proposals and receipts, and retained zero article bytes.

| Article | Representation | Canonical bytes | Content SHA-256 | Receipt SHA-256 |
|---|---|---:|---|---|
| `PMC3283537` | Publisher HTML v1 | 105,398 | `b4392904021e9348bf2afa1849cc7d7989ce4e8722d2d25bb2f5b38e1a488961` | `595c59a42167ec936dfbf5c15b1acaa7b336cad6a4357ebc836552d2e1049e02` |
| `PMC3508193` | PMC OAI article XML v1 | 102,553 | `031e6a137da78fba560ecae7ea5529c823737d56b27931536950051f9f5b1cd4` | `0606ae4ca1a42d648a70096ac1b789402063e2832e5a76da9af0f0b3936830c9` |
| `PMC7791620` | PMC OAI article XML v1 | 108,432 | `8a5c2e521596e4f636f203b3a12b8935d0a651b65bd4811aecdadeb1b62d7f7f` | `775b1f2321793ba75d25bd1702dd6a26742494b64a54655fdd039c85f281af64` |

Canonicalization excludes changing delivery-envelope fields; it does not alter
the article narrative and does not grant storage, redistribution, or commercial
reuse rights.

## Founder review summary

### PMC3283537 — simplified three-gene subtype model

Reported observations:

- Compared six classifiers across 36 public microarray datasets containing 5,715
  tumors.
- Defined SCMGENE using ESR1, ERBB2, and AURKA with Gaussian-mixture assignment.
- Reported greater robustness for subtype-classification models than
  single-sample predictors and SCMGENE kappa values of `0.65–0.70` against other
  subtype-classification models.
- Applied dataset-level robust scaling and evaluated one training dataset plus
  32 test datasets.
- Reported that biological subtype truth is unknown and that source datasets
  were retrospectively accrued and not commonly renormalized.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | High |
| Reference comparator | High |
| Analysis and statistics | Some concerns |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Low |

Review position: retain as `context_only`. The study is a large, transparent
comparison demonstrating that simpler classifier structure can improve
cross-dataset robustness. Its assignment still uses receiving-dataset scaling or
fitting, lacks an independent subtype truth, and does not validate a frozen
patient-independent artifact, uncertainty calibration, or abstention rule.

### PMC3508193 — SCAN single-sample microarray normalization

Reported observations:

- Introduced a within-array, sequence-aware linear model and two-component
  Gaussian mixture that requires no external reference samples.
- Compared SCAN with RMA, fRMA, and MAS5 using known-concentration spike-ins,
  public brain arrays, cell-line compendia, and multiple Affymetrix platforms.
- Reported mean spike-in AUC of `0.976` for SCAN and estimated signal-to-noise
  improvement from `1.357` to `6.554` in one 100-array example.
- Described probe sampling, intensity-matched bins, trimmed-mean gene
  summarization, equations, public datasets, and open-source software.
- Did not test a PAM50 decision rule, subtype uncertainty, treatment decision,
  or patient outcome.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Some concerns |
| Reference comparator | Some concerns |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. SCAN is direct evidence that
reference-free preprocessing of individual microarrays is technically feasible.
Developer-selected benchmarks, limited uncertainty and multiplicity handling,
absence of independent end-to-end clinical replication, and no PAM50-specific
decision validation prevent treating it as proof of subtype reliability or
patient benefit.

### PMC7791620 — Swedish IHC/PAM50 concordance

Reported observations:

- Compared three IHC surrogate schemes with PAM50 in 561 STO-3 and 237 Clinseq
  tumors.
- Reported kappa `0.36–0.57` and accuracy `0.54–0.75` across four-class
  comparisons.
- Reported kappa `0.69–0.71` and accuracy `0.90–0.91` only after Luminal A and B
  were collapsed.
- Used different eras, IHC workflows, HER2 handling, Ki67 scoring, and PAM50
  implementations across the two cohorts.
- Reported that surrogate-defined Luminal A/B groups did not reproduce the PAM50
  difference in tamoxifen treatment benefit.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | High |
| Classifier implementation | High |
| Reference comparator | High |
| Analysis and statistics | High |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. The two-cohort, within-study comparison
is strong direct evidence that IHC surrogates do not reliably reproduce PAM50
Luminal A/B labels. PAM50 remains a comparator rather than biological truth;
study-optimized Ki67 cutoffs, assay differences, historic treatment, regional
sampling, and absent locked external threshold validation prohibit patient-level
adjudication or treatment claims.

## Cross-study interpretation boundary

These studies jointly support three bounded propositions:

1. Reference-free single-sample microarray preprocessing is technically possible.
2. Simplifying a classifier can improve empirical robustness without establishing
   a correct biological label or patient-independent calibration.
3. Clinical IHC surrogates and gene-expression labels are especially
   non-interchangeable at the Luminal A/B boundary.

They do not validate a NaS classifier, establish PAM50 as biological ground truth,
show that any relabeling improves outcomes, provide a patient-level treatment
rule, establish novelty, or authorize molecular-data execution.

## Founder decision

To authorize this exact packet, reply with:

`I confirm citation appraisal batch 0007 as written.`

Any edit to the packet or proposal changes its checksum and requires a new
version and a new exact confirmation.
