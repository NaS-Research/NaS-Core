# NAS-BRCA-002 Screening Protocol

Version: `1.0.0`

Input execution: `83d33fb2…4434`

Status: **Locked before title/abstract decisions**

## Objective

Identify records requiring full-text review for the Phase 0 novelty audit while
preserving uncertainty and a complete exclusion trail. Screening is evidence
selection, not evidence synthesis and not proof of novelty.

## Title and abstract decisions

Each of the 457 deduplicated records receives exactly one founder decision:

- `include`: plausibly satisfies at least one locked inclusion criterion and
  should advance to full-text review;
- `exclude`: clearly fails eligibility and receives exactly one primary reason;
- `unclear`: available metadata is insufficient or conflicting, so the record
  advances for manual resolution rather than being silently removed; or
- `pending`: no human decision has been recorded.

When uncertain, use `unclear`, not `exclude`. Journal, author, citation count,
direction of findings, and perceived prestige are not eligibility criteria.

## Primary exclusion reasons

Use the first applicable reason in this ordered taxonomy:

1. `nonhuman_or_no_primary_human_tumor_cohort`
2. `no_molecular_intrinsic_subtype_measure`
3. `no_relevant_discordance_stability_or_classifier_method`
4. `review_editorial_or_commentary_for_citation_chaining_only`
5. `duplicate_or_superseded_report_without_distinct_contribution`
6. `outside_breast_cancer_scope`

Missing abstract, inaccessible full text, unclear assay description, or uncertain
cohort overlap is not a title/abstract exclusion reason; use `unclear`.

## Human and AI roles

Dalron J. Robertson performs and records every final screening decision as founder
and internal reviewer. Any future AI triage is advisory only, is stored separately,
and cannot populate the final decision, reviewer, timestamp, or exclusion reason.
The initial queue contains zero human and zero AI decisions.

Final decisions are recorded as append-only events. Corrections and resolution of
an `unclear` decision must explicitly supersede the current event and state why;
prior events remain immutable. Each batch is bound to the latest verified progress
receipt so stale submissions cannot silently replace newer review work.

## Full-text stage

Included and unresolved records proceed to a separately versioned full-text queue.
Full-text access and retention must respect item-level rights. Every full-text
exclusion receives one reason, and related reports from the same cohort are linked
rather than discarded as duplicates when they contribute distinct methods or outcomes.

## Completion gate

Title/abstract screening is complete only when no record remains `pending`, every
exclusion has one human reviewer, timestamp, and reason, all `unclear` records are
resolved or advanced, counts reconcile to 457, and an aggregate receipt is
independently verified. Completion does not establish novelty or authorize data analysis.
