# Founder Citation Appraisal Batch 0011

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Founder decision required**

This packet presents two AI-assisted, checksum-bound full-text appraisal
proposals created from citation pass 4. It contains no founder appraisal
decision, scientific conclusion, novelty finding, causal treatment claim, or
clinical recommendation.

## Immutable proposal set

| Article | Proposal SHA-256 | Proposed role |
|---|---|---|
| `PMC5947827-v1.0.0.yaml` | `3a5b9f4616c3ed3fe3ee632dedd4922859b2da40a7a28d7b84fab9590ae8a951` | `context_only` |
| `PMC9604175-v1.0.0.yaml` | `af35e193c33af58508b377ea4137f313d25033172d09fc83f419abc9a70ecf2d` | `context_only` |

Both proposals pass the typed non-authoritative schema. `PMC5947827` was
reverified against 100,076 canonical official PMC OAI bytes, including identity,
content checksum, bounded derivative narrative, and verbatim-leakage checks;
zero article bytes were retained. `PMC9604175` is stored only in governed
external object storage under CC BY 4.0.

## Source reconciliation

| Article | Source representation | Canonical bytes | Content SHA-256 | Receipt SHA-256 |
|---|---|---:|---|---|
| `PMC5947827` | canonical PMC OAI article XML, ephemeral | 100,076 | `a8ec9db3b49d6fdd63439710e53f5375554ae75c97bc014866c617307193f637` | `3486d2252856d19a0312d578aa7369af112698a4459da31b18441104827f2ae1` |
| `PMC9604175` | licensed Europe PMC article XML | 155,295 | `7ef0ce57c28959daa8be1624c22fe0595c16dbcb4f404f0afa353eb5331ed142` | `652fc4050a4d051d62dcf7658a629aae7b6730819aef8aff8a3f90e9271337e0` |

## Founder review summary

### PMC5947827 — colorectal biopsy classifier robustness

Reported observations:

- Combines eight public rectal-biopsy datasets with laser-captured, serial,
  multiregional, and prospective-trial biopsy material.
- Reports substantially more unclassified biopsies with CMS than in resection
  material and greater spatial and temporal stability with CRIS.
- Several repeated-sample analyses contain only seven or ten patients.

Review position: retain as `context_only`. This is directly relevant prior art
for biopsy, spatial, and temporal classifier reliability, but stability is not
biological correctness, the smallest strata are fragile, and colorectal results
cannot validate a breast method or clinical utility.

### PMC9604175 — morphology versus expression classifiers

Reported observations:

- Compares four blinded pathology features with CMS and CRIS calls in 218 stage
  II or III colon cancers from two retrospective cohorts.
- Reports feature-subtype associations and uncertainty estimates.
- Finds that morphology, alone or in combinations, cannot adequately reproduce
  molecular subtype assignment.

Review position: retain as `context_only`. The limiting result supports explicit
clinical-molecular discordance accounting, but exploratory multiplicity,
partly single-observer scoring, platform differences, and an imperfect molecular
reference prevent a stronger evidence role.

## Decision requested

Confirming this packet will convert both proposals into founder-authorized,
AI-assisted locked appraisals. It will not make them scientific conclusions,
breast validation, or clinical recommendations.

Exact confirmation statement:

`I confirm citation appraisal batch 0011 as written.`
