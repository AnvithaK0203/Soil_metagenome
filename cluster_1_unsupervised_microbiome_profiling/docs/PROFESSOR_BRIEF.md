# Professor Brief

## What has been completed

- The intended 24-SRR dataset has been fully recovered and validated.
- The merged microbiome dataset was split into metadata and taxonomy components.
- Rank-specific phylum, genus, and species matrices were built and filtered.
- Relative abundance, Hellinger, and CLR transformations were generated on rank-specific matrices.
- Sample-level ecological metrics, PCA, hierarchical clustering, and pairwise similarity summaries were produced.
- A reduced feature table was created for future exploratory use.

## What the current analysis supports

- Exploratory microbiome structure analysis
- Diversity and composition summaries
- Lower-dimensional feature engineering for future work

## What it does not support

- Crop prediction
- Crop recommendation
- Any supervised claim tied to agronomic outcomes

## Why supervised ML remains blocked

- No directly observed crop or suitability label is present.
- n = 24 is still too small for the original high-dimensional feature space without a defensible target and stronger metadata.
