# NAS-BRCA-002 Project-to-Publication Plan

Study: **Not All Discordance Is Equal: Robust and Unstable Molecular
Reclassification in HR-Positive/HER2-Negative Breast Cancer**

Study ID: `NAS-BRCA-002`  
Question ID: `NAS-RQ-BRCA002`  
Current state: **Proposed; not approved for literature retrieval or data analysis**  
Planned public URL:
`https://nasresearch.bio/research/pam50-classification-stability-breast-cancer`

## Live progress tracker

Update this table whenever a gate changes. `pipeline.yaml` is the
machine-readable lifecycle record; this table is the human operating view.
Completion requires a link to the reviewed artifact or release that proves the
gate was satisfied.

| Phase | Workstream | Status | Completion evidence / next action |
| ---: | --- | --- | --- |
| 0 | Register proposal | Complete | Workspace, draft intake, project plan, and oncology charter entry created |
| 1 | Review and select question | In progress | AI advisory complete; complete founder review and record a decision |
| 2 | Lock evidence-review protocol | Queue verified; human screening next | Queue `b02c2abf…f042` has 457 complete abstracts pending founder decisions |
| 3 | Establish data and assay feasibility | Locked; assessment next | Source and non-outcome metadata assessment authorized; outcome access remains prohibited |
| 4 | Preregister analysis plan | Not started | Requires evidence review, feasibility, and documented founder protocol approval |
| 5 | Capture discovery snapshots | Not started | Requires preregistration and completion of the `NAS-BRCA-001` qualification gate |
| 6 | Build and quality-check cohort | Not started | Requires an independently verified immutable snapshot |
| 7 | Execute discovery analysis | Not started | Requires approved cohort QA and frozen analysis code |
| 8 | Execute exploratory outcome analysis | Not started | Run only if prespecified event, follow-up, and diagnostic criteria are met |
| 9 | Reproduce and stress-test | Not started | Requires a frozen discovery run |
| 10 | Perform external validation | Not started | Requires a locked validation addendum and approved independent source |
| 11 | Assemble evidence and freeze release | Not started | Requires completed discovery, validation, claim audit, and reviews |
| 12 | Draft scientific paper | Not started | Must derive exclusively from the approved frozen release |
| 13 | Complete publication review | Not started | Resolve clinical, statistical, reproducibility, governance, claim, and editorial reviews |
| 14 | Produce website edition | Not started | Build approved web content, figures, tables, PDF, metadata, and accessibility assets |
| 15 | Publish and verify production | Not started | Approve deployment preview, publish version 1.0, and verify production artifacts |
| 16 | Maintain, correct, and decide next study | Not started | Monitor feedback, version corrections, and hold translation decision review |

### Current blockers

- `NAS-BRCA-001` received a conditional platform-qualification pass; its founder
  results/remediation gate remains pending before outcome-bearing discovery work.
- The founder's scientific/product, molecular/pathology, and statistical
  self-review passes have not been completed for `NAS-RQ-BRCA002`.
- The discovery question is proposed, not selected. A separately documented
  founder decision authorizes only the bounded Phase 0 literature and source audit.
- No compatible independent validation source has been assessed or approved.

### Immediate working queue

1. Execute the locked PubMed and Europe PMC searches and retain their exact logs.
2. Deduplicate records, screen them, populate the evidence matrix, and draft the
   claim-by-claim novelty memorandum.
3. Map discovery fields/files and assess external-validation terms, compatibility,
   independence, overlap, and reproducibility without accessing molecular outcomes.
4. Complete the three founder review perspectives in
   `reviews/QUESTION_REVIEW_PACKET.md`.
5. Resolve the AI-advisory blockers and record `go`, `change`, `hold`, or `reject`.

## Phase 1 execution board — Question review and selection

Phase objective: decide whether `NAS-RQ-BRCA002` is sufficiently useful,
testable, differentiated, feasible, governable, and externally validatable to
authorize a formal literature review.

- Phase owner: **Dalron J. Robertson — Founder and Study Lead**
- Current question version: `0.2.0`
- Current decision: `pending`
- Current gate state: `in_progress`

