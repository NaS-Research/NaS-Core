# Ingestion

NaS ingestion adapters register exact external requests, capture upstream
release metadata, preserve raw response bytes, calculate SHA-256 checksums, and
write content-addressed snapshot manifests to object storage.

The first adapter targets the public GDC cases endpoint. Preview the exact
TCGA-BRCA request without contacting GDC or writing data:

```bash
make gdc-plan-dry-run
```

Execution is intentionally gated. The study protocol must be independently
approved and marked `preregistered`, the exact GDC data release must be supplied,
and configured object storage must be available:

```bash
uv run nas-core ingest gdc-plan \
  workflows/tcga_brca_stage_survival/analysis_plan.yaml \
  --data-release 45.0 \
  --execute
```

Never use `--execute` with a draft or pending protocol. The runtime rejects that
operation before making a network request.

Versioned source connectors and normalization code will live here. The first
connector will target public/open GDC data and will record queries, releases,
file identifiers, access classifications, and checksums.
