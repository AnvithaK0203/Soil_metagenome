# GitHub Upload Scope

This repository is prepared as a clean GitHub upload rather than a full archival copy of the local bioinformatics workspace.

## Included

- Source notebooks and scripts used for audit, recovery, cleaning, and feasibility analysis
- Lightweight original project snapshot files
- Cleaned and processed CSV outputs
- Recovery manifests and documentation
- Kraken2 `.report` summary files

## Excluded

- `raw_data/recovered_fastq/`
- `kraken_db/`
- `kraken_out/*.kraken`
- local virtual environments
- bulky execution logs
- stray experimental notebook `Untitled17 (1).ipynb`

## Why

The excluded artifacts are either too large for standard GitHub hosting, are machine-specific, or are intermediate recovery outputs that can be regenerated from the committed manifests and scripts.

## Regeneration Path

1. Recreate the Python environment from `requirements.txt`.
2. Review the project status in `final_project_status_summary.md`.
3. Use `scripts/reconstruct_extraction.py` and `scripts/wsl_recover_missing_srrs.sh` for heavy recovery.
4. Rebuild final tables with:
   - `scripts/clean_data.py`
   - `scripts/execute_srr_recovery.py`
   - `scripts/disk_truth_reaudit.py`
   - `scripts/rebuild_final_dataset.py`
   - `scripts/inspect_datasets.py`
   - `scripts/reassess_feasibility.py`