| ID | Task | Owner | Status | Required evidence |
| --- | --- | --- | --- | --- |
| P1.1 | Register permanent study and question IDs | NaS Research | Complete | `study.yaml` and `research_question.yaml` |
| P1.2 | Narrow the question to robust versus unstable PAM50 assignment | NaS Research | Complete | Question version `0.2.0` |
| P1.3 | Prepare the multidisciplinary review packet | NaS Research | Complete | `reviews/QUESTION_REVIEW_PACKET.md` |
| P1.4 | Confirm the accountable study lead | Dalron J. Robertson | Complete | Name and role recorded in `study.yaml` |
| P1.5 | Complete scientific/product self-review pass | Dalron J. Robertson | Not started | Checklist, comments, rationale, and conflict disclosure |
| P1.6 | Complete molecular pathology/oncology self-review pass | Dalron J. Robertson | Not started | Checklist, comments, rationale, and knowledge limitations |
| P1.7 | Complete biostatistical self-review pass | Dalron J. Robertson | Not started | Checklist, comments, rationale, and knowledge limitations |
| P1.8 | Complete AI-assisted adversarial review | OpenAI Codex | Complete | `reviews/AI_QUESTION_REVIEW_v0.2.0.md`; advisory and non-authoritative |
| P1.9 | Resolve every requested change | Dalron J. Robertson | Not started | Comment-resolution log and versioned question changes |
| P1.10 | Re-score the final candidate | Dalron J. Robertson | Not started | Evidence-backed scores and written rationale for all eight dimensions |
| P1.11 | Record final selection decision | Dalron J. Robertson | Not started | Founder approval, changes requested, on hold, or rejection with timestamp |
| P1.12 | Update lifecycle records | NaS Core maintainer | Not started | Intake, study, pipeline, charter, and tracker agree |
| P1.13 | Validate and freeze the selected question | NaS Core maintainer | Not started | Validation output, clean tests, commit, and question-version Git tag |

### What is already implemented for Phase 1

- permanent study and question identity;
- typed question validation and lifecycle enforcement;
- a proposed decision context, scientific question, data path, validation path,
  output, success criteria, limitations, and provisional 30/40 score;
- a structured multidisciplinary self-review packet;
- a typed Phase 0 novelty/data-feasibility plan, reproducible draft search
  strategy, evidence-matrix structure, and candidate-source requirements;
- a completed AI-assisted adversarial review with explicit scientific and
  operational blockers;
- explicit nonclinical, nonpredictive, and no-gold-standard boundaries;
- a live human tracker and machine-readable `pipeline.yaml`;
- automated tests preventing an unapproved question from becoming selected or
  literature-ready; and
- a defined handoff into the governed literature-review stage.

### What is deliberately not implemented yet

- automated literature retrieval or full-text processing;
- the final list of PAM50 implementations and preprocessing configurations;
- consensus, confidence, centroid-margin, instability, or abstention thresholds;
- TCGA field extraction or biomedical-data snapshots;
- cohort construction, molecular analyses, survival models, or figures;
- an external validation dataset integration; and
- paper or website content based on study results.

Those choices depend on completed Phase 1 review, then the Phase 2 literature
review and Phase 3 data-feasibility assessment. Implementing them now would risk
encoding unreviewed assumptions or tuning the question to available results.

### Required founder input

NaS is currently a one-person organization. Dalron J. Robertson performs and
documents the internal gate review. Before selection, the review record must
contain separate passes from the following perspectives:

1. scientific/product usefulness and differentiation;
2. breast molecular pathology or oncology validity; and
3. biostatistical design and external-validation feasibility.

The same founder may cover every perspective, but must disclose that he is also
the study author, analyst, and approver, and must record knowledge limits. The
AI-assisted review is an adversarial aid only: it may identify omissions and
propose changes but cannot approve, reject, or authorize the gate. External
experts from the founder's network may review a near-final manuscript in Phase
13; their feedback is separately attributed and is not journal peer review.

### Review meeting agenda

1. Restate the intended user and research decision in one sentence.
2. Decide whether classification stability is useful beyond publication.
3. Challenge the restriction to HR-positive/HER2-negative primary disease.
4. Examine whether candidate PAM50 implementations would be meaningfully distinct.
5. Decide whether stability, uncertainty, and abstention can be prespecified.
6. Examine TCGA discovery fitness and the independent-validation path.
7. Identify the minimum claim that remains valuable if results are null.
8. Re-score the eight selection dimensions.
9. Record one formal decision and every required change.

