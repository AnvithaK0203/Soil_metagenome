"""Build a transparent Soil Microbiome Health Index prototype from unsupervised metrics only."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


CLUSTER_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = CLUSTER_ROOT / "data"
OUTPUT_DIR = CLUSTER_ROOT / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"

CORE_WEIGHTS = {
    "richness_combined": 0.25,
    "shannon_diversity": 0.20,
    "simpson_diversity": 0.15,
    "evenness": 0.15,
    "dominance_balance": 0.15,
    "classification_completeness": 0.10,
}
PREFERRED_VERSION = "smhi_version_b_percentile_0_100"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def minmax_scale(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    minimum = float(series.min())
    maximum = float(series.max())
    if maximum == minimum:
        scaled = pd.Series(0.5, index=series.index, dtype=float)
    else:
        scaled = (series - minimum) / (maximum - minimum)
    return scaled if higher_is_better else 1.0 - scaled


def percentile_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    ranked = series.rank(method="average", pct=True)
    return ranked if higher_is_better else 1.0 - ranked + (1.0 / len(series))


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics = pd.read_csv(DATA_DIR / "sample_level_metrics.csv")
    genus_hellinger = pd.read_csv(DATA_DIR / "taxonomy_genus_matrix_prev3_hellinger.csv")
    reduced = pd.read_csv(DATA_DIR / "reduced_feature_table.csv")
    return metrics, genus_hellinger, reduced


def compute_typicality(genus_hellinger: pd.DataFrame) -> pd.Series:
    feature_frame = genus_hellinger.set_index("sample")
    centroid = feature_frame.mean(axis=0)
    distances = np.sqrt(((feature_frame - centroid) ** 2).sum(axis=1))
    distance_series = pd.Series(distances, index=feature_frame.index, name="genus_hellinger_centroid_distance")
    typicality = percentile_score(distance_series, higher_is_better=False)
    typicality.name = "typicality_percentile"
    return pd.concat([distance_series, typicality], axis=1)


def weighted_average(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    aligned_weights = pd.Series(weights, dtype=float)
    return frame.loc[:, aligned_weights.index].mul(aligned_weights, axis=1).sum(axis=1)


def score_band(series: pd.Series) -> pd.Series:
    ranked = series.rank(method="first")
    return pd.qcut(ranked, q=4, labels=["lower", "moderate", "higher", "highest"])


def make_ranked_score_plot(summary: pd.DataFrame, path: Path) -> None:
    ordered = summary.sort_values(PREFERRED_VERSION, ascending=False).reset_index(drop=True)
    x_positions = np.arange(len(ordered))

    plt.figure(figsize=(12, 6))
    plt.bar(x_positions, ordered[PREFERRED_VERSION], color="#1f77b4", alpha=0.75, label="Version B (preferred)")
    plt.plot(x_positions, ordered["smhi_version_a_minmax_0_100"], color="#d62728", linewidth=1.8, label="Version A")
    plt.plot(x_positions, ordered["smhi_version_c_percentile_typicality_0_100"], color="#2ca02c", linewidth=1.8, label="Version C")
    plt.xticks(x_positions, ordered["sample"], rotation=90, fontsize=7)
    plt.ylabel("SMHI score (0-100)")
    plt.title("SMHI Prototype Version Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def make_component_heatmap(components: pd.DataFrame, summary: pd.DataFrame, path: Path) -> None:
    ordered_samples = summary.sort_values(PREFERRED_VERSION, ascending=False)["sample"].tolist()
    selected = components.set_index("sample").loc[
        ordered_samples,
        [
            "richness_combined_percentile",
            "shannon_diversity_percentile",
            "simpson_diversity_percentile",
            "evenness_percentile",
            "dominance_balance_percentile",
            "classification_completeness_percentile",
            "typicality_percentile",
        ],
    ]

    plt.figure(figsize=(9, 8))
    plt.imshow(selected.to_numpy(), aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    plt.xticks(range(selected.shape[1]), selected.columns, rotation=45, ha="right", fontsize=8)
    plt.yticks(range(selected.shape[0]), selected.index, fontsize=7)
    plt.colorbar(label="Percentile-oriented component score")
    plt.title("SMHI Component Heatmap")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def make_metric_scatter(summary: pd.DataFrame, path: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].scatter(summary["shannon_diversity"], summary[PREFERRED_VERSION], color="#1f77b4")
    axes[0].set_xlabel("Shannon diversity")
    axes[0].set_ylabel("SMHI Version B")
    axes[0].set_title("SMHI vs Shannon Diversity")

    axes[1].scatter(summary["dominant_taxon_proportion"], summary[PREFERRED_VERSION], color="#d62728")
    axes[1].set_xlabel("Dominant genus proportion")
    axes[1].set_ylabel("SMHI Version B")
    axes[1].set_title("SMHI vs Dominance")

    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def make_pca_colored_plot(summary: pd.DataFrame, reduced: pd.DataFrame, path: Path) -> None:
    merged = reduced.loc[:, ["sample", "genus_pc1", "genus_pc2"]].merge(
        summary.loc[:, ["sample", PREFERRED_VERSION]],
        on="sample",
        how="inner",
    )

    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(
        merged["genus_pc1"],
        merged["genus_pc2"],
        c=merged[PREFERRED_VERSION],
        cmap="viridis",
        s=55,
    )
    for row in merged.itertuples(index=False):
        plt.text(row.genus_pc1, row.genus_pc2, row.sample, fontsize=7, alpha=0.8)
    plt.xlabel("Genus PC1")
    plt.ylabel("Genus PC2")
    plt.title("Genus PCA Colored by SMHI Version B")
    plt.colorbar(scatter, label="SMHI Version B")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def report_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(str(frame.iloc[index][column]) for column in columns) + " |"
        for index in range(len(frame))
    ]
    return "\n".join([header, divider, *rows])


def main() -> None:
    ensure_dirs()

    metrics, genus_hellinger, reduced = load_inputs()
    typicality_frame = compute_typicality(genus_hellinger)
    metrics = metrics.merge(typicality_frame.reset_index().rename(columns={"index": "sample"}), on="sample", how="left")

    components = pd.DataFrame({"sample": metrics["sample"]})
    components["species_richness_raw"] = metrics["richness"]
    components["genus_richness_raw"] = metrics["genus_richness"]
    components["shannon_diversity_raw"] = metrics["shannon_diversity"]
    components["simpson_diversity_raw"] = metrics["simpson_diversity"]
    components["evenness_raw"] = metrics["evenness"]
    components["dominant_taxon_proportion_raw"] = metrics["dominant_taxon_proportion"]
    components["unclassified_proportion_raw"] = metrics["unclassified_proportion"]
    components["classification_completeness_raw"] = 1.0 - metrics["unclassified_proportion"]
    components["genus_hellinger_centroid_distance_raw"] = metrics["genus_hellinger_centroid_distance"]

    components["species_richness_minmax"] = minmax_scale(metrics["richness"], higher_is_better=True)
    components["genus_richness_minmax"] = minmax_scale(metrics["genus_richness"], higher_is_better=True)
    components["richness_combined_minmax"] = (
        components["species_richness_minmax"] + components["genus_richness_minmax"]
    ) / 2.0
    components["shannon_diversity_minmax"] = minmax_scale(metrics["shannon_diversity"], higher_is_better=True)
    components["simpson_diversity_minmax"] = minmax_scale(metrics["simpson_diversity"], higher_is_better=True)
    components["evenness_minmax"] = minmax_scale(metrics["evenness"], higher_is_better=True)
    components["dominance_balance_minmax"] = minmax_scale(metrics["dominant_taxon_proportion"], higher_is_better=False)
    components["classification_completeness_minmax"] = minmax_scale(
        1.0 - metrics["unclassified_proportion"],
        higher_is_better=True,
    )

    components["species_richness_percentile"] = percentile_score(metrics["richness"], higher_is_better=True)
    components["genus_richness_percentile"] = percentile_score(metrics["genus_richness"], higher_is_better=True)
    components["richness_combined_percentile"] = (
        components["species_richness_percentile"] + components["genus_richness_percentile"]
    ) / 2.0
    components["shannon_diversity_percentile"] = percentile_score(metrics["shannon_diversity"], higher_is_better=True)
    components["simpson_diversity_percentile"] = percentile_score(metrics["simpson_diversity"], higher_is_better=True)
    components["evenness_percentile"] = percentile_score(metrics["evenness"], higher_is_better=True)
    components["dominance_balance_percentile"] = percentile_score(
        metrics["dominant_taxon_proportion"],
        higher_is_better=False,
    )
    components["classification_completeness_percentile"] = percentile_score(
        1.0 - metrics["unclassified_proportion"],
        higher_is_better=True,
    )
    components["typicality_percentile"] = typicality_frame["typicality_percentile"].values

    version_a_input = components.loc[
        :,
        [
            "richness_combined_minmax",
            "shannon_diversity_minmax",
            "simpson_diversity_minmax",
            "evenness_minmax",
            "dominance_balance_minmax",
            "classification_completeness_minmax",
        ],
    ].rename(columns={column: column.replace("_minmax", "") for column in [
        "richness_combined_minmax",
        "shannon_diversity_minmax",
        "simpson_diversity_minmax",
        "evenness_minmax",
        "dominance_balance_minmax",
        "classification_completeness_minmax",
    ]})

    version_b_input = components.loc[
        :,
        [
            "richness_combined_percentile",
            "shannon_diversity_percentile",
            "simpson_diversity_percentile",
            "evenness_percentile",
            "dominance_balance_percentile",
            "classification_completeness_percentile",
        ],
    ].rename(columns={column: column.replace("_percentile", "") for column in [
        "richness_combined_percentile",
        "shannon_diversity_percentile",
        "simpson_diversity_percentile",
        "evenness_percentile",
        "dominance_balance_percentile",
        "classification_completeness_percentile",
    ]})

    smhi_a = weighted_average(version_a_input, CORE_WEIGHTS) * 100.0
    smhi_b = weighted_average(version_b_input, CORE_WEIGHTS) * 100.0
    smhi_c = 0.85 * smhi_b + 15.0 * components["typicality_percentile"]

    summary = metrics.loc[
        :,
        [
            "sample",
            "richness",
            "genus_richness",
            "shannon_diversity",
            "simpson_diversity",
            "evenness",
            "dominant_taxon_proportion",
            "unclassified_proportion",
            "genus_hellinger_centroid_distance",
        ],
    ].copy()
    summary["smhi_version_a_minmax_0_100"] = smhi_a.round(2)
    summary["smhi_version_b_percentile_0_100"] = smhi_b.round(2)
    summary["smhi_version_c_percentile_typicality_0_100"] = smhi_c.round(2)
    summary["rank_version_a"] = summary["smhi_version_a_minmax_0_100"].rank(ascending=False, method="min").astype(int)
    summary["rank_version_b"] = summary["smhi_version_b_percentile_0_100"].rank(ascending=False, method="min").astype(int)
    summary["rank_version_c"] = summary["smhi_version_c_percentile_typicality_0_100"].rank(ascending=False, method="min").astype(int)
    summary["preferred_reporting_score_0_100"] = summary[PREFERRED_VERSION]
    summary["preferred_reporting_rank"] = summary["rank_version_b"]
    summary["preferred_reporting_band"] = score_band(summary[PREFERRED_VERSION]).astype(str)
    summary = summary.sort_values(PREFERRED_VERSION, ascending=False).reset_index(drop=True)

    rank_spread = summary.loc[:, ["rank_version_a", "rank_version_b", "rank_version_c"]].max(axis=1) - summary.loc[
        :,
        ["rank_version_a", "rank_version_b", "rank_version_c"],
    ].min(axis=1)
    summary["rank_spread_across_versions"] = rank_spread

    component_output = DATA_DIR / "soil_microbiome_health_index_components.csv"
    index_output = DATA_DIR / "soil_microbiome_health_index.csv"
    summary_output = OUTPUT_DIR / "soil_microbiome_health_index_summary.csv"
    legacy_output = OUTPUT_DIR / "soil_microbiome_health_index_prototype.csv"
    components.to_csv(component_output, index=False)
    summary.to_csv(index_output, index=False)
    summary.to_csv(summary_output, index=False)
    summary.to_csv(legacy_output, index=False)

    make_ranked_score_plot(summary, FIGURE_DIR / "smhi_version_comparison.png")
    make_component_heatmap(components, summary, FIGURE_DIR / "smhi_component_heatmap.png")
    make_metric_scatter(summary, FIGURE_DIR / "smhi_b_vs_metrics.png")
    make_pca_colored_plot(summary, reduced, FIGURE_DIR / "genus_pca_colored_by_smhi_b.png")

    version_correlation = summary.loc[
        :,
        [
            "smhi_version_a_minmax_0_100",
            "smhi_version_b_percentile_0_100",
            "smhi_version_c_percentile_typicality_0_100",
        ],
    ].corr(method="spearman")
    metric_correlations = summary.loc[
        :,
        [
            "richness",
            "genus_richness",
            "shannon_diversity",
            "simpson_diversity",
            "evenness",
            "dominant_taxon_proportion",
            "unclassified_proportion",
            "genus_hellinger_centroid_distance",
            PREFERRED_VERSION,
        ],
    ].corr(method="spearman")[PREFERRED_VERSION].drop(labels=[PREFERRED_VERSION]).sort_values(ascending=False)

    largest_rank_spread = summary.sort_values("rank_spread_across_versions", ascending=False).iloc[0]
    lowest = summary.iloc[-3:][["sample", PREFERRED_VERSION, "preferred_reporting_band"]]
    highest = summary.iloc[:3][["sample", PREFERRED_VERSION, "preferred_reporting_band"]]

    candidate_table = pd.DataFrame(
        [
            {
                "component": "richness (species + genus)",
                "what_it_measures": "observed taxonomic breadth",
                "prototype_direction": "higher tentatively better",
                "use_status": "included",
            },
            {
                "component": "Shannon diversity",
                "what_it_measures": "richness-evenness balance",
                "prototype_direction": "higher tentatively better",
                "use_status": "included",
            },
            {
                "component": "Simpson diversity",
                "what_it_measures": "inverse dominance emphasis",
                "prototype_direction": "higher tentatively better",
                "use_status": "included",
            },
            {
                "component": "evenness",
                "what_it_measures": "balance across taxa",
                "prototype_direction": "higher tentatively better",
                "use_status": "included",
            },
            {
                "component": "dominant taxon proportion",
                "what_it_measures": "single-taxon concentration",
                "prototype_direction": "lower tentatively better",
                "use_status": "included as inverse dominance",
            },
            {
                "component": "unclassified proportion",
                "what_it_measures": "fraction not resolved by current reference space",
                "prototype_direction": "lower tentatively better",
                "use_status": "included with lower weight",
            },
            {
                "component": "genus Hellinger centroid distance",
                "what_it_measures": "compositional outlierness within this cohort",
                "prototype_direction": "lower may indicate more typicality",
                "use_status": "included only in Version C sensitivity analysis",
            },
            {
                "component": "cluster membership",
                "what_it_measures": "membership in unsupervised groups",
                "prototype_direction": "no health direction",
                "use_status": "excluded",
            },
        ]
    )

    report_lines = [
        "# Soil Microbiome Health Index Report",
        "",
        "## What was found",
        "",
        f"- Samples scored: {len(summary)}",
        f"- Preferred reporting version: `Version B`",
        f"- Version B score range: {summary[PREFERRED_VERSION].min():.2f} to {summary[PREFERRED_VERSION].max():.2f}",
        f"- Version B median score: {summary[PREFERRED_VERSION].median():.2f}",
        f"- Largest cross-version rank spread: {int(largest_rank_spread['rank_spread_across_versions'])} ranks for {largest_rank_spread['sample']}",
        "",
        "## What was executed",
        "",
        "- Evaluated current unsupervised sample-level metrics as candidate index components.",
        "- Computed three transparent SMHI versions: weighted min-max, weighted percentile, and percentile plus a small typicality term.",
        "- Calculated sample-level component scores, version scores, ranks, and internal sanity-check correlations.",
        "- Generated summary tables and diagnostic figures inside Cluster 1 only.",
        "",
        "## Candidate components",
        "",
        report_table(candidate_table),
        "",
        "## Index versions and formulas",
        "",
        "Let:",
        "",
        "- `R` = combined richness score from species and genus richness",
        "- `H` = Shannon diversity score",
        "- `S` = Simpson diversity score",
        "- `E` = evenness score",
        "- `D` = inverse dominance score from dominant genus proportion",
        "- `C` = classification completeness score from `1 - unclassified proportion`",
        "- `T` = typicality score from inverse percentile of genus Hellinger centroid distance",
        "",
        "Core weights:",
        "",
        "- `w_R = 0.25`",
        "- `w_H = 0.20`",
        "- `w_S = 0.15`",
        "- `w_E = 0.15`",
        "- `w_D = 0.15`",
        "- `w_C = 0.10`",
        "",
        "### Version A: weighted min-max index",
        "",
        "`SMHI_A = 100 * (0.25R_mm + 0.20H_mm + 0.15S_mm + 0.15E_mm + 0.15D_mm + 0.10C_mm)`",
        "",
        "### Version B: weighted percentile index",
        "",
        "`SMHI_B = 100 * (0.25R_pct + 0.20H_pct + 0.15S_pct + 0.15E_pct + 0.15D_pct + 0.10C_pct)`",
        "",
        "### Version C: percentile index with typicality sensitivity term",
        "",
        "`SMHI_C = 0.85 * SMHI_B + 15 * T_pct`",
        "",
        "Version B is the preferred reporting version because percentile scoring is more robust than min-max scaling for a 24-sample cohort and does not rely on an extra typicality assumption.",
        "",
        "## Internal sanity checks",
        "",
        "### Version agreement (Spearman correlation)",
        "",
        report_table(version_correlation.reset_index().rename(columns={"index": "version"}).round(3)),
        "",
        "### Spearman correlation of Version B with source metrics",
        "",
        report_table(
            metric_correlations.reset_index()
            .rename(columns={"index": "metric", PREFERRED_VERSION: "spearman_r"})
            .round(3)
        ),
        "",
        "### Highest-scoring samples by Version B",
        "",
    ]
    report_lines.extend(
        f"- {row.sample}: {row.smhi_version_b_percentile_0_100:.2f} ({row.preferred_reporting_band})"
        for row in highest.itertuples(index=False)
    )
    report_lines.extend(
        [
            "",
            "### Lowest-scoring samples by Version B",
            "",
        ]
    )
    report_lines.extend(
        f"- {row.sample}: {row.smhi_version_b_percentile_0_100:.2f} ({row.preferred_reporting_band})"
        for row in lowest.itertuples(index=False)
    )
    report_lines.extend(
        [
            "",
            "## What outputs were created",
            "",
            "- `cluster_1_unsupervised_microbiome_profiling/data/soil_microbiome_health_index.csv`",
            "- `cluster_1_unsupervised_microbiome_profiling/data/soil_microbiome_health_index_components.csv`",
            "- `cluster_1_unsupervised_microbiome_profiling/outputs/soil_microbiome_health_index_summary.csv`",
            "- `cluster_1_unsupervised_microbiome_profiling/outputs/soil_microbiome_health_index_report.md`",
            "- `cluster_1_unsupervised_microbiome_profiling/outputs/figures/smhi_version_comparison.png`",
            "- `cluster_1_unsupervised_microbiome_profiling/outputs/figures/smhi_component_heatmap.png`",
            "- `cluster_1_unsupervised_microbiome_profiling/outputs/figures/smhi_b_vs_metrics.png`",
            "- `cluster_1_unsupervised_microbiome_profiling/outputs/figures/genus_pca_colored_by_smhi_b.png`",
            "",
            "## What assumptions were made",
            "",
            "- Higher diversity and evenness were treated as favorable within this prototype because they represent broader and less concentrated community structure within the current cohort.",
            "- Lower dominance and lower unclassified proportion were treated as favorable within this prototype, while recognizing that database coverage and ecology both affect those quantities.",
            "- The centroid-distance typicality term was used only as a sensitivity analysis, not as the main scoring basis.",
            "",
            "## What limitations remain",
            "",
            "- This index is an internal descriptive prototype, not a validated soil-health diagnosis.",
            "- No soil chemistry or crop outcome data were used, so agronomic interpretation remains blocked.",
            "- With only 24 samples, rankings are cohort-relative and can shift if new samples are added.",
        ]
    )
    (OUTPUT_DIR / "soil_microbiome_health_index_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
