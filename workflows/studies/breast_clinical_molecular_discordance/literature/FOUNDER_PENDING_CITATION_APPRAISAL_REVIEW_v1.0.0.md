# Founder Citation Appraisal Review Index

Version: `1.0.0`

Study: `NAS-BRCA-002`

Status: **Complete—no pending citation appraisal decisions**

Purpose: preserve one audit index for the seven checksum-frozen appraisal packets,
their independent founder confirmations, and the exact evidence roles that were
materialized. The historical filename is retained so existing references do not
break.

## Decision inventory

| Batch | Packet SHA-256 | Appraisals | Version links | Supporting | Context only | Status |
|---|---|---:|---:|---:|---:|---|
| `0002` | `f45518a31273c0fed4bca6c1b53025dacbe5270ada54fcb0786afabcdedf92e2` | 4 | 0 | 2 | 2 | Confirmed |
| `0003` | `2645951e5aa9f1e72c19b5b87d88839f448b4bebbd734db2cb7dd6a4ed5bedc2` | 6 | 0 | 4 | 2 | Confirmed |
| `0004` | `b03ea2151ebb8ce4d00acb203c15ff712ab5d6f7e626949d6619a5ae259d7eda` | 1 | 0 | 1 | 0 | Confirmed |
| `0005` | `990c74c2ff79ed82088807d3dafe7fcfa9bc326825ae7f9901a2d00f3f0b8117` | 1 | 0 | 0 | 1 | Confirmed |
| `0006` | `a1bbada9a8830fedc3f3776a7bf16c9e36cce84e6c3ab1d6072fddab4cb8c002` | 2 | 0 | 0 | 2 | Confirmed |
| `0007` | `43410b02f7eef83e4fd75fd3ca16b9f84ffbede39e32660e248cef7df5c821d5` | 3 | 0 | 0 | 3 | Confirmed |
| `0008` | `30b59efed257ad8ff699b4ccf3dcd3fa33be4e0f85b75b509401a0c59c34454f` | 5 | 1 | 0 | 5 | Confirmed |
| **Total** | — | **22** | **1** | **7** | **15** | **Authorized** |

Batch `0001` is intentionally absent because it is already founder-authorized and
materialized. Batches `0002`–`0008` were independently confirmed on
2026-07-26. Their append-only confirmation artifacts are:

1. [`FOUNDER_CITATION_APPRAISAL_BATCH_0002_CONFIRMATION_v1.0.0.yaml`](FOUNDER_CITATION_APPRAISAL_BATCH_0002_CONFIRMATION_v1.0.0.yaml)
2. [`FOUNDER_CITATION_APPRAISAL_BATCH_0003_CONFIRMATION_v1.0.0.yaml`](FOUNDER_CITATION_APPRAISAL_BATCH_0003_CONFIRMATION_v1.0.0.yaml)
3. [`FOUNDER_CITATION_APPRAISAL_BATCH_0004_CONFIRMATION_v1.0.0.yaml`](FOUNDER_CITATION_APPRAISAL_BATCH_0004_CONFIRMATION_v1.0.0.yaml)
4. [`FOUNDER_CITATION_APPRAISAL_BATCH_0005_CONFIRMATION_v1.0.0.yaml`](FOUNDER_CITATION_APPRAISAL_BATCH_0005_CONFIRMATION_v1.0.0.yaml)
5. [`FOUNDER_CITATION_APPRAISAL_BATCH_0006_CONFIRMATION_v1.0.0.yaml`](FOUNDER_CITATION_APPRAISAL_BATCH_0006_CONFIRMATION_v1.0.0.yaml)
6. [`FOUNDER_CITATION_APPRAISAL_BATCH_0007_CONFIRMATION_v1.0.0.yaml`](FOUNDER_CITATION_APPRAISAL_BATCH_0007_CONFIRMATION_v1.0.0.yaml)
7. [`FOUNDER_CITATION_APPRAISAL_BATCH_0008_CONFIRMATION_v1.0.0.yaml`](FOUNDER_CITATION_APPRAISAL_BATCH_0008_CONFIRMATION_v1.0.0.yaml)

## Historical review order

Review in numerical order because later packets extend the earlier evidence
boundary:

1. [`FOUNDER_CITATION_APPRAISAL_BATCH_0002_v1.0.0.md`](FOUNDER_CITATION_APPRAISAL_BATCH_0002_v1.0.0.md)
2. [`FOUNDER_CITATION_APPRAISAL_BATCH_0003_v1.0.0.md`](FOUNDER_CITATION_APPRAISAL_BATCH_0003_v1.0.0.md)
3. [`FOUNDER_CITATION_APPRAISAL_BATCH_0004_v1.0.0.md`](FOUNDER_CITATION_APPRAISAL_BATCH_0004_v1.0.0.md)
4. [`FOUNDER_CITATION_APPRAISAL_BATCH_0005_v1.0.0.md`](FOUNDER_CITATION_APPRAISAL_BATCH_0005_v1.0.0.md)
5. [`FOUNDER_CITATION_APPRAISAL_BATCH_0006_v1.0.0.md`](FOUNDER_CITATION_APPRAISAL_BATCH_0006_v1.0.0.md)
6. [`FOUNDER_CITATION_APPRAISAL_BATCH_0007_v1.0.0.md`](FOUNDER_CITATION_APPRAISAL_BATCH_0007_v1.0.0.md)
7. [`FOUNDER_CITATION_APPRAISAL_BATCH_0008_v1.0.0.md`](FOUNDER_CITATION_APPRAISAL_BATCH_0008_v1.0.0.md)

Each packet states its observations, seven domain judgments, review position, and
interpretation boundary. Each confirmation authorized only those exact proposal
bytes as founder-with-AI-assistance appraisals. It did not approve the manuscript,
authorize molecular-data access, establish novelty, or make a clinical claim.

## Recorded exact confirmation statements

The founder supplied these seven independent exact statements in one message:

```text
I confirm citation appraisal batch 0002 as written.
I confirm citation appraisal batch 0003 as written.
I confirm citation appraisal batch 0004 as written.
I confirm citation appraisal batch 0005 as written.
I confirm citation appraisal batch 0006 as written.
I confirm citation appraisal batch 0007 as written.
I confirm citation appraisal batch 0008 as written.
```

Each line is preserved as an independent decision. Any future packet or proposal
change alters its checksum and requires a new version and new exact confirmation.
