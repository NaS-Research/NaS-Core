# Retrieval

The governed literature runner captures locked PubMed and Europe PMC searches,
stores raw API exports and normalized records in immutable external object storage,
and emits a content-addressed manifest. It requires active source registrations,
founder Phase 0 authorization, a locked search strategy, and a valid contact email.

Preview without network or storage access:

```bash
uv run nas-core literature search \
  workflows/studies/breast_clinical_molecular_discordance/question/phase_zero_plan.yaml \
  workflows/studies/breast_clinical_molecular_discordance/literature/search_strategy.yaml \
  workflows/studies/breast_clinical_molecular_discordance/ingestion/data_feasibility.yaml
```

Count feasibility adds `--count-only --contact-email <valid-contact>` and contacts
each API once without storing records. Execution adds `--execute` instead. The
runner fails closed when either source exceeds 5,000 records so an overbroad query
must be transparently revised and re-locked before capture. The plaintext contact
address is sent to the source APIs as required but is represented in the immutable
manifest only by its SHA-256 digest. The default transport enforces no more than
three requests per second, uses bounded transient-error retries, caps Europe PMC
core pages at 100 records, and caps PubMed summary batches at 100 IDs. Raw exports,
abstracts, and normalized records never belong in Git; abstract and full-text reuse
remains subject to item-level rights.
