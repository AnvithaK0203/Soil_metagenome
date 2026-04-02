"""Apply prevalence-based filtering to microbiome analysis matrices."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path
from microbiome_utils import filter_by_prevalence, rank_level_counts


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = ["| " + " | ".join(str(frame.iloc[idx][column]) for column in columns) + " |" for idx in range(len(frame))]
    return "\n".join([header, divider, *rows])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "feature_filtering.log")
    parser.add_argument(
        "--mean-abundance-threshold",
        type=float,
        default=0.0,
        help="Optional post-prevalence mean abundance threshold on the raw matrix scale. Default: 0.0 (disabled).",
    )
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "feature_filtering.log")
    report_path = output_dir / "outputs" / "feature_filtering_report.md"
    ensure_parent(report_path)

    matrix_paths = {
        "full": project_root / "processed_data" / "taxonomy_full_matrix.csv",
        "analysis": project_root / "processed_data" / "taxonomy_analysis_matrix.csv",
        "phylum": project_root / "processed_data" / "taxonomy_phylum_matrix.csv",
        "genus": project_root / "processed_data" / "taxonomy_genus_matrix.csv",
        "species": project_root / "processed_data" / "taxonomy_species_matrix.csv",
    }

    summary_rows: list[dict[str, object]] = []
    output_lines = [
        "# Feature Filtering Report",
        "",
        "## What was found",
        "",
        "- Filtering was applied to the frozen analysis matrices generated from the validated 24-sample dataset.",
        "- Prevalence is defined as abundance > 0 in a sample.",
        "",
        "## What was executed",
        "",
        "- Removed all-zero features.",
        "- Computed prevalence >= 2 and prevalence >= 3 feature sets for each matrix.",
        "- Left the mean abundance threshold disabled by default to avoid over-pruning an already small 24-sample dataset.",
        "",
    ]

    for matrix_name, matrix_path in matrix_paths.items():
        matrix = pd.read_csv(matrix_path)
        prev2, prev2_summary = filter_by_prevalence(
            matrix,
            min_prevalence=2,
            mean_abundance_threshold=args.mean_abundance_threshold,
        )
        prev3, prev3_summary = filter_by_prevalence(
            matrix,
            min_prevalence=3,
            mean_abundance_threshold=args.mean_abundance_threshold,
        )

        prev2_path = output_dir / "processed_data" / f"{matrix_path.stem}_prev2.csv"
        prev3_path = output_dir / "processed_data" / f"{matrix_path.stem}_prev3.csv"
        ensure_parent(prev2_path)
        ensure_parent(prev3_path)
        prev2.to_csv(prev2_path, index=False)
        prev3.to_csv(prev3_path, index=False)

        summary_rows.append(
            {
                "matrix_name": matrix_name,
                "original_features": prev2_summary.original_feature_count,
                "nonzero_features": prev2_summary.nonzero_feature_count,
                "prevalence_ge_2": prev2_summary.prevalence_ge_2_count,
                "prevalence_ge_3": prev2_summary.prevalence_ge_3_count,
                "retained_prev2_output": prev2.shape[1] - 1,
                "retained_prev3_output": prev3.shape[1] - 1,
            }
        )

        append_log(log_path, f"Wrote filtered matrices for {matrix_name} to {prev2_path} and {prev3_path}")

    summary_df = pd.DataFrame(summary_rows)

    full_matrix = pd.read_csv(matrix_paths["full"])
    rank_counts = rank_level_counts([column for column in full_matrix.columns if column != "sample"])

    output_lines.extend(
        [
            "## What outputs were created",
            "",
            "- Prevalence-filtered matrices for the full, analysis, phylum, genus, and species tables were saved under `processed_data/` with `_prev2.csv` and `_prev3.csv` suffixes.",
            "",
            "## Filtering summary",
            "",
            markdown_table(summary_df),
            "",
            "## Counts per taxonomic level in the full matrix",
            "",
            markdown_table(rank_counts),
            "",
            "## What assumptions were made",
            "",
            f"- Mean abundance threshold applied: `{args.mean_abundance_threshold}` on the raw matrix scale.",
            "- Default outputs keep the abundance threshold at 0.0 because prevalence filtering already removes unsupported rare features without forcing an arbitrary extra cutoff.",
            "",
            "## What limitations remain",
            "",
            "- The full and analysis matrices remain hierarchically nested, so filtered versions are retained mainly for traceability.",
            "- Rank-specific filtered matrices are the correct inputs for compositional transformation and exploratory multivariate analysis.",
        ]
    )
    report_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    append_log(log_path, f"Wrote feature filtering report to {report_path}")


if __name__ == "__main__":
    main()
