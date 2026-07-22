# Synthetic tests

Store study-specific tests and synthetic fixtures here. Never commit raw TCGA
records or outcome-bearing biomedical data.

The repository-level `tests/test_survival.py` suite verifies the cohort approval
gate, source checksums, cohort invariants, minimum-event abstention, deterministic
artifacts, typed schemas, and all required analysis branches using synthetic data.
