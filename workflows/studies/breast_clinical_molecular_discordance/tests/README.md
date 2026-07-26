# Synthetic tests

Store study-specific tests and synthetic fixtures here.

Repository tests now exercise the single-sample reliability kernel with an exact
50-gene synthetic panel. Coverage includes deterministic scoring and hashing,
historical alias mapping, duplicate-alias rejection, missing and nonfinite inputs,
invalid centroids, tied scores, 50 leave-one-gene-out runs, threshold-triggered
abstention, explicit rejection of non-`SYNTHETIC-*` sample identifiers, and
combined execution of explicit synthetic technical-error panels. Tests prove
family-to-aggregate reconciliation, stable-vector retention, label-changing
instability, and fail-closed handling of invalid perturbation vectors.

No fixture contains a patient identifier or observed molecular value.
