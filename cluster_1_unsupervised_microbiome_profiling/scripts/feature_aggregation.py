"""Summarize selected phylum and genus features for the unsupervised workflow cluster."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


CLUSTER_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = CLUSTER_ROOT / "data"
OUTPUT_DIR = CLUSTER_ROOT / "outputs"


def summarize_features(path: Path, level: str, min_prevalence: int, min_mean_abundance: float) -> pd.DataFrame:
    frame = pd.read_csv(path)
    data = frame.drop(columns=["sample"]).apply(pd.to_numeric, errors="coerce").fillna(0.0)
    prevalence = (data > 0).sum(axis=0)
    summary = pd.DataFrame(
        {
            "taxonomic_level": level,
            "taxon": data.columns,
            "prevalence_count": prevalence.values,
            "prevalence_fraction": prevalence.values / len(frame),
            "mean_relative_abundance": data.mean(axis=0).values,
            "median_relative_abundance": data.median(axis=0).values,
            "max_relative_abundance": data.max(axis=0).values,
        }
    )
    selected = summary.loc[
        (summary["prevalence_count"] >= min_prevalence)
        & (summary["mean_relative_abundance"] >= min_mean_abundance)
    ].copy()
    return selected.sort_values(
        ["mean_relative_abundance", "prevalence_count"],
        ascending=[False, False],
    ).reset_index(drop=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    phylum_summary = summarize_features(
        DATA_DIR / "taxonomy_phylum_matrix_prev2_relative_abundance.csv",
        level="phylum",
        min_prevalence=3,
        min_mean_abundance=0.01,
    )
    genus_summary = summarize_features(
        DATA_DIR / "taxonomy_genus_matrix_prev3_relative_abundance.csv",
        level="genus",
        min_prevalence=3,
        min_mean_abundance=0.005,
    )

    combined = pd.concat([phylum_summary, genus_summary], ignore_index=True)
    output_csv = OUTPUT_DIR / "aggregated_taxa_feature_selection.csv"
    combined.to_csv(output_csv, index=False)

    report_lines = [
        "# Feature Aggregation Report",
        "",
        "## What was found",
        "",
        f"- Selected phylum features: {len(phylum_summary)}",
        f"- Selected genus features: {len(genus_summary)}",
        "",
        "## What was executed",
        "",
        "- Loaded the Cluster 1 relative-abundance phylum and genus matrices.",
        "- Retained phylum features with prevalence >= 3 samples and mean relative abundance >= 1%.",
        "- Retained genus features with prevalence >= 3 samples and mean relative abundance >= 0.5%.",
        "",
        "## What outputs were created",
        "",
        "- `cluster_1_unsupervised_microbiome_profiling/outputs/aggregated_taxa_feature_selection.csv`",
        "",
        "## What assumptions were made",
        "",
        "- Aggregation thresholds match the reduced-feature-table rules already used in the main repository workflow.",
        "- This script is descriptive and does not create any label or prediction target.",
        "",
        "## What limitations remain",
        "",
        "- Selected taxa are stable descriptive features only; they are not validated biomarkers of soil health or crop outcome.",
    ]
    (OUTPUT_DIR / "feature_aggregation_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
