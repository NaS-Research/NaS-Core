# GSE81538 family SOFT acquisition 1.0.0

## Decision

The separate public sample-metadata acquisition passed. The official GSE81538
family SOFT object is stored immutably in governed external storage and is ready
for a later field-isolated parser. No metadata field was parsed during acquisition.

## Provenance

- Frozen implementation revision: `8e105f1`
- Acquisition-plan SHA-256: `b2485481903e7852bcad2743105db6188d718e5ca4959105dfed9649d76ba43a`
- Exact source bytes: `51,036`
- Source SHA-256: `8d7bab685bb6ed135f64da10273e9b159e761e813a100a057829f5159957332c`
- Last-Modified header: `Sat, 13 Jun 2026 05:24:56 GMT`
- Acquisition-receipt SHA-256: `920a40f89c1049ce58c95d1a486a22fb53cdeba8366e56dfb09655cacca29f98`
- Object key: `raw/nas-brca-002/ncbi-geo-gse81538/gse81538_family.soft.gz`

Independent local `stat` and SHA-256 checks reproduced the receipt's exact byte
length and object checksum.

## Boundary

The receipt classifies the artifact as `sample_metadata`, records that source
bytes were stored, and explicitly records that molecular source bytes were not
stored by this acquisition. It accessed no molecular values, outcomes, treatment,
subtype, classifier result, or validation dataset. The source object remains
outside Git and was not sent to a generative model.

## Next gate

A later deterministic parser may read only the separately authorized sample
title, GEO accession, and ER-consensus field. The exact interpretation of ER
consensus categories and the preprocessing amendment remain scientific decisions;
this acquisition does not lock either one.
