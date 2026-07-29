# Founder Phase 1 Scientific and Statistical Planning Packet 0.1.0

Study: `NAS-BRCA-002`  
Question: `0.3.0`  
Route: `ROUTE-C`  
Status: founder planning decision required

## Bound inputs

| Artifact | SHA-256 |
|---|---|
| `protocol/prospective_calibration_planning_activation_v1.0.0.yaml` | `f92d0558811d8ecb066d8dae96386c10582588093da737df3460c879aa393dbc` |
| `protocol/calibration-scenarios/HYPOTHETICAL_LEAN.yaml` | `1781add72f4448e47e9a8012645c6af89145e1de13d2d681886503b20b5f53a0` |
| `protocol/calibration-scenarios/HYPOTHETICAL_LEAN_RESULT.yaml` | `fd13a7f50d364c68bea5805fd010187be787806f9b699694abc6f5b49fe3ae65` |
| `protocol/calibration-scenarios/HYPOTHETICAL_BALANCED.yaml` | `16f59e500489a7fda68bf47e8e1f11837d5ed55d52672a28c76f9ae6c33391b8` |
| `protocol/calibration-scenarios/HYPOTHETICAL_BALANCED_RESULT.yaml` | `29f6e9f875884bec26c86cbc56076b96c5edfc6b1c331326e9dd42dba2756f59` |
| `protocol/calibration-scenarios/HYPOTHETICAL_HIGH_PRECISION.yaml` | `e062592ee3a5f605e297699725b65bcc7890f5d290516e067f2a8a2a60a39ead` |
| `protocol/calibration-scenarios/HYPOTHETICAL_HIGH_PRECISION_RESULT.yaml` | `98c30b7b6c0d7ff2522cb563b9c08b2426c84d2dbc192ec8cd3eb80cb88f61c0` |

## Scientific recommendations

1. Preserve bulk RNA sequencing as the intended platform family. Do not select
   an exact instrument, library kit, chemistry, or vendor until a compatibility
   review shows how the workflow relates to the locked reference and GSE96058.
2. Use independent library preparation and sequencing from the same homogenized
   RNA as the primary technical-repeat architecture.
3. Treat repeated extraction from matched homogenized tissue as an optional,
   separately analyzed sensitivity arm. Do not pool it into the primary
   post-extraction error distribution.
4. Require coverage across receptor categories, RNA-quality bands, and the
   preliminary blinded score-margin distribution without using outcomes.
5. Preserve every invalid assay, missing gene, failed pair, rerun, and abstention
   in declared denominators.

## Statistical recommendations

1. Use the balanced result—185 attempted pairs and 370 measurements—only as an
   internal operational feasibility reference.
2. Do not approve 185 as the final sample size. The inputs are hypothetical and
   exclude pilot, extraction-sensitivity, controls, reruns, and reference materials.
3. Design an excluded feasibility pilot before final calibration. Pilot specimens
   can estimate variance, attrition, missingness, and batch structure but can
   never enter threshold calibration or external validation.
4. Preserve one independent biological source per primary pair where possible.
   Otherwise, declare clustering prospectively and inflate the design.
5. Separate the single primary binary estimand from confirmatory continuous
   objectives and exploratory gene-level analyses. Freeze multiplicity before
   primary calibration access.
6. Derive the final pair count only after the assay, estimands, pilot, coverage,
   attrition, clustering, and multiplicity decisions are approved.

## Operational and budget-scenario boundary

Internal planning may express costs symbolically as:

`total = specimens × specimen_cost + measurements × measurement_cost + controls + storage + analysis`

No dollar input is approved. No laboratory may be contacted, no quotation may be
requested, and no purchase, specimen commitment, or external coordination is
authorized.

## NaS review position

Approve these recommendations for continued planning. The balanced scenario is
the most useful middle case because it reveals that continuous technical-error
precision may dominate binary label retention. It also suggests that a rigorous
prospective experiment could be materially larger than initially expected.

If later operational estimates make the design infeasible, NaS should narrow the
claim or reconsider the route rather than weaken precision after viewing data.

## Exact decision statements

Select exactly one:

1. **Recommended—approve continued planning**

   `I approve NAS-BRCA-002 Phase 1 scientific and statistical planning recommendations 0.1.0 as written.`

2. **Request changes**

   `I request changes to NAS-BRCA-002 Phase 1 scientific and statistical planning recommendations 0.1.0.`

3. **Hold Route C**

   `I place NAS-BRCA-002 Route C scientific and statistical planning on hold.`

## Authorization boundary

Approval authorizes internal development of the platform-compatibility audit,
pilot precision design, coverage plan, multiplicity plan, and symbolic budget
model. It does not authorize final scientific parameters, an approved pair count,
external contact, laboratory quotations, spending, procurement, specimens, data
access, source selection, threshold selection, execution, clinical use,
scientific conclusions, publication, or submission.
