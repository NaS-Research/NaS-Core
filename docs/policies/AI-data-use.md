# AI Data Use Policy

Model use is a distinct processing action and must be explicitly permitted by
the source registration.

## Cortex v0 controls

- Controlled data and PHI may not be sent to any model provider.
- Raw genomic matrices should not be sent to a model provider.
- Only the minimum retrieved passages and compact derived results needed for a
  defined task may be transmitted.
- Model training is denied unless a source explicitly permits it; the initial
  GDC registration does not.
- Embedding creation requires a separate explicit permission.
- Model output remains unverified until linked to evidence and human-reviewed.
- Provider, model, prompt version, source identifiers, and output disposition
  will be recorded in an audit event.

Model-provider configuration cannot override governance policy.
