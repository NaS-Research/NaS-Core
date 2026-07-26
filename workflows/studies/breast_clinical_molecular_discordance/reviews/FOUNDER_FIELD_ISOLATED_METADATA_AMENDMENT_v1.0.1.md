# Founder Field-Isolated Metadata Audit Amendment

Version: `1.0.1`

Study: `NAS-BRCA-002`

Question: `NAS-RQ-BRCA002` version `0.3.0`

Status: **Founder decision required**

## Why this amendment is required

Founder-authorized audit `1.0.0` passed four of five feasibility checks. It
verified complete historical PAM50 gene coverage in the frozen TCGA-BRCA and
GSE96058 representations and quantified ER/PR/HER2 completeness in both sources.

The GSE96058 SOFT characteristic fields did not contain the declared
primary-versus-technical-replicate linkage. The fail-closed parser therefore
classified zero records and returned `changes_requested`.

The official GEO accession description states that the sample title encodes this
relationship: a primary sample may be titled `F30` and its technical replicate
`F30repl`. The current authorization did not include `!Sample_title`, so audit
`1.0.0` did not parse or retain that field.

Audit `1.0.0` also observed already-authorized receptor category values `0`, `1`,
and `NA`. It counted completeness correctly but did not prespecify their
source-specific category labels.

## Proposed authorized change

If confirmed, NaS Core may implement and execute audit `1.0.1`, using the same
four source representations and all prior prohibitions, with only these changes:

1. permit `!Sample_title` solely for replicate classification;
2. require every parsed title to match `^F[0-9]+(?:repl)?$`;
3. classify a title ending in `repl` as a technical replicate and link it to the
   primary title obtained by removing that suffix;
4. classify a matching title without the suffix as primary;
5. retain only aggregate primary, technical-replicate, linked, unlinked, and
   unclassified counts—never sample titles or accessions;
6. verify that every technical-replicate base title exists among the projected
   primary titles;
7. map the already-authorized GSE96058 receptor values `1` to `positive`, `0` to
   `negative`, and `NA` to missing;
8. reject any unrecognized sample-title form or receptor category;
9. require exact re-fetch checksums and record any representation change; and
10. emit a new immutable `1.0.1` receipt without modifying or replacing the
    `1.0.0` `changes_requested` receipt.

Official source:
<https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE96058>

## Unchanged prohibitions

- No sample accession or title may be retained.
- No patient-level receptor or replicate record may be retained.
- No molecular value may be parsed or stored.
- No treatment, survival, subtype, prediction, or unapproved field value may be
  parsed or stored.
- No raw source may be stored.
- No cohort may be constructed.
- No expression calculation, subtype scoring, threshold selection, model fitting,
  validation, outcome analysis, or clinical inference may be performed.
- No preregistration, scientific conclusion, or publication claim is authorized.

## Exact confirmation statement

After reviewing this amendment, the founder may authorize it by replying exactly:

```text
I authorize field-isolated metadata audit amendment 1.0.1 as written.
```

Any other material change requires a new packet version and a new exact
confirmation.
