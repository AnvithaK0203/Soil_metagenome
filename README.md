# Soil Microbiome Health Index Development with Metagenomic Data

This repository is a recovered and rebuilt undergraduate/capstone project focused on soil metagenomics, microbiome profiling, and cautious downstream analysis for soil-health and agronomic decision-support research.

## Current Project Status

- Expected SRRs recovered from project evidence: `24`
- Locally processed SRRs with validated Kraken2 outputs: `24`
- Metadata-enriched SRRs from ENA: `24`
- Samples in the teammate-derived metadata merge table: `10`
- Supervised crop prediction: `not justified`
- Current defensible scope: `exploratory microbiome plus metadata analysis`

The biological recovery is complete for the 24 expected SRRs, but the project still does **not** contain a directly observed crop label, crop suitability label, or full soil chemistry panel suitable for supervised modeling. The current scientific conclusion is therefore exploratory, not predictive.

## What Is Included In GitHub

- Recovery and audit scripts in `scripts/`
- Compact wrapper notebooks in `notebooks/`
- Cleaned and processed tabular outputs in `cleaned_data/` and `processed_data/`
- Recovery reports, manifests, and feasibility summaries in the repository root, `docs/`, and `outputs/`
- Original lightweight project snapshot files in the repository root and `raw_data/original_snapshot/`
- Kraken2 per-sample `.report` summaries in `kraken_out/`

## What Is Intentionally Excluded

These artifacts stay local because they are too large for a clean GitHub repository or are environment-specific:

- `raw_data/recovered_fastq/`  
  Full downloaded FASTQ files, about 44.5 GB locally.
- `kraken_db/`  
  Local Kraken2 database files, about 13 GB locally.
- `kraken_out/*.kraken`  
  Raw Kraken classification streams, about 12.9 GB locally.
- `.venv/` and `.wsl_venv/`  
  Local Python environments.
- bulky execution logs under `logs/**/*.log` and `logs/wsl_recovery/runs/`

The excluded data can still be reconstructed from the committed manifests and scripts.

## Repository Layout

- `scripts/`  
  Reproducible recovery, audit, cleaning, reconstruction, and feasibility scripts.
- `docs/`  
  Narrative recovery notes and execution summaries.
- `outputs/`  
  Audit tables, ENA metadata recovery outputs, feasibility reports, and model gate reports.
- `cleaned_data/`  
  Cleaned derivatives of the local source data.
- `processed_data/`  
  Sample-level manifests and merged analysis-ready tables.
- `raw_data/original_snapshot/`  
  Lightweight original project files preserved for forensic traceability.
- `kraken_out/*.report`  
  Compact taxonomic report summaries retained for provenance.

## Key Files

- `README_project_recovery.md`  
  Recovery-oriented overview of the rescued project state.
- `final_project_status_summary.md`  
  High-level scientific and computational status.
- `srr_audit_report.csv`  
  Per-SRR completeness and provenance audit.
- `processed_data/sample_manifest.csv`  
  One-row-per-sample manifest with local and remote metadata context.
- `processed_data/final_merged_dataset_preview.csv`  
  Final merged preview dataset after recovery.
- `dataset_audit_report.md`  
  Dataset-by-dataset audit and readiness assessment.
- `outputs/post_recovery_feasibility_report.md`  
  Honest feasibility reassessment after recovery.

## Reproducing The Analysis

### Windows Python environment

Use the committed `requirements.txt` in a local virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### WSL / Linux bioinformatics environment

The heavy recovery path was run in WSL Ubuntu with Kraken2. The committed scripts assume a Linux-like environment for download and classification:

- `scripts/wsl_recover_missing_srrs.sh`
- `scripts/run_remaining_disk_truth_recovery.sh`
- `scripts/reconstruct_extraction.py`

### Scripted rebuild sequence

For a clean rebuild from the committed lightweight artifacts:

```bash
python scripts/clean_data.py
python scripts/execute_srr_recovery.py
python scripts/disk_truth_reaudit.py
python scripts/rebuild_final_dataset.py
python scripts/inspect_datasets.py
python scripts/reassess_feasibility.py
```

## Scientific Guardrails

- One sample is currently treated as one SRR sequencing run.
- The recovered dataset is high-dimensional relative to sample count.
- No directly observed agronomic target is present.
- Crop prediction and crop recommendation claims are blocked.
- The strongest defensible scope is exploratory microbiome analysis and cautious soil-health-style feature aggregation.

## Notes For Reviewers

This repository is intentionally structured as a **clean, auditable GitHub version** of a much larger local recovery workspace. The committed code and reports are enough to understand the project, reproduce the tabular outputs, and inspect the scientific decisions, while the very large raw sequencing artifacts remain local and are referenced through the committed manifests.