### Decision paths

**Approved**

- change question status to `selected`;
- change literature status to `ready`;
- update the question version to `1.0.0`;
- record founder identity, review type, rationale, decision, and time;
- mark the question stage complete and literature stage in progress;
- create a signed-off Git commit and question-version tag; and
- begin Phase 2 by locking the literature-review protocol.

**Changes requested**

- retain `proposed` and `not_ready` states;
- assign every comment an owner;
- revise the question with a new `0.x.0` version;
- document resolutions; and
- return the full revision to founder review.

**On hold**

- record the specific missing expertise, evidence, data source, or validation path;
- prohibit literature automation and biomedical-data ingestion; and
- define the condition required to resume.

**Rejected**

- preserve the decision and rationale;
- retire the proposal without outcome-bearing analysis; and
- decide whether to revise the concept under a new question version or create a
  genuinely different study ID.

### Phase 1 validation commands

Run from the NaS Core repository root:

```bash
uv run nas-core question validate \
  workflows/studies/breast_clinical_molecular_discordance/question/research_question.yaml
uv run nas-core study validate \
  workflows/studies/breast_clinical_molecular_discordance
uv run nas-core program validate workflows/oncology/program_charter.yaml
make check
```

### Phase 1 definition of done

- an accountable study lead is recorded;
- all three founder review perspectives, conflicts, and knowledge limits are documented;
- AI-assisted advisory findings are resolved or accepted as limitations;
- every review comment is resolved or explicitly accepted as a limitation;
- final selection scores have evidence-backed rationales;
- the founder records the gate decision and timestamp;
- an approved question is version `1.0.0`, `selected`, and `literature-ready`;
- `study.yaml`, `pipeline.yaml`, the oncology charter, and this tracker agree;
- all validators and tests pass; and
- the approved question commit is tagged before Phase 2 retrieval begins.

Until those conditions are satisfied, Phase 1 remains in progress and no
automated literature or biomedical-data ingestion is authorized.

## 1. Purpose and claim boundary

The project will examine clinically HR-positive/HER2-negative breast cancers,
identify which non-luminal PAM50 assignments remain stable across defensible
preprocessing and classifier implementations, distinguish robust biological
discordance from analytical instability, and test the primary pattern in an
independent cohort.

The study may support a translational hypothesis about where additional
molecular characterization deserves evaluation. It cannot establish that a
test improves treatment selection, that a treatment works differently, or that
an individual patient should receive different care.

The word **discordance** means disagreement under prespecified rules. A robust
non-luminal call and an unstable call are different results. No clinical label,
PAM50 implementation, or consensus is assumed to be a universal gold standard.

## 2. Completion definition

The project is complete only when all of the following are true:

- the research question and literature protocol received documented founder approval;
- the analysis plan was preregistered and Git-tagged before outcome inspection;
- every data source was approved and captured in immutable snapshots;
- the complete discovery pipeline ran from a clean environment;
- all prespecified analyses, diagnostics, nulls, and deviations were retained;
- the primary result was attempted in an independent dataset;
- every public claim traces to an executed result or approved external source;
- scientific, statistical, governance, and publication reviews were resolved;
- a frozen NaS research release was created and reproducibility-checked;
- the version-of-record PDF and accessible web edition agree;
- the production page, downloads, citations, metadata, and figures were tested;
- the publication is live on `nasresearch.bio` with a version and correction path.

Completion does not make the output a clinical decision-support system.

## 3. Roles and review provenance

NaS is a founder-led, one-person organization during this study. Dalron J.
Robertson may perform multiple operational and approval roles, but each role,
self-review pass, conflict, and limitation must be recorded explicitly. AI has
no gate authority. External expert feedback and journal peer review remain
separate review types.

