# Data Classification Policy

## Public/open

Data made available without individual authorization requirements, subject to
its terms and applicable law. Registration must still capture attribution,
prohibited re-identification, version, and permitted uses.

## Licensed

Data governed by a contract, subscription, license, or other agreement. Use is
limited to the documented parties, purposes, duration, environments, and output
rights. AI processing, embeddings, and model training are separate permissions.

## Controlled

Data requiring project-specific authorization or restricted access, including
many human genomic file types. Controlled data is prohibited in Cortex v0 even
if a team member personally possesses access credentials.

## PHI

Individually identifiable health information subject to HIPAA or comparable
obligations. PHI is prohibited in Cortex v0. Pseudonymization or removal of a
name alone does not change the classification.

## Inheritance

Combined and derived datasets inherit the most restrictive input
classification: `public_open < licensed < controlled < phi`. A classification
may be reduced only through an authorized, documented determination outside the
normal workflow.
