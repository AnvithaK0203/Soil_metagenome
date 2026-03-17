param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

function Get-ExpectedSrrs {
    $text = Get-Content (Join-Path $ProjectRoot "Anvitha.ipynb") -Raw
    return [regex]::Matches($text, 'SRR\d+') | ForEach-Object Value | Sort-Object -Unique
}

function Normalize-SampleId {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return $Value.ToString().Trim().ToUpperInvariant()
}

function Infer-Category {
    param([string]$ColumnName)
    $lower = $ColumnName.ToLowerInvariant()
    if ($lower -in @("sample", "biosample", "run", "accession") -or $lower.EndsWith("_id")) { return "id" }
    if ($lower -match "crop|label|target|class|suitability") { return "label_candidate" }
    if ($lower -in @("geo_loc_name", "lat_lon", "env_medium", "env_local_scale", "collection_date")) { return "metadata" }
    if ($ColumnName.Contains("|")) { return "microbial_feature" }
    return "other"
}

function Infer-Description {
    param([string]$ColumnName)
    $category = Infer-Category $ColumnName
    switch ($category) {
        "id" { return "Identifier column for the sample or accession." }
        "label_candidate" { return "Potential supervised-learning label or grouping variable." }
        "metadata" { return "Observed contextual metadata carried with the sample." }
        "microbial_feature" { return "Taxonomic abundance feature encoded from the Kraken report." }
        default { return "Unclassified column carried from the source dataset." }
    }
}

function Write-NotebookWrapper {
    param(
        [string]$Path,
        [string]$Title,
        [string]$Body,
        [string]$Command
    )

    $notebook = @{
        cells = @(
            @{
                cell_type = "markdown"
                metadata = @{}
                source = @("# $Title`n", "`n", "$Body`n")
            },
            @{
                cell_type = "code"
                execution_count = $null
                metadata = @{}
                outputs = @()
                source = @("$Command`n")
            }
        )
        metadata = @{
            kernelspec = @{
                display_name = "Python 3"
                language = "python"
                name = "python3"
            }
            language_info = @{
                name = "python"
            }
        }
        nbformat = 4
        nbformat_minor = 5
    }

    ($notebook | ConvertTo-Json -Depth 8) | Set-Content -Encoding utf8 $Path
}

$expectedSrrs = Get-ExpectedSrrs
$partialDf = Import-Csv (Join-Path $ProjectRoot "taxonomy_kraken2_minikraken.csv")
$supersetDf = Import-Csv (Join-Path $ProjectRoot "taxonomy_kraken2_minikraken (1).csv")
$optimizedDf = Import-Csv (Join-Path $ProjectRoot "Optimized_Taxonomy_ML.csv")

$partialSamples = $partialDf | Select-Object -ExpandProperty sample | ForEach-Object { Normalize-SampleId $_ } | Sort-Object -Unique
$supersetSamples = $supersetDf | Select-Object -ExpandProperty sample | ForEach-Object { Normalize-SampleId $_ } | Sort-Object -Unique
$optimizedSamples = $optimizedDf | Select-Object -ExpandProperty sample | ForEach-Object { Normalize-SampleId $_ } | Sort-Object -Unique

$cleanPartial = $partialDf | ForEach-Object {
    $_.sample = Normalize-SampleId $_.sample
    $_
} | Sort-Object sample -Unique
$cleanSuperset = $supersetDf | ForEach-Object {
    $_.sample = Normalize-SampleId $_.sample
    $_
} | Sort-Object sample -Unique
$cleanOptimized = $optimizedDf | ForEach-Object {
    $_.sample = Normalize-SampleId $_.sample
    $_
} | Sort-Object sample -Unique

$cleanPartial | Export-Csv (Join-Path $ProjectRoot "cleaned_data\taxonomy_kraken2_minikraken_subset_clean.csv") -NoTypeInformation -Encoding utf8
$cleanSuperset | Export-Csv (Join-Path $ProjectRoot "cleaned_data\taxonomy_kraken2_minikraken_superset_clean.csv") -NoTypeInformation -Encoding utf8
$cleanOptimized | Export-Csv (Join-Path $ProjectRoot "cleaned_data\optimized_taxonomy_ml_clean.csv") -NoTypeInformation -Encoding utf8
$cleanSuperset | Export-Csv (Join-Path $ProjectRoot "processed_data\current_best_taxonomy_matrix.csv") -NoTypeInformation -Encoding utf8

