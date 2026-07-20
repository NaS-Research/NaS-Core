# NaS Biomedical Data Source Landscape

Last reviewed: 2026-07-20

This document is a candidate-source catalog, not an authorization list. Source
availability, terms, licensing, releases, and access requirements can change.
Before any automated retrieval, storage, embedding, AI processing, analysis, or
publication, assess the exact source and register the approved purpose in
[`data/source-registry.yaml`](../data/source-registry.yaml).

## Access legend

- **Open:** Publicly accessible, subject to terms, attribution, and dataset-level
  restrictions.
- **Registered:** Requires an account, agreement, application, or institutional
  affiliation.
- **Controlled:** Individual-level, genomic, sensitive, or otherwise restricted
  data requiring formal authorization and secure analysis controls.
- **Commercial:** Requires a license or paid agreement.
- **Partnership:** Requires collaboration with a health system, laboratory,
  registry, biobank, pharmaceutical company, or other data holder.

Cortex v0 permits public/open and explicitly approved licensed data. Controlled
data and PHI remain prohibited.

## Cancer genomics and multi-omics

| Source | Primary data | Access | Best use |
| --- | --- | --- | --- |
| [NCI Genomic Data Commons](https://gdc.cancer.gov/about-data) | TCGA, TARGET, HCMI and other harmonized clinical, genomic, transcriptomic, epigenomic and biospecimen data | Mixed open/controlled | Cancer subtyping, biomarker and survival research |
| ICGC ARGO | International cancer genomes and clinical outcomes | Registered/controlled | International and external validation |
| AACR Project GENIE | Clinico-genomic testing and outcomes-oriented releases | Mixed | Mutation prevalence and clinico-genomic validation |
| cBioPortal | Aggregated cancer studies including public institutional cohorts | Mixed by underlying study | Exploration and rapid cohort feasibility |
| METABRIC | Breast-cancer expression, copy number, clinical variables and outcomes | Dataset-specific | Independent breast-cancer validation |
| [NCI Proteomic Data Commons](https://datacommons.cancer.gov/repository/proteomic-data-commons) | CPTAC and other proteomic, phosphoproteomic, proteogenomic and clinical data | Open with attribution | Protein biomarkers and multi-omics |
| Human Tumor Atlas Network | Single-cell, spatial and longitudinal tumor atlases | Mixed | Tumor evolution and microenvironment |
| NCI Clinical and Translational Data Commons | Clinical-trial and translational study data | Dataset-specific | Trial and translational research |

GDC data are valuable for qualification and discovery, but NCI characterizes
their use as research/exploratory rather than definitive clinical-outcome
evidence. Treatment and follow-up completeness vary by project.

## Population cancer and outcomes

| Source | Primary data | Access | Best use |
| --- | --- | --- | --- |
| [SEER](https://seer.cancer.gov/data-software/index.html) | Incidence, stage, survival, demographics and geography | Registered/data agreement | Epidemiology, disparities and population survival |
| SEER-Medicare | SEER linked to Medicare claims | Controlled | Treatment, utilization and outcomes |
| SEER-Medicaid and SEER survey linkages | Registry linked to insurance and survey data | Controlled | Access, outcomes and patient experience |
| National Childhood Cancer Registry | Pediatric and young-adult cancer | Registered/specialized | Pediatric and AYA oncology |
| National Cancer Database | Hospital-based oncology registry | Institutional/research access | Treatment patterns and hospital outcomes |
| CDC NPCR and U.S. Cancer Statistics | National cancer incidence | Aggregate/open; detail varies | National surveillance |
| State and institutional registries | Regional cancer diagnosis, stage, treatment and outcome | Partnership | Local RWE and validation |

[SEER access](https://seer.cancer.gov/data/access.html) requires individual
registration and acknowledgment of data agreements; specialized and linked
products require additional approval.

## Biobanks and longitudinal cohorts

| Source | Primary data | Access | Best use |
| --- | --- | --- | --- |
| [NIH All of Us](https://researchallofus.org/data-tools/data-access/) | EHR, surveys, physical measurements, wearables and genomics | Public aggregate; registered/controlled individual-level | Longitudinal phenotype and genomic studies |
| UK Biobank | Genomics, imaging, biomarkers, linked health records and lifestyle | Registered, fee, secure platform | Broad prospective validation |
| FinnGen | Genomics linked to Finnish national registries | Public summaries; collaboration for detail | Genotype-phenotype validation |
| Million Veteran Program | Genomics linked to VA health data | Approved collaboration | Large-scale longitudinal research |
| dbGaP | Genotype-phenotype studies | Study-specific open/controlled | Genetics and external validation |
| eMERGE Network | EHR-linked genomics and phenotypes | Controlled/study-specific | Clinical genomics |
| BioVU and institutional biobanks | De-identified EHR-linked biospecimens | Partnership | Translational and local validation |

Some of these resources require analysis inside their own secure cloud
workspace. Their participant-level data may not be exported to the Seagate
drive or to NaS object storage.

## Real-world clinical and administrative data

The long-term NaS strategy depends on longitudinal data produced during routine
care. These sources are generally not open.

### Government and administrative

- [CMS Medicare and Medicaid research files](https://www.cms.gov/data-research/cms-data/data-available-researchers)
- Chronic Conditions Warehouse
- Healthcare Cost and Utilization Project
- Veterans Health Administration data
- State all-payer claims databases
- State Medicaid and public-health linkages

CMS Research Identifiable Files can contain PHI or PII and require applications,
agreements, fees, and approved secure environments. They are prohibited in
Cortex v0.

### Commercial

- Flatiron Health
- Tempus
- ConcertAI
- TriNetX
- Optum
- Merative MarketScan
- IQVIA
- Komodo Health
- HealthVerity
- COTA
- Foundation Medicine clinico-genomic datasets
- Guardant Health and Caris Life Sciences datasets

Availability and permitted commercial, publication, model-training, and export
uses must be negotiated for the exact product and project.

### Direct health-system and laboratory partnerships

- EHR encounters, diagnoses and clinical notes
- oncology treatment plans, medication administrations, dose changes and stops
- laboratory, pharmacy and organ-function measurements
- pathology, radiology and molecular diagnostic reports
- tumor-board decisions and clinical-trial screening
- response, progression, adverse events and mortality
- patient-reported outcomes and wearable data
- biospecimens, biobanks and serial tissue or liquid biopsies

These sources can support genuine longitudinal RWD and decision-oriented
precision medicine, but require contracting, consent/authorization analysis,
privacy engineering, security, data-quality work, and clinical collaboration.

## Functional genomics and experimental models

| Source | Primary data | Access | Best use |
| --- | --- | --- | --- |
| [DepMap](https://depmap.org/portal/data_page/?tab=currentRelease) | CRISPR dependency, expression, mutation, copy number, fusion and drug screens | Public releases | Target discovery and vulnerabilities |
| CCLE | Molecularly characterized cancer cell lines | Public through DepMap | Model and biomarker selection |
| PRISM | Pooled cancer cell-line drug screens | Public releases | Drug-response hypotheses |
| Genomics of Drug Sensitivity in Cancer | Cell-line molecular and drug-response data | Dataset-specific | Pharmacogenomic validation |
| LINCS / Connectivity Map | Perturbational expression signatures | Open/registered | Mechanism and repurposing |
| Cell Model Passports | Cancer model molecular characterization | Open/registered | Translational model selection |
| Organoid and patient-derived model datasets | Ex-vivo response and molecular profiles | Study/partnership-specific | Functional validation |

Experimental models can establish mechanism and prioritize candidates, but
their results must not be represented as patient outcomes.

## General genomics and variant knowledge

- GEO, SRA, ENA and ArrayExpress/BioStudies
- GTEx
- gnomAD
- [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/intro/) and ClinGen
- dbSNP and dbVar
- [NHGRI-EBI GWAS Catalog](https://www.ebi.ac.uk/gwas/docs/about)
- ENCODE and Roadmap Epigenomics
- COSMIC — licensing and redistribution restrictions require review
- CIViC
- OncoKB — use and licensing require review
- PharmGKB

ClinVar stores submitted variant classifications and their supporting evidence;
it is not a patient-specific interpretation engine and can contain conflicting
assertions. Knowledge bases must retain evidence level, submitter, review state,
version and uncertainty.

## Single-cell and spatial biology

- CELLxGENE Census
- Human Cell Atlas
- Broad Single Cell Portal
- Human Tumor Atlas Network
- HuBMAP
- Tabula Sapiens
- GEO/SRA single-cell and spatial studies
- publication-specific spatial transcriptomics datasets

These sources support research into tumor microenvironments, immune cell states,
lineage evolution, spatial biomarkers and resistance mechanisms.

## Imaging and digital pathology

- [The Cancer Imaging Archive](https://www.cancerimagingarchive.net/browse-collections/)
- NCI Imaging Data Commons
- TCGA and CPTAC digital pathology slides
- HTAN imaging and spatial pathology
- CAMELYON, PANDA and other challenge datasets
- National Lung Screening Trial imaging
- institutional PACS and pathology archives through partnership

TCIA hosts de-identified CT, MRI, PET and digital-pathology collections and may
include outcomes, treatment, genomics, segmentations or expert annotations.
Access and use restrictions still apply at the collection level.

## Drugs, targets and chemical biology

- [ChEMBL](https://www.ebi.ac.uk/chembl/)
- PubChem
- BindingDB
- DrugCentral
- DrugBank — commercial and redistribution terms require review
- Open Targets
- Therapeutic Target Database
- IUPHAR/BPS Guide to Pharmacology
- PharmGKB
- FDA Orange Book, Drugs@FDA and DailyMed
- SureChEMBL and other patent-derived resources

These sources support drug-target mapping, bioactivity, pharmacology, approved
product context, target prioritization and drug-repurposing hypotheses.

## Trials, regulatory evidence and safety

- ClinicalTrials.gov and its API
- AACT structured ClinicalTrials.gov database
- WHO International Clinical Trials Registry Platform
- EU Clinical Trials Information System
- NCI clinical-trial datasets
- FDA labels, approval packages and review documents
- Drugs@FDA and openFDA
- [FDA Adverse Event Reporting System](https://open.fda.gov/data/faers/)
- European Medicines Agency documents

FAERS is appropriate for pharmacovigilance signal generation. Voluntary
reporting, duplicate reports, missing information and the lack of a population
denominator mean it cannot independently establish incidence or causation.

## Literature and bibliographic evidence

- [PubMed/MEDLINE](https://pubmed.ncbi.nlm.nih.gov/about/)
- PubMed Central
- Europe PMC
- Crossref
- OpenAlex
- Semantic Scholar
- Cochrane Library
- Embase, Web of Science and Scopus — commercial
- conference abstracts, preprint servers and patent databases
- FDA, EMA, professional-society and guideline publications

PubMed provides citations and abstracts, not blanket rights to publisher full
text. Full-text storage, passage extraction, embeddings and AI processing must
follow the license of the actual article source.

## Proteins, structures, interactions and pathways

- UniProt
- [RCSB Protein Data Bank](https://www.rcsb.org/pages/about-us/index)
- [AlphaFold Protein Structure Database](https://alphafold.ebi.ac.uk/about)
- ESM Atlas and model-generated structures
- InterPro and Pfam
- STRING, BioGRID and IntAct
- Reactome, Gene Ontology and pathway resources
- KEGG — licensing requires review

Cortex must distinguish experimentally determined PDB structures from predicted
structures, preserve confidence metrics, and prevent either from becoming a
clinical claim without appropriate validation.

## Project-to-source examples

| Decision-led question | Likely source combination |
| --- | --- |
| Prognostic breast-cancer biomarker | GDC/TCGA + CPTAC + METABRIC or GENIE validation |
| Treatment-response prediction | Molecular diagnostics + longitudinal EHR/registry + therapy and progression |
| Resistance detection | Serial tissue or ctDNA + treatment sequence + imaging/progression + functional data |
| Trial matching | ClinicalTrials.gov + patient phenotype + biomarkers + local trial availability |
| Toxicity or dosing | Medication and dose + labs/organ function + adverse events + claims/EHR |
| Target discovery | GDC/PDC + DepMap/CRISPR + ChEMBL/Open Targets + experimental validation |
| Antibody or binder research | UniProt/PDB + AlphaFold/ESMFold + binding data + laboratory assays |
| Population disparities | SEER + Census/social context + claims or EHR where permitted |

## Source promotion workflow

Awareness does not equal approval. Promote a candidate source through:

```text
approved question
  -> required modality and variables
  -> source feasibility and overlap assessment
  -> terms, license, privacy and security review
  -> access classification and approved purpose
  -> source registry approval
  -> exact release/query snapshot
  -> quality and fitness-for-purpose assessment
  -> governed analysis
  -> independent validation
```

For the current qualification study, only the public/open GDC registration is
active. Likely next assessments are PubMed bibliographic metadata, permitted
PubMed Central full text, ClinicalTrials.gov, and an independent breast-cancer
validation dataset after the decision-led question is selected.
