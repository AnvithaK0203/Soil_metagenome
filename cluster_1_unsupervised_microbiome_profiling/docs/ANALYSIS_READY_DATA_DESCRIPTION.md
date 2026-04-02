# Analysis-Ready Data Description

## What was created

- `processed_data/reduced_feature_table.csv`

## Column groups

- Sample identifiers and resolved metadata
- Sample-level ecological metrics
- Selected phylum relative-abundance features
- Selected genus relative-abundance features
- Genus PCA coordinates and a descriptive cluster label

## Feature selection rules

- Phylum features kept in the reduced table: prevalence >= 3 samples and mean relative abundance >= 1%.
- Genus features kept in the reduced table: prevalence >= 3 samples and mean relative abundance >= 0.5%.
- PCA coordinates come from the genus Hellinger matrix after prevalence >= 3 filtering.

## Important guardrail

- This reduced table is future-ready for exploratory work only.
- It must not be used for supervised crop prediction until a directly observed agronomic target is added.
