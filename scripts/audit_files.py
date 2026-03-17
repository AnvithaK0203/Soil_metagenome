"""Create a recursive file inventory for the recovery workspace."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path


ROLE_OVERRIDES = {
    "Anvitha.ipynb": ("workflow_notebook", "critical", "original_evidence", "Primary Colab workflow log."),
    "Untitled17 (1).ipynb": ("merge_notebook", "high", "original_evidence", "Metadata merge and prevalence-filter notebook."),
    "taxonomy_kraken2_minikraken.csv": (
        "taxonomy_matrix_partial",
        "high",
        "original_evidence",
        "Early 5-sample Kraken2 feature matrix.",
    ),
    "taxonomy_kraken2_minikraken (1).csv": (
        "taxonomy_matrix_superset",
        "critical",
        "original_evidence",
        "Current best 13-sample Kraken2 feature matrix.",
    ),
    "Optimized_Taxonomy_ML.csv": (
        "derived_ml_table",
        "critical",
        "original_evidence",
        "10-sample derived table with sparse metadata and no target column.",
    ),
}


def classify_file(path: Path, project_root: Path) -> tuple[str, str, str, str]:
    if path.name in ROLE_OVERRIDES:
        return ROLE_OVERRIDES[path.name]

    relative = path.relative_to(project_root).as_posix()
    suffix = path.suffix.lower()
    if relative.startswith("scripts/"):
        return ("recovery_script", "high", "generated", "Recovery automation or analysis script.")
    if relative.startswith("notebooks/"):
        return ("reporting_notebook", "medium", "generated", "Notebook wrapper around recovery scripts.")
    if relative.startswith("cleaned_data/"):
        return ("cleaned_dataset", "high", "generated", "Cleaned derivative preserving sample grain.")
    if relative.startswith("processed_data/"):
        return ("processed_dataset", "high", "generated", "Manifest or processed analysis-ready table.")
    if relative.startswith("outputs/"):
        return ("report_output", "medium", "generated", "Generated summary table, report, or command manifest.")
    if relative.startswith("logs/"):
        return ("log_or_trace", "medium", "generated", "Execution or trace log for the recovery pass.")
    if relative.startswith("docs/"):
        return ("project_documentation", "medium", "generated", "Supporting project documentation.")
    if suffix in {".csv", ".tsv", ".xlsx"}:
        return ("tabular_data", "medium", "unknown", "Tabular project artifact.")
    if suffix == ".ipynb":
        return ("notebook", "medium", "unknown", "Notebook artifact.")
    if suffix == ".md":
        return ("markdown_document", "medium", "generated", "Markdown report or documentation.")
    return ("other_file", "low", "unknown", "Unclassified file type.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "audit_files.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "audit_files.log")
    output_path = output_dir / "file_inventory.csv"
    ensure_parent(output_path)

    rows: list[dict[str, object]] = []
    for path in sorted(project_root.rglob("*")):
        if not path.is_file():
            continue
        guessed_role, importance, status, notes = classify_file(path, project_root)
        rows.append(
            {
                "relative_path": path.relative_to(project_root).as_posix(),
                "file_name": path.name,
                "extension": path.suffix.lower() or "[no_extension]",
                "size_bytes": path.stat().st_size,
                "guessed_role": guessed_role,
                "importance": importance,
                "status": status,
                "notes": notes,
            }
        )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "relative_path",
                "file_name",
                "extension",
                "size_bytes",
                "guessed_role",
                "importance",
                "status",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    append_log(log_path, f"Wrote {len(rows)} inventory rows to {output_path}")


if __name__ == "__main__":
    main()
