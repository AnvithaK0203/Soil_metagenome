# Sample-Level Metrics Report

## What was found

- Samples analyzed: 24
- Species richness range: 59 to 627
- Genus richness range: 57 to 510
- Shannon diversity range (genus): 1.381 to 5.055
- Unclassified proportion range: 0.001 to 0.954

## What was executed

- Computed species richness from the exact species-level matrix.
- Computed Shannon, Simpson, and evenness on the genus-level closed composition.
- Measured unclassified proportion from the `U|unclassified` top-level structural column.
- Recorded dominant phylum and dominant genus per sample.

## What outputs were created

- `processed_data/sample_level_metrics.csv`
- `outputs/sample_level_metrics_report.md`

## What assumptions were made

- Species richness is used as the primary richness count, with genus richness retained as a stability-oriented companion metric.
- Shannon, Simpson, and evenness are reported at genus level because species-level assignments are much sparser.

## What limitations remain

- Diversity estimates are descriptive only and should not be over-interpreted with n = 24.
- They do not imply agronomic suitability without external labels or soil chemistry.
