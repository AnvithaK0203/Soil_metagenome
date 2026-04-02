# Exploratory Summary

## What was found

- Genus Hellinger PCA variance explained: PC1 = 39.24%, PC2 = 14.93%
- Phylum Hellinger PCA variance explained: PC1 = 53.74%, PC2 = 24.99%
- Closest sample pair by genus Bray-Curtis distance: SRR26201959 vs SRR26201961 (0.0054)
- Most dissimilar sample pair by genus Bray-Curtis distance: SRR13396075 vs SRR1825760 (0.9883)

## What was executed

- Performed PCA on Hellinger-transformed phylum and genus matrices.
- Performed Ward hierarchical clustering on the genus Hellinger matrix.
- Computed Bray-Curtis pairwise distances on the genus relative abundance matrix.
- Summarized top phyla and genera by prevalence and mean relative abundance.

## What outputs were created

- `outputs/exploratory_summary.md`
- `outputs/top_taxa_summary.csv`
- `outputs/sample_similarity_summary.csv`
- `outputs/figures/phylum_pca.png`
- `outputs/figures/genus_pca.png`
- `outputs/figures/genus_hierarchical_clustering.png`
- `outputs/figures/genus_braycurtis_heatmap.png`

## What assumptions were made

- Genus-level Hellinger transformation is the primary exploratory matrix because it balances interpretability with resolution.
- Phylum-level ordination is included for broad ecological structure, not for fine sample discrimination.

## Key observations

- The most influential phylum-level PC1 loadings were: P|Actinobacteria, P|Planctomycetes, P|Bacteroidetes, P|Verrucomicrobia, P|Acidobacteria.
- The most influential genus-level PC1 loadings were: G|Streptomyces, G|Pirellula, G|Bradyrhizobium, G|Verrucomicrobium, G|Gemmata.
- Ward clustering with k = 3 produced cluster sizes: cluster 1 = 12, cluster 2 = 9, cluster 3 = 3.
- These unsupervised patterns describe microbiome structure only; they do not define crop classes or suitability groups.

## What limitations remain

- No supervised target exists, so these ordinations and clusters cannot be evaluated against agronomic outcomes.
- The sample size is still small relative to the genus and species feature spaces.
