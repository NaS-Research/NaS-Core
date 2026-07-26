# Synthetic tests

Store study-specific tests and synthetic fixtures here.

Repository tests now exercise the single-sample reliability kernel with an exact
50-gene synthetic panel. Coverage includes deterministic scoring and hashing,
historical alias mapping, duplicate-alias rejection, missing and nonfinite inputs,
invalid centroids, tied scores, 50 leave-one-gene-out runs, threshold-triggered
abstention, and explicit rejection of non-`SYNTHETIC-*` sample identifiers.

No fixture contains a patient identifier or observed molecular value.
