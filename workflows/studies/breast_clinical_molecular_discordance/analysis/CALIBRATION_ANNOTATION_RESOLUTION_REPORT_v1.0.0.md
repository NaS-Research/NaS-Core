# Calibration annotation-resolution report 1.0.0

Frozen revision `b7e50cf` re-fetched the checksum-identical GSE130397 family
SOFT representation and reconciled every sample's official processing metadata.
Receipt `calibration_annotation_resolution_receipt_v1.0.0.yaml` has SHA-256
`532cda236f511f489b80221fb740cd8ea2011dc5bea2bd0d9c86f95f3f028f22`.

- All 21 samples declare STAR GeneCounts against GRCh38, Ensembl release 84.
- All 15 Access-library samples specify the reverse (`rev`) count column.
- All six NuGEN Ovation samples specify the forward (`fwd`) count column.
- The exact annotation candidate is Ensembl's archived
  `Homo_sapiens.GRCh38.84.gtf.gz`, 45,686,368 bytes.

No sample identifier, processing row, molecular value, outcome, or raw metadata
artifact was retained. This resolves the annotation release and strandedness
decision but does not itself map a gene, inspect an outcome, execute a classifier,
estimate a threshold, authorize export, or authorize publication.
