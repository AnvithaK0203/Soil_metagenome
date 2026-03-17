"""Build an exploratory genus-level feature matrix from the local taxonomy table."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path


def shannon(values: pd.Series) -> float:
    positive = values[values > 0]
    if positive.empty:
        return 0.0
    return float(-(positive * np.log(positive)).sum())


def simpson(values: pd.Series) -> float:
    return float(1.0 - (values**2).sum())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "preprocess.log")
    parser.add_argument(
        "--taxonomy-file",
        default="cleaned_data/taxonomy_kraken2_minikraken_superset_clean.csv",
        help="Input taxonomy matrix to preprocess.",
    )
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "preprocess.log")
    taxonomy_path = project_root / args.taxonomy_file
    output_path = output_dir / "processed_data" / "taxonomy_genus_exploratory_matrix.csv"
    ensure_parent(output_path)

    df = pd.read_csv(taxonomy_path)
    if "sample" not in df.columns:
        raise ValueError("Expected a 'sample' column in the taxonomy matrix.")

    samples = df["sample"].copy()
    features = df.drop(columns=["sample"]).copy()
    drop_cols = [col for col in ["R|root", "R1|cellular organisms"] if col in features.columns]
    features = features.drop(columns=drop_cols, errors="ignore")
    features = features.apply(pd.to_numeric, errors="coerce").fillna(0.0) / 100.0

    genus_cols = [col for col in features.columns if col.startswith("G|")]
    species_cols = [col for col in features.columns if col.startswith("S|")]
    if genus_cols:
        genus_frame = features[genus_cols].copy()
    else:
        mapped = {col: f"G|{col.split('|', 1)[1].split()[0]}" for col in species_cols}
        genus_frame = features[species_cols].rename(columns=mapped).groupby(axis=1, level=0).sum()

    prevalence = (genus_frame > 0).mean(axis=0)
    mean_abundance = genus_frame.mean(axis=0)
    keep = (prevalence >= 0.20) & (mean_abundance >= 0.0001)
    filtered = genus_frame.loc[:, keep].copy()

    eps = 1e-6
    shifted = filtered + eps
    geometric_mean = np.exp(np.mean(np.log(shifted), axis=1))
    clr = np.log(shifted.div(geometric_mean, axis=0))

    diversity = pd.DataFrame(
        {
            "sample": samples,
            "richness_gt_1e-4": (genus_frame > 1e-4).sum(axis=1),
            "shannon": features.apply(shannon, axis=1),
            "simpson": features.apply(simpson, axis=1),
        }
    )

    final_frame = pd.concat([samples, clr.reset_index(drop=True), diversity.drop(columns=["sample"])], axis=1)
    final_frame.to_csv(output_path, index=False)
    append_log(log_path, f"Wrote exploratory genus matrix to {output_path}")


if __name__ == "__main__":
    main()
