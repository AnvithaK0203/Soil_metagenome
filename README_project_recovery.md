# Project Recovery Overview

## What was found

- The original root snapshot contained a very small project footprint anchored by `Anvitha.ipynb`, two Kraken-derived CSV tables, and one 10-sample metadata merge table.
- `Anvitha.ipynb` documented an intended 24-SRR workflow, but the local processed state was initially incomplete and the merged ML-style table had no defensible target label.
- The interrupted WSL recovery run had already completed 10 of the 11 previously missing SRRs before the latest safe restart audit.
- The final missing SRR, `SRR9830591`, was recovered by preserving the live WSL Kraken2 process, validating its outputs, and rebuilding the project from verified files only.

## Why it matters

- The project now has full local processed coverage for the 24 expected SRRs recovered from project evidence.
- The biological recovery problem is no longer the main blocker.
- The main scientific blocker is now target validity: there is still no directly observed crop label, crop suitability label, or soil physicochemical dataset suitable for supervised learning.

## What is still wrong or uncertain

- `Optimized_Taxonomy_ML.csv` remains only a 10-sample derived merge and should not be treated as the authoritative full dataset.
- Remote ENA metadata improves provenance, but it does not replace primary agronomic annotation.
- The final merged dataset has 24 rows but still contains 10,826 microbial feature columns, which is far too high-dimensional for confident prediction with this sample count.

## What should be done next

- Freeze the current recovery outputs as the verified baseline for this project snapshot.
- Use `processed_data/final_merged_dataset_preview.csv` and the supporting manifests for exploratory microbiome analysis, diversity summaries, and defensible feature aggregation.
- Keep supervised ML blocked unless a trusted source of directly observed crop labels and soil chemistry is added.

## What files and code were created or refreshed

- Recovery and rebuild scripts in `scripts/`
- Verified recovery logs in `logs/`
- Cleaned and processed datasets in `cleaned_data/` and `processed_data/`
- Updated manifests and scientific status reports in the project root, `outputs/`, and `docs/`

## Current status

- Local Python environment: working
- Expected SRRs: 24
- Locally processed SRRs: 24
- Locally metadata-merged SRRs from the teammate merge table: 10
- Remotely metadata-enriched SRRs: 24
- Missing locally processed SRRs: 0
- Supervised modeling: blocked

## Current defensible scope

- Exploratory microbiome plus metadata analysis
- Soil-health-style exploratory feature aggregation only
- No crop prediction or crop recommendation claims yet
