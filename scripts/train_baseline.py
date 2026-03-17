"""Gate and, when valid, train a simple baseline model."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, ensure_parent, infer_column_category, make_log_path


def choose_target(df: pd.DataFrame, explicit_target: str | None) -> str | None:
    if explicit_target:
        return explicit_target if explicit_target in df.columns else None
    for column in df.columns:
        if infer_column_category(column) == "label_candidate":
            return column
    return None


def write_no_go(path: Path, reasons: list[str]) -> None:
    ensure_parent(path)
    lines = ["# Baseline Modeling Status", "", "Baseline modeling was not executed for the following reasons:", ""]
    lines.extend([f"- {reason}" for reason in reasons])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "train_baseline.log")
    parser.add_argument(
        "--feature-matrix",
        default="processed_data/taxonomy_genus_exploratory_matrix.csv",
        help="Feature matrix to use for training.",
    )
    parser.add_argument("--target-col", default=None, help="Optional explicit target column.")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "train_baseline.log")
    feature_path = project_root / args.feature_matrix
    no_go_path = output_dir / "outputs" / "model_no_go_report.md"

    df = pd.read_csv(feature_path)
    target = choose_target(df, args.target_col)
    reasons: list[str] = []
    if target is None:
        reasons.append("No valid observed target column exists in the current local snapshot.")
    else:
        counts = df[target].value_counts(dropna=False)
        if counts.nunique() < 2 or len(counts) < 2:
            reasons.append("At least two target classes are required.")
        if not counts.empty and int(counts.min()) < 3:
            reasons.append("Each target class must contain at least 3 samples.")

    if reasons:
        write_no_go(no_go_path, reasons)
        append_log(log_path, "Baseline training skipped because the modeling gate did not pass.")
        return

    raise NotImplementedError(
        "The modeling gate passed unexpectedly. Extend this script with a validated baseline once observed labels are available."
    )


if __name__ == "__main__":
    main()
