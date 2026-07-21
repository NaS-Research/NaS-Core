# NAS-BRCA-002 Question Review Packet

Packet version: 0.1.0  
Question version: 0.2.0  
Status: Awaiting named human reviewers  
Decision requested: Approve, request changes, place on hold, or reject

## Proposed question

> Among clinically HR-positive/HER2-negative primary breast cancers, which
> non-luminal molecular subtype assignments remain stable across prespecified,
> defensible PAM50 preprocessing and classifier implementations, and what
> distinguishes robust non-luminal biology from unstable classification?

## Intended research decision

Decide whether a reproducibly identifiable subgroup warrants a focused external
validation or translational study of molecular classification confidence. The
project does not decide patient testing or treatment.

## Why this version is being reviewed

A general comparison between clinical receptor categories and PAM50 is already
well represented in the literature. The proposed contribution is narrower:

1. restrict the primary population to clinically HR-positive/HER2-negative disease;
2. compare prespecified defensible PAM50 implementations;
3. separate stable luminal, robust non-luminal, unstable, and unclassifiable results;
4. retain classification confidence and first-versus-second centroid margins;
5. test whether robust and unstable states have distinct prespecified biology; and
6. attempt the primary analysis in an independent cohort.

This design treats instability as a result, not a nuisance to hide.

## Initial evidence motivating review

- NCI describes receptor biomarkers and molecular subtypes as clinically and
  biologically relevant but distinct information layers:
  [NCI breast-cancer biomarker tests](https://www.cancer.gov/types/breast/diagnosis/breast-cancer-biomarker-tests).
- A prior cohort reported substantial clinical/PAM50 disagreement and outcome
  differences, demonstrating that simple discordance itself is not a new claim:
  [Kim et al., 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6473265/).
- A population-based study showed that PAM50 assignments can be sensitive to
  biological-process perturbation and that the second-nearest subtype contains
  information:
  [Ellis et al., 2023](https://pubmed.ncbi.nlm.nih.gov/37857634/).
- An open-source PCA-PAM50 implementation has been demonstrated on TCGA-BRCA,
  making implementation choice a current reproducibility question:
  [Enhanced PAM50 subtyping, 2026](https://pubmed.ncbi.nlm.nih.gov/41390542/).

These citations establish plausibility, not novelty or approval. A locked
literature protocol and complete review begin only after question selection.

## Proposed primary output

Within eligible HR-positive/HER2-negative tumors, estimate with uncertainty:

- stable luminal proportion;
- robust non-luminal proportion;
- classification-unstable proportion; and
- unclassifiable/insufficient-confidence proportion.

The exact implementations, preprocessing, consensus rule, confidence rule, and
minimum sample requirements must be locked after the literature and feasibility
stages and before outcome inspection.

## Proposed secondary work

- cross-implementation transition and agreement analysis;
- first-versus-second centroid margins;
- clinicopathologic correlates;
- prespecified pathway, immune, mutation, and copy-number comparisons;
- external reproduction of the primary stability categories; and
- exploratory overall survival only when event and diagnostic criteria permit.

No treatment-response or clinical-utility analysis is proposed.

## Principal risks

1. **Implementation circularity:** implementations may share code, centroids, or
   assumptions and therefore not provide independent evidence.
2. **Cohort-dependent centering:** subtype calls may change with cohort composition.
3. **No clinical gold standard:** agreement is not equivalent to truth.
4. **Assay mismatch:** research RNA sequencing is not interchangeable with a
   clinically validated commercial assay.
5. **Small robust non-luminal group:** sparse groups may prevent stable modeling.
6. **Outcome confounding:** TCGA treatment and follow-up context is incomplete.
7. **External compatibility:** validation cohorts may differ in platform,
   preprocessing, eligibility, population, and treatment era.
8. **Clinical overstatement:** an analytical stability finding cannot recommend
   additional testing or altered treatment.

## Hard selection gates

The question should not be selected unless reviewers agree that:

- classification stability is a meaningful research question;
- at least two defensible implementations or configurations can be prespecified;
- stable, unstable, and unclassifiable rules can be defined without seeing outcomes;
- the TCGA variables are plausibly sufficient for discovery;
- an independent validation path is credible;
- the study can produce useful evidence even when the result is null;
- the public output can remain clearly nonclinical; and
- success would justify a specific next research decision.

## Review checklist

### Scientific/product review

- [ ] The intended research user and decision are specific.
- [ ] The project is useful beyond producing an attractive paper.
- [ ] The contribution is sufficiently differentiated from prior discordance studies.
- [ ] A null or instability-dominant result would remain interpretable.
- [ ] The proposed output suggests a credible next research decision.

### Molecular/pathology review

- [ ] HR-positive/HER2-negative eligibility is defined appropriately.
- [ ] Research PAM50 calls are not equated with a clinical assay.
- [ ] The candidate implementations and preprocessing choices are defensible.
- [ ] Centroid margin/confidence has a scientifically defensible interpretation.
- [ ] Tumor purity, sampling, heterogeneity, and assay variation are addressed.
- [ ] No system is incorrectly labeled a universal gold standard.

### Statistical review

- [ ] Primary groups and estimands can be prespecified.
- [ ] Confidence intervals and sparse-group rules are appropriate.
- [ ] Agreement measures are interpreted with prevalence limitations.
- [ ] Multiplicity families can be defined for secondary molecular analyses.
- [ ] Outcome analysis is secondary, adequately powered, and diagnostically gated.
- [ ] External-validation success criteria can be declared in advance.

### Governance/publication review

- [ ] Discovery data have a plausible public/open or approved licensed path.
- [ ] Validation access, license, overlap, export, and attribution can be assessed.
- [ ] The paper can follow STROBE and applicable REMARK principles.
- [ ] Data, code, AI use, funding, conflicts, and TCGA acknowledgements will be disclosed.
- [ ] Patient-level testing and treatment claims remain prohibited.

## Required reviewer record

| Field | Scientific/product | Molecular/pathology | Statistical |
| --- | --- | --- | --- |
| Reviewer name | To be assigned | To be assigned | To be assigned |
| Affiliation/qualification | | | |
| Conflict disclosure | | | |
| Decision | Pending | Pending | Pending |
| Reviewed question version | 0.2.0 | 0.2.0 | 0.2.0 |
| Review date | | | |
| Required changes | | | |
| Rationale | | | |

At least the required perspectives must be documented. One qualified person may
cover more than one perspective when disclosed, but the study author and an AI
assistant cannot substitute for independent scientific approval.

## Decision consequences

- **Approved:** update the intake to `selected`, mark literature `ready`, record
  reviewer metadata, and begin the locked literature protocol.
- **Changes requested:** keep the question proposed, version the revision, and
  return the complete packet for review.
- **On hold:** document the missing person, evidence, data, or validation path.
- **Rejected:** record the reason and retire or replace the proposal without
  collecting outcome-bearing data.
