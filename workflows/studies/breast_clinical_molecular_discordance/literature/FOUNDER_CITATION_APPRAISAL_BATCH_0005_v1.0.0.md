# Founder Citation Appraisal Batch 0005

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents one AI-assisted, checksum-bound full-text appraisal proposal
for a paired comparison of genomic PAM50-plus-claudin-low classification with
pathology-based breast cancer subtype surrogates. It does not contain a founder
decision, locked appraisal, scientific conclusion, novelty finding, causal
treatment claim, or clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMID23907291-v1.0.0.yaml` | `e10db2780e780987cf9f551ab16b9ed0b81178da9a64c9070e65cfdf7e7a8cd6` | `context_only` |

The proposal is stored under `citation-appraisal-proposals/batch-0005/`. The
public UNC Lineberger institutional author copy was reviewed through the bounded
ephemeral proposal workflow. It matched the existing 518,968-byte review receipt
and content SHA-256
`5ffda15140cd4ecd7b7d49626a06964c007d7bd1b626a392e39d1e2e9255805a`.
The workflow reverified article identity and checksum, constrained derivative
narrative lengths, rejected long verbatim source passages, retained the proposal,
and retained zero article bytes.

## Founder review summary

### PMID23907291 — genomic versus pathology-based subtype assignment

Reported observations:

- Studied 94 women with locally advanced breast cancer enrolled in a randomized
  neoadjuvant doxorubicin-versus-docetaxel trial.
- Compared PAM50 plus a claudin-low predictor with an IHC/FISH surrogate scheme
  using ER, PR, HER2, Ki-67, EGFR, and CK5/6.
- Reported 68% observed agreement and kappa `0.551` with 95% CI
  `0.467–0.641` between the genomic and pathology-based classifications.
- Found that only 57% of triple-negative tumors were basal-like and that 27%
  were claudin-low by the genomic scheme.
- Reported C-indices of `0.66`, `0.75`, and `0.70` for overall-survival models
  using clinical variables alone, PAM50-plus-claudin-low plus clinical variables,
  and pathology surrogates plus clinical variables, respectively; the paper did
  not establish a significant C-index improvement over the clinical model.
- Used cohort-level median centering for microarray preprocessing and released
  primary expression data as GEO accession `GSE21997`.
- Disclosed public and nonprofit funding, equity in BioClassifier LLC, and a
  filed PAM50 patent held by one author.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | High |
| Reference comparator | Some concerns |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. The paired design directly demonstrates
that pathology surrogates and genomic intrinsic subtypes are not interchangeable,
which is relevant to the NaS discordance and reliability question. It should not
be supporting or anchor evidence for a patient-independent method or treatment
decision: preprocessing depends on the study cohort; the selected sample is small;
subtype-treatment analyses are imprecise and multiplicity is not controlled;
treatment crossover complicates causal interpretation; and no unchanged external
cohort validates the reported concordance, outcome, or interaction results.

## Founder decision

To authorize this exact packet, reply with:

`I confirm citation appraisal batch 0005 as written.`

Any edit to the packet or proposal changes its checksum and requires a new
version and a new exact confirmation.
