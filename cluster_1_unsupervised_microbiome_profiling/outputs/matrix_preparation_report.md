# Matrix Preparation Report

## What was found

- Input merged dataset: `processed_data/final_merged_dataset_preview.csv`
- Samples: 24
- Metadata/provenance columns: 30
- Taxonomic feature columns: 11086
- Structural taxonomy buckets excluded from the analysis matrix: U|unclassified, R|root, R1|cellular organisms

## What was executed

- Split the validated merged dataset into a metadata/provenance table and a taxonomy-only matrix.
- Built exact-rank phylum, genus, and species matrices using only columns with prefixes `P|`, `G|`, and `S|`.
- Built an analysis matrix that excludes structural buckets used only for bookkeeping, not interpretation.

## What outputs were created

- `processed_data/metadata_table.csv`
- `processed_data/taxonomy_full_matrix.csv`
- `processed_data/taxonomy_analysis_matrix.csv`
- `processed_data/taxonomy_phylum_matrix.csv`
- `processed_data/taxonomy_genus_matrix.csv`
- `processed_data/taxonomy_species_matrix.csv`

## What assumptions were made

- The first 30 non-microbial columns in the merged dataset are metadata, provenance, or identifiers.
- Single-rank matrices are mathematically preferable for compositional normalization because the full hierarchy double-counts nested abundances across ranks.

## What limitations remain

- The full hierarchical taxonomy matrix is retained for traceability but should not be treated as a closed composition for CLR or ordination.
- No directly observed crop or suitability label exists in the merged dataset.
