# Calibration-Source Lineage Report 1.0.0

Study: `NAS-BRCA-002`  
Route: `ROUTE-C`  
Executed: 2026-07-28  
Receipt SHA-256: `ef3cce520232df76640685bf3e5936e934264fdfa66c6ab05cb85eb4ec1389d2`

## Audit boundary

Frozen revision `d256342` streamed the official GEO family SOFT
representations for GSE60788, GSE96058, and GSE130397. The parser projected only
sample accession and title long enough to calculate aggregate lineage counts and
cross-source public-identity overlap. It retained no accessions, titles, rows, raw
artifacts, expression values, outcomes, treatment fields, cohorts, or classifier
results.

The official representations contained additional fields that were transiently
transferred but never parsed into the projection. This is disclosed in the
receipt rather than being silently described as a field-level remote query.

## Results

| Source | Sample records | Primary or unlabeled | Replicate labeled | Linked replicates |
|---|---:|---:|---:|---:|
| GSE60788 | 55 | 49 | 6 | 6 |
| GSE96058 | 3,409 | 3,273 | 136 | 136 |
| GSE130397 | 21 | 10 | 11 | 11 |

GSE60788 and GSE96058 share zero public GEO sample accessions and zero public
sample titles.

## Interpretation

The audit establishes metadata lineage feasibility: every public sample title
matched the source-specific projection, and every replicate-labeled record linked
to a public title group.

It does **not** establish that GSE60788 and GSE96058 use disjoint biological
specimens or RNA extractions. Different GEO accessions and titles are insufficient
to rule out re-registration, renamed samples, or related source material.
Likewise, title patterns alone do not distinguish same-RNA library reconstruction
from resequencing or another replicate design.

## Decision

No calibration source is selected. GSE60788 remains a due-diligence candidate;
GSE96058 remains external-validation-only; and GSE130397 remains a small
variance-feasibility resource. Authoritative lineage confirmation and a separately
governed gene-panel audit remain required before source eligibility can change.
