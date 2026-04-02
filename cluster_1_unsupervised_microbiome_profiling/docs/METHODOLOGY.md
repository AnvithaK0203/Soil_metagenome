# Methodology

## What was used

- `data/final_merged_dataset_preview.csv`
- `data/metadata_table.csv`
- rank-specific taxonomy matrices in `data/`
- filtered and transformed phylum/genus/species matrices in `data/`
- `data/sample_level_metrics.csv`

## Workflow

1. Freeze the validated merged dataset into metadata and taxonomy blocks.
2. Build exact-rank phylum, genus, and species matrices.
3. Remove structural bookkeeping taxa from the analysis matrix where appropriate.
4. Filter features by nonzero presence and sample prevalence.
5. Apply row-closed relative abundance, Hellinger, and CLR transforms only to single-rank matrices.
6. Compute ecological metrics per sample.
7. Run unsupervised ordination, clustering, and sample-similarity analysis.
8. Build a reduced exploratory feature table.
9. Build an unsupervised prototype health index strictly as a descriptive composite.

## Mathematical choices

- Prevalence thresholds: `>= 2` and `>= 3` samples
- Primary exploratory matrix: genus-level Hellinger after prevalence `>= 3`
- Broad compositional summary matrix: phylum-level relative abundance / Hellinger
- No supervised target was introduced

## Why this is the correct current direction

- The repository has a validated microbiome dataset but no directly observed crop/suitability target.
- Unsupervised ecological analysis is supported by the available data.
- Supervised crop prediction is not scientifically justified yet.