$metadataRows = $cleanOptimized | Select-Object sample, BioSample, geo_loc_name, lat_lon, env_medium, env_local_scale, Collection_Date
$metadataRows | Export-Csv (Join-Path $ProjectRoot "cleaned_data\sample_metadata_observed.csv") -NoTypeInformation -Encoding utf8

$srrRows = foreach ($srr in $expectedSrrs) {
    $metadataPresent = if ($srr -in $optimizedSamples) { "present" } else { "absent" }
    $processedPresent = if ($srr -in $supersetSamples) { "present" } else { "absent" }
    $status = if ($processedPresent -eq "present" -and $metadataPresent -eq "present") {
        "processed_with_metadata"
    } elseif ($processedPresent -eq "present") {
        "processed_no_metadata"
    } else {
        "expected_missing_processed"
    }
    $notes = ""
    if ($srr -in @("SRR12376372", "SRR33853917", "SRR33963317")) {
        $notes = "Present in the 13-sample Kraken table but absent from the derived 10-sample ML table."
    } elseif ($status -eq "expected_missing_processed") {
        $notes = "Mentioned in Anvitha.ipynb but not represented in any current local processed CSV."
    }
    [pscustomobject]@{
        srr_id = $srr
        expected_or_detected = "expected"
        local_raw_presence = "absent"
        local_processed_presence = $processedPresent
        metadata_presence = $metadataPresent
        status = $status
        evidence_source = "Anvitha.ipynb"
        notes = $notes
    }
}
$srrRows | Export-Csv (Join-Path $ProjectRoot "srr_audit_report.csv") -NoTypeInformation -Encoding utf8

$sampleManifest = foreach ($srr in $expectedSrrs) {
    $auditRow = $srrRows | Where-Object { $_.srr_id -eq $srr } | Select-Object -First 1
    $metadataRow = $metadataRows | Where-Object { $_.sample -eq $srr } | Select-Object -First 1
    [pscustomobject]@{
        sample = $srr
        expected_or_detected = $auditRow.expected_or_detected
        local_raw_presence = $auditRow.local_raw_presence
        local_processed_presence = $auditRow.local_processed_presence
        metadata_presence = $auditRow.metadata_presence
        status = $auditRow.status
        BioSample = if ($metadataRow) { $metadataRow.BioSample } else { "" }
        geo_loc_name = if ($metadataRow) { $metadataRow.geo_loc_name } else { "" }
        lat_lon = if ($metadataRow) { $metadataRow.lat_lon } else { "" }
        env_medium = if ($metadataRow) { $metadataRow.env_medium } else { "" }
        env_local_scale = if ($metadataRow) { $metadataRow.env_local_scale } else { "" }
        Collection_Date = if ($metadataRow) { $metadataRow.Collection_Date } else { "" }
    }
}
$sampleManifest | Export-Csv (Join-Path $ProjectRoot "processed_data\sample_manifest.csv") -NoTypeInformation -Encoding utf8

$manifestRows = foreach ($srr in $expectedSrrs) {
    $auditRow = $srrRows | Where-Object { $_.srr_id -eq $srr } | Select-Object -First 1
    $checkpoint = if ($auditRow.local_processed_presence -eq "present") { "classified" } else { "not_started" }
    [pscustomobject]@{
        srr_id = $srr
        planned_classifier = "kraken2"
        local_raw_presence = $auditRow.local_raw_presence
        local_processed_presence = $auditRow.local_processed_presence
        checkpoint_status = $checkpoint
        kraken2_command = "prefetch $srr -O sra ; fasterq-dump sra/$srr/$srr.sra -O raw_fastq --split-files -e 4 --temp tmp_sra ; pigz -f raw_fastq/$srr*.fastq ; kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 2 --paired raw_fastq/${srr}_1.fastq.gz raw_fastq/${srr}_2.fastq.gz --report kraken_out/${srr}.report --output kraken_out/${srr}.kraken"
        metaphlan_command = "metaphlan raw_fastq/${srr}_1.fastq.gz,raw_fastq/${srr}_2.fastq.gz --input_type fastq --db_dir metaphlan_db -x mpa_vJan25_CHOCOPhlAnSGB_202503 --nproc 1 --mapout metaphlan_mapout/${srr}.bowtie2.bz2 -o metaphlan_out/${srr}_profile.tsv"
        notes = if ($auditRow.local_processed_presence -eq "present") { "Already represented in the current local Kraken output." } else { "Missing from the local processed outputs; requires remote recovery." }
    }
}
$manifestRows | Export-Csv (Join-Path $ProjectRoot "outputs\extraction_manifest.csv") -NoTypeInformation -Encoding utf8

