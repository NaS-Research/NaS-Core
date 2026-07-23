# NAS-BRCA-002 Question Review Packet

Packet version: `0.2.0`

Question version: `0.3.0`

Status: **Draft; prerequisite specifications and evidence review pending**

Decision requested later: `go`, `change`, `hold`, or `reject`

Accountable study lead: **Dalron J. Robertson — Founder and Study Lead**

## Proposed question

> In clinically HR-positive/HER2-negative primary breast tumors, can a frozen,
> patient-independent PAM50 procedure reproducibly distinguish analysis-ready
> subtype labels from unstable, insufficient-data, and abstain states, and can
> those analytical reliability outputs be reproduced unchanged in an independent
> processed RNA-seq cohort?

## Intended research decision

Decide whether a research subtype label may enter downstream subgroup analysis or
must be withheld with a traceable reason. This project does not decide whether the
label is biologically true, whether a clinical assay should be ordered, or how a
patient should be treated.

## Material change from v0.2.0

Version `0.2.0` broadly studied stability across PAM50 implementations. The Phase 0
review found substantial overlap with published SCAN-B perturbation work. Version
`0.3.0` instead requires:

1. one-sample operation whose output cannot change when unrelated test samples are
   added or removed;
2. a fixed-centroid implementation and locked platform-specific input
   transformation;
3. explicit first/second scores, margin, perturbation repeatability, quality state,
   reliability state, and abstention reason;
4. preserved missing-gene, mapping, transformation, and numerical failures;
5. thresholds selected without molecular, validation, survival, or treatment
   outcomes; and
6. an unchanged external attempt in processed SCAN-B GSE96058.

## Prerequisites before founder review

- [ ] Minimum implementation and perturbation set is versioned.
- [ ] Every output field, formula, state transition, and abstention reason is defined.
- [ ] Calibration target is explicitly analytical and does not imply biological truth.
- [ ] Revised high-quality evidence review satisfies its citation-chain stopping rule.
- [ ] TCGA receptor fields and PAM50 gene coverage are verified through metadata-only checks.
- [ ] GSE96058 gene coverage, sample/replicate handling, and platform bridge are verified.
- [ ] No molecular or outcome values were used to draft or tune the method.

## Scientific/product review

- [ ] The research user and downstream decision are specific.
- [ ] A reliability result changes research behavior beyond adding another figure.
- [ ] The contribution is differentiated from existing PAM50 perturbation studies.
- [ ] A high-abstention or transport-failure result remains publishable and useful.
- [ ] The method can become a governed Cortex component without becoming a clinical claim.

## Molecular/pathology review

- [ ] HR-positive/HER2-negative eligibility and assay limitations are explicit.
- [ ] Research PAM50 scores are not equated with Prosigna or another clinical assay.
- [ ] Gene identifiers, missing-gene rules, transformations, and centroids are defensible.
- [ ] Margin and repeatability are interpreted as analytical properties only.
- [ ] Purity, sampling, heterogeneity, and platform effects are preserved as limitations.
- [ ] No subtype, clinical category, or consensus rule is treated as a gold standard.

## Statistical review

- [ ] Reliability-state estimands and confidence intervals are prespecified.
- [ ] Perturbation families and thresholds are not tuned to observed group sizes.
- [ ] Technical replicates are not treated as independent patients.
- [ ] External success and failure criteria are locked before validation.
- [ ] Missingness and sparse-state rules preserve failure rather than silently exclude it.
- [ ] No outcome association is required for primary analytical success.

## Governance/publication review

- [ ] Only registered public/open source fields are in scope.
- [ ] Outcome access remains disabled.
- [ ] Full input, rule, code, environment, and review provenance is retained.
- [ ] Null, failure-heavy, contradictory, and abstention results are publishable.
- [ ] AI assistance, founder role conflicts, funding, and source attribution will be disclosed.
- [ ] Patient-level diagnostic, prognostic, testing, and treatment claims remain prohibited.

## Review provenance

The founder is also the prospective analyst, author, internal reviewer, and gate
approver. Separate scientific/product, molecular/pathology, and statistical passes
are required and must disclose knowledge limitations. AI review is advisory and
cannot authorize selection, preregistration, data access, analysis, or publication.

Question `0.3.0` remains `proposed` and `not_ready` until all prerequisites and
reviews are complete and a new founder decision is recorded.
