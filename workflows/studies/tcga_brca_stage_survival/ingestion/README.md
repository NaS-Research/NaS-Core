# Ingestion

Store source-specific query definitions and transformation code here. Immutable
responses, manifests, and snapshots belong in external object storage.

## Locked source release

- Declared GDC Data Release: `45.0`
- Official release date: 2025-12-04
- Official release-notes reference:
  <https://docs.gdc.cancer.gov/Data/Release_Notes/Data_Release_Notes/>
- Verified against the official page: 2026-07-21

Data Release `45.0` and API version `8.5.0` are different provenance facts. The
snapshot freezes the official release-notes bytes and checksum separately from
the GDC API `/status` response.

## Commands

The dry run prints the exact case query without network or storage activity:

```bash
uv run nas-core ingest gdc-plan \
  workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml
```

Real execution additionally requires the declared release and official
reference. Do not execute until external object storage has been checked:

```bash
uv run nas-core ingest gdc-plan \
  workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml \
  --data-release 45.0 \
  --release-notes-url \
  https://docs.gdc.cancer.gov/Data/Release_Notes/Data_Release_Notes/ \
  --execute
```
