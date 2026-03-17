# Final Dataset Reconstruction Notes

## What was found

- Best local taxonomy table rows: 24
- Processed manifest rows with local taxonomy: 24
- Final merged preview rows: 24
- Taxonomic feature columns retained in the preview: 11086

## What was executed

- Joined the best local taxonomy matrix to the enriched sample manifest on the SRR sample key.
- Resolved metadata by preferring local observed fields and falling back to remote ENA metadata when local fields were empty.
- Preserved provenance columns so metadata origin remains transparent.

## What changed

- Created `cleaned_data/final_resolved_metadata.csv`.
- Created `processed_data/final_merged_dataset_preview.csv`.

## What remains blocked or uncertain

- The merged dataset now spans all expected locally processed SRRs recovered in this project snapshot.
- No directly observed crop label was reconstructed, so the dataset is still exploratory rather than predictive.

## What the next immediate step is

- Use the complete locally processed SRR set for exploratory microbiome analysis and feature aggregation.
- Keep supervised modeling blocked until a directly observed target is added from primary project records.
