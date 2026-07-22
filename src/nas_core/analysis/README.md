# Analysis

Deterministic cohort construction and statistical pipelines live here. Cohort
QA must remain separate from outcome modeling: it may report field missingness,
normalization, and exclusion flow, but must not expose the prespecified
stage-survival association before the cohort is frozen.

The survival runner verifies the founder-approved cohort receipt and every input
checksum before fitting models. It captures estimates, uncertainty, diagnostics,
warnings, null or failed analyses, environment versions, and immutable artifacts.
Language models must never manufacture numerical research results.