$missingExpected = $expectedSrrs | Where-Object { $_ -notin $supersetSamples }
$psRecovery = @(
    '$ErrorActionPreference = "Stop"',
    '$missing = @(' + (($missingExpected | ForEach-Object { "'$_'" }) -join ", ") + ')',
    'foreach ($srr in $missing) {',
    '  Write-Host "Recovering $srr"',
    '  prefetch $srr -O sra',
    '  fasterq-dump "sra/$srr/$srr.sra" -O raw_fastq --split-files -e 4 --temp tmp_sra',
    '  Get-ChildItem "raw_fastq/$srr*.fastq" | ForEach-Object { pigz -f $_.FullName }',
    '  kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 2 --paired raw_fastq/${srr}_1.fastq.gz raw_fastq/${srr}_2.fastq.gz --report kraken_out/${srr}.report --output kraken_out/${srr}.kraken',
    '}'
)
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "scripts\run_missing_srr_recovery.ps1") ($psRecovery -join "`n")

$shRecovery = @(
    '#!/usr/bin/env bash',
    'set -euo pipefail',
    'missing=(' + ($missingExpected -join ' ') + ')',
    'for srr in "${missing[@]}"; do',
    '  echo "Recovering ${srr}"',
    '  prefetch "${srr}" -O sra',
    '  fasterq-dump "sra/${srr}/${srr}.sra" -O raw_fastq --split-files -e 4 --temp tmp_sra',
    '  pigz -f raw_fastq/${srr}*.fastq',
    '  kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 2 --paired raw_fastq/${srr}_1.fastq.gz raw_fastq/${srr}_2.fastq.gz --report kraken_out/${srr}.report --output kraken_out/${srr}.kraken',
    'done'
)
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "scripts\run_missing_srr_recovery.sh") ($shRecovery -join "`n")

$extractionNotes = @"
# Extraction Recovery Notes

- Expected SRRs recovered from Anvitha.ipynb: 24
- Locally processed SRRs in the current best Kraken table: 13
- Missing locally processed SRRs: 11
- Primary recovery route: Kraken2
- Secondary documented route: MetaPhlAn only after memory constraints and command syntax issues are addressed

The local snapshot does not contain raw FASTQ or SRA files. The generated recovery scripts are templates for later execution when internet access and bioinformatics dependencies are available.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "docs\extraction_recovery_notes.md") $extractionNotes

