# SMHI Interpretation Guide

## What the prototype means

The SMHI is a structured summary of microbiome community properties across the validated 24-sample dataset.

It is useful for:

- comparing samples within the current cohort
- highlighting samples with strongly skewed or low-diversity community structure
- creating a discussion-ready prototype deliverable for the capstone
- preparing a future calibration step once real soil chemistry and agronomic metadata arrive

## What the prototype does not mean

- It does not prove that a high-scoring sample is agronomically healthier.
- It does not predict crop suitability.
- It does not replace measured soil chemistry.
- It does not create a supervision target for machine learning.

## Recommended reporting practice

- Report Version B as the primary SMHI because it is the most robust of the three versions for this small cohort.
- Present Versions A and C as sensitivity checks, not competing biological truths.
- Always pair the SMHI with its component scores and the methodology note.

## What is needed next for validation

- soil pH
- NPK or equivalent nutrient measurements
- moisture
- temperature
- directly observed crop outcome, crop grown, or a curated suitability target

Those data are needed before the SMHI can be calibrated against real agronomic outcomes.
