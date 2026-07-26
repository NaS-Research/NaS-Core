# Founder Field-Isolated Metadata Authorization

Version: `1.0.0`

Study: `NAS-BRCA-002`

Question: `NAS-RQ-BRCA002` version `0.3.0`

Status: **Founder decision required**

## Why this decision is required

Metadata feasibility audit `1.0.0` verified source availability but could not
establish ER/PR/HER2 completeness or exact PAM50 gene coverage. The required
fields are not exposed through safe source-level aggregates:

- TCGA receptor fields reside in clinical-supplement content rather than the
  current indexed GDC case mapping;
- expression-table gene identifiers are packaged with expression values; and
- GSE96058 receptor and replicate fields are packaged with treatment, survival,
  published subtype, and prediction attributes.

The existing Phase 0 authorization prohibits patient-level biomedical data,
molecular expression, and outcome retrieval. It cannot authorize the transient
bytes required for a field-isolated projection.

## Proposed authorized work

If confirmed, NaS Core may implement and execute a versioned projection gate that:

1. retrieves only registered public/open TCGA-BRCA clinical supplements required
   to locate ER, PR, and HER2 fields;
2. retains only aggregate completeness counts, permitted category counts, field
   provenance, source-file identifiers, and checksums;
3. retrieves one frozen open TCGA-BRCA STAR-count artifact solely to read its gene
   identifier column;
4. retrieves the public GSE96058 processed gene-expression artifact solely to read
   its gene identifier column;
5. retains only canonical/alias PAM50 coverage, duplicate/unmapped identifiers,
   source checksums, and parser provenance;
6. retrieves GSE96058 family metadata through a fail-closed parser that permits
   only sample accession, primary-versus-technical-replicate linkage, and ER, PR,
   and HER2 status;
7. rejects and discards age, treatment, survival, published PAM50 subtype,
   classifier predictions, and every unapproved field before any derivative is
   computed;
8. stores no raw clinical supplement, expression matrix, or GEO family bundle;
9. performs no expression calculation, subtype scoring, association test,
   threshold fitting, model training, or outcome analysis; and
10. produces one checksum-bound feasibility receipt and an explicit
    `pass`, `changes_requested`, `hold`, or `fail` recommendation.

The implementation must be tested with synthetic fixtures before contacting a
remote source. Every endpoint, file identifier, checksum, permitted field, rejected
field, count, warning, and software revision must be recorded.

## Explicitly not authorized

- Retaining patient-level receptor, replicate, expression, treatment, subtype,
  prediction, survival, or clinical records.
- Reading expression values for any calculation.
- Using published subtype labels or predictions as classifier targets.
- Cohort construction or eligibility assignment.
- PAM50 scoring, perturbation, threshold selection, model fitting, or validation.
- Clinical-outcome retrieval or analysis.
- Diagnostic, prognostic, treatment, biological-truth, or clinical-utility claims.
- Preregistration, release freezing, manuscript conclusions, or website publication.

## Risk and interpretation boundary

Network retrieval will transiently transfer files containing fields outside the
retained projection. Mechanical allowlists, deny lists, zero raw storage, bounded
memory/disk handling, checksums, and tests reduce—but do not eliminate—the risk of
accidental retention. Confirmation accepts this narrow transient-access risk only
for feasibility verification.

A complete gene list proves input availability, not assay equivalence. Receptor
completeness proves eligibility feasibility, not diagnostic accuracy. Neither
finding validates the NaS method or permits patient-level interpretation.

## Exact confirmation statement

After reviewing this packet, the founder may authorize the work by replying exactly:

```text
I authorize field-isolated metadata audit 1.0.0 as written.
```

Any material change to the permitted fields, endpoints, retained derivatives,
prohibited operations, or interpretation boundary requires a new packet version
and a new exact confirmation.
