# Founder AI Provider Authorization — Policy 1.0.1

- Study: `NAS-BRCA-002`
- Founder: Dalron J. Robertson
- Decision date: 2026-07-22
- Decision: authorized
- Retention path: standard API abuse monitoring

## Authorized use

The founder authorizes the governed OpenAI model gateway to transmit batches of
at most ten public/open bibliographic titles and abstracts from verified screening
queue `b02c2abf…f042` for advisory title-and-abstract screening. Standard API
abuse-monitoring retention, which may retain customer content for up to 30 days,
is acknowledged for this bounded use. Provider application storage remains
disabled with `store: false`.

The first live execution is limited to a ten-record calibration batch. Its output
is advisory and must record zero final decisions. Every recommendation requires
founder review; the model cannot include, exclude, supersede, or otherwise modify
the human decision ledger.

## Explicit exclusions

This authorization does not cover licensed full text, controlled data, PHI,
patient-level data, genomic matrices, outcome-bearing analysis artifacts, another
study or queue, autonomous exclusions, scientific conclusions, or publication
claims. Any expansion requires a prospective, versioned authorization.

The API credential must remain in the repository-local ignored `.env` file. It
must not be committed, copied into provenance, or placed in a prompt, receipt,
log, or research artifact.

## Provenance

The founder explicitly stated “I authorize” in the project conversation after the
standard-retention and Zero Data Retention alternatives were presented. This record
implements that authorization as the narrower recommended standard-retention path
for the exact public/open screening queue described above.
