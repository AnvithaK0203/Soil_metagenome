"""Create transformed microbiome matrices for exploratory analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path
from microbiome_utils import clr_transform, close_composition, feature_frame, hellinger_transform, with_sample


def save_transformed_set(project_root: Path, output_dir: Path, matrix_name: str, pseudocount: float) -> tuple[Path, Path, Path, int]:
    matrix_path = project_root / "processed_data" / f"{matrix_name}.csv"
    matrix = pd.read_csv(matrix_path)
    sample = matrix["sample"].copy()
    data = feature_frame(matrix)
    relative = close_composition(data)
    hellinger = hellinger_transform(relative)
    clr = clr_transform(relative, pseudocount=pseudocount)

    relative_path = output_dir / "processed_data" / f"{matrix_name}_relative_abundance.csv"
    hellinger_path = output_dir / "processed_data" / f"{matrix_name}_hellinger.csv"
    clr_path = output_dir / "processed_data" / f"{matrix_name}_clr.csv"
    for path in (relative_path, hellinger_path, clr_path):
        ensure_parent(path)

    with_sample(sample, relative).to_csv(relative_path, index=False)
    with_sample(sample, hellinger).to_csv(hellinger_path, index=False)
    with_sample(sample, clr).to_csv(clr_path, index=False)
    return relative_path, hellinger_path, clr_path, data.shape[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "prepare_microbiome_matrix.log")
    parser.add_argument(
        "--clr-pseudocount",
        type=float,
        default=1e-6,
        help="Pseudocount added after row closure for CLR transformation. Default: 1e-6.",
    )
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "prepare_microbiome_matrix.log")
    report_path = output_dir / "outputs" / "transformation_report.md"
    ensure_parent(report_path)

    matrix_names = [
        "taxonomy_phylum_matrix_prev2",
        "taxonomy_genus_matrix_prev3",
        "taxonomy_species_matrix_prev3",
    ]

    report_lines = [
        "# Transformation Report",
        "",
        "## What was found",
        "",
        "- The full taxonomy matrix is hierarchical and does not form a closed composition because nested ranks are recorded simultaneously.",
        "- Single-rank phylum, genus, and species matrices are the appropriate inputs for row closure and compositional transformations.",
        "",
        "## What was executed",
        "",
        "- Converted selected rank-specific filtered matrices to row-closed relative abundance tables.",
        "- Generated Hellinger-transformed versions for Euclidean ordination and clustering.",
        "- Generated CLR-transformed versions using a documented pseudocount after row closure.",
        "",
    ]

    for matrix_name in matrix_names:
        relative_path, hellinger_path, clr_path, feature_count = save_transformed_set(
            project_root,
            output_dir,
            matrix_name,
            pseudocount=args.clr_pseudocount,
        )
        report_lines.extend(
            [
                f"### {matrix_name}",
                "",
                f"- Input features: {feature_count}",
                f"- Relative abundance output: `{relative_path.relative_to(output_dir).as_posix()}`",
                f"- Hellinger output: `{hellinger_path.relative_to(output_dir).as_posix()}`",
                f"- CLR output: `{clr_path.relative_to(output_dir).as_posix()}`",
                "",
            ]
        )
        append_log(log_path, f"Wrote transformed matrices for {matrix_name}")

    report_lines.extend(
        [
            "## What each transformation does",
            "",
            "- Relative abundance closes each rank-specific row to sum to 1.0, making samples comparable within that taxonomic level.",
            "- Hellinger transformation takes the square root of relative abundance and is preferred for PCA and hierarchical clustering because it stabilizes dominant taxa while remaining Euclidean-friendly.",
            f"- CLR transformation applies log-ratio scaling after adding a pseudocount of `{args.clr_pseudocount}` to handle zeros. It is useful for sensitivity analysis of compositional structure, but it is less directly interpretable than Hellinger for presentation.",
            "",
            "## Preferred downstream use",
            "",
            "- Phylum relative abundance: descriptive summaries and interpretable stacked composition comparisons.",
            "- Genus Hellinger: primary matrix for PCA and clustering.",
            "- Genus CLR: sensitivity analysis if log-ratio geometry needs to be inspected.",
            "- Species transforms: exploratory only, because the species matrix remains high-dimensional relative to n = 24.",
            "",
            "## What assumptions were made",
            "",
            "- Only rank-specific matrices were transformed compositionally.",
            "- Prevalence-filtered matrices were used to reduce zero inflation before transformation.",
            "",
            "## What limitations remain",
            "",
            "- CLR results depend on the chosen pseudocount and should be interpreted cautiously.",
            "- The full hierarchical matrix is retained for traceability, not for direct compositional analysis.",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    append_log(log_path, f"Wrote transformation report to {report_path}")


if __name__ == "__main__":
    main()
