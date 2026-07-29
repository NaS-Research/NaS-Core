# NAS-BRCA-002 Phase 1 Internal Planning Report 1.0.0

Status: **internally frozen pending evidence**  
Route: **C — prospective independent calibration**  
Execution authority: **none**

## Decision summary

Standing founder autonomy replaces routine approval packets for reasonable,
reversible internal decisions while preserving explicit stop conditions and the
founder's final human review.

The plan retains bulk RNA sequencing as the intended platform family without
selecting an instrument, kit, chemistry, laboratory, or vendor. Primary
technical repeatability is defined as independent library preparation and
sequencing from paired aliquots of the same homogenized RNA. Repeated extraction
remains a separate optional sensitivity arm.

## Excluded feasibility pilot

The provisional pilot target is 30 attempted pairs from 30 independent
biological sources, with two measurements per pair. This is large enough to
produce operational estimates of attrition, missingness, paired-error variance,
within-pair correlation, and batch structure while remaining a practical
feasibility exercise.

Thirty is not the final calibration sample size. Pilot specimens are permanently
excluded from primary calibration and external validation. The pilot cannot use
clinical outcomes, calibrate thresholds, or support the final reliability claim.
Final primary-calibration size must be recalculated from blinded pilot nuisance
estimates before primary calibration access.

## Coverage

Coverage constraints are marginal, not a fully crossed factorial design:

- at least five pilot sources in each major receptor category;
- at least five in each prespecified RNA-quality band;
- at least four in each preliminary blinded score-margin quartile; and
- at least five in each early, middle, or late processing-position category.

The quotas deliberately prevent a convenience sample dominated by high-quality,
high-margin specimens. Because the same specimen may satisfy several marginal
quotas, the constraints remain compatible with a 30-pair pilot.

## Multiplicity

The single primary endpoint is technical subtype-label retention at two-sided
alpha `0.05`, without adjustment because there is one primary endpoint.

Five locked subtype-score paired errors plus runner-up-margin paired error form
one confirmatory family controlled by Holm's method at familywise alpha `0.05`.
Failure, invalidity, rerun, missingness, and abstention measures are descriptive
with confidence intervals and no null-hypothesis claims. The 50 gene-level
paired-error analyses are exploratory and use Benjamini–Hochberg false-discovery
rate control at `q=0.10`; they cannot support the primary claim.

## Platform-compatibility gate

Eight evidence requirements must close before the platform bridge can lock:

1. complete unambiguous PAM50 gene mapping;
2. a containerized transformation and normalization bridge;
3. a compatible locked reference and centering operation;
4. a metadata-only, performance-blind bridge to GSE96058;
5. prespecified assay quality controls and failure rules;
6. randomized replicate placement with complete lineage;
7. cross-implementation numerical conformance; and
8. checksum-bound governed artifact storage.

## Symbolic budget

The model records specimens, measurements, controls, reference materials,
storage, compute, analysis, and attrition reserve as symbols. It contains no
currency, quotation, price, or total. It therefore supports later feasibility
review without contacting a laboratory or authorizing spending.

## Interpretation

This plan converts the earlier broad recommendations into an auditable design
that can guide evidence collection. It does not establish analytical validity,
select a calibration source, approve 185 pairs, set a reliability threshold, or
authorize any experiment. Phase 1 remains open until the required compatibility
evidence, excluded-pilot estimates, final blinded size reestimation, reference,
bridge, thresholds, abstention rule, and numerical tolerances are frozen.
