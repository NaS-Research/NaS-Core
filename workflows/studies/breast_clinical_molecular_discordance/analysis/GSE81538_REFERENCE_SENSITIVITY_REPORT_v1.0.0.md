# GSE81538 Reference Sensitivity Report 1.0.0

## Decision

`pass_with_limitation`

Frozen revision `5c1eba8b368605f075c962452807005b807ee331` executed the
prespecified outcome-blind reference sensitivity panel. Receipt SHA-256 is
`be2322e4d5123a84b205b8cceda5a8778280ad72f21bbbef81f9da018f1613ff`.
The external artifact independently reproduces SHA-256
`cca6b8672a3ea7b19821a3fa31014203e011b3303c31a7ac37b62ffd46cad53b`.

## Median versus trimmed mean

The primary gene-wise median was reproduced exactly. A 20%-per-tail trimmed mean
retained 60 of 100 observations per gene. Across the 50-gene vectors:

- Pearson correlation: 0.9934376980
- Spearman correlation: 0.9911644658
- Mean absolute difference: 0.1340591525 log2 units
- Maximum absolute difference: 0.6755214138 log2 units
- Root mean square difference: 0.2016443845 log2 units

The estimators are strongly aligned but not numerically interchangeable. This
supports retaining the prespecified median while showing that estimator choice
can materially affect at least some genes.

## Centered-profile stability

For each selected profile, the 50-gene rank correlation between median-centered
and trimmed-mean-centered expression was summarized without Git identifiers:

- Mean: 0.9854108043
- Median: 0.9879951981
- Minimum: 0.9388235294

These are centered-profile diagnostics, not PAM50 centroid scores, subtype calls,
reliability estimates, or classifier validation.

## Alternative-sample feasibility

After excluding the primary manifest, 32 eligible ER-negative and 254 eligible
ER-positive records remain. The prespecified exact next-50-per-stratum reference
is therefore not estimable. No smaller, imbalanced, or post hoc cohort was used.

## Boundaries and interpretation

The run accessed exactly 5,000 selected molecular values and permitted ER
metadata. It accessed no outcomes, treatment, GSE96058 data, classifier output,
or threshold. No participant molecular data was supplied to generative AI. The
reference remains candidate and unlocked.

The main technical signal is reassuring but not dispositive: estimator agreement
is high, yet the maximum gene-level difference and minimum profile correlation
show that reference choice is not irrelevant. Classifier-level score sensitivity
must wait for a locked method contract. Independent technical-error calibration
remains the major unresolved Phase 1 dependency.