$masterDictionary = New-Object System.Collections.Generic.List[object]
foreach ($file in @("taxonomy_kraken2_minikraken.csv", "taxonomy_kraken2_minikraken (1).csv", "Optimized_Taxonomy_ML.csv")) {
    $rows = Import-Csv (Join-Path $ProjectRoot $file)
    if (-not $rows) { continue }
    $columns = $rows[0].PSObject.Properties.Name
    foreach ($column in $columns) {
        $values = @($rows | ForEach-Object { $_.$column })
        $missingCount = @($values | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count
        $category = Infer-Category $column
        $dataType = if ($category -eq "microbial_feature") { "float" } elseif ($column -eq "sample" -or $column -eq "BioSample") { "string" } else { "string" }
        $masterDictionary.Add([pscustomobject]@{
            source_file = $file
            column_name = $column
            inferred_description = Infer-Description $column
            data_type = $dataType
            category = $category
            missing_count = $missingCount
            missing_fraction = [math]::Round(($missingCount / [double]$rows.Count), 6)
            notes = if ($category -eq "microbial_feature") { "Taxonomic abundance feature column." } else { "" }
        }) | Out-Null
    }
}
$masterDictionary | Export-Csv (Join-Path $ProjectRoot "master_data_dictionary.csv") -NoTypeInformation -Encoding utf8

$datasetAudit = @"
# Dataset Audit Report

## taxonomy_kraken2_minikraken.csv

- Rows: 5
- Columns: 7689
- Probable grain: One row per SRR sequencing run in an early Kraken2 feature matrix.
- Candidate ID columns: sample
- Candidate metadata columns: None detected
- Candidate label columns: None detected
- Microbial feature block: 7688 taxonomic abundance columns spanning multiple ranks.
- Quality issues: No crop or suitability target. High dimensionality relative to sample count.
- Completeness concerns: Early partial batch that covers only the first 5 SRRs.

## taxonomy_kraken2_minikraken (1).csv

- Rows: 13
- Columns: 9784
- Probable grain: One row per SRR sequencing run in the current best local Kraken2 matrix.
- Candidate ID columns: sample
- Candidate metadata columns: None detected
- Candidate label columns: None detected
- Microbial feature block: 9783 taxonomic abundance columns spanning multiple ranks.
- Quality issues: No labels, no physicochemical metadata, and extreme feature-to-sample imbalance.
- Completeness concerns: Covers only 13 of the 24 expected SRRs recovered from `Anvitha.ipynb`.

## Optimized_Taxonomy_ML.csv

- Rows: 10
- Columns: 2026
- Probable grain: One row per SRR sequencing run after an undocumented metadata merge and prevalence filter.
- Candidate ID columns: sample, BioSample
- Candidate metadata columns: geo_loc_name, lat_lon, env_medium, env_local_scale, Collection_Date
- Candidate label columns: None detected
- Microbial feature block: 2019 taxonomic abundance columns spanning multiple ranks.
- Quality issues: No crop target, no soil chemistry, and 70% missingness in `env_medium` and `env_local_scale`.
- Completeness concerns: Drops `SRR12376372`, `SRR33853917`, and `SRR33963317` from the 13-sample taxonomy table and cannot support crop prediction as-is.

## Current Scientific Readiness

- The current local snapshot is suitable for exploratory microbiome profiling and recovery auditing only.
- It is not scientifically ready for crop recommendation or crop suitability prediction.
- Incomplete SRR coverage invalidates any strong downstream claim about the intended 24-SRR project.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "dataset_audit_report.md") $datasetAudit

$assumptions = @"
# Assumptions and Risks

## Assumptions

- The current 5-file root folder is the complete snapshot available for this recovery pass.
- One row currently represents one SRR sequencing run unless later evidence proves run consolidation.
- Original root files are treated as immutable evidence.

## Scientific Uncertainties

- No crop labels are present locally.
- No soil physicochemical measurements are present locally.
- Metadata coverage is sparse and inconsistent across the 10-sample derived table.

## Leakage Risks

- Any future target engineered from accession, date, or country-level metadata would be invalid.
- The current 10-sample table should not be used for supervised learning without provenance-backed labels.

## Modeling Risks

- The current feature space is far too high-dimensional for 10 to 13 samples.
- Class balance cannot be assessed because there is no valid target column.

## Small-Sample Risks

- Even after genus aggregation, the present local sample count is too small for stable predictive claims.
- Any future baseline from this snapshot alone would be proof-of-concept at best.

## Incomplete Extraction Risks

- Only 13 of 24 expected SRRs appear in the best local taxonomy table.
- The missing 11 SRRs may materially change abundance patterns and any downstream interpretation.
- MetaPhlAn failed in the notebook before producing stable outputs, so Kraken2 is the only current local extraction evidence.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "assumptions_and_risks.md") $assumptions

$rebuildPlan = @"
# Project Rebuild Plan

## Phase 1 - Preserve and Normalize

- Keep the original 5 root files untouched.
- Maintain a copied snapshot under `raw_data/original_snapshot/`.
- Use generated subfolders for all new outputs.

## Phase 2 - Audit

- Rebuild the file inventory, SRR audit, and dataset dictionary on every future run.
- Treat `Anvitha.ipynb` as the authoritative workflow log until stronger provenance exists.

## Phase 3 - Recovery

- Use Kraken2 as the primary recovery path for missing SRRs.
- Track every SRR through `not_started`, `raw_downloaded`, `fastq_ready`, `classified`, and `merged`.
- Keep MetaPhlAn as an optional documented route only after memory constraints are addressed.

## Phase 4 - Scientific Narrowing

- Default the project to exploratory microbiome profiling plus metadata recovery.
- Upgrade to a soil-health-index prototype only if defensible metadata arrives.
- Do not attempt crop prediction until observed crop labels and adequate class support exist.

