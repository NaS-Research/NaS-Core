# NAS-BRCA-002 Literature-Gap Review Protocol

Protocol version: `0.1.1`
Question version: `0.2.0`
Status: **Locked for the founder-authorized bounded Phase 0 audit**

## Purpose

Determine whether NAS-BRCA-002 has a specific, defensible contribution beyond
published clinical/PAM50 discordance and subtype-stability work. This is a
preselection evidence audit, not a systematic-review claim, meta-analysis, or
authorization to retrieve biomedical outcome data.

## Review questions

1. How have clinical HR/HER2 categories and PAM50 subtypes been mapped and compared?
2. Which normalization, centering, classifier, gene-mapping, and cohort-composition
   choices have been shown to change subtype assignments?
3. How have first-versus-second subtype margins, uncertainty, entropy, stability,
   or abstention been defined?
4. Have stable non-luminal, unstable, and unclassifiable HR-positive/HER2-negative
   tumors been separated under prespecified rules?
5. Which clinicopathologic, genomic, pathway, immune, or outcome correlates have
   been reported, and which were independently validated?
6. What exact contribution remains unanswered and feasible for NaS to test?

## Eligibility

The locked criteria, databases, queries, extraction fields, synthesis plan, and
stopping rule are maintained in [`search_strategy.yaml`](search_strategy.yaml).
The structured extraction target is [`evidence_matrix.csv`](evidence_matrix.csv).

The review will include primary human-tumor cohorts and reproducible methods
papers relevant to PAM50 assignment, clinical/molecular disagreement,
classification stability, confidence, or validation. Reviews will support
citation chaining but will not be treated as primary cohort evidence.

## Screening and adjudication

NaS is founder-led. Dalron J. Robertson will make and document final screening
decisions. AI may help deduplicate, surface candidate studies, compare extracted
fields, and identify inconsistencies, but cannot make final inclusion decisions
or authorize the question gate.

Every full-text exclusion will receive one recorded reason. Ambiguous records
will remain pending until adjudicated. Corrections to extracted evidence will be
versioned rather than overwritten without provenance.

## Evidence synthesis

The first output is an evidence map, not a pooled effect estimate. Studies will
be grouped into:

- clinical versus molecular discordance;
- PAM50 implementation and preprocessing comparisons;
- classification confidence, margins, uncertainty, and stability;
- biological characterization of discordant or unstable tumors;
- prognostic or treatment-response analyses; and
- independent reproduction and transportability studies.

The novelty memorandum must distinguish:

- established findings;
- conflicting findings;
- findings supported only in one cohort;
- analytical-method gaps;
- biological-evidence gaps;
- external-validation gaps; and
- claims that cannot be tested with available data.

Absence from the search is not proof that a claim is novel. Any novelty statement
must be time-bounded, qualified, and supported by the executed search record.

## Outputs

- versioned search export and exact execution timestamps;
- deduplication and screening log;
- completed evidence matrix;
- evidence-map summary;
- novelty and gap memorandum;
- candidate contribution and claim-boundary revision;
- unresolved-evidence list; and
- founder question-gate decision.

## Gate

The strategy is locked and `retrieval_authorized` is true under the separate
founder Phase 0 authorization. This permits the preselection evidence audit while
the scientific question remains proposed; it does not mark the formal literature
stage ready. Any protocol change requires a new version and authorization review.
Literature completion does not authorize biomedical-data ingestion, molecular
outcome inspection, question selection, or a novelty claim.

Version `0.1.1` changes only the Europe PMC syntax after a count-only feasibility
check showed that unquoted, unfielded phrases expanded to 79,501 records. The
scientific concepts and eligibility criteria are unchanged. See
[`SEARCH_AMENDMENT_v0.1.1.md`](SEARCH_AMENDMENT_v0.1.1.md).
