# Feature Filtering Report

## What was found

- Filtering was applied to the frozen analysis matrices generated from the validated 24-sample dataset.
- Prevalence is defined as abundance > 0 in a sample.

## What was executed

- Removed all-zero features.
- Computed prevalence >= 2 and prevalence >= 3 feature sets for each matrix.
- Left the mean abundance threshold disabled by default to avoid over-pruning an already small 24-sample dataset.

## What outputs were created

- Prevalence-filtered matrices for the full, analysis, phylum, genus, and species tables were saved under `processed_data/` with `_prev2.csv` and `_prev3.csv` suffixes.

## Filtering summary

| matrix_name | original_features | nonzero_features | prevalence_ge_2 | prevalence_ge_3 | retained_prev2_output | retained_prev3_output |
| --- | --- | --- | --- | --- | --- | --- |
| full | 11086 | 4059 | 3089 | 2604 | 3089 | 2604 |
| analysis | 11083 | 4056 | 3086 | 2601 | 3086 | 2601 |
| phylum | 42 | 38 | 37 | 36 | 37 | 36 |
| genus | 1514 | 887 | 738 | 634 | 738 | 634 |
| species | 5207 | 1701 | 1187 | 931 | 1187 | 931 |

## Counts per taxonomic level in the full matrix

| rank_prefix | feature_count |
| --- | --- |
| C | 81 |
| C1 | 13 |
| C2 | 7 |
| C3 | 1 |
| C4 | 1 |
| D | 4 |
| D1 | 19 |
| D2 | 15 |
| D3 | 6 |
| D4 | 1 |
| F | 450 |
| F1 | 113 |
| F2 | 25 |
| F3 | 3 |
| G | 1514 |
| G1 | 144 |
| G2 | 12 |
| K | 1 |
| K1 | 1 |
| K2 | 1 |
| K3 | 1 |
| O | 181 |
| O1 | 32 |
| O2 | 14 |
| O3 | 1 |
| O4 | 1 |
| P | 42 |
| P1 | 18 |
| P2 | 6 |
| P3 | 1 |
| P4 | 1 |
| P5 | 1 |
| P6 | 1 |
| P7 | 1 |
| P8 | 1 |
| P9 | 1 |
| R | 1 |
| R1 | 2 |
| S | 5207 |
| S1 | 2703 |
| S2 | 384 |
| S3 | 73 |
| U | 1 |

## What assumptions were made

- Mean abundance threshold applied: `0.0` on the raw matrix scale.
- Default outputs keep the abundance threshold at 0.0 because prevalence filtering already removes unsupported rare features without forcing an arbitrary extra cutoff.

## What limitations remain

- The full and analysis matrices remain hierarchically nested, so filtered versions are retained mainly for traceability.
- Rank-specific filtered matrices are the correct inputs for compositional transformation and exploratory multivariate analysis.
