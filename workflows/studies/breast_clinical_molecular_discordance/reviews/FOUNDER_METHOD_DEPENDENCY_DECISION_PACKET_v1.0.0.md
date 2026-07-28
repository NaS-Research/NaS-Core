# Founder Method-Dependency Decision Packet 1.0.0

Study: `NAS-BRCA-002`  
Question: `NAS-RQ-BRCA002`, version `0.3.0`  
Prepared: 2026-07-28  
Decision type: founder scientific and product-method decision

## Checksum boundary

This packet reviews
`protocol/method_dependency_audit_proposal_v1.0.0.yaml`, SHA-256
`595e32bf32af0a10f2960306318975704e9a998070ff3e05c0ae0a79eba48968`.

The proposal is itself bound to founder-authorized saturated synthesis SHA-256
`e3374a8781e2e42b14d7b536e5df281d68eda9cc7efa1ffbaad1d9269de83e77`
and draft reliability specification SHA-256
`4c9ba242e8c09ef1502a69179644c8c02f2fa93a3d583961c626b34915895f07`.
Any byte change invalidates this packet.

## What was resolved

Official Bioconductor `genefu` 2.44.0 distributes the official unscaled PAM50
model under Artistic-2.0. The source archive SHA-256 is
`666654431aa3b65a30eb23983fe8d7bc6c5daba0c957ddf33e4e990d7333b858`;
embedded `genefu/inst/extdata/pam50_model.csv` SHA-256 is
`a189eb07569ee25b9aebd189c466faab4e4886559bae97ee5ad8e72a3c0aba4e`.
This is a verified candidate, not yet an approved NaS method artifact.

Route-neutral artifact QA has since materialized the canonical candidate under
frozen importer revision `2843a6e`. The candidate contains exactly 250 finite
coefficients across five subtype vectors and 50 canonical genes. It applies only
the three prespecified historical aliases. Candidate artifact SHA-256 is
`51a1b186a32ba02fa61a001ee7dc7e21876b9b09f78cb7eb8f0fdd068b4f8c2b`.
The import receipt records zero molecular or outcome access and zero method
execution authorization. This additional verification does not select a route.

## What remains unresolved

The historical-PAM50 design still lacks:

1. an independently validated, platform-appropriate fixed centering reference;
2. a defensible numerical bridge between TCGA and GSE96058;
3. an independent RNA-seq technical-error calibration resource;
4. evidence-backed margin and label-retention thresholds; and
5. cross-language numerical conformance tolerances.

GSE96058 has 136 public technical replicates, but it is the designated external
validation source. Calibrating on those replicates would adapt the method to that
source. The strongest separate 144-pair NanoString study publishes aggregate
reproducibility but states that its participant-level data are not public.

## Decision routes

### Route A — retain historical PAM50

Keep the current question and historical Spearman centroid classifier. NaS must
obtain or independently establish a lawful fixed reference and separate
technical-error calibration before molecular execution.

### Route B — change to MPAM50

Amend the question to use published MPAM50 weighted uncentered centroids and
Pearson correlation. This removes centering but materially changes the
classifier, does not resolve technical calibration, and weakens TCGA independence
because TCGA contributed to MPAM50 training.

### Route C — hold execution and acquire independent calibration

Preserve question `0.3.0`, stage the verified centroid candidate for coefficient
QA, and withhold molecular execution while seeking an independent calibration
source, lawful restricted-data access, or a future NaS replicate experiment.

## AI review position

Codex recommends **Route C**. Route A is not currently executable without an
arbitrary reference and error model. Route B is possible but changes the question
and still lacks independent calibration. Route C preserves the strongest eventual
publication: a method locked before external validation, with thresholds tied to
genuinely independent technical evidence.

## Authorization boundary

No route is selected by this packet. It authorizes no patient-level access,
molecular access, outcome access, classifier execution, threshold selection,
clinical use, publication, or submission.

## Founder decision statements

Choose exactly one:

- `I approve NAS-BRCA-002 method dependency Route A as written.`
- `I approve NAS-BRCA-002 method dependency Route B as written.`
- `I approve NAS-BRCA-002 method dependency Route C as written.`
- `I reject all NAS-BRCA-002 method dependency routes and request question redesign.`
