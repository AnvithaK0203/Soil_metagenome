# Feature Aggregation Report

## What was found

- Selected phylum features: 9
- Selected genus features: 38

## What was executed

- Loaded the Cluster 1 relative-abundance phylum and genus matrices.
- Retained phylum features with prevalence >= 3 samples and mean relative abundance >= 1%.
- Retained genus features with prevalence >= 3 samples and mean relative abundance >= 0.5%.

## What outputs were created

- `cluster_1_unsupervised_microbiome_profiling/outputs/aggregated_taxa_feature_selection.csv`

## What assumptions were made

- Aggregation thresholds match the reduced-feature-table rules already used in the main repository workflow.
- This script is descriptive and does not create any label or prediction target.

## What limitations remain

- Selected taxa are stable descriptive features only; they are not validated biomarkers of soil health or crop outcome.
