# Data Description

## Sample count

- Expected SRRs: `24`
- Processed and validated SRRs: `24`

## Main merged dataset

File: `processed_data/final_merged_dataset_preview.csv`

- rows: `24`
- columns: `11116`
- one row represents one SRR sequencing run treated as one sample

## Column groups

- metadata / provenance / identifier block: about `30` columns
- microbial taxonomic feature block: about `11086` columns

## Key derived data products

- `processed_data/metadata_table.csv`
- `processed_data/taxonomy_phylum_matrix.csv`
- `processed_data/taxonomy_genus_matrix.csv`
- `processed_data/taxonomy_species_matrix.csv`
- filtered rank-specific matrices in `processed_data/`
- transformed rank-specific matrices in `processed_data/`
- `processed_data/sample_level_metrics.csv`
- `processed_data/reduced_feature_table.csv`

## Cluster 1 outputs

Cluster 1 contains reviewer-friendly copies of the active unsupervised workflow outputs, including:

- exploratory summaries
- figures
- reduced feature table
- SMHI tables
- SMHI figures

## Current label status

No directly observed crop outcome, crop grown, or crop suitability label is present in the current repository state.
