# Assumptions and Risks

## Assumptions

- One row remains one SRR sequencing run unless a later consolidation manifest proves otherwise.
- ENA metadata is treated as secondary provenance and not a replacement for primary local lab metadata.

## Scientific Uncertainties

- No validated crop target or suitability label is present after reconstruction.
- Soil physicochemical features remain absent in the local dataset.

## Leakage Risks

- Sample titles, geography, accession IDs, and study identifiers could become leakage proxies if used as targets or as near-target features.

## Modeling Risks

- The current ratio of 11086 microbial features to 24 processed samples is not appropriate for confident prediction.
- Full SRR recovery improves completeness, but the dataset is still too small and label-poor for predictive claims.

## Small-Sample Risks

- Any model trained now would be unstable and proof-of-concept only.

## Incomplete Extraction Risks

- 0 expected SRRs still lack local processed outputs.
- Biological recovery is complete for the expected SRR list recovered from the local project evidence.
