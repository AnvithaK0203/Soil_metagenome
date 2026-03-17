# Restart Integrity Summary

Generated: 2026-03-15

## What Was Audited

- `logs/wsl_recovery/run_recovery_status.csv`
- `logs/wsl_recovery_execution.log`
- `logs/wsl_recovery/wsl_recovery_master.log`
- `outputs/extraction_manifest.csv`
- `srr_audit_report.csv`
- `processed_data/sample_manifest.csv`
- `kraken_out/`
- `raw_data/recovered_fastq/`
- `logs/wsl_recovery/`

## Verified Checkpoint State

- `SRR33963318` to `SRR33963324`, `SRR5365029`, `SRR8468865`, and `SRR9093167` have validated FASTQ plus Kraken outputs on disk.
- `SRR9830591` has validated FASTQ files on disk and an in-progress Kraken output file.
- The first SRR that is not yet `completed_validated` is `SRR9830591`.

## Filesystem Evidence Used

- Validated Kraken reports exist for 10 recovered runs under `kraken_out/`.
- `kraken_out/SRR9830591.kraken` exists, is non-zero, and was observed growing during the restart audit.
- No zero-byte files remain in `kraken_out/`.
- No zero-byte files remain in `raw_data/recovered_fastq/`.
- Previously quarantined placeholder retained:
  - `logs/wsl_recovery/quarantine/SRR33963322/SRR33963322_1.fastq.gz.20260314T235403.zero_byte`

## Live Process Check

- An active WSL Kraken2 process for `SRR9830591` was detected during restart audit.
- Supporting `gzip -dc` reader processes for both `SRR9830591` FASTQs were also active.
- Because the classification was still running and the output file size increased between checks, no restart or quarantine action was taken for `SRR9830591`.

## Manifest Reconciliation Notes

- `run_recovery_status.csv` still reflects the older `classification_failed` state for `SRR9830591` from the prior failed attempt.
- `outputs/extraction_manifest.csv`, `srr_audit_report.csv`, and `processed_data/sample_manifest.csv` are stale relative to the validated recovered filesystem state and must be rebuilt only after `SRR9830591` finishes or is conclusively blocked.

## Resume Decision

- Preserve all validated existing outputs.
- Do not restart the queue from scratch.
- Resume point remains `SRR9830591`.
- Allow the live WSL classification to continue unless validation later proves it stalled or produced invalid outputs.
