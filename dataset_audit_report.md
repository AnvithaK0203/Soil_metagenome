# Dataset Audit Report

This report summarizes the current local datasets available in the recovery snapshot.

## taxonomy_kraken2_minikraken.csv

- Rows: 5
- Columns: 7689
- Probable grain: One row per SRR sequencing run or sample-level feature vector.
- Candidate ID columns: sample
- Candidate metadata columns: None detected
- Candidate label columns: None detected
- Microbial feature block: 7688 microbial feature columns (C=81, C1=13, C2=7, C3=1, C4=1, D=4, D1=14, D2=10, D3=3, D4=1)
- Quality issues: No explicit crop/target label column detected.
- Completeness concerns: Only 5 samples are represented; this is an early partial batch.

## taxonomy_kraken2_minikraken (1).csv

- Rows: 13
- Columns: 9784
- Probable grain: One row per SRR sequencing run or sample-level feature vector.
- Candidate ID columns: sample
- Candidate metadata columns: None detected
- Candidate label columns: None detected
- Microbial feature block: 9783 microbial feature columns (C=81, C1=13, C2=7, C3=1, C4=1, D=4, D1=19, D2=15, D3=5, D4=1)
- Quality issues: No explicit crop/target label column detected.
- Completeness concerns: Only 13 of 24 expected SRRs are represented locally.

## Optimized_Taxonomy_ML.csv

- Rows: 10
- Columns: 2026
- Probable grain: One row per SRR sequencing run or sample-level feature vector.
- Candidate ID columns: sample, BioSample
- Candidate metadata columns: geo_loc_name, lat_lon, env_medium, env_local_scale, Collection_Date
- Candidate label columns: None detected
- Microbial feature block: 2019 microbial feature columns (C=69, C1=11, C2=5, C3=1, C4=1, D=3, D1=6, D2=4, D3=2, D4=1)
- Quality issues: No explicit crop/target label column detected.; Metadata missingness present (env_medium=70.0%, env_local_scale=70.0%).
- Completeness concerns: Only 10 samples remain after an undocumented metadata merge.; No crop label or soil physicochemical variables are present.

## cleaned_data/sample_metadata_observed.csv

- Rows: 10
- Columns: 7
- Probable grain: One row per SRR sequencing run or sample-level feature vector.
- Candidate ID columns: sample, BioSample
- Candidate metadata columns: geo_loc_name, lat_lon, env_medium, env_local_scale, Collection_Date
- Candidate label columns: None detected
- Microbial feature block: No explicit microbial feature block detected.
- Quality issues: No explicit crop/target label column detected.; Metadata missingness present (env_medium=70.0%, env_local_scale=70.0%).
- Completeness concerns: None detected

## cleaned_data/remote_sample_metadata.csv

- Rows: 24
- Columns: 36
- Probable grain: Unknown; manual review required.
- Candidate ID columns: srr_id, source_material_id
- Candidate metadata columns: collection_date, depth, elev, env_broad_scale, env_local_scale, env_medium, geo_loc_name, host, host_disease, isolation_source, lat_lon, soil_type
- Candidate label columns: None detected
- Microbial feature block: No explicit microbial feature block detected.
- Quality issues: No explicit crop/target label column detected.; Metadata missingness present (depth=45.8%, elev=45.8%, env_broad_scale=45.8%, env_local_scale=45.8%, env_medium=45.8%, host=95.8%, host_disease=100.0%, isolation_source=50.0%, soil_type=100.0%).
- Completeness concerns: Remote metadata is recovered from ENA and should be treated as secondary provenance.

## processed_data/current_best_taxonomy_matrix.csv

- Rows: 24
- Columns: 11087
- Probable grain: One row per SRR sequencing run or sample-level feature vector.
- Candidate ID columns: sample
- Candidate metadata columns: None detected
- Candidate label columns: None detected
- Microbial feature block: 11086 microbial feature columns (C=81, C1=13, C2=7, C3=1, C4=1, D=4, D1=19, D2=15, D3=6, D4=1)
- Quality issues: No explicit crop/target label column detected.
- Completeness concerns: This matrix is the best available combined taxonomy table after merging the teammate CSV with validated recovered Kraken reports.

## processed_data/recovered_kraken_taxonomy_rows.csv

- Rows: 24
- Columns: 11087
- Probable grain: One row per SRR sequencing run or sample-level feature vector.
- Candidate ID columns: sample
- Candidate metadata columns: None detected
- Candidate label columns: None detected
- Microbial feature block: 11086 microbial feature columns (C=81, C1=13, C2=7, C3=1, C4=1, D=4, D1=19, D2=15, D3=6, D4=1)
- Quality issues: No explicit crop/target label column detected.
- Completeness concerns: These rows are derived directly from validated Kraken2 report files generated during recovery.

## processed_data/sample_manifest.csv

- Rows: 24
- Columns: 84
- Probable grain: One row per SRR sequencing run or sample-level feature vector.
- Candidate ID columns: sample, source_material_id
- Candidate metadata columns: collection_date_remote, depth_remote, elev_remote, env_broad_scale_remote, env_local_scale_remote, env_medium_remote, geo_loc_name_remote, host_remote, host_disease_remote, isolation_source_remote, lat_lon_remote, soil_type_remote, geo_loc_name_local, lat_lon_local, env_medium_local, env_local_scale_local, collection_date_local, resolved_geo_loc_name, resolved_lat_lon, resolved_env_medium, resolved_env_local_scale, resolved_collection_date
- Candidate label columns: None detected
- Microbial feature block: No explicit microbial feature block detected.
- Quality issues: No explicit crop/target label column detected.; Metadata missingness present (depth_remote=45.8%, elev_remote=45.8%, env_broad_scale_remote=45.8%, env_local_scale_remote=45.8%, env_medium_remote=45.8%, host_remote=95.8%, host_disease_remote=100.0%, isolation_source_remote=50.0%, soil_type_remote=100.0%, geo_loc_name_local=58.3%, lat_lon_local=58.3%, env_medium_local=87.5%, env_local_scale_local=87.5%, collection_date_local=58.3%, resolved_env_medium=45.8%, resolved_env_local_scale=45.8%).
- Completeness concerns: Manifest tracks all 24 expected SRRs and every row now has validated local processed outputs.

## processed_data/final_merged_dataset_preview.csv

- Rows: 24
- Columns: 11116
- Probable grain: One row per SRR sequencing run or sample-level feature vector.
- Candidate ID columns: sample
- Candidate metadata columns: geo_loc_name_resolved, lat_lon_resolved, env_medium_resolved, env_local_scale_resolved, collection_date_resolved, env_broad_scale_remote, depth_remote, soil_type_remote, host_remote, isolation_source_remote
- Candidate label columns: None detected
- Microbial feature block: 11086 microbial feature columns (C=81, C1=13, C2=7, C3=1, C4=1, D=4, D1=19, D2=15, D3=6, D4=1)
- Quality issues: No explicit crop/target label column detected.; Metadata missingness present (env_medium_resolved=45.8%, env_local_scale_resolved=45.8%, env_broad_scale_remote=45.8%, depth_remote=45.8%, soil_type_remote=100.0%, host_remote=95.8%, isolation_source_remote=50.0%).
- Completeness concerns: This merged preview only includes locally processed taxonomy rows.; All expected SRRs are now represented in the merged preview, but the dataset still lacks a directly observed predictive target.
