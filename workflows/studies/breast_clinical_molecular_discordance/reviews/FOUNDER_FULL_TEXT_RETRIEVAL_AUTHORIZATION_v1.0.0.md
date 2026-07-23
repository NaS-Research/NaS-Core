# Founder Full-Text Retrieval Authorization — Version 1.0.0

- Study: `NAS-BRCA-002`
- Founder: Dalron J. Robertson
- Decision date: 2026-07-22
- Decision: authorized for explicitly licensed provisional inclusions

The founder confirmed the governed full-text retrieval plan after the 27-record
access inventory was presented. Retrieval is limited to current founder-included
records obtained through official automated repositories when item-level metadata
declares an approved reuse license. Version `1.0.0` permits CC BY 4.0 only.

The retriever must verify article identity and license from the returned document,
store exact content immutably outside Git, record hashes and source provenance, and
emit only an aggregate receipt to Git. It must fail closed for absent, ambiguous, or
unapproved licenses and must not bypass authentication or publisher access controls.
Retrieval does not establish eligibility, quality, or a scientific conclusion.
