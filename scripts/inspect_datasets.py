"""Inspect local tabular datasets and build a data dictionary."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import (
    add_standard_args,
    append_log,
    default_project_root,
    ensure_parent,
    infer_column_category,
    infer_column_description,
    make_log_path,
    normalize_sample_id,
    rank_prefix,
)


BASE_CANDIDATES = [
    "taxonomy_kraken2_minikraken.csv",
    "taxonomy_kraken2_minikraken (1).csv",
    "Optimized_Taxonomy_ML.csv",
    "cleaned_data/sample_metadata_observed.csv",
    "cleaned_data/remote_sample_metadata.csv",
    "processed_data/current_best_taxonomy_matrix.csv",
    "processed_data/recovered_kraken_taxonomy_rows.csv",
    "processed_data/sample_manifest.csv",
    "processed_data/final_merged_dataset_preview.csv",
]


def likely_grain(df: pd.DataFrame) -> str:
    lowered = {col.lower(): col for col in df.columns}
    if "sample" in lowered:
        sample_col = lowered["sample"]
        unique_samples = df[sample_col].astype(str).str.strip().nunique(dropna=True)
        if unique_samples == len(df):
            return "One row per SRR sequencing run or sample-level feature vector."
    if all("|" in col for col in df.columns[1:]):
        return "Sample-by-feature microbial abundance matrix."
    return "Unknown; manual review required."


def id_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if infer_column_category(col) == "id"]


def metadata_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if infer_column_category(col) == "metadata"]


def label_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if infer_column_category(col) == "label_candidate"]


def microbial_summary(df: pd.DataFrame) -> str:
    microbial_cols = [col for col in df.columns if infer_column_category(col) == "microbial_feature"]
    if not microbial_cols:
        return "No explicit microbial feature block detected."
    ranks: dict[str, int] = {}
    for column in microbial_cols:
        prefix = rank_prefix(column) or "unknown"
        ranks[prefix] = ranks.get(prefix, 0) + 1
    pieces = [f"{rank}={count}" for rank, count in sorted(ranks.items())]
    return f"{len(microbial_cols)} microbial feature columns ({', '.join(pieces[:10])})"


def quality_issues(df: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    if "sample" in df.columns:
        normalized = df["sample"].map(normalize_sample_id)
        duplicate_count = normalized.duplicated().sum()
        if duplicate_count:
            issues.append(f"{duplicate_count} duplicate sample IDs.")
    if not label_columns(df):
        issues.append("No explicit crop/target label column detected.")
    metadata_cols = metadata_columns(df)
    if metadata_cols:
        missing = {
            col: float(df[col].isna().mean())
            for col in metadata_cols
            if float(df[col].isna().mean()) > 0
        }
        if missing:
            formatted = ", ".join(f"{col}={frac:.1%}" for col, frac in missing.items())
            issues.append(f"Metadata missingness present ({formatted}).")
    return issues


def completeness_concerns(path: Path, df: pd.DataFrame) -> list[str]:
    concerns: list[str] = []
    if path.name == "taxonomy_kraken2_minikraken.csv":
        concerns.append("Only 5 samples are represented; this is an early partial batch.")
    if path.name == "taxonomy_kraken2_minikraken (1).csv":
        concerns.append("Only 13 of 24 expected SRRs are represented locally.")
    if path.name == "Optimized_Taxonomy_ML.csv":
        concerns.append("Only 10 samples remain after an undocumented metadata merge.")
        concerns.append("No crop label or soil physicochemical variables are present.")
    if path.name == "sample_manifest.csv":
        if "local_processed_presence" in df.columns and df["local_processed_presence"].eq("present").all():
            concerns.append("Manifest tracks all 24 expected SRRs and every row now has validated local processed outputs.")
        else:
            concerns.append("Manifest is intended to track all 24 expected SRRs, including unrecovered runs.")
    if path.name == "current_best_taxonomy_matrix.csv":
        concerns.append("This matrix is the best available combined taxonomy table after merging the teammate CSV with validated recovered Kraken reports.")
    if path.name == "recovered_kraken_taxonomy_rows.csv":
        concerns.append("These rows are derived directly from validated Kraken2 report files generated during recovery.")
    if path.name == "remote_sample_metadata.csv":
        concerns.append("Remote metadata is recovered from ENA and should be treated as secondary provenance.")
    if path.name == "final_merged_dataset_preview.csv":
        concerns.append("This merged preview only includes locally processed taxonomy rows.")
        if len(df) >= 24:
            concerns.append("All expected SRRs are now represented in the merged preview, but the dataset still lacks a directly observed predictive target.")
        else:
            concerns.append("Missing SRRs still prevent full biological dataset completeness.")
    return concerns


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "inspect_datasets.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "inspect_datasets.log")
    report_path = output_dir / "dataset_audit_report.md"
    dictionary_path = output_dir / "master_data_dictionary.csv"
    ensure_parent(report_path)
    ensure_parent(dictionary_path)

    report_lines = [
        "# Dataset Audit Report",
        "",
        "This report summarizes the current local datasets available in the recovery snapshot.",
        "",
    ]
    dictionary_frames: list[pd.DataFrame] = []

    candidates = [name for name in BASE_CANDIDATES if (project_root / name).exists()]
    for name in candidates:
        path = project_root / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        ids = id_columns(df)
        metadata = metadata_columns(df)
        labels = label_columns(df)
        issues = quality_issues(df)
        concerns = completeness_concerns(path, df)

        report_lines.extend(
            [
                f"## {name}",
                "",
                f"- Rows: {len(df)}",
                f"- Columns: {len(df.columns)}",
                f"- Probable grain: {likely_grain(df)}",
                f"- Candidate ID columns: {', '.join(ids) if ids else 'None detected'}",
                f"- Candidate metadata columns: {', '.join(metadata) if metadata else 'None detected'}",
                f"- Candidate label columns: {', '.join(labels) if labels else 'None detected'}",
                f"- Microbial feature block: {microbial_summary(df)}",
                f"- Quality issues: {('; '.join(issues)) if issues else 'None detected'}",
                f"- Completeness concerns: {('; '.join(concerns)) if concerns else 'None detected'}",
                "",
            ]
        )

        rows = []
        for column in df.columns:
            series = df[column]
            missing_count = int(series.isna().sum())
            rows.append(
                {
                    "source_file": name,
                    "column_name": column,
                    "inferred_description": infer_column_description(column),
                    "data_type": str(series.dtype),
                    "category": infer_column_category(column),
                    "missing_count": missing_count,
                    "missing_fraction": round(float(series.isna().mean()), 6),
                    "notes": "Taxonomic feature column." if infer_column_category(column) == "microbial_feature" else "",
                }
            )
        dictionary_frames.append(pd.DataFrame(rows))

    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    if dictionary_frames:
        pd.concat(dictionary_frames, ignore_index=True).to_csv(dictionary_path, index=False)

    append_log(log_path, f"Wrote dataset audit to {report_path}")
    append_log(log_path, f"Wrote master data dictionary to {dictionary_path}")


if __name__ == "__main__":
    main()
