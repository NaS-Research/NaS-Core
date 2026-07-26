# Founder Citation Appraisal Batch 0001

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents three AI-assisted full-text appraisal proposals. It does not
contain a founder decision, locked appraisal, scientific conclusion, novelty
finding, or clinical recommendation. Confirmation authorizes the proposed
eligibility, seven domain judgments, evidence roles, strengths, limitations, and
conflict disclosures exactly as written in the checksum-bound proposal files.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC11217366-v1.0.0.yaml` | `1f3188421b6b4d1f832ab114a43afa960d1f2074107ca7551854c482594469bc` | `context_only` |
| `PMC3487945-v1.0.0.yaml` | `621add70dede86407bb437e6933a4d3d5feb9b5059abbcc268f6aed996292ae1` | `context_only` |
| `PMC6547580-v1.0.0.yaml` | `b86612dbfa620ca4ad0297073987b97dd2a14a5eb18b24cdb2faefbffb1995a8` | `context_only` |

All source full texts were exact-identity, item-license, and checksum verified before
appraisal. Their article XML remains in governed object storage and is not copied
into Git.

## Founder review summary

### PMC11217366 — PALOMA-2 and PALLET

Reported observations:

- PALOMA-2 had 54% agreement in 222 paired results (`κ = 0.30`).
- PALLET had 69% agreement in 224 RNA-seq samples.
- In PALOMA-2, 22.5% of patients changed to the second-nearest centroid under an
  exploratory `0.10` correlation-distance switch.

Proposed domain judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | High |
| Classifier implementation | High |
| Reference comparator | Some concerns |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. It directly demonstrates clinically
important disagreement and boundary ambiguity, but its principal comparison
conflates platform and algorithm changes, uses cohort-dependent transformations,
and does not externally validate one unchanged reliability method.

### PMC6547580 — paired RNA-seq and NanoString in triple-negative disease

Reported observations:

- The raw subtype-call agreement was 89 of 96 (`92.7%`).
- The article reports `96%` after interpreting three of seven raw discordances as
  ambiguous under a `≤0.10` centroid-distance rule.
- The same FFPE-extracted RNA was measured on both platforms.

Proposed domain judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Low |
| Classifier implementation | Some concerns |
| Reference comparator | Some concerns |
| Analysis and statistics | High |
| Validation and transportability | High |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. It is strong paired analytical evidence
that platform agreement can be high under controlled conditions, but the small,
Basal-like-enriched population, post hoc ambiguity interpretation, and absence of
external replication prevent a general reliability claim.

### PMC3487945 — RT-qPCR PAM50 and clinical markers

Reported observations:

- Fixed training-derived centroids and cut-points were applied to 814 independent
  GEICAM/9906 trial patients.
- Only 56% of IHC-defined triple-negative tumors were Basal-like; 30% were HER2-enriched.
- Technical-repeat and normal-tissue dilution experiments showed systematic subtype
  switching, including Luminal B to Luminal A under contamination.

Proposed domain judgments:

| Domain | Judgment |
|---|---|
| Population selection | Some concerns |
| Specimen and measurement | Some concerns |
| Classifier implementation | Some concerns |
| Reference comparator | Some concerns |
| Analysis and statistics | High |
| Validation and transportability | Some concerns |
| Reporting and reproducibility | Some concerns |

Review position: retain as `context_only`. This is valuable assay-development and
gap-defining evidence, especially for technical-error and tissue-contamination
mechanisms. Exploratory prototype derivation, stepwise outcome modeling, imperfect
reference standards, and no prospective decision-impact validation prevent it from
supporting a central effectiveness claim.

## Cross-study interpretation boundary

Together, the three papers support a bounded premise for method development:
PAM50 agreement is conditional on population spectrum, specimen handling, platform,
normalization, classifier implementation, and treatment of small centroid margins.
They do **not** establish that a NaS method is accurate, novel, clinically useful,
or ready for patient-level decisions.

## Exact founder confirmation

If every proposal is acceptable without modification, reply exactly:

`I confirm citation appraisal batch 0001 as written.`

Any requested edit creates a new packet version and new proposal checksums. After
exact confirmation, the workflow may create founder-authorized locked appraisals,
update the citation appraisal ledger, and preserve this packet as the authorization
source.
