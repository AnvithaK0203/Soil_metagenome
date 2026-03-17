"""Reconstruct observed local metadata without inventing new labels."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path, normalize_sample_id


EXPECTED_COLUMNS = [
    "sample",
    "BioSample",
    "geo_loc_name",
    "lat_lon",
    "env_medium",
    "env_local_scale",
    "Collection_Date",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "build_metadata.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "build_metadata.log")

    optimized_path = project_root / "Optimized_Taxonomy_ML.csv"
    srr_audit_path = project_root / "srr_audit_report.csv"
    manifest_path = output_dir / "processed_data" / "sample_manifest.csv"
    metadata_path = output_dir / "cleaned_data" / "sample_metadata_observed.csv"
    gap_report_path = output_dir / "outputs" / "metadata_gap_report.md"
    ensure_parent(manifest_path)
    ensure_parent(metadata_path)
    ensure_parent(gap_report_path)

    metadata_df = pd.read_csv(optimized_path, usecols=EXPECTED_COLUMNS)
    metadata_df["sample"] = metadata_df["sample"].map(normalize_sample_id)
    metadata_df = metadata_df.drop_duplicates(subset=["sample"]).sort_values("sample")
    metadata_df.to_csv(metadata_path, index=False)

    audit_df = pd.read_csv(srr_audit_path)
    audit_df["srr_id"] = audit_df["srr_id"].map(normalize_sample_id)
    manifest = audit_df.rename(columns={"srr_id": "sample"}).merge(metadata_df, on="sample", how="left")
    observed_fields = [col for col in EXPECTED_COLUMNS if col != "sample"]
    manifest["metadata_completeness_fraction"] = manifest[observed_fields].notna().mean(axis=1).round(3)
    manifest.to_csv(manifest_path, index=False)

    gap_report_lines = [
        "# Metadata Gap Report",
        "",
        "This report describes the locally observed metadata and its gaps.",
        "",
        f"- Samples with observed metadata rows: {len(metadata_df)}",
        f"- Expected SRRs from the audit: {len(audit_df)}",
        f"- Samples lacking any locally merged metadata: {int((manifest['BioSample'].isna()).sum())}",
        f"- `env_medium` missing fraction among local metadata rows: {metadata_df['env_medium'].isna().mean():.1%}",
        f"- `env_local_scale` missing fraction among local metadata rows: {metadata_df['env_local_scale'].isna().mean():.1%}",
        "",
        "No crop labels, soil chemistry variables, or suitability targets were reconstructed because they do not exist in the local snapshot.",
    ]
    gap_report_path.write_text("\n".join(gap_report_lines), encoding="utf-8")

    append_log(log_path, f"Wrote observed metadata to {metadata_path}")
    append_log(log_path, f"Wrote sample manifest to {manifest_path}")


if __name__ == "__main__":
    main()
