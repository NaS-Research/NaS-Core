# Question 0.3.0 Full-Text Appraisal Protocol

Version: `1.1.0`

Queue: `af08a334…8a2a3`

Founder progress: `b0c31f7e…00945f`

Status: **Locked before question-specific appraisals**

This protocol applies the seven-domain appraisal contract to the 13 founder-included
priority papers. The general quality rules in `FULL_TEXT_APPRAISAL_PROTOCOL.md`
remain controlling; this version adds the question-`0.3.0` extraction boundary.

For each eligible paper, determine:

1. whether the method truly operates on one patient independently;
2. every required centroid, reference, transform, mapping, and software artifact;
3. the uncertainty, margin, ambiguity, unclassifiable, or abstention definition;
4. the source and independence of any technical-error or perturbation model;
5. whether thresholds were calibrated without outcomes or test-cohort adaptation;
6. whether validation used unchanged artifacts in independent patients and platforms;
7. null, contradictory, failure-heavy, and high-abstention findings; and
8. whether the paper defeats, narrows, supports, or only contextualizes the proposed
   NaS reliability contribution.

Evidence roles retain their strict meanings:

- `anchor`: no high or unclear domain, with low-risk analysis and transport validation;
- `supporting`: relevant with limitations but no high-risk domain;
- `context_only`: important for method history, contradiction, or gap definition but
  too weak for a central effectiveness or clinical claim;
- `excluded`: fails full-text eligibility with one explicit reason.

AI may extract and propose judgments only with disclosure. Dalron J. Robertson
authorizes every locked appraisal. An appraisal is an evidence-quality assessment,
not a scientific result, novelty finding, or clinical recommendation.
