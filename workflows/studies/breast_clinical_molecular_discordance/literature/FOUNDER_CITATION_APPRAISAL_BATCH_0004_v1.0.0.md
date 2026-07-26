# Founder Citation Appraisal Batch 0004

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents one AI-assisted, checksum-bound full-text appraisal proposal
for the version-2 medRxiv preprint describing analytical bridging of Prosigna
from nCounter to a whole-transcriptome NGS laboratory-developed test. It does not
contain a founder decision, locked appraisal, scientific conclusion, novelty
finding, or clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PPR1259744-v1.0.0.yaml` | `2bc1b32d3c8639a0203b2f76c992e9b3871db9acf4bcb356a43b9d3534dc93f3` | `supporting` |

The proposal is stored under `citation-appraisal-proposals/batch-0004/`. The
official medRxiv version-2 plain full text passed exact DOI-in-URL, title,
version, rights, and checksum verification. It was reviewed ephemerally under
CC BY-NC 4.0; zero article bytes were retained in the durable NaS corpus. Its
stable content SHA-256 is
`47b4a207278aa19e0f19532dc47cb7e197d9e176b45001ee2761abb99ceb7576`.

## Founder review summary

### PPR1259744 — Prosigna nCounter-to-NGS analytical bridge

Reported observations:

- Used a 245-specimen platform-bridging cohort followed by a separate
  187-specimen analytical-validation cohort.
- Compared paired NGS LDT and established nCounter Prosigna outputs in surgical
  resections and core needle biopsies.
- Prespecified score-equivalence, precision, risk-category, subtype-concordance,
  lower-limit, and interference criteria.
- Reported validation-set ROR correlations of `R² = 0.968` for surgical
  resections and `R² = 0.966` for core biopsies.
- Reported intrinsic-subtype pairwise concordance of `92.31%` and `92.77%`,
  respectively.
- Added independent testing on 109 long-stored Oslo1 RNA specimens and 28
  archival FFPE blocks.
- Is a Veracyte-funded preprint; underlying data and the complete fitted
  calibration artifact are not publicly frozen.

Proposed judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Low |
| Classifier implementation | Some concerns |
| Reference comparator | Low |
| Analysis and statistics | Low |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Some concerns |

Review position: retain as `supporting`. The separated bridge and validation
cohorts, paired comparator, prespecified acceptance criteria, technical stress
tests, and archival cohort make this direct analytical evidence for platform
transport. It should not be anchor evidence because it is not peer reviewed,
the sponsor has a direct commercial interest, exact calibration artifacts and
data are unavailable, testing was centralized, and no clinical outcome or
treatment-utility claim was tested.

## Founder decision

To authorize this exact packet, reply with:

`I confirm citation appraisal batch 0004 as written.`

Any edit to the packet or proposal changes its checksum and requires a new
version and a new exact confirmation.
