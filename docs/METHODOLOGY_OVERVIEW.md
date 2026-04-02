# Methodology Overview

## 1. SRR recovery and completeness audit

The project was first treated as a recovery problem. Expected SRRs were reconstructed from the original notebook and project artifacts. Local outputs were validated against real disk files rather than stale summaries.

## 2. Kraken processing

Validated sequencing runs were classified with Kraken2. Compact `.report` outputs are retained in the repository for provenance, while raw `.kraken` streams remain local because they are large.

## 3. Dataset reconstruction

Taxonomy outputs and available metadata were merged into a sample-level dataset. The rebuilt merged dataset has:

- `24` rows
- `11116` columns
- about `30` metadata/provenance columns
- about `11086` microbial feature columns

## 4. Exploratory microbiome analysis

The current analysis workflow includes:

- taxonomic rank extraction
- prevalence filtering
- relative abundance, Hellinger, and CLR transformations
- PCA
- hierarchical clustering
- Bray-Curtis sample similarity summaries
- top taxa summaries
- ecological diversity metrics

## 5. SMHI prototype

Cluster 1 contains a transparent prototype Soil Microbiome Health Index built only from unsupervised microbiome metrics such as richness, diversity, evenness, dominance balance, and classification completeness. It is descriptive, not externally validated.
