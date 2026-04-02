# Soil Microbiome Health Index Development with Metagenomic Data

This repository contains the recovered, validated, and reorganized state of an undergraduate soil metagenome project.

The project is currently complete as an exploratory microbiome analysis workflow. It is not a completed crop-prediction system.

## Current Verified Status

- Expected SRRs processed and validated: `24`
- Final merged dataset: `24 x 11116`
- Current valid outputs:
  - exploratory microbiome profiling
  - taxonomic filtering and aggregation
  - relative-abundance / Hellinger / CLR transformations
  - PCA, clustering, and sample similarity analysis
  - sample-level ecological metrics
  - reduced feature table
  - Cluster 1 Soil Microbiome Health Index (SMHI) prototype
- Supervised crop prediction: `blocked`

## What Is Complete

### Cluster 1: current active workflow

Path: `cluster_1_unsupervised_microbiome_profiling/`

This is the main completed workstream. It contains:

- the current analysis-ready microbiome tables
- exploratory ordination and clustering outputs
- sample-level ecological metrics
- reduced exploratory feature tables
- a transparent prototype Soil Microbiome Health Index built only from unsupervised microbiome metrics

### Cluster 2: future supervised workflow

Path: `cluster_2_future_supervised_modeling/`

This cluster is intentionally blocked until real sample-level metadata and targets are added:

- soil pH
- NPK
- moisture
- temperature
- known crop outcome / crop grown / crop suitability

## What Remains Blocked

Supervised modeling is not justified yet because:

- there is no directly observed crop or suitability target in the current dataset
- agronomic metadata is incomplete
- `n = 24` remains small relative to the microbial feature space

## Repository Structure

- `cluster_1_unsupervised_microbiome_profiling/`
  Active unsupervised microbiome workflow and SMHI prototype
- `cluster_2_future_supervised_modeling/`
  Future supervised workflow templates and planning files
- `processed_data/`
  Canonical rebuilt merged tables and derived matrices
- `outputs/`
  Canonical summaries, figures, and audit outputs
- `scripts/`
  Recovery, audit, reconstruction, preprocessing, and exploratory-analysis scripts
- `docs/`
  Reviewer-facing project summaries and methodology notes
- `notebooks/`
  Lightweight notebook wrappers
- `raw_data/original_snapshot/`
  Lightweight preserved forensic snapshot
- `kraken_out/*.report`
  Compact per-sample Kraken2 report summaries retained for provenance

## What Is Not Included In Git

Large local-only artifacts are excluded:

- `raw_data/recovered_fastq/`
- `raw_data/recovered_sra_cache/`
- `raw_data/recovered_sra_tmp/`
- `kraken_db/`
- `kraken_out/*.kraken`
- local virtual environments
- bulky execution logs and caches

See [docs/DATA_AVAILABILITY.md](docs/DATA_AVAILABILITY.md) for details.

## How To Run The Python Analysis

Create a local environment and install the lightweight Python requirements:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Key exploratory workflow scripts:

```powershell
python scripts/prepare_analysis_matrices.py
python scripts/feature_filtering.py
python scripts/prepare_microbiome_matrix.py
python scripts/exploratory_analysis.py
python cluster_1_unsupervised_microbiome_profiling/scripts/health_index_prototype.py
```

## Read These Files First

- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- [docs/METHODOLOGY_OVERVIEW.md](docs/METHODOLOGY_OVERVIEW.md)
- [docs/DATA_DESCRIPTION.md](docs/DATA_DESCRIPTION.md)
- [docs/LIMITATIONS.md](docs/LIMITATIONS.md)
- [docs/CLUSTER_OVERVIEW.md](docs/CLUSTER_OVERVIEW.md)
- [cluster_1_unsupervised_microbiome_profiling/outputs/soil_microbiome_health_index_report.md](cluster_1_unsupervised_microbiome_profiling/outputs/soil_microbiome_health_index_report.md)

## Scientific Guardrail

This repository currently supports exploratory microbiome profiling and a transparent prototype SMHI. It does not yet support a validated crop prediction claim.
