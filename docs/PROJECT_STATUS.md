# Project Status

## Current real state

- The intended `24` SRR runs have been processed and validated.
- The rebuilt merged dataset is available at `processed_data/final_merged_dataset_preview.csv`.
- The current merged dataset shape is `24 x 11116`.
- Exploratory microbiome analysis is complete.
- Cluster 1 includes a transparent prototype Soil Microbiome Health Index derived from unsupervised microbiome metrics only.

## What is scientifically complete now

- SRR recovery and validation
- Kraken-based taxonomic profiling
- sample-level dataset reconstruction
- exploratory ordination, clustering, and similarity analysis
- ecological metric computation
- reduced feature-table creation
- prototype SMHI construction

## What is still blocked

- supervised crop prediction
- crop recommendation
- any validated agronomic claim tied to the current SMHI

## Why it is blocked

- no directly observed crop/suitability target exists in the current repository
- agronomic metadata is incomplete
- sample size is small relative to the feature space
