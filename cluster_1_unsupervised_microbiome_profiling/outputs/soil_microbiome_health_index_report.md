# Soil Microbiome Health Index Report

## What was found

- Samples scored: 24
- Preferred reporting version: `Version B`
- Version B score range: 14.27 to 89.90
- Version B median score: 50.80
- Largest cross-version rank spread: 13 ranks for SRR26201960

## What was executed

- Evaluated current unsupervised sample-level metrics as candidate index components.
- Computed three transparent SMHI versions: weighted min-max, weighted percentile, and percentile plus a small typicality term.
- Calculated sample-level component scores, version scores, ranks, and internal sanity-check correlations.
- Generated summary tables and diagnostic figures inside Cluster 1 only.

## Candidate components

| component | what_it_measures | prototype_direction | use_status |
| --- | --- | --- | --- |
| richness (species + genus) | observed taxonomic breadth | higher tentatively better | included |
| Shannon diversity | richness-evenness balance | higher tentatively better | included |
| Simpson diversity | inverse dominance emphasis | higher tentatively better | included |
| evenness | balance across taxa | higher tentatively better | included |
| dominant taxon proportion | single-taxon concentration | lower tentatively better | included as inverse dominance |
| unclassified proportion | fraction not resolved by current reference space | lower tentatively better | included with lower weight |
| genus Hellinger centroid distance | compositional outlierness within this cohort | lower may indicate more typicality | included only in Version C sensitivity analysis |
| cluster membership | membership in unsupervised groups | no health direction | excluded |

## Index versions and formulas

Let:

- `R` = combined richness score from species and genus richness
- `H` = Shannon diversity score
- `S` = Simpson diversity score
- `E` = evenness score
- `D` = inverse dominance score from dominant genus proportion
- `C` = classification completeness score from `1 - unclassified proportion`
- `T` = typicality score from inverse percentile of genus Hellinger centroid distance

Core weights:

- `w_R = 0.25`
- `w_H = 0.20`
- `w_S = 0.15`
- `w_E = 0.15`
- `w_D = 0.15`
- `w_C = 0.10`

### Version A: weighted min-max index

`SMHI_A = 100 * (0.25R_mm + 0.20H_mm + 0.15S_mm + 0.15E_mm + 0.15D_mm + 0.10C_mm)`

### Version B: weighted percentile index

`SMHI_B = 100 * (0.25R_pct + 0.20H_pct + 0.15S_pct + 0.15E_pct + 0.15D_pct + 0.10C_pct)`

### Version C: percentile index with typicality sensitivity term

`SMHI_C = 0.85 * SMHI_B + 15 * T_pct`

Version B is the preferred reporting version because percentile scoring is more robust than min-max scaling for a 24-sample cohort and does not rely on an extra typicality assumption.

## Internal sanity checks

### Version agreement (Spearman correlation)

| version | smhi_version_a_minmax_0_100 | smhi_version_b_percentile_0_100 | smhi_version_c_percentile_typicality_0_100 |
| --- | --- | --- | --- |
| smhi_version_a_minmax_0_100 | 1.0 | 0.795 | 0.701 |
| smhi_version_b_percentile_0_100 | 0.795 | 1.0 | 0.975 |
| smhi_version_c_percentile_typicality_0_100 | 0.701 | 0.975 | 1.0 |

### Spearman correlation of Version B with source metrics

| metric | spearman_r |
| --- | --- |
| simpson_diversity | 0.95 |
| shannon_diversity | 0.949 |
| genus_richness | 0.783 |
| richness | 0.772 |
| evenness | 0.35 |
| genus_hellinger_centroid_distance | -0.158 |
| unclassified_proportion | -0.337 |
| dominant_taxon_proportion | -0.887 |

### Highest-scoring samples by Version B

- SRR23183349: 89.90 (highest)
- SRR23183348: 87.71 (highest)
- SRR23183368: 84.17 (highest)

### Lowest-scoring samples by Version B

- SRR33853917: 23.85 (lower)
- SRR13396075: 14.79 (lower)
- SRR9093167: 14.27 (lower)

## What outputs were created

- `cluster_1_unsupervised_microbiome_profiling/data/soil_microbiome_health_index.csv`
- `cluster_1_unsupervised_microbiome_profiling/data/soil_microbiome_health_index_components.csv`
- `cluster_1_unsupervised_microbiome_profiling/outputs/soil_microbiome_health_index_summary.csv`
- `cluster_1_unsupervised_microbiome_profiling/outputs/soil_microbiome_health_index_report.md`
- `cluster_1_unsupervised_microbiome_profiling/outputs/figures/smhi_version_comparison.png`
- `cluster_1_unsupervised_microbiome_profiling/outputs/figures/smhi_component_heatmap.png`
- `cluster_1_unsupervised_microbiome_profiling/outputs/figures/smhi_b_vs_metrics.png`
- `cluster_1_unsupervised_microbiome_profiling/outputs/figures/genus_pca_colored_by_smhi_b.png`

## What assumptions were made

- Higher diversity and evenness were treated as favorable within this prototype because they represent broader and less concentrated community structure within the current cohort.
- Lower dominance and lower unclassified proportion were treated as favorable within this prototype, while recognizing that database coverage and ecology both affect those quantities.
- The centroid-distance typicality term was used only as a sensitivity analysis, not as the main scoring basis.

## What limitations remain

- This index is an internal descriptive prototype, not a validated soil-health diagnosis.
- No soil chemistry or crop outcome data were used, so agronomic interpretation remains blocked.
- With only 24 samples, rankings are cohort-relative and can shift if new samples are added.
