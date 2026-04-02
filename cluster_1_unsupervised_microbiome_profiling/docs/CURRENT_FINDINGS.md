# Current Findings

## Dataset status

- Validated samples: `24`
- Current defensible scope: exploratory microbiome profiling
- Directly observed agronomic target: absent

## Main quantitative findings

- Genus Hellinger PCA variance explained: `PC1 = 39.24%`, `PC2 = 14.93%`
- Phylum Hellinger PCA variance explained: `PC1 = 53.74%`, `PC2 = 24.99%`
- Closest Bray-Curtis sample pair: `SRR26201959` vs `SRR26201961` (`0.0054`)
- Most dissimilar Bray-Curtis pair: `SRR13396075` vs `SRR1825760` (`0.9883`)
- Ward clustering at `k = 3` produced cluster sizes `12`, `9`, and `3`

## Diversity and composition

- Species richness range: `59` to `627`
- Genus richness range: `57` to `510`
- Genus Shannon diversity range: `1.381` to `5.055`
- Unclassified proportion range: `0.001` to `0.954`

## Prototype health-index status

- A transparent three-version SMHI prototype has been generated from current unsupervised microbiome metrics only.
- Preferred reporting version: `Version B` (weighted percentile index)
- Version B score range: `14.27` to `89.90`
- Highest Version B scores: `SRR23183349`, `SRR23183348`, `SRR23183368`
- Lowest Version B scores: `SRR33853917`, `SRR13396075`, `SRR9093167`
- The SMHI is explicitly heuristic and not an agronomic prediction score.
