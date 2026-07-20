# Access Control Policy

Access is deny-by-default and evaluated against source status, classification,
action, project purpose, and actor role.

- Only active sources may be used.
- Roles are granted the minimum actions required for their responsibilities.
- Credentials are individual, revocable, and never stored in Git.
- Service accounts must be scoped to a single technical purpose.
- Access to licensed data is reviewed at least on the source review date.
- Suspended, expired, archived, and deleted sources are unavailable to jobs and
  model tools.

Controlled and PHI access will require additional controls before those data
classes can be enabled in a future Cortex version.
