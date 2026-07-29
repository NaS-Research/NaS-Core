# NAS-BRCA-002 Numerical Conformance Report 1.0.0

Decision: **pass for synthetic software conformance**  
Cases passed: **8 of 8**  
Absolute score and margin tolerance: **1 × 10⁻¹²**

## What was compared

The production NumPy kernel was compared with a separately implemented
pure-Python reference that uses no NumPy or SciPy. Both implementations
independently perform average-rank assignment, Spearman correlation, deterministic
subtype ordering, top and runner-up selection, margin calculation, and tie
abstention.

The frozen suite contains:

- one exact-centroid synthetic archetype for each of five PAM50 subtypes;
- one synthetic sample with tied input ranks;
- one top-score tie requiring abstention; and
- one runner-up-score tie requiring abstention.

## Result

All subtype labels, runner-up ranks, and reason states matched exactly. Every
reported top score, runner-up score, and margin had absolute difference `0.0`
between implementations, within the prespecified `1e-12` tolerance.

This closes the arithmetic portion of platform criterion `PLAT-007` for the
frozen synthetic suite. It does not validate an assay, reference, preprocessing
bridge, technical-error distribution, reliability threshold, or clinical use.

## Boundary

No patient, molecular, or outcome values were accessed. The fixtures are
synthetic method tests and do not represent biological or assay distributions.
Passing numerical conformance is necessary for reproducibility but is not
evidence of analytical validity, transportability, diagnostic performance, or
clinical utility.
