# AI-Assisted Question Review — NAS-BRCA-002 v0.2.0

Reviewed at: `2026-07-22T12:49:15-05:00`
Reviewer: OpenAI Codex
Authority: Advisory only; cannot select the question or authorize retrieval

## Disposition

The proposal is scientifically stronger and better aligned with NaS than a
single-cohort survival comparison. It is suitable for a governed novelty and
feasibility audit, but it is not yet ready for founder selection, literature
retrieval, data ingestion, or a claim of doctoral-level novelty.

## Strengths

1. It separates robust non-luminal biology from analytical instability rather
   than treating every disagreement as equivalent.
2. It treats uncertainty and abstention as scientific outputs.
3. It does not assume that the clinical category or one PAM50 implementation is
   a universal gold standard.
4. It requires independent validation and preserves a valuable null result.
5. It maintains nonclinical claim boundaries and separates prognosis from
   treatment-effect evidence.

## Gate-blocking findings

### 1. Novelty is plausible but unproven

Clinical/PAM50 discordance, outcome differences, second-nearest subtype
information, and PAM50 perturbation have prior literature. The exact remaining
contribution must be established through a reproducible evidence matrix. The
phrase “doctoral-level” cannot substitute for a demonstrated gap.

Required resolution: complete the locked evidence review and write a
claim-by-claim novelty memorandum before final question approval.

### 2. The perturbation set is not yet defined

The proposal does not name the implementations, centroids, normalization,
centering populations, gene-mapping rules, or perturbations that constitute
meaningfully distinct evidence. Superficially different pipelines may share the
same assumptions and create false consensus.

Required resolution: create an implementation-dependency matrix and justify
each locked perturbation scientifically before outcome inspection.

### 3. Clinical eligibility is underspecified

HR-positive/HER2-negative status can depend on assay type, threshold, equivocal
resolution, historical criteria, and missing PR or amplification results.

Required resolution: perform a field-level assay feasibility audit and define
eligibility, ambiguity, and unclassifiable rules before molecular analysis.

### 4. Confidence and abstention require locked estimands

Centroid margin, probability, entropy, cross-pipeline consensus, and missing-gene
failure describe different uncertainty concepts. Thresholds chosen after viewing
biology or survival would invalidate the primary analysis.

Required resolution: select primary stability and abstention estimands through
methods evidence and synthetic stress testing, then preregister thresholds.

### 5. Independent validation is not established

METABRIC is a candidate, not an approved source. Platform, clinical definitions,
identifier linkage, license, export, participant overlap, and ability to recompute
the primary classification have not been verified.

Required resolution: complete source terms and compatibility review, register an
approved validation source, and declare transport rules before preregistration.

### 6. Sparse-group feasibility is unknown

The robust non-luminal subgroup may be too small for stable multi-omic or outcome
models after requiring interpretable receptor and expression data.

Required resolution: perform non-outcome eligibility and gene-coverage counts,
then declare minimum group and event thresholds without hypothesis testing.

### 7. Multi-omic scope can become unfocused

Expression, mutation, copy number, immune signatures, pathways, survival, and
classification stability create multiple inferential families. An unrestricted
analysis would become a fishing expedition.

Required resolution: designate a single primary stability family, a small set of
prespecified biological families, explicit multiplicity control, and exploratory
analyses that cannot support the primary claim.

### 8. Clinical value remains a future hypothesis

The study can identify a translational research subgroup but cannot show that
testing, treatment selection, or patient outcomes improve.

Required resolution: retain the current no-treatment and no-clinical-utility
boundaries and define the specific later validation decision.

## Recommendation

Keep question `0.2.0` proposed while Phase 0 is in progress. Approve only the
non-outcome novelty and feasibility audit. After its deliverables are complete,
revise the question, rescore it, and submit the full package for founder
selection. No literature automation, molecular-data ingestion, survival testing,
or novelty claim is authorized by this advisory review.
