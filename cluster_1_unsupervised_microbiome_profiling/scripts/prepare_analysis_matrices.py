"""Freeze the validated merged dataset into metadata and taxonomy analysis tables."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path
from microbiome_utils import STRUCTURAL_FEATURES, exact_rank_columns, feature_columns, load_final_merged_dataset, split_metadata_and_taxonomy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "prepare_analysis_matrices.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "prepare_analysis_matrices.log")

    merged = load_final_merged_dataset(project_root)
    metadata, taxonomy = split_metadata_and_taxonomy(merged)
    taxonomy_columns = feature_columns(merged)

    metadata_path = output_dir / "processed_data" / "metadata_table.csv"
    taxonomy_full_path = output_dir / "processed_data" / "taxonomy_full_matrix.csv"
    taxonomy_analysis_path = output_dir / "processed_data" / "taxonomy_analysis_matrix.csv"
    phylum_path = output_dir / "processed_data" / "taxonomy_phylum_matrix.csv"
    genus_path = output_dir / "processed_data" / "taxonomy_genus_matrix.csv"
    species_path = output_dir / "processed_data" / "taxonomy_species_matrix.csv"
    report_path = output_dir / "outputs" / "matrix_preparation_report.md"

    for path in (
        metadata_path,
        taxonomy_full_path,
        taxonomy_analysis_path,
        phylum_path,
        genus_path,
        species_path,
        report_path,
    ):
        ensure_parent(path)

    taxonomy_analysis = taxonomy[["sample"] + [column for column in taxonomy.columns if column not in {"sample", *STRUCTURAL_FEATURES}]].copy()
    phylum_matrix = taxonomy[["sample"] + exact_rank_columns(taxonomy_columns, "phylum")].copy()
    genus_matrix = taxonomy[["sample"] + exact_rank_columns(taxonomy_columns, "genus")].copy()
    species_matrix = taxonomy[["sample"] + exact_rank_columns(taxonomy_columns, "species")].copy()

    metadata.to_csv(metadata_path, index=False)
    taxonomy.to_csv(taxonomy_full_path, index=False)
    taxonomy_analysis.to_csv(taxonomy_analysis_path, index=False)
    phylum_matrix.to_csv(phylum_path, index=False)
    genus_matrix.to_csv(genus_path, index=False)
    species_matrix.to_csv(species_path, index=False)

    report_lines = [
        "# Matrix Preparation Report",
        "",
        "## What was found",
        "",
        f"- Input merged dataset: `processed_data/final_merged_dataset_preview.csv`",
        f"- Samples: {len(merged)}",
        f"- Metadata/provenance columns: {metadata.shape[1]}",
        f"- Taxonomic feature columns: {taxonomy.shape[1] - 1}",
        f"- Structural taxonomy buckets excluded from the analysis matrix: {', '.join(STRUCTURAL_FEATURES)}",
        "",
        "## What was executed",
        "",
        "- Split the validated merged dataset into a metadata/provenance table and a taxonomy-only matrix.",
        "- Built exact-rank phylum, genus, and species matrices using only columns with prefixes `P|`, `G|`, and `S|`.",
        "- Built an analysis matrix that excludes structural buckets used only for bookkeeping, not interpretation.",
        "",
        "## What outputs were created",
        "",
        "- `processed_data/metadata_table.csv`",
        "- `processed_data/taxonomy_full_matrix.csv`",
        "- `processed_data/taxonomy_analysis_matrix.csv`",
        "- `processed_data/taxonomy_phylum_matrix.csv`",
        "- `processed_data/taxonomy_genus_matrix.csv`",
        "- `processed_data/taxonomy_species_matrix.csv`",
        "",
        "## What assumptions were made",
        "",
        "- The first 30 non-microbial columns in the merged dataset are metadata, provenance, or identifiers.",
        "- Single-rank matrices are mathematically preferable for compositional normalization because the full hierarchy double-counts nested abundances across ranks.",
        "",
        "## What limitations remain",
        "",
        "- The full hierarchical taxonomy matrix is retained for traceability but should not be treated as a closed composition for CLR or ordination.",
        "- No directly observed crop or suitability label exists in the merged dataset.",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    append_log(log_path, f"Wrote metadata split to {metadata_path}")
    append_log(log_path, f"Wrote taxonomy split to {taxonomy_full_path}")
    append_log(log_path, f"Wrote analysis matrices to {taxonomy_analysis_path}, {phylum_path}, {genus_path}, and {species_path}")
    append_log(log_path, f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
