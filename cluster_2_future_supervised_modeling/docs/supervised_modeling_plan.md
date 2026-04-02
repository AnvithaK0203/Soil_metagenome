# Supervised Modeling Plan

## Current status

Blocked. The repository does not yet contain a directly observed agronomic target or complete soil physicochemical metadata.

## Required sequence before modeling

1. Populate `data/future_metadata_template.csv` with real measurements and observed target values.
2. Confirm one row still equals one sample/SRR after metadata merging.
3. Define exactly one supervised target for the first modeling pass.
4. Check missingness, class balance, and leakage risk.
5. Build a leakage-safe merged dataset.
6. Start with a simple baseline only after the target is defensible.

## Allowed first supervised scopes

- Binary or multiclass crop outcome prediction if the target is directly observed
- Crop-group prediction rather than fine-grained crop recommendation
- Regression/classification on an externally measured soil-health score if such a score is added

## Not allowed

- Inferring labels from location, accession, or unsupervised clusters
- Training on the current repository state without real targets
- Treating the current prototype health index as supervised truth
