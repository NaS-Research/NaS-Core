# Founder Citation Appraisal Batch 0006

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents two AI-assisted, checksum-bound full-text appraisal proposals
for direct comparisons of PAM50 intrinsic subtyping with
immunohistochemistry-based clinical surrogates. It does not contain a founder
decision, locked appraisal, scientific conclusion, novelty finding, causal
treatment claim, or clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC6473265-v1.0.0.yaml` | `6e918cf420ef5bc1561c50733ed65f34ecda3e45c28e63a8623a00db8d8d84d2` | `context_only` |
| `PMC10147771-v1.0.0.yaml` | `7effc65080533c2aeae0f5a04237c13b0f460a39b68ee4fb3bfd55b369e7a917` | `context_only` |

The proposals are stored under `citation-appraisal-proposals/batch-0006/`.
Both official publisher PDFs were reviewed through the bounded ephemeral
proposal workflow. The workflow reverified article identity and exact bytes,
constrained derivative narrative lengths, rejected copied source sequences of
12 words or more, retained only the proposals and receipts, and retained zero
article bytes.

| Article | Source bytes | Source SHA-256 | Receipt SHA-256 |
|---|---:|---|---|
| `PMC6473265` | 1,220,150 | `7ed5e9b9bb8a73734616f12ac300227330dca9e574c9a123b36a8c10f1ef2302` | `64528652b25890c3daf09a63b71b692844c339b280a1476a4fd5282e9f757bc9` |
| `PMC10147771` | 834,928 | `04a65edf61f9338abb12dafe0ab967477502dd6825d6afef33d42231083c2898` | `99c4c5806a924dce44747e0fbe7a69c11368322720d373fa1cab01d40f71ae59` |

`PMC3283537` was considered for this batch but was not included. Its
institutional-repository PDF changed bytes between the review receipt and delayed
proposal verification, and the fail-closed checksum gate rejected it. That paper
remains queued for a stable-source route.

## Founder review summary

### PMC6473265 — Korean multi-cohort IHC/PAM50 discordance

Reported observations:

- Combined 607 patients from five retrospective studies and one clinical trial
  conducted at a single Korean center.
- Reported 38.4% discordance between pathology-surrogate and PAM50 labels.
- Applied ComBat after merging Samsung NanoString expression with TCGA data,
  then used Bioclassifier centroids.
- Examined genomic alterations in a selected 118-sample subset and reported
  observational survival comparisons.
- Reported Fisher tests, false-discovery-rate correction, Kaplan–Meier,
  log-rank, and Cox methods.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | High |
| Specimen and measurement | Some concerns |
| Classifier implementation | High |
| Reference comparator | Some concerns |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. The study directly demonstrates that
clinical surrogate and research PAM50 labels can diverge, but the PAM50
implementation is reference- and cohort-dependent. Retrospective cohort
aggregation, a selected mutation subset, treatment differences, absent unchanged
external validation, and observational survival comparisons prevent causal,
patient-level, or transportability claims.

### PMC10147771 — South African IHC/PAM50 discordance

Reported observations:

- Included 378 quality-passing, self-identified Black African women treated at
  one Soweto clinic; age matching within an HIV-outcomes study produced a
  younger cohort with mostly stage II or III disease.
- Reported PAM50 frequencies of 19.3% Luminal A, 32.5% Luminal B, 23.5%
  HER2-enriched, and 24.6% basal-like.
- Reported clinical IHC-surrogate frequencies of 6.9% A, 72.7% B, 5.3% HER2,
  and 15.1% triple-negative.
- Explored multiple Ki67 thresholds and an alternate HER2 grouping using kappa
  and descriptive comparisons.
- Did not report an outcome analysis or held-out validation of the proposed
  Ki67 range.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | High |
| Specimen and measurement | Some concerns |
| Classifier implementation | Some concerns |
| Reference comparator | Some concerns |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. The study provides valuable evidence
from an underrepresented population and makes the dependence of clinical subtype
distributions on measurement and threshold choices visible. A single younger,
later-stage cohort, exploratory thresholds without multiplicity or held-out
calibration, proprietary classification, request-only patient data, and no
outcome analysis prohibit treating the suggested threshold range as validated
decision support.

## Cross-study interpretation boundary

Together, these studies support a bounded observation: clinical-surrogate and
PAM50 labels are not interchangeable, and observed agreement depends on the
population, specimen, assay, preprocessing, classifier implementation, reference
cohort, clinical mapping, and threshold choices. They do not establish which
discordant label is biologically correct, validate a universal Ki67 threshold,
show that relabeling improves treatment outcomes, validate a NaS classifier, or
support patient-level decisions.

## Founder decision

To authorize this exact packet, reply with:

`I confirm citation appraisal batch 0006 as written.`

Any edit to the packet or proposal changes its checksum and requires a new
version and a new exact confirmation.
