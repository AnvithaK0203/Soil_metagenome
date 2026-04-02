# Cluster 1: Unsupervised Microbiome Profiling

This cluster is the active, scientifically valid workflow for the current repository state.

It contains copied analysis-ready data, copied provenance outputs, and cluster-local prototype work built only from the validated 24-SRR microbiome dataset. It does not contain supervised crop prediction.

## Contents

- `data/`: validated microbiome matrices, filtered/transformed matrices, sample metrics, and the reduced feature table
- `scripts/`: provenance copies of the current exploratory scripts plus cluster-local aggregation and health-index prototype utilities
- `outputs/`: exploratory reports, figures, and the Cluster 1 prototype outputs
- `docs/`: cluster-specific methodology, findings, limitations, and next-step notes

## Guardrail

This cluster uses only existing validated microbiome data. No crop labels or synthetic agronomic metadata are introduced here.

## Execution note

The canonical project-wide scripts remain under the repository root at `scripts/`. The copied scripts in this cluster preserve the workflow breakdown, while the new `feature_aggregation.py` and `health_index_prototype.py` are cluster-local utilities that generated the additional Cluster 1 outputs.

## Major deliverables

- exploratory phylum/genus/species microbiome profiling
- filtered and transformed microbiome matrices
- sample-level ecological metrics
- reduced exploratory feature table
- a prototype Soil Microbiome Health Index derived from validated metagenomic community structure metrics

For the index-specific methodology and guardrails, see:

- `docs/SMHI_METHODOLOGY.md`
- `docs/SMHI_LIMITATIONS.md`
- `docs/SMHI_INTERPRETATION_GUIDE.md`
