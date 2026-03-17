# Disk-Truth Re-Audit Report

## What was found

- Expected SRRs: 24
- Validated complete SRRs on disk: 24
- Classification currently in progress: 0
- Downloaded but not yet classified: 0
- Partial local artifacts requiring review: 0
- Missing completely locally: 0

## Validated complete SRRs

- `SRR12376372`
- `SRR13342225`
- `SRR13396075`
- `SRR13396103`
- `SRR1825760`
- `SRR23183348`
- `SRR23183349`
- `SRR23183368`
- `SRR26201959`
- `SRR26201960`
- `SRR26201961`
- `SRR33853917`
- `SRR33963317`
- `SRR33963318`
- `SRR33963319`
- `SRR33963320`
- `SRR33963321`
- `SRR33963322`
- `SRR33963323`
- `SRR33963324`
- `SRR5365029`
- `SRR8468865`
- `SRR9093167`
- `SRR9830591`

## Classification In Progress

- none

## Downloaded But Not Yet Classified

- none

## Partial Local Artifacts

- none

## Missing completely locally

- none

## Rule applied

- A run is counted as processed only if both `.report` and `.kraken` exist on disk and are non-empty.
- CSV-only derived rows without supporting Kraken artifacts are not counted as processed.
- In-progress and partial states are reported from on-disk FASTQ and Kraken artifacts only.

## Files written

- `outputs/kraken_disk_validation.csv`
- `outputs/missing_srr_fastq_check.csv`
- `outputs/disk_truth_reaudit_report.md`
