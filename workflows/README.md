# Workflows

Versioned program charters, research-question intakes, analysis plans, schemas,
and executable research workflows live here.

The required sequence for decision-led research is:

1. validate the oncology program charter;
2. propose, score, review, and select a research-question intake;
3. lock the literature-review protocol;
4. preregister the analysis plan;
5. execute governed ingestion and deterministic analysis;
6. freeze evidence and research releases.

`NAS-BRCA-001` is a platform-qualification workflow, not a product claim.

## One governed workspace per study

Every approved research question receives a permanent study ID and one
canonical directory under `workflows/studies/`. Multiple prespecified
hypotheses may belong to the same study. Create a separate study when the
intended decision, population, principal exposure/intervention, primary
outcome, or validation claim materially changes.

```text
workflows/studies/<study_slug>/
├── README.md
├── study.yaml              # durable identity, ownership, artifact namespace
├── pipeline.yaml           # ordered stages, statuses, and completion gates
├── question/               # approved decision-led research question
├── literature/             # locked review protocol and search strategy
├── protocol/               # preregistered analysis plan
├── ingestion/              # source queries and deterministic transforms
├── analysis/               # cohort construction and statistical/ML code
├── evidence/               # claims, citations, nulls, conflicts, limitations
├── release/                # frozen-release definitions
├── tests/                  # study-specific tests and synthetic fixtures
└── reviews/                # review decisions and resolved comments
```

Create a new workspace from the repository root:

```bash
uv run nas-core study init NAS-BRCA-002 \
  --slug example_biomarker_study \
  --title "Example breast-cancer biomarker study" \
  --program-id NAS-ONC-001 \
  --role discovery
```

The command rejects noncanonical IDs and slugs and never overwrites an existing
workspace. Validate lifecycle manifests with:

```bash
uv run nas-core study validate workflows/studies/example_biomarker_study
```

Git stores definitions, code, tests, and review records. Raw data and generated
artifacts remain under `NAS_DATA_ROOT`, using the manifest namespace:

```text
studies/<study_id>/snapshots/<snapshot_id>
studies/<study_id>/runs/<run_id>
studies/<study_id>/releases/<release_id>
```

Snapshot, run, and release identifiers are immutable. This separation keeps a
study reproducible without putting biomedical data or large artifacts in Git.
