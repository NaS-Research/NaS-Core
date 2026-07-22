# Zero-Cost Deterministic Screening Prioritization

Algorithm: `literature-deterministic-priority-1.0.0`

This workflow orders pending records for founder review without contacting a model
provider. It does not decide eligibility or methodological quality.

## Ranking signals

The versioned implementation scores explicit title-and-abstract terms for PAM50 or
intrinsic subtype, stability or robustness, classification uncertainty, clinical/
molecular discordance, preprocessing or centering, independent validation, human
cohorts, classifier methods, and outcomes. Secondary literature and apparent
nonhuman or cell-line focus are caution signals. Ties resolve deterministically by
publication year and screening ID.

The `core` tier requires a score of at least 17, `supporting` requires at least 12,
and lower scores are `context`. These thresholds were locked after the first
diagnostic run showed that a core threshold of 12 was too permissive (187 of 452
pending records). No screening decision had been made from that diagnostic run.

The `core`, `supporting`, and `context` tiers mean review priority only. Reviews can
remain useful for citation chaining. A low-ranked record cannot be automatically
excluded, and the command writes no human decision or scientific conclusion.

## Run

```bash
uv run nas-core literature screening-prioritize \
  workflows/studies/breast_clinical_molecular_discordance/literature/screening_queue_receipt.yaml \
  --progress-receipt workflows/studies/breast_clinical_molecular_discordance/literature/screening-progress/batch-0001.yaml \
  --limit 30
```

Review the core tier first in small batches. Apply the locked inclusion and exclusion
criteria to every final decision. After title-and-abstract inclusion, retrieve
permitted full text and apply a study-design-specific quality appraisal. The target
of fewer than 30 synthesized primary studies is an expectation, not an exclusion
rule or stopping rule.
