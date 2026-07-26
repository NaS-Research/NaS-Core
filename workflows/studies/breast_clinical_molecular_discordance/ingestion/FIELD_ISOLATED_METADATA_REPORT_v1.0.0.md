# Field-Isolated Metadata Audit Report

Version: `1.0.0`

Study: `NAS-BRCA-002`

Question: `NAS-RQ-BRCA002` version `0.3.0`

Decision: **Changes requested**

Receipt SHA-256:
`b5f8c3599219c8b13aa218e9aff3e380cbdf789aa7897b30c5ae6dfd4fea822a`

Executed code revision:
`2f0b15f4c73043ba41864040861a22fe6bc74d0c`

## Governance result

The founder supplied the exact authorization
`I authorize field-isolated metadata audit 1.0.0 as written.` The execution
verified that authorization and its packet checksum before contacting any source.

The audit streamed four public/open representations and stored none of them:

1. the registered TCGA-BRCA BCR Biotab patient table;
2. one deterministic open TCGA-BRCA STAR-count file;
3. the GSE96058 processed gene-expression artifact; and
4. the GSE96058 family SOFT representation.

Only gene identifiers, ER/PR/HER2 fields, sample accessions, and allowlisted
replicate characteristics were parsed. The receipt retains aggregate counts,
field names, source identifiers, checksums, and parser provenance. It retains no
patient-level record, sample accession, molecular value, treatment, outcome,
published subtype, prediction, raw source, cohort, or classifier output.

The receipt explicitly discloses that prohibited fields were transiently
transferred inside source bundles before the mechanical parser rejected them.

## Verified findings

### PAM50 coverage

- The deterministic GDC STAR-count representation contained all 50 historical
  PAM50 canonical genes, with zero missing genes and zero ambiguous canonical
  mappings.
- The GSE96058 processed representation contained all 50 historical PAM50
  canonical genes, with zero missing genes and zero ambiguous canonical mappings.
- These checks prove gene availability only. They do not establish compatible
  units, transformations, centering, assay equivalence, or classifier validity.

### TCGA-BRCA receptor fields

Among 1,098 BCR patient records:

- ER was present for 1,049;
- PR was present for 1,048;
- HER2 was present for 983; and
- all three were present for 981.

The counts establish that the registered clinical supplement can support a
future prespecified completeness and eligibility procedure. They do not establish
diagnostic correctness or authorize cohort construction.

### GSE96058 receptor fields

Among 3,409 GEO sample records:

- ER was present for 3,189;
- PR was present for 3,051;
- HER2 was present for 3,281; and
- all three were present for 2,931.

The source encodes receptor categories as `0`, `1`, and `NA`. Audit `1.0.0`
correctly counted nonmissing values but conservatively labeled the retained
nonmissing category counts as `other`; a future parser version must prespecify
the source-specific `0`/`1` interpretation before reporting positive/negative
counts.

## Unresolved finding

The approved GEO characteristic allowlist contained receptor fields but no
primary-versus-technical-replicate characteristic. All 3,409 sample records
therefore remained unclassified for replicate state, and the audit correctly
returned `changes_requested`.

The official GEO accession description states that sample titles distinguish
primary samples such as `F30` from technical replicates such as `F30repl`, and
that 136 cases have technical replicates. Audit `1.0.0` did not read or retain
`!Sample_title`, because that field was not in the approved parser allowlist.
Expanding the allowlist requires a separately versioned founder decision.

Official source:
<https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE96058>

## Interpretation boundary

This is an input-feasibility result, not a biological or clinical finding. No
expression calculation, subtype score, association test, threshold fit, model
training, cohort analysis, survival analysis, diagnostic conclusion, treatment
recommendation, or clinical-utility claim was performed or authorized.

Molecular and outcome execution remain prohibited.

