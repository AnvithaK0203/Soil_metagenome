# Post-Recovery Feasibility Report

## What was found

- Expected SRRs: 24
- Locally processed SRRs: 24
- Locally metadata-merged SRRs: 10
- SRRs with remote sample metadata recovered from ENA: 24
- Missing processed SRRs: 0
- Final merged preview rows: 24
- Microbial feature columns in the final merged preview: 11086
- Metadata columns in the final merged preview: 10

## Scientific Answers

- One sample is currently defined as one SRR sequencing run.
- Label status: No directly observed crop or suitability label column exists after reconstruction.
- Sample size sufficiency: 24 processed samples is too small for defensible crop prediction.
- Metadata sufficiency: remote metadata enrichment improves context, but it still does not supply a validated crop target or full soil chemistry.
- Leakage risk: high if any label were inferred from accession, study, geography, or sample title rather than observed field measurements.
- High-dimensionality risk: 11086 microbial features over 24 processed samples remains severely underpowered.
- Crop prediction ambition: still too ambitious for the current recovered state.

## Decision

- Crop prediction: not scientifically justified.
- Crop recommendation: not scientifically justified.
- Soil health index development: only as a cautious exploratory prototype after feature aggregation, not as a validated index.
- Exploratory analysis only: justified.
- Proof-of-concept baseline only: possible only after a real observed target exists.

## What remains blocked or uncertain

- All expected SRRs now have local processed outputs in this recovery pass.
- A directly observed crop label is still absent.
- Even with full local SRR processing, the metadata remains insufficient for supervised crop prediction.

## What the next immediate step is

- Freeze the biological recovery as complete and continue only with exploratory microbiome plus metadata analysis unless primary label data is added.
