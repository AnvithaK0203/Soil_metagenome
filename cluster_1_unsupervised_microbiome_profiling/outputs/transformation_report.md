# Transformation Report

## What was found

- The full taxonomy matrix is hierarchical and does not form a closed composition because nested ranks are recorded simultaneously.
- Single-rank phylum, genus, and species matrices are the appropriate inputs for row closure and compositional transformations.

## What was executed

- Converted selected rank-specific filtered matrices to row-closed relative abundance tables.
- Generated Hellinger-transformed versions for Euclidean ordination and clustering.
- Generated CLR-transformed versions using a documented pseudocount after row closure.

### taxonomy_phylum_matrix_prev2

- Input features: 37
- Relative abundance output: `processed_data/taxonomy_phylum_matrix_prev2_relative_abundance.csv`
- Hellinger output: `processed_data/taxonomy_phylum_matrix_prev2_hellinger.csv`
- CLR output: `processed_data/taxonomy_phylum_matrix_prev2_clr.csv`

### taxonomy_genus_matrix_prev3

- Input features: 634
- Relative abundance output: `processed_data/taxonomy_genus_matrix_prev3_relative_abundance.csv`
- Hellinger output: `processed_data/taxonomy_genus_matrix_prev3_hellinger.csv`
- CLR output: `processed_data/taxonomy_genus_matrix_prev3_clr.csv`

### taxonomy_species_matrix_prev3

- Input features: 931
- Relative abundance output: `processed_data/taxonomy_species_matrix_prev3_relative_abundance.csv`
- Hellinger output: `processed_data/taxonomy_species_matrix_prev3_hellinger.csv`
- CLR output: `processed_data/taxonomy_species_matrix_prev3_clr.csv`

## What each transformation does

- Relative abundance closes each rank-specific row to sum to 1.0, making samples comparable within that taxonomic level.
- Hellinger transformation takes the square root of relative abundance and is preferred for PCA and hierarchical clustering because it stabilizes dominant taxa while remaining Euclidean-friendly.
- CLR transformation applies log-ratio scaling after adding a pseudocount of `1e-06` to handle zeros. It is useful for sensitivity analysis of compositional structure, but it is less directly interpretable than Hellinger for presentation.

## Preferred downstream use

- Phylum relative abundance: descriptive summaries and interpretable stacked composition comparisons.
- Genus Hellinger: primary matrix for PCA and clustering.
- Genus CLR: sensitivity analysis if log-ratio geometry needs to be inspected.
- Species transforms: exploratory only, because the species matrix remains high-dimensional relative to n = 24.

## What assumptions were made

- Only rank-specific matrices were transformed compositionally.
- Prevalence-filtered matrices were used to reduce zero inflation before transformation.

## What limitations remain

- CLR results depend on the chosen pseudocount and should be interpreted cautiously.
- The full hierarchical matrix is retained for traceability, not for direct compositional analysis.
