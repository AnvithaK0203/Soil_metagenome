# Data Availability

## Included in Git

Included because they are lightweight and useful for review:

- processed and reduced tabular outputs in `processed_data/`
- exploratory reports and small figures in `outputs/`
- Cluster 1 reviewer-facing data, figures, and SMHI outputs
- Cluster 2 metadata templates and planning files
- compact Kraken2 `.report` summaries in `kraken_out/`
- lightweight original snapshot files in `raw_data/original_snapshot/`

## Excluded from Git

Excluded because they are large, noisy, or machine-specific:

- `raw_data/recovered_fastq/`
- `raw_data/recovered_sra_cache/`
- `raw_data/recovered_sra_tmp/`
- `kraken_db/`
- `kraken_out/*.kraken`
- `.venv/`
- `.wsl_venv/`
- bulky `.log` files in `logs/`
- cache files such as `__pycache__/`

## Why this split was chosen

The repository is intended to stay reviewable while preserving the code, summaries, and compact outputs needed to understand and reproduce the analytical workflow.