| Role | Responsibility | Required before |
| --- | --- | --- |
| Founder, study lead, analyst, and author — Dalron J. Robertson | Scope, analysis, decisions, authorship, and accountable internal approval | Every internal gate |
| Founder clinical/molecular review pass | Definitions, applicability, receptor assays, PAM50 interpretation, mappings, and claim boundaries | Protocol lock and public release |
| Founder statistical review pass | Estimands, missingness, multiplicity, diagnostics, survival, and sensitivities | Protocol lock and release |
| Founder governance/reproducibility review pass | Terms, classifications, exports, clean rerun, checksums, manifests, and numerical agreement | Ingestion and frozen release |
| OpenAI Codex — AI-assisted reviewer | Adversarial critique, consistency checks, and issue discovery; no decision authority | Advisory throughout |
| External domain or statistical experts | Attributed critique of a near-final manuscript when available | Planned in Phase 13 |
| Journal editors and reviewers | Formal independent peer-review process | After journal submission |
| Founder web publisher | Website implementation, accessibility, metadata, build, and production verification | Deployment |

An AI model cannot fill an independent approval role.

## 4. Master stage map

| Gate | Stage | Principal output | Exit decision |
| --- | --- | --- | --- |
| G0 | Proposal | Study workspace, draft intake, project plan | Continue to review or retire |
| G1 | Question selection | Approved `research_question.yaml` | Select, revise, hold, or reject |
| G2 | Evidence protocol | Locked literature-review protocol and searches | Evidence work may begin |
| G3 | Data feasibility | Field matrix, source assessments, sample/event feasibility | Feasible, redesign, or stop |
| G4 | Analysis protocol | Approved preregistered `analysis_plan.yaml` and Git tag | Ingestion may begin |
| G5 | Discovery snapshot | Verified immutable TCGA-BRCA snapshot | Analysis may begin |
| G6 | Discovery result | Frozen discovery run and internal review | Validate, revise, or stop |
| G7 | External validation | Independent locked validation run | Supported, not supported, or inconclusive |
| G8 | Research release | Independently verified immutable release | Draft paper or withhold |
| G9 | Publication | Approved PDF and website preview | Publish, revise, or withhold |
| G10 | Post-publication | Live checks, feedback, corrections, update record | Maintain, revise, or retire |

`NAS-BRCA-001` must also satisfy the oncology program's platform-qualification
gate before `NAS-BRCA-002` executes outcome-bearing discovery analysis.

## 5. Phase-by-phase operating plan

### Phase 0 — Register the proposal

Status: **In progress**

Actions:

1. Assign the permanent study and question identifiers.
2. Record the decision context, scientific question, proposed output, data
   needs, validation path, claim boundaries, and provisional selection score.
3. Confirm that the project is discovery research and not a clinical tool.
4. Add the candidate study to the oncology program charter as `proposed`.
5. Record known data, licensing, biological, and translation risks.

Deliverables:

- `study.yaml`
- `pipeline.yaml`
- `question/research_question.yaml`
- this project plan

G0 exit criteria:

- IDs and scope are internally consistent;
- no prohibited data or clinical claim is introduced;
- the question is ready for independent selection review.

### Phase 1 — Review and select the question

Actions:

1. Review the intended user and the research decision being supported.
2. Challenge whether the classification comparison can change a meaningful
   research decision rather than merely produce an attractive figure.
3. Review the proposed PAM50 implementations, stability/consensus rules, and the
   danger of treating one implementation as a universal gold standard.
4. Verify that the primary outcome is measurable and that an independent
   validation path is plausible.
5. Re-score all eight selection dimensions with written evidence.
6. Resolve comments and record one decision: approved, changes requested,
   rejected, or on hold.

G1 exit criteria:

- an identified reviewer approves the intake;
- status becomes `selected`;
- `literature_status` becomes `ready`;
- unresolved scope questions are not deferred into the analysis.

Stop rule: reject or hold the project if it lacks a defensible mapping,
external-validation path, or decision beyond publication alone.

### Phase 2 — Lock the evidence-review protocol

Actions:

1. Define a targeted evidence review covering clinical receptor categories,
   intrinsic subtypes, PAM50 implementations, classification stability,
   discordance studies, prognosis, assay variability, tumor purity, and confounding.
2. Register PubMed and any permitted full-text sources before automated use.
3. Record exact queries, dates, filters, APIs, exports, counts, and checksums.
4. Define duplicate handling, screening criteria, extraction fields, two-person
   verification expectations, and conflict resolution.
5. Extract population, assay, mapping, effect estimates, adjustment sets,
   missingness, limitations, funding, and cohort overlap.