## Phase 5 - Controlled Modeling

- Build only interpretable baselines first.
- Enforce the modeling gate: no target, no training.
- Treat any later model as proof-of-concept until the full SRR set and observed labels are available.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "project_rebuild_plan.md") $rebuildPlan

$finalStatus = @"
# Final Project Status Summary

## What the project can claim now

- A partial Kraken2-based soil metagenomic feature matrix exists for 13 SRR sequencing runs.
- A smaller 10-sample derived table exists with limited contextual metadata.
- The original workflow intent can be reconstructed from `Anvitha.ipynb`.

## What the project cannot claim now

- It cannot claim full SRR completeness.
- It cannot claim crop prediction or crop recommendation readiness.
- It cannot claim a scientifically defensible soil health index from the current local snapshot alone.

## ML Feasibility

- Supervised ML is not currently feasible because no valid observed target exists.
- Even with a future target, the present sample count is too small for strong generalization claims.

## SRR Recovery Status

- Expected SRRs recovered from the notebook: 24
- Locally processed in the best Kraken table: 13
- Locally metadata-merged in the derived ML table: 10
- Missing locally processed SRRs: 11

## Best Next Step

- Recover or ingest the missing 11 SRRs and any real sample metadata before attempting any predictive modeling.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "final_project_status_summary.md") $finalStatus

$readme = @"
# Project Recovery Overview

## What was found

- The root snapshot contains 5 original files: two notebooks and three CSVs.
- `Anvitha.ipynb` documents a 24-SRR intended workflow built in Google Colab.
- The available local Kraken outputs are partial and overlap.
- The only local metadata-bearing table is `Optimized_Taxonomy_ML.csv`, which has 10 samples and no target label.

## Why it matters

- The current project is not a completed prediction pipeline.
- Missing SRRs and missing labels prevent defensible crop recommendation claims.
- The repository needed normalization, provenance tracking, and a reproducible recovery toolkit.

## What is wrong or uncertain

- Full SRR extraction was not completed locally.
- Raw FASTQ or SRA files are not present in the current folder.
- MetaPhlAn did not complete successfully in the notebook evidence.
- Crop labels and soil chemistry are absent from the local snapshot.

## What should be done next

- Use the generated recovery scripts and manifests to complete SRR extraction.
- Ingest real observed metadata before enabling supervised ML.
- Treat the present work as exploratory microbiome profiling until the dataset is completed.

## What files and code were created

- Recovery scripts in scripts/
- Cleaned and processed derivatives in cleaned_data/ and processed_data/
- Audit reports in the project root
- Supporting outputs in outputs/, logs/, and notebooks/

## What limitations remain

- Python is not installed on PATH on this machine, so the new Python scripts were created but not executed here.
- The generated command manifests for SRR recovery still require remote access and bioinformatics tooling to run.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "README_project_recovery.md") $readme

$metadataGap = @"
# Metadata Gap Report

- Samples with observed metadata rows: 10
- Expected SRRs in the notebook list: 24
- Samples without locally merged metadata: 14
- `env_medium` missing fraction among observed metadata rows: 70.0%
- `env_local_scale` missing fraction among observed metadata rows: 70.0%

No crop labels, soil chemistry, or suitability targets were recovered from the local snapshot.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "outputs\metadata_gap_report.md") $metadataGap

$modelNoGo = @"
# Baseline Modeling Status

Baseline modeling was not executed in this recovery pass.

- No valid observed crop or suitability target exists in the local snapshot.
- The current sample count is too small for a defensible predictive claim.
- SRR completeness is not sufficient to claim representative biological coverage.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "outputs\model_no_go_report.md") $modelNoGo

$evalSummary = @"
# Evaluation Summary

No model evaluation was generated in this recovery pass because the modeling gate did not pass.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "outputs\evaluation_summary.md") $evalSummary

$trace = @"
# Recovery Trace

- Created normalized project folders and preserved the original root snapshot under `raw_data/original_snapshot/`.
- Generated Python recovery scripts for auditing, cleaning, metadata reconstruction, extraction planning, preprocessing, training gates, and evaluation.
- Generated current-snapshot audit outputs with PowerShell because no Python interpreter was available on PATH.
- Did not run any modeling because no valid target column exists locally.
"@
Set-Content -Encoding utf8 (Join-Path $ProjectRoot "logs\recovery_trace.md") $trace

