# SRR Recovery Execution Report

## What was found

- Expected SRRs audited: 24
- Local processed SRRs still present: 24
- Local metadata-merged SRRs still present: 10
- Missing processed SRRs: 0
- Missing processed compressed FASTQ volume advertised by ENA: 0.0 GB

## What was executed

- Queried ENA run metadata for all expected SRRs.
- Queried ENA sample XML records to recover richer sample attributes.
- Re-scanned the project snapshot for raw FASTQ and SRA files.
- Rebuilt the SRR audit, sample manifest, and extraction manifest with remote recovery context.

## What changed

- Added remote sample accession, study accession, experiment accession, layout, and public FASTQ URLs for the expected SRRs.
- Added remote sample metadata fields such as collection date and geo-location where available.
- Generated a WSL recovery helper at `scripts/wsl_recover_missing_srrs_autogen.sh`.

## What remains blocked or uncertain

- No expected SRRs remain missing from local processed outputs in this recovery pass.
- Windows-native Kraken2 is still not provisioned in the workspace, but WSL-based recovery has already produced the required local outputs.

## What files were created or updated

- `srr_audit_report.csv`
- `processed_data/sample_manifest.csv`
- `outputs/extraction_manifest.csv`
- `outputs/remote_run_metadata.csv`
- `outputs/remote_sample_attributes_long.csv`
- `cleaned_data/remote_sample_metadata.csv`
- `scripts/wsl_recover_missing_srrs.sh`

## What the next immediate step is

- Freeze the verified biological recovery state and rebuild downstream analytical datasets from the recovered SRR set.
- Keep supervised modeling blocked unless a directly observed target is added later.

## Missing SRRs

None

## WSL Availability

```text
WSL unavailable: [Errno 2] No such file or directory: 'wsl'
```