6. Build an evidence table separating supporting, conflicting, null, and
   nonapplicable results.
7. Identify the original TCGA breast-cancer analysis and subsequent discordance
   and stability literature without assuming novelty.

Required standards:

- follow the principles of the [STROBE statement](https://www.strobe-statement.org/)
  for observational research reporting;
- use [REMARK](https://pmc.ncbi.nlm.nih.gov/articles/PMC3362085/) where tumor-marker
  prognostic analyses apply;
- follow [NCI instructions for citing TCGA](https://www.cancer.gov/ccg/research/genome-sequencing/tcga/using-tcga-data/citing).

G2 exit criteria:

- protocol and search strategy are review-approved and versioned;
- sources and permissions are registered;
- the evidence review identifies the precise knowledge gap, expected overlap,
  plausible mappings, confounders, and analysis implications.

### Phase 3 — Establish data and assay feasibility

Actions:

1. Build a variable-level matrix for clinical receptors, assay methods,
   pathology, age, stage, histology, tumor purity, RNA expression, PAM50 calls,
   mutations, copy number, follow-up, and survival.
2. Determine whether to use an approved existing PAM50 assignment or compute
   one; document preprocessing, gene mapping, centering population, classifier
   version, confidence, and unclassifiable rules.
3. Enumerate TCGA cases with the minimum required modalities without examining
   group-outcome results.
4. Assess missingness, class size, event counts, measurement compatibility, and
   site/assay heterogeneity.
5. Select an external validation candidate and complete its source, license,
   access, export, attribution, and cohort-overlap assessment.
6. Decide whether CPTAC proteomics or other modalities add prespecified value;
   optional sources cannot be added merely because they are available.
7. Write source assessments and register only approved uses.

G3 exit criteria:

- a reviewer accepts the data dictionary and feasibility report;
- primary and validation cohorts are plausible;
- minimum sample/event requirements and sparse-cell rules are specified;
- every required source has a lawful, governed access path;
- the project is redesigned or stopped if external validation is not credible.

### Phase 4 — Preregister the analysis plan

The analysis plan must separate confirmatory descriptive work from exploratory
biology and prognosis.

Primary analysis:

1. Freeze the HR-positive/HER2-negative clinical eligibility definition.
2. Freeze each PAM50 preprocessing and classifier implementation.
3. Freeze the consensus, confidence, instability, and unclassifiable rules.
4. Estimate stable luminal, robust non-luminal, unstable, and unclassifiable
   proportions with 95% confidence intervals.
5. Report complete cross-implementation transitions and centroid margins.
6. Use an alluvial/Sankey figure to show individual assignment movement.

Prespecified secondary analyses:

- classification agreement metrics with known prevalence limitations;
- associations between stability group and age, stage, histology, purity, and
  relevant assay variables;
- selected pathway, immune, mutation, and copy-number comparisons;
- exploratory overall-survival analysis with effect estimates and diagnostics;
- sensitivity to prespecified PAM50 preprocessing and consensus rules;
- analyses excluding low-confidence, missing, or ambiguous classifications.

The protocol must specify:

- cohort inclusion, exclusion, sample selection, and duplicate handling;
- exposure, outcomes, covariates, estimands, and model formulas;
- missing-data handling and cohort-flow reporting;
- minimum cell/event rules and separation/convergence handling;
- multiplicity families and false-discovery control;
- batch, purity, site, and preprocessing checks;
- all figures, tables, diagnostics, sensitivities, and negative outputs;
- deviations, amendments, random seeds, and software/environment capture;
- explicit noncausal, nonpredictive, and nonclinical interpretation boundaries.

G4 exit criteria:

- oncology, molecular/pathology, statistical, and governance reviews are resolved;
- status is `preregistered`;
- the approved protocol commit is Git-tagged;
- no outcome-bearing data were inspected to tune the plan.

### Phase 5 — Capture governed discovery snapshots

Actions:

1. Execute the exact approved GDC queries against an identified data release.
2. Save query bodies, API metadata, raw responses, manifests, file IDs,
   timestamps, checksums, access classes, and object-store locations.
3. Verify all counts, checksums, duplicates, modality links, and failed files.
4. Quarantine malformed or unexpected inputs; never silently repair raw data.
5. Transform raw data deterministically into normalized and analysis-ready
   layers while retaining lineage.
6. Have a second reviewer verify the snapshot manifest and external-drive paths.

G5 exit criteria:

- snapshot is immutable and independently verified;
- raw-to-analysis-ready lineage is complete;
- no controlled data or PHI entered Cortex v0;
- the cohort can be rebuilt without manual file manipulation.

### Phase 6 — Build and quality-check the cohort

Actions:

1. Resolve participants, samples, aliquots, and assay records deterministically.
2. Apply prespecified primary-tumor and sample-selection rules.
3. Normalize receptor values without erasing raw values or uncertainty.
4. Apply the locked intrinsic-subtype method and retain scores/confidence.
5. Derive clinical categories and concordance status.
6. Produce a mutually exclusive exclusion log and cohort-flow diagram.
7. Report missingness before and after exclusions.
8. Test invariants with synthetic fixtures and manually inspect a blinded sample
   of transformations without examining outcomes.

Required outputs:

- cohort-flow table and diagram;
- variable dictionary and derivation audit;
- missingness matrix;
- class counts and low-cell warnings;
- quality-control report and exclusion ledger.

Gate: no scientific result is interpreted until cohort QA is approved.

### Phase 7 — Execute the discovery analysis

Actions:

1. Run the preregistered primary classification analysis once on the frozen cohort.
2. Generate cross-implementation transitions, stability estimates, uncertainty,
   centroid-margin results, and the alluvial figure.
3. Execute prespecified clinicopathologic association models.
4. Execute only the molecular analyses defined in the protocol.
5. Apply multiplicity control by analysis family.
6. Preserve failed models, warnings, nulls, contradictory findings, and effect
   estimates regardless of significance.
7. Capture the Git commit, environment, parameters, seeds, inputs, logs, tables,
   figures, and machine-readable outputs in one run manifest.

G6 discovery decision:

- **advance:** result is technically sound and meaningful enough to validate;
- **conditional advance:** limitations require a locked amendment or narrower claim;
- **stop:** result is unsupported, uninformative, or not reproducible.

Statistical significance alone cannot trigger advancement.

### Phase 8 — Perform exploratory outcome analysis

Overall survival is secondary and exploratory because TCGA treatment and
follow-up context are limited.

Actions:

1. Report events, follow-up, missingness, and group sizes before modeling.
2. Generate Kaplan-Meier estimates where appropriate.
3. Fit only preregistered Cox models with justified adjustment sets.
4. Report hazard ratios, confidence intervals, absolute descriptive context,
   proportional-hazards tests, convergence, and influence diagnostics.
5. Execute the locked sensitivity analyses.
6. Avoid treatment-effect, recurrence, or clinical-utility language.

Stop or abstain when event counts, follow-up, confounding, or diagnostics do not
support interpretable estimation.

### Phase 9 — Reproduce and stress-test internally

Actions:

1. Rerun the complete pipeline in a clean environment from immutable snapshots.
2. Compare all key numerical outputs within declared tolerances.
3. Verify that tables and figures are generated directly from frozen outputs.
4. Test implementation, preprocessing, and consensus perturbations exactly as preregistered.
5. Conduct subgroup and fairness-oriented checks only where sample sizes permit.
6. Run leakage, cohort-overlap, duplicate-sample, and data-lineage checks.
7. Have the founder inspect a declared random sample of claim-to-result links
   during a separate reproducibility pass and preserve the sample seed.

Gate: unexplained numerical drift or manual result transcription blocks validation.

### Phase 10 — Execute independent external validation

Before opening validation outcomes:

1. Lock a validation addendum defining cohort, mapping compatibility, primary
   estimand, transportability differences, missingness, and success criteria.
2. Snapshot the approved external source and record cohort overlap.
3. Do not alter discovery definitions to improve validation performance.

Validation actions:

- reproduce the primary stable and unstable proportions and transition pattern;
- test prespecified key correlates;
- quantify heterogeneity rather than requiring identical point estimates;
- report assay, population, treatment-era, and preprocessing differences;
- classify the result as supported, partially supported, unsupported, or
  inconclusive using predeclared criteria.

G7 exit criteria:

- validation is complete and reviewed, including a failed or inconclusive result;
- any post hoc explanation is labeled exploratory;
- claims are narrowed to the evidence actually reproduced.

### Phase 11 — Assemble evidence and freeze the research release

Actions:

1. Create atomic claims with identifiers and claim types: descriptive,
   association, prognostic, mechanistic hypothesis, or interpretation.
2. Link every number to a frozen table cell or machine-readable result.
3. Link every literature statement to an approved citation and supporting passage.
4. Record conflicting evidence, nulls, limitations, deviations, funding,
   conflicts, data acknowledgements, and AI use.
5. Run numerical-fidelity, citation-validity, unsupported-claim, provenance,
   and appropriate-abstention evaluations.
6. Freeze the protocol, snapshots, code, environment, runs, evidence graph,
   tables, figures, reviews, and disclosures under a release ID.
7. Reproduce checksums and the release inventory in a clean, separate run.

G8 exit criteria:

- the founder approves the frozen release with complete review provenance;
- no paper wording is permitted to exceed its claim class;
- a failed or null study may still be released when scientifically informative.

### Phase 12 — Draft the scientific paper

Use an IMRaD structure and complete STROBE plus applicable REMARK items.

Planned manuscript:

1. Title and structured abstract
2. Introduction and precise knowledge gap
3. Methods
   - design, cohorts, sources, ethics/data status, and governance;
   - assays, preprocessing, classification mapping, and quality control;
   - outcomes, estimands, models, missingness, multiplicity, and sensitivities;
   - validation, software, reproducibility, and AI-use disclosure.
4. Results
   - cohort flow and characteristics;
   - primary stability groups, transitions, and confidence results;
   - clinicopathologic and molecular characterization;
   - exploratory outcome results;
   - sensitivity and external-validation results.
5. Discussion
   - principal findings, prior evidence, biological interpretation;
   - alternative explanations, limitations, generalizability;
   - research implications without clinical overreach.
6. Data and code availability
7. Author contributions, funding, conflicts, acknowledgements, and references

Every number and substantive sentence must carry a trace to the frozen release,
an approved external source, or an explicitly labeled interpretation.

### Phase 13 — Scientific and publication review

Founder review passes:

1. **Clinical/molecular:** definitions, mappings, relevance, and overstatement.
2. **Statistical:** estimands, denominators, models, diagnostics, uncertainty,
   multiplicity, and consistency between text, tables, and figures.
3. **Reproducibility:** clean run, release inventory, checksums, and code/data statement.
4. **Governance:** source terms, attribution, privacy, exports, and disclosures.
5. **Claim audit:** sentence-level evidence trace and prohibited clinical language.
6. **Editorial:** clarity, accessibility, terminology, references, and figure captions.

The AI-assisted reviewer performs an additional adversarial claim, numerical,
and consistency audit. Its findings are advisory and cannot authorize release.
The founder then invites one or more qualified domain or statistical experts
from his network to critique the near-final manuscript when available. Their
identity, qualifications, conflicts, reviewed version, comments, and resolutions
are recorded as `independent_human_review`; this is external expert feedback,
not journal peer review.

All comments receive an owner and resolution. Material analytical changes
require a versioned protocol deviation, rerun, and renewed founder review.

G9 prerequisite: the founder approves the exact PDF and web-content commit
derived from the frozen release after the review record is complete.

### Phase 14 — Produce the website edition

The existing `nas-website` publication system will be used.

Core-to-website handoff package:

- publication release ID and checksums;
- approved title, abstract, summary, authors, date, version, and citation;
- web-ready paper sections generated from the approved manuscript;
- publication-quality SVG/PNG figures and accessible alt text;
- tables with notes, denominators, units, and downloadable data where permitted;
- approved sources, data/code availability, acknowledgements, limitations,
  conflicts, funding, and AI-use disclosure;
- version-of-record PDF and change log.

Website implementation:

1. Add a dedicated paper-data module under `src/data/`.
2. Add a `researchItems` record in `src/data/researchLibrary.js`.
3. Add figures under `public/research/pam50-stability/visuals/`.
4. Add the PDF under `public/research/papers/`.
5. Render the long-form route at the planned `/research/...` URL.
6. Provide summary, methods, results, limitations, sources, citation, related
   research, PDF download, version, and publication note.
7. Add page metadata, canonical URL, social preview, structured data where
   appropriate, and sitemap inclusion.
8. Verify accessible headings, tables, keyboard navigation, contrast, alt text,
   responsive layouts, print/PDF integrity, and link behavior.
9. Run the production build and inspect a deployment preview on desktop and mobile.
10. Compare every displayed number and figure checksum with the frozen release.

No result is copied manually from a notebook into the website.

### Phase 15 — Publish and verify production

Actions:

1. Record final founder scientific, governance, publication, and web approvals.
2. Tag the NaS Core research release and website publication version.
3. Merge/push the approved website commit through the normal deployment path.
4. Verify the live canonical URL, PDF, images, metadata, citation, and mobile view.
5. Archive production screenshots and an HTML/PDF checksum in the release record.
6. Publish a concise release note that states the design and limitations.
7. Prepare social posts only from approved claims and link to the paper—not to
   unsupported interpretations.

The initial public version is `1.0`. It must be labeled founder-led, internally
reviewed, and not peer reviewed unless and until a journal completes formal
peer review. Silent substantive edits are prohibited.

### Phase 16 — Maintain, correct, and decide what follows

Actions:

1. Provide a visible route for scientific feedback and correction requests.
2. Triage issues as typographic, metadata, interpretive, analytical, or retraction-level.
3. Version material corrections and preserve prior releases.
4. Re-run source/link checks and monitor relevant new evidence on a declared schedule.
5. Record citations, external critiques, replication attempts, and partnership interest.
6. Hold a translation decision review.

Possible final decisions:

- no further work because evidence is unsupported or not useful;
- publish a narrower follow-up analysis;
- validate in a stronger clinical or real-world cohort;
- pursue biological or assay validation with a partner;
- design a separate clinical-utility study of additional molecular review.

The published paper is an evidence milestone, not automatic authorization to
build or deploy patient-level decision support.

## 6. Planned primary tables and figures

| ID | Artifact | Purpose |
| --- | --- | --- |
| Figure 1 | Study and cohort-flow diagram | Make selection and missingness visible |
| Figure 2 | Cross-implementation alluvial plot | Show how individual subtype assignments move |
| Figure 3 | Stability and centroid-margin results | Report primary groups, confidence, and denominators |
| Figure 4 | Clinicopathologic correlates | Compare stable luminal, robust non-luminal, and unstable groups |
| Figure 5 | Prespecified molecular/pathway landscape | Test whether robust discordance has distinct biology |
| Figure 6 | External-validation comparison | Show transportability and heterogeneity |
| Table 1 | Cohort characteristics and missingness | Describe discovery and validation cohorts |
| Table 2 | Primary stability-group proportions | Report estimates with confidence intervals |
| Table 3 | Prespecified adjusted associations | Report effect sizes, uncertainty, and multiplicity |
| Table 4 | Sensitivity and validation results | Preserve robustness, nulls, and contradictions |

Survival figures appear only if the preregistered event and diagnostic criteria
are satisfied.

## 7. Project-wide stop and abstention rules

Stop, narrow, or explicitly abstain when:

- classification mappings are not clinically or scientifically defensible;
- sample linkage, assay provenance, or cohort selection cannot be reproduced;
- missingness or sparse categories make the primary estimate misleading;
- outcome event counts or model diagnostics are inadequate;
- an apparent signal depends on an unplanned preprocessing choice;
- multiplicity-adjusted results do not support the stated molecular claim;
- external validation is unavailable, incompatible, failed, or inconclusive;
- source terms do not permit the intended analysis or public artifact;
- a result cannot be traced to an immutable input and executed run;
- the founder or an external critic cannot clearly distinguish the evidence
  from a clinical recommendation.

An honest negative or inconclusive paper is an acceptable scientific completion.

## 8. Immediate next actions

1. Complete the founder scientific/product, molecular/pathology, and statistical
   self-review passes plus the non-authoritative AI adversarial pass.
2. Resolve findings and have the founder approve, revise, hold, or reject
   `NAS-RQ-BRCA002`.
3. Finish `NAS-BRCA-001` platform qualification before discovery execution.
4. If selected, register bibliographic sources and lock the literature protocol.
5. Build the field-level TCGA and external-validation feasibility matrix.

No article retrieval, biomedical-data ingestion, or outcome inspection is
authorized by this planning document.