Write-NotebookWrapper -Path (Join-Path $ProjectRoot "notebooks\01_project_audit.ipynb") `
    -Title "Project Audit" `
    -Body "This notebook is a thin wrapper around the scripted project audit." `
    -Command "!python scripts/audit_files.py`n!python scripts/inspect_datasets.py"
Write-NotebookWrapper -Path (Join-Path $ProjectRoot "notebooks\02_srr_recovery.ipynb") `
    -Title "SRR Recovery" `
    -Body "This notebook wraps the SRR audit and extraction reconstruction scripts." `
    -Command "!python scripts/audit_srrs.py`n!python scripts/reconstruct_extraction.py"
Write-NotebookWrapper -Path (Join-Path $ProjectRoot "notebooks\03_data_cleaning.ipynb") `
    -Title "Data Cleaning" `
    -Body "This notebook wraps the cleaning and metadata reconstruction scripts." `
    -Command "!python scripts/clean_data.py`n!python scripts/build_metadata.py"
Write-NotebookWrapper -Path (Join-Path $ProjectRoot "notebooks\04_baseline_model.ipynb") `
    -Title "Baseline Model Gate" `
    -Body "This notebook documents the preprocessing and modeling gate." `
    -Command "!python scripts/preprocess.py`n!python scripts/train_baseline.py`n!python scripts/evaluate.py"

$inventory = foreach ($file in Get-ChildItem -Recurse -File | Sort-Object FullName) {
    $relative = $file.FullName.Substring($ProjectRoot.Length + 1).Replace('\', '/')
    $role = "other_file"
    $importance = "low"
    $status = "generated"
    $notes = ""
    switch -Wildcard ($relative) {
        "Anvitha.ipynb" {
            $role = "workflow_notebook"; $importance = "critical"; $status = "original_evidence"; $notes = "Primary workflow notebook."
        }
        "Untitled17 (1).ipynb" {
            $role = "merge_notebook"; $importance = "high"; $status = "original_evidence"; $notes = "Notebook that merges metadata and filters features."
        }
        "taxonomy_kraken2_minikraken.csv" {
            $role = "taxonomy_matrix_partial"; $importance = "high"; $status = "original_evidence"; $notes = "Early 5-sample Kraken2 matrix."
        }
        "taxonomy_kraken2_minikraken (1).csv" {
            $role = "taxonomy_matrix_superset"; $importance = "critical"; $status = "original_evidence"; $notes = "Current best 13-sample Kraken2 matrix."
        }
        "Optimized_Taxonomy_ML.csv" {
            $role = "derived_ml_table"; $importance = "critical"; $status = "original_evidence"; $notes = "Derived 10-sample table with sparse metadata."
        }
        "scripts/*" {
            $role = "recovery_script"; $importance = "high"; $status = "generated"; $notes = "Recovery automation script."
        }
        "cleaned_data/*" {
            $role = "cleaned_dataset"; $importance = "high"; $status = "generated"; $notes = "Cleaned derivative dataset."
        }
        "processed_data/*" {
            $role = "processed_dataset"; $importance = "high"; $status = "generated"; $notes = "Processed manifest or matrix."
        }
        "outputs/*" {
            $role = "report_output"; $importance = "medium"; $status = "generated"; $notes = "Generated summary or manifest."
        }
        "logs/*" {
            $role = "log_or_trace"; $importance = "medium"; $status = "generated"; $notes = "Execution trace or log."
        }
        "notebooks/*" {
            $role = "reporting_notebook"; $importance = "medium"; $status = "generated"; $notes = "Notebook wrapper around scripts."
        }
        "*.md" {
            $role = "markdown_document"; $importance = "medium"; $status = "generated"; $notes = "Generated recovery report."
        }
        "*.csv" {
            $role = "tabular_data"; $importance = "medium"; $status = "generated"; $notes = "Tabular artifact."
        }
    }
    [pscustomobject]@{
        relative_path = $relative
        file_name = $file.Name
        extension = if ($file.Extension) { $file.Extension.ToLowerInvariant() } else { "[no_extension]" }
        size_bytes = $file.Length
        guessed_role = $role
        importance = $importance
        status = $status
        notes = $notes
    }
}
$inventory | Export-Csv (Join-Path $ProjectRoot "file_inventory.csv") -NoTypeInformation -Encoding utf8
