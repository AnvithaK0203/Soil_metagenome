"""Rebuild the best available sample-level merged dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, ensure_parent, infer_column_category, make_log_path


def resolve_series(frame: pd.DataFrame, local_col: str, remote_col: str) -> pd.Series:
    local = frame[local_col] if local_col in frame.columns else pd.Series([""] * len(frame))
    remote = frame[remote_col] if remote_col in frame.columns else pd.Series([""] * len(frame))
    local = local.fillna("").astype(str)
    remote = remote.fillna("").astype(str)
    return local.where(local.str.strip() != "", remote)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "rebuild_final_dataset.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "rebuild_final_dataset.log")

    taxonomy_path = project_root / "processed_data" / "current_best_taxonomy_matrix.csv"
    manifest_path = project_root / "processed_data" / "sample_manifest.csv"
    preview_path = output_dir / "processed_data" / "final_merged_dataset_preview.csv"
    resolved_meta_path = output_dir / "cleaned_data" / "final_resolved_metadata.csv"
    notes_path = output_dir / "docs" / "final_dataset_reconstruction_notes.md"
    ensure_parent(preview_path)
    ensure_parent(resolved_meta_path)
    ensure_parent(notes_path)

    taxonomy_df = pd.read_csv(taxonomy_path)
    manifest_df = pd.read_csv(manifest_path)
    manifest_df = manifest_df.rename(columns={"sample": "sample"})

    processed_manifest = manifest_df[manifest_df["local_processed_presence"] == "present"].copy()
    missing_count = int((manifest_df["local_processed_presence"] != "present").sum())
    merged = processed_manifest.merge(taxonomy_df, on="sample", how="inner", suffixes=("", "_tax"))

    resolved = pd.DataFrame(
        {
            "sample": merged["sample"],
            "row_unit": "SRR sequencing run",
            "local_biosample": merged.get("biosample_local", ""),
            "remote_sample_accession": merged.get("sample_accession", ""),
            "remote_secondary_sample_accession": merged.get("secondary_sample_accession", ""),
            "remote_study_accession": merged.get("study_accession", ""),
            "remote_experiment_accession": merged.get("experiment_accession", ""),
            "library_layout": merged.get("library_layout", ""),
            "library_source": merged.get("library_source", ""),
            "scientific_name": merged.get("scientific_name_remote", ""),
            "sample_title": resolve_series(merged, "sample_title_local", "sample_title_remote"),
            "geo_loc_name_resolved": resolve_series(merged, "geo_loc_name_local", "geo_loc_name_remote"),
            "lat_lon_resolved": resolve_series(merged, "lat_lon_local", "lat_lon_remote"),
            "env_medium_resolved": resolve_series(merged, "env_medium_local", "env_medium_remote"),
            "env_local_scale_resolved": resolve_series(merged, "env_local_scale_local", "env_local_scale_remote"),
            "collection_date_resolved": resolve_series(merged, "collection_date_local", "collection_date_remote"),
            "env_broad_scale_remote": merged.get("env_broad_scale_remote", ""),
            "depth_remote": merged.get("depth_remote", ""),
            "soil_type_remote": merged.get("soil_type_remote", ""),
            "host_remote": merged.get("host_remote", ""),
            "isolation_source_remote": merged.get("isolation_source_remote", ""),
            "has_local_metadata": merged.get("has_local_metadata", False),
            "has_remote_metadata": merged.get("has_remote_metadata", False),
            "has_local_taxonomy": merged.get("has_local_taxonomy", False),
            "local_processed_presence": merged.get("local_processed_presence", ""),
            "recovery_attempt_status": merged.get("recovery_attempt_status", ""),
            "candidate_label_present": False,
            "candidate_label_notes": "No directly observed crop or suitability label is present in the reconstructed local dataset.",
            "taxonomy_source_file": "processed_data/current_best_taxonomy_matrix.csv",
            "manifest_source_file": "processed_data/sample_manifest.csv",
        }
    )
    resolved.to_csv(resolved_meta_path, index=False)

    provenance_cols = list(resolved.columns)
    taxonomy_cols = [col for col in taxonomy_df.columns if infer_column_category(col) == "microbial_feature"]
    final_df = pd.concat([resolved, taxonomy_df.set_index("sample").loc[resolved["sample"], taxonomy_cols].reset_index(drop=True)], axis=1)
    final_df.to_csv(preview_path, index=False)

    remains_blocked_lines = []
    if missing_count == 0:
        remains_blocked_lines.extend(
            [
                "- The merged dataset now spans all expected locally processed SRRs recovered in this project snapshot.",
                "- No directly observed crop label was reconstructed, so the dataset is still exploratory rather than predictive.",
            ]
        )
        next_step_lines = [
            "- Use the complete locally processed SRR set for exploratory microbiome analysis and feature aggregation.",
            "- Keep supervised modeling blocked until a directly observed target is added from primary project records.",
        ]
    else:
        remains_blocked_lines.extend(
            [
                f"- The merged dataset currently spans {len(final_df)} locally processed SRRs, with {missing_count} expected SRRs still missing processed outputs.",
                "- No directly observed crop label was reconstructed.",
                f"- The {missing_count} missing SRRs still need raw recovery and Kraken2 classification for full dataset completeness.",
            ]
        )
        next_step_lines = [
            "- Use the enriched manifests to decide whether to complete missing-SRR classification or freeze the project scope at exploratory analysis.",
        ]

    notes_lines = [
        "# Final Dataset Reconstruction Notes",
        "",
        "## What was found",
        "",
        f"- Best local taxonomy table rows: {len(taxonomy_df)}",
        f"- Processed manifest rows with local taxonomy: {len(processed_manifest)}",
        f"- Final merged preview rows: {len(final_df)}",
        f"- Taxonomic feature columns retained in the preview: {len(taxonomy_cols)}",
        "",
        "## What was executed",
        "",
        "- Joined the best local taxonomy matrix to the enriched sample manifest on the SRR sample key.",
        "- Resolved metadata by preferring local observed fields and falling back to remote ENA metadata when local fields were empty.",
        "- Preserved provenance columns so metadata origin remains transparent.",
        "",
        "## What changed",
        "",
        "- Created `cleaned_data/final_resolved_metadata.csv`.",
        "- Created `processed_data/final_merged_dataset_preview.csv`.",
        "",
        "## What remains blocked or uncertain",
        "",
        *remains_blocked_lines,
        "",
        "## What the next immediate step is",
        "",
        *next_step_lines,
    ]
    notes_path.write_text("\n".join(notes_lines) + "\n", encoding="utf-8")

    append_log(log_path, f"Wrote resolved metadata to {resolved_meta_path}")
    append_log(log_path, f"Wrote merged dataset preview to {preview_path}")


if __name__ == "__main__":
    main()
