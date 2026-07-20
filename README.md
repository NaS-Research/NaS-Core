# NaS Core

NaS Core is the private research and evidence platform behind the NaS Cortex.
It is being built to turn approved biomedical data and literature into
reproducible analyses, structured evidence, and traceable research releases.

The project has its infrastructure and governance foundations and is now
preparing its first governed TCGA-BRCA reproduction study. It does not provide
clinical advice and must not be used with protected health information or
controlled-access data until the relevant governance controls are approved.

## Local requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker with Compose (for PostgreSQL and object storage)

## Quick start

```bash
cp .env.example .env
uv sync
uv run nas-core storage init
docker compose up -d postgres minio-init
uv run uvicorn nas_core.api.main:app --reload
```

The API will be available at `http://localhost:8000`.

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Development checks

```bash
make check
```

## Oncology program and topic selection

The authoritative program charter is
[`workflows/oncology/program_charter.yaml`](workflows/oncology/program_charter.yaml).
It identifies breast oncology as the initial learning domain and explicitly
leaves the first product wedge unselected.

Before collecting articles for a new discovery topic, copy and complete
[`workflows/templates/research_question_intake.yaml`](workflows/templates/research_question_intake.yaml),
score it, obtain review approval, and mark it literature-ready. See
[`docs/topic-selection.md`](docs/topic-selection.md).

```bash
make research-foundation-check
```

## Standardized research pipelines

Each approved topic becomes a uniquely identified study workspace with the same
question, literature, protocol, ingestion, analysis, evidence, release, test,
and review stages. Create and validate new workspaces through the CLI; do not
assemble study directories by hand. See [`workflows/README.md`](workflows/README.md)
for the structure, lifecycle gates, and Git-versus-external-storage boundary.

## Where NaS gets data

NaS maintains a broad landscape of possible biomedical sources, but every
project uses only the minimum sources required by its approved research
question. A source appearing below does **not** mean NaS is authorized to use or
store it.

| Source family | Major candidates | What they can support |
| --- | --- | --- |
| Cancer genomics | NCI GDC/TCGA/TARGET, ICGC ARGO, AACR GENIE, cBioPortal, METABRIC | Molecular subtypes, biomarkers, survival, external validation |
| Proteomics and functional biology | NCI PDC/CPTAC, DepMap, CCLE, PRISM, GDSC, LINCS | Protein biomarkers, target discovery, dependencies, drug sensitivity |
| Population oncology | SEER, NCCR, NPCR, NCDB, SEER-linked datasets | Incidence, survival, treatment patterns, disparities |
| Biobanks and longitudinal cohorts | All of Us, UK Biobank, FinnGen, dbGaP, eMERGE, BioVU | Genotype-phenotype, EHR, biomarkers, imaging, longitudinal outcomes |
| Real-world clinical data | Health-system EHRs, registries, claims, labs, pharmacy, pathology, radiology, molecular diagnostics | Treatment response, resistance, toxicity, utilization, patient journeys |
| Imaging and pathology | TCIA, NCI Imaging Data Commons, HTAN, TCGA/CPTAC slides | Radiomics, pathomics, response assessment, multimodal modeling |
| Variants and molecular knowledge | ClinVar, ClinGen, gnomAD, GWAS Catalog, GTEx, COSMIC, CIViC, OncoKB, PharmGKB | Variant annotation, population frequency, gene regulation, clinical evidence |
| Drugs and targets | ChEMBL, PubChem, BindingDB, Open Targets, DrugCentral, DrugBank, Drugs@FDA | Drug-target evidence, bioactivity, pharmacology, approved products |
| Trials and safety | ClinicalTrials.gov, AACT, WHO ICTRP, openFDA, FAERS, FDA/EMA documents | Trial intelligence, eligibility, regulatory evidence, safety signals |
| Literature | PubMed/MEDLINE, PubMed Central, Europe PMC, Crossref, OpenAlex, Cochrane, Embase | Evidence discovery, citation retrieval, review and synthesis |
| Single-cell and spatial | CELLxGENE, Human Cell Atlas, Single Cell Portal, HTAN, HuBMAP | Tumor microenvironment, cell states, spatial biomarkers |
| Proteins and structures | UniProt, RCSB PDB, AlphaFold DB, ESM Atlas, InterPro, STRING, Reactome | Protein function, interactions, structural and mechanistic hypotheses |

The detailed catalog, access tiers, limitations, project-to-source mappings,
and official links are maintained in
[`docs/data-source-landscape.md`](docs/data-source-landscape.md).

The distinction is important:

- `docs/data-source-landscape.md` lists sources NaS may evaluate.
- [`data/source-registry.yaml`](data/source-registry.yaml) contains sources
  actually assessed and approved for defined purposes.
- Controlled data and PHI remain prohibited in Cortex v0.
- Open availability never replaces license, attribution, provenance, and
  project-specific governance review.

Every source follows:

```text
approved research question
  -> required modality
  -> source assessment
  -> access and license review
  -> source registration
  -> immutable snapshot
  -> quality assessment
  -> analysis and independent validation
```

## First study protocol

The first pilot plan is
[`workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml`](workflows/studies/tcga_brca_stage_survival/protocol/analysis_plan.yaml).
It remains pending scientific review. Validate its structure and data-governance
permissions without downloading study data:

```bash
make study-validate
make plan-validate
```

## GDC ingestion

Preview the exact governed request without contacting GDC or writing data:

```bash
make gdc-plan-dry-run
```

The execution path writes content-addressed raw responses and an immutable
dataset manifest to configured object storage. It refuses to run until the
analysis plan is independently approved and marked `preregistered`. See
[`src/nas_core/ingestion/README.md`](src/nas_core/ingestion/README.md) for the
operational command and safeguards.

## Repository boundaries

Git contains source code, schemas, workflow definitions, prompts, tests, small
synthetic fixtures, and permitted dataset manifests. Raw datasets, credentials,
embeddings, generated artifacts, database dumps, PHI, and controlled-access
data never belong in Git.

See [docs/architecture.md](docs/architecture.md) for the initial system shape.

## Project direction

The continuously updated implementation status and next-step queue live in
[PROJECT_STATUS.md](PROJECT_STATUS.md). Read it before beginning material work
and update it whenever an implementation is completed.

The complete phased build plan lives in
[docs/research-engine-plan.md](docs/research-engine-plan.md).
