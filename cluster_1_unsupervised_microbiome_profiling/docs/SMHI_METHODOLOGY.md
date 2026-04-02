# SMHI Methodology

## Purpose

The Soil Microbiome Health Index (SMHI) in Cluster 1 is a prototype built only from current unsupervised microbiome descriptors. It is designed to summarize internal microbiome structure across the 24 validated samples in a transparent and reproducible way.

It is not a crop model and not a validated agronomic diagnosis tool.

## Input metrics

The SMHI uses the following sample-level metrics from `data/sample_level_metrics.csv`:

- species richness
- genus richness
- Shannon diversity
- Simpson diversity
- evenness
- dominant genus proportion
- unclassified proportion

An optional sensitivity term is also derived from `data/taxonomy_genus_matrix_prev3_hellinger.csv`:

- genus Hellinger centroid distance

## Component rationale

- Richness: broader observed taxonomic breadth may indicate a less depleted community, but it is still cohort-relative.
- Shannon diversity: combines richness and balance; useful as a general structure descriptor.
- Simpson diversity: emphasizes dominance and helps separate highly skewed communities.
- Evenness: rewards a less concentrated distribution of abundance.
- Dominance balance: inverse of dominant genus proportion; penalizes extreme single-genus concentration.
- Classification completeness: inverse of unclassified proportion; down-weighted because database coverage affects it.
- Typicality: inverse percentile of genus Hellinger centroid distance; used only in a sensitivity version, not the main version.

## Excluded candidates

- Cluster membership was not used because membership in an unsupervised cluster is not itself a health property.
- No taxon-specific “beneficial” component was introduced because the current project does not contain validated taxon-health rules.

## Index versions

Let:

- `R` = combined richness score from species and genus richness
- `H` = Shannon diversity score
- `S` = Simpson diversity score
- `E` = evenness score
- `D` = inverse dominance score
- `C` = classification completeness score
- `T` = typicality score

Core weights:

- `w_R = 0.25`
- `w_H = 0.20`
- `w_S = 0.15`
- `w_E = 0.15`
- `w_D = 0.15`
- `w_C = 0.10`

### Version A

Weighted min-max index:

`SMHI_A = 100 * (0.25R_mm + 0.20H_mm + 0.15S_mm + 0.15E_mm + 0.15D_mm + 0.10C_mm)`

### Version B

Weighted percentile index:

`SMHI_B = 100 * (0.25R_pct + 0.20H_pct + 0.15S_pct + 0.15E_pct + 0.15D_pct + 0.10C_pct)`

This is the preferred reporting version because it is more robust than min-max scaling for a small 24-sample cohort.

### Version C

Percentile index with a modest typicality term:

`SMHI_C = 0.85 * SMHI_B + 15 * T_pct`

This version is a sensitivity analysis only. It tests whether cohort outlierness meaningfully shifts the ranking.

## Output files

- `data/soil_microbiome_health_index.csv`
- `data/soil_microbiome_health_index_components.csv`
- `outputs/soil_microbiome_health_index_summary.csv`
- `outputs/soil_microbiome_health_index_report.md`

## Practical interpretation

- Higher scores mean the sample has, within this cohort, a more diverse, less dominated, more classifiable microbiome profile under the chosen scoring rules.
- Lower scores mean the sample is relatively more dominated, less diverse, or more weakly resolved under the same rules.
- These statements are internal structural comparisons only.
