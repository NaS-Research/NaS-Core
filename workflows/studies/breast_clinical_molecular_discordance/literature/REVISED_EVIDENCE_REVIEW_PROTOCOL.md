# NAS-BRCA-002 Revised Reliability Evidence Review

Protocol version: `0.2.4`
Question version: `0.3.0`
Status: **Locked for the founder-authorized bounded evidence audit**

## Purpose

Determine whether question `0.3.0` has a defensible contribution after direct
comparison with existing single-sample classifiers, patient-level uncertainty
methods, not-assigned or ambiguous states, centering approaches, measurement-error
models, and externally transported implementations.

This is a bounded analytical-method evidence review. It is not a systematic-review
publication, a clinical guideline, a diagnostic-accuracy claim, or permission to
inspect molecular or outcome data.

## Why the prior review cannot simply carry forward

The `0.2.0` review was stopped by a no-go trigger after broad PAM50 perturbation and
stability work was identified. It did not satisfy citation saturation, and 423
records remained pending. The narrowed `0.3.0` question changes the primary object
from broad biological stability to a fixed one-sample reliability and abstention
procedure.

Prior records and appraisals remain valid historical artifacts, but their relevance
must be adjudicated against the revised question. In particular, the existing
inventory contains direct single-subject uncertainty, absolute single-sample, and
current multi-method implementation reports that were not appraised before the
question changed.

## Review domains

Every eligible study must resolve, challenge, or delimit at least one domain:

1. fixed patient-independent classifier;
2. reference construction and gene centering;
3. gene mapping, input scale, and transformation;
4. top-versus-runner-up margin or patient-level uncertainty;
5. independently measured technical error;
6. perturbation and repeatability;
7. ambiguous, unclassifiable, not-assigned, or abstention states;
8. unchanged external transport; or
9. exact implementation artifacts, versions, and lawful reuse.

Outcome associations alone are not sufficient. Agreement with PAM50 is not treated
as biological truth, and reproducibility is not treated as clinical validity.

## Bounded evidence set

[`revised_priority_evidence.yaml`](revised_priority_evidence.yaml) contains the first
13 direct candidates. It deliberately includes evidence that may defeat or narrow
the proposed contribution. The final evidence set is capped at 30 studies unless a
versioned amendment demonstrates that the stopping rule cannot otherwise be assessed.

AI may identify and prioritize candidates, extract structured fields, and flag
inconsistencies. Dalron J. Robertson records every final include or exclude decision.
No autonomous exclusion is allowed.

## Search and deduplication

The revised database strategy is
[`search_strategy_v0.3.0.yaml`](search_strategy_v0.3.0.yaml). Version `0.2.4`
passed count-only feasibility with 56 PubMed and 99 Europe PMC records. It preserves
the focused strategy and explicitly unions the 13-record direct-priority set after
pre-screening coverage QA found four priority records absent from version `0.2.3`.
It is locked under the question-`0.3.0` founder authorization and remains
non-outcome and non-molecular.

Executed results will be deduplicated against the immutable `0.2.0` inventory while
preserving all source and version provenance. A prior screening decision does not
automatically become a question-`0.3.0` relevance decision.

## Full-text and appraisal rule

Every founder-included record must end in exactly one state:

- completed versioned appraisal;
- access restricted, with permitted metadata and abstract evidence retained; or
- duplicate, linked to one canonical report.

Appraisal must extract the exact method target, thresholds, training and calibration
data, test-cohort dependence, external-validation independence, null and failure-heavy
results, implementation artifacts, conflicts, and license limitations.

## Citation-chain stopping rule

Citation chaining uses the official Europe PMC references and citations endpoints.
A pass is not complete unless both directions are queried for every item in the
cumulative eligible evidence set, records are deduplicated, and every unique candidate
receives a final founder screening decision.

The procedure is:

1. Execute pass 1 over the cumulative eligible set.
2. Add and appraise any new eligible methodological or external-transport evidence.
3. Execute the next pass over the updated cumulative eligible set.
4. Reset the zero-pass count whenever a pass adds eligible evidence.
5. Stop only after the latest two consecutive complete passes each add zero eligible
   methodological or external-transport studies.

The two zero passes are an audit condition, not proof that no other publication exists.
Unresolved claims must remain explicit and absence cannot be represented as novelty.

[`revised_evidence_review_progress.yaml`](revised_evidence_review_progress.yaml) is the
machine-validated state. It cannot report saturation unless the locked search,
deduplication, screening, appraisal accounting, and both zero-yield passes reconcile.

## Outputs

- immutable revised search receipt and deduplication record;
- founder screening decisions;
- full-text access and appraisal artifacts;
- dependency-by-evidence matrix;
- citation-pass receipts;
- revised novelty and no-go memorandum;
- exact changes required in reliability specification `0.1.0`; and
- founder scientific, molecular/pathology, and statistical review packets.

## Current boundary

The protocol and search authorize bounded bibliographic retrieval. They do not
authorize molecular data access, outcome access, classifier execution, threshold
selection, novelty, or clinical use.
