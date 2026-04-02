"""Compute ecological metrics, exploratory analysis outputs, and a reduced feature table."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import pdist, squareform
from sklearn.decomposition import PCA

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path
from microbiome_utils import (
    close_composition,
    dominant_taxon,
    feature_frame,
    pielou_evenness,
    richness,
    shannon_index,
    simpson_index,
    taxon_summary,
)


def sanitize_feature_name(label: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", label.replace("|", "__")).strip("_")
    return cleaned.lower()


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = ["| " + " | ".join(str(frame.iloc[idx][column]) for column in columns) + " |" for idx in range(len(frame))]
    return "\n".join([header, divider, *rows])


def load_matrix(project_root: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(project_root / "processed_data" / f"{name}.csv")


def pca_coordinates(matrix: pd.DataFrame) -> tuple[pd.DataFrame, PCA]:
    pca = PCA(n_components=2, random_state=0)
    coords = pca.fit_transform(matrix.to_numpy())
    coord_df = pd.DataFrame(coords, columns=["PC1", "PC2"], index=matrix.index)
    return coord_df, pca


def top_loadings(pca: PCA, columns: list[str], component_index: int, top_n: int = 5) -> list[str]:
    component = pca.components_[component_index]
    series = pd.Series(component, index=columns)
    top = series.abs().sort_values(ascending=False).head(top_n).index.tolist()
    return top


def save_pca_figure(coords: pd.DataFrame, explained: np.ndarray, samples: pd.Series, title: str, path: Path) -> None:
    ensure_parent(path)
    plt.figure(figsize=(8, 6))
    plt.scatter(coords["PC1"], coords["PC2"], s=40, color="#1f77b4")
    for sample, x_coord, y_coord in zip(samples, coords["PC1"], coords["PC2"], strict=True):
        plt.text(x_coord, y_coord, sample, fontsize=7, alpha=0.8)
    plt.xlabel(f"PC1 ({explained[0] * 100:.1f}% variance)")
    plt.ylabel(f"PC2 ({explained[1] * 100:.1f}% variance)")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def save_dendrogram(linkage_matrix: np.ndarray, labels: list[str], path: Path) -> None:
    ensure_parent(path)
    plt.figure(figsize=(10, 6))
    dendrogram(linkage_matrix, labels=labels, leaf_rotation=90)
    plt.title("Genus Hellinger Hierarchical Clustering")
    plt.ylabel("Ward linkage distance")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def save_heatmap(distance_matrix: np.ndarray, labels: list[str], path: Path) -> None:
    ensure_parent(path)
    plt.figure(figsize=(8, 7))
    plt.imshow(distance_matrix, cmap="viridis", interpolation="nearest")
    plt.xticks(range(len(labels)), labels, rotation=90, fontsize=6)
    plt.yticks(range(len(labels)), labels, fontsize=6)
    plt.colorbar(label="Bray-Curtis distance")
    plt.title("Genus Bray-Curtis Sample Distance Heatmap")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "exploratory_analysis.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "exploratory_analysis.log")

    figure_dir = output_dir / "outputs" / "figures"
    ensure_parent(figure_dir / "placeholder.txt")

    metadata = pd.read_csv(project_root / "processed_data" / "metadata_table.csv")
    full_matrix = load_matrix(project_root, "taxonomy_full_matrix")
    phylum_matrix = load_matrix(project_root, "taxonomy_phylum_matrix")
    genus_matrix = load_matrix(project_root, "taxonomy_genus_matrix")
    species_matrix = load_matrix(project_root, "taxonomy_species_matrix")

    phylum_rel = close_composition(feature_frame(phylum_matrix))
    genus_rel = close_composition(feature_frame(genus_matrix))
    species_rel = close_composition(feature_frame(species_matrix))

    metrics = pd.DataFrame({"sample": metadata["sample"]})
    species_richness = richness(feature_frame(species_matrix))
    genus_richness = richness(feature_frame(genus_matrix))
    shannon_genus = shannon_index(genus_rel)
    simpson_genus = simpson_index(genus_rel)
    evenness_genus = pielou_evenness(shannon_genus, genus_richness)
    dominant_phylum_name, dominant_phylum_abundance = dominant_taxon(phylum_rel)
    dominant_genus_name, dominant_genus_abundance = dominant_taxon(genus_rel)

    metrics["richness"] = species_richness.values
    metrics["genus_richness"] = genus_richness.values
    metrics["shannon_diversity"] = shannon_genus.values
    metrics["simpson_diversity"] = simpson_genus.values
    metrics["evenness"] = evenness_genus.values
    metrics["unclassified_proportion"] = full_matrix["U|unclassified"].astype(float).fillna(0.0) / 100.0
    metrics["dominant_taxon_proportion"] = dominant_genus_abundance.values
    metrics["dominant_phylum"] = dominant_phylum_name.values
    metrics["dominant_phylum_proportion"] = dominant_phylum_abundance.values
    metrics["dominant_genus"] = dominant_genus_name.values
    metrics["dominant_genus_proportion"] = dominant_genus_abundance.values

    sample_metrics_path = output_dir / "processed_data" / "sample_level_metrics.csv"
    ensure_parent(sample_metrics_path)
    metrics.to_csv(sample_metrics_path, index=False)

    phylum_prev2_rel = pd.read_csv(project_root / "processed_data" / "taxonomy_phylum_matrix_prev2_relative_abundance.csv")
    genus_prev3_rel = pd.read_csv(project_root / "processed_data" / "taxonomy_genus_matrix_prev3_relative_abundance.csv")
    phylum_prev2_hell = pd.read_csv(project_root / "processed_data" / "taxonomy_phylum_matrix_prev2_hellinger.csv")
    genus_prev3_hell = pd.read_csv(project_root / "processed_data" / "taxonomy_genus_matrix_prev3_hellinger.csv")

    phylum_rel_features = phylum_prev2_rel.set_index("sample")
    genus_rel_features = genus_prev3_rel.set_index("sample")
    phylum_hell_features = phylum_prev2_hell.set_index("sample")
    genus_hell_features = genus_prev3_hell.set_index("sample")

    phylum_pca_coords, phylum_pca = pca_coordinates(phylum_hell_features)
    genus_pca_coords, genus_pca = pca_coordinates(genus_hell_features)

    phylum_pca_coords.index.name = "sample"
    genus_pca_coords.index.name = "sample"

    save_pca_figure(
        phylum_pca_coords,
        phylum_pca.explained_variance_ratio_,
        phylum_rel_features.index.to_series().reset_index(drop=True),
        "Phylum Hellinger PCA",
        output_dir / "outputs" / "figures" / "phylum_pca.png",
    )
    save_pca_figure(
        genus_pca_coords,
        genus_pca.explained_variance_ratio_,
        genus_rel_features.index.to_series().reset_index(drop=True),
        "Genus Hellinger PCA",
        output_dir / "outputs" / "figures" / "genus_pca.png",
    )

    genus_linkage = linkage(genus_hell_features.to_numpy(), method="ward")
    cluster_labels = fcluster(genus_linkage, t=3, criterion="maxclust")
    save_dendrogram(
        genus_linkage,
        labels=genus_hell_features.index.tolist(),
        path=output_dir / "outputs" / "figures" / "genus_hierarchical_clustering.png",
    )

    bray_condensed = pdist(genus_rel_features.to_numpy(), metric="braycurtis")
    bray_square = squareform(bray_condensed)
    sample_order = dendrogram(genus_linkage, no_plot=True)["leaves"]
    ordered_labels = [genus_rel_features.index[idx] for idx in sample_order]
    ordered_dist = bray_square[np.ix_(sample_order, sample_order)]
    save_heatmap(
        ordered_dist,
        ordered_labels,
        output_dir / "outputs" / "figures" / "genus_braycurtis_heatmap.png",
    )

    pair_rows: list[dict[str, object]] = []
    samples = list(genus_rel_features.index)
    counter = 1
    for left in range(len(samples)):
        for right in range(left + 1, len(samples)):
            pair_rows.append(
                {
                    "similarity_rank": counter,
                    "sample_a": samples[left],
                    "sample_b": samples[right],
                    "genus_braycurtis_distance": bray_square[left, right],
                }
            )
            counter += 1
    similarity_df = pd.DataFrame(pair_rows).sort_values("genus_braycurtis_distance", ascending=True).reset_index(drop=True)
    similarity_df["similarity_rank"] = np.arange(1, len(similarity_df) + 1)
    similarity_path = output_dir / "outputs" / "sample_similarity_summary.csv"
    similarity_df.to_csv(similarity_path, index=False)

    phylum_summary = taxon_summary(phylum_rel_features, "phylum").head(15)
    genus_summary = taxon_summary(genus_rel_features, "genus").head(25)
    top_taxa = pd.concat([phylum_summary, genus_summary], ignore_index=True)
    top_taxa_path = output_dir / "outputs" / "top_taxa_summary.csv"
    top_taxa.to_csv(top_taxa_path, index=False)

    sample_metrics_report_path = output_dir / "outputs" / "sample_level_metrics_report.md"
    exploratory_summary_path = output_dir / "outputs" / "exploratory_summary.md"
    reduced_table_path = output_dir / "processed_data" / "reduced_feature_table.csv"
    analysis_ready_path = output_dir / "docs" / "ANALYSIS_READY_DATA_DESCRIPTION.md"
    project_status_path = output_dir / "docs" / "PROJECT_STATUS.md"
    next_steps_path = output_dir / "docs" / "NEXT_STEPS.md"
    professor_brief_path = output_dir / "docs" / "PROFESSOR_BRIEF.md"
    for path in (
        sample_metrics_report_path,
        exploratory_summary_path,
        reduced_table_path,
        analysis_ready_path,
        project_status_path,
        next_steps_path,
        professor_brief_path,
    ):
        ensure_parent(path)

    recurring_phyla = phylum_summary.loc[
        (phylum_summary["prevalence_count"] >= 3) & (phylum_summary["mean_relative_abundance"] >= 0.01),
        "taxon",
    ].tolist()[:8]
    recurring_genera = genus_summary.loc[
        (genus_summary["prevalence_count"] >= 3) & (genus_summary["mean_relative_abundance"] >= 0.005),
        "taxon",
    ].tolist()[:12]

    reduced_metadata_columns = [
        "sample",
        "local_biosample",
        "geo_loc_name_resolved",
        "lat_lon_resolved",
        "env_medium_resolved",
        "env_local_scale_resolved",
        "collection_date_resolved",
        "soil_type_remote",
        "depth_remote",
        "has_local_metadata",
        "has_remote_metadata",
    ]
    reduced = metadata[reduced_metadata_columns].merge(metrics, on="sample", how="left")
    reduced["genus_pc1"] = reduced["sample"].map(genus_pca_coords["PC1"])
    reduced["genus_pc2"] = reduced["sample"].map(genus_pca_coords["PC2"])
    reduced["genus_cluster_k3"] = reduced["sample"].map(dict(zip(genus_rel_features.index, cluster_labels, strict=True)))

    for taxon in recurring_phyla:
        reduced[f"phylum__{sanitize_feature_name(taxon)}"] = reduced["sample"].map(phylum_rel_features[taxon])
    for taxon in recurring_genera:
        reduced[f"genus__{sanitize_feature_name(taxon)}"] = reduced["sample"].map(genus_rel_features[taxon])
    reduced.to_csv(reduced_table_path, index=False)

    cluster_sizes = pd.Series(cluster_labels).value_counts().sort_index()
    closest_pair = similarity_df.iloc[0]
    farthest_pair = similarity_df.iloc[-1]

    sample_metrics_report_lines = [
        "# Sample-Level Metrics Report",
        "",
        "## What was found",
        "",
        f"- Samples analyzed: {len(metrics)}",
        f"- Species richness range: {int(metrics['richness'].min())} to {int(metrics['richness'].max())}",
        f"- Genus richness range: {int(metrics['genus_richness'].min())} to {int(metrics['genus_richness'].max())}",
        f"- Shannon diversity range (genus): {metrics['shannon_diversity'].min():.3f} to {metrics['shannon_diversity'].max():.3f}",
        f"- Unclassified proportion range: {metrics['unclassified_proportion'].min():.3f} to {metrics['unclassified_proportion'].max():.3f}",
        "",
        "## What was executed",
        "",
        "- Computed species richness from the exact species-level matrix.",
        "- Computed Shannon, Simpson, and evenness on the genus-level closed composition.",
        "- Measured unclassified proportion from the `U|unclassified` top-level structural column.",
        "- Recorded dominant phylum and dominant genus per sample.",
        "",
        "## What outputs were created",
        "",
        "- `processed_data/sample_level_metrics.csv`",
        "- `outputs/sample_level_metrics_report.md`",
        "",
        "## What assumptions were made",
        "",
        "- Species richness is used as the primary richness count, with genus richness retained as a stability-oriented companion metric.",
        "- Shannon, Simpson, and evenness are reported at genus level because species-level assignments are much sparser.",
        "",
        "## What limitations remain",
        "",
        "- Diversity estimates are descriptive only and should not be over-interpreted with n = 24.",
        "- They do not imply agronomic suitability without external labels or soil chemistry.",
    ]
    sample_metrics_report_path.write_text("\n".join(sample_metrics_report_lines) + "\n", encoding="utf-8")

    phylum_top_pc1 = ", ".join(top_loadings(phylum_pca, list(phylum_hell_features.columns), 0))
    genus_top_pc1 = ", ".join(top_loadings(genus_pca, list(genus_hell_features.columns), 0))
    exploratory_lines = [
        "# Exploratory Summary",
        "",
        "## What was found",
        "",
        f"- Genus Hellinger PCA variance explained: PC1 = {genus_pca.explained_variance_ratio_[0] * 100:.2f}%, PC2 = {genus_pca.explained_variance_ratio_[1] * 100:.2f}%",
        f"- Phylum Hellinger PCA variance explained: PC1 = {phylum_pca.explained_variance_ratio_[0] * 100:.2f}%, PC2 = {phylum_pca.explained_variance_ratio_[1] * 100:.2f}%",
        f"- Closest sample pair by genus Bray-Curtis distance: {closest_pair['sample_a']} vs {closest_pair['sample_b']} ({closest_pair['genus_braycurtis_distance']:.4f})",
        f"- Most dissimilar sample pair by genus Bray-Curtis distance: {farthest_pair['sample_a']} vs {farthest_pair['sample_b']} ({farthest_pair['genus_braycurtis_distance']:.4f})",
        "",
        "## What was executed",
        "",
        "- Performed PCA on Hellinger-transformed phylum and genus matrices.",
        "- Performed Ward hierarchical clustering on the genus Hellinger matrix.",
        "- Computed Bray-Curtis pairwise distances on the genus relative abundance matrix.",
        "- Summarized top phyla and genera by prevalence and mean relative abundance.",
        "",
        "## What outputs were created",
        "",
        "- `outputs/exploratory_summary.md`",
        "- `outputs/top_taxa_summary.csv`",
        "- `outputs/sample_similarity_summary.csv`",
        "- `outputs/figures/phylum_pca.png`",
        "- `outputs/figures/genus_pca.png`",
        "- `outputs/figures/genus_hierarchical_clustering.png`",
        "- `outputs/figures/genus_braycurtis_heatmap.png`",
        "",
        "## What assumptions were made",
        "",
        "- Genus-level Hellinger transformation is the primary exploratory matrix because it balances interpretability with resolution.",
        "- Phylum-level ordination is included for broad ecological structure, not for fine sample discrimination.",
        "",
        "## Key observations",
        "",
        f"- The most influential phylum-level PC1 loadings were: {phylum_top_pc1}.",
        f"- The most influential genus-level PC1 loadings were: {genus_top_pc1}.",
        f"- Ward clustering with k = 3 produced cluster sizes: {', '.join(f'cluster {idx} = {count}' for idx, count in cluster_sizes.items())}.",
        "- These unsupervised patterns describe microbiome structure only; they do not define crop classes or suitability groups.",
        "",
        "## What limitations remain",
        "",
        "- No supervised target exists, so these ordinations and clusters cannot be evaluated against agronomic outcomes.",
        "- The sample size is still small relative to the genus and species feature spaces.",
    ]
    exploratory_summary_path.write_text("\n".join(exploratory_lines) + "\n", encoding="utf-8")

    analysis_description_lines = [
        "# Analysis-Ready Data Description",
        "",
        "## What was created",
        "",
        "- `processed_data/reduced_feature_table.csv`",
        "",
        "## Column groups",
        "",
        "- Sample identifiers and resolved metadata",
        "- Sample-level ecological metrics",
        "- Selected phylum relative-abundance features",
        "- Selected genus relative-abundance features",
        "- Genus PCA coordinates and a descriptive cluster label",
        "",
        "## Feature selection rules",
        "",
        "- Phylum features kept in the reduced table: prevalence >= 3 samples and mean relative abundance >= 1%.",
        "- Genus features kept in the reduced table: prevalence >= 3 samples and mean relative abundance >= 0.5%.",
        "- PCA coordinates come from the genus Hellinger matrix after prevalence >= 3 filtering.",
        "",
        "## Important guardrail",
        "",
        "- This reduced table is future-ready for exploratory work only.",
        "- It must not be used for supervised crop prediction until a directly observed agronomic target is added.",
    ]
    analysis_ready_path.write_text("\n".join(analysis_description_lines) + "\n", encoding="utf-8")

    project_status_lines = [
        "# Project Status",
        "",
        "- Biological recovery is complete for all 24 expected SRRs.",
        "- The project now has a validated merged microbiome dataset, filtered rank-specific matrices, transformed analysis matrices, ecological metrics, exploratory ordinations, clustering outputs, and a reduced feature table.",
        "- The current scientifically correct scope remains exploratory microbiome analysis and feature reduction.",
        "- Supervised crop prediction remains blocked because no directly observed crop or suitability label exists.",
    ]
    project_status_path.write_text("\n".join(project_status_lines) + "\n", encoding="utf-8")

    next_steps_lines = [
        "# Next Steps",
        "",
        "1. Acquire a directly observed agronomic target such as crop outcome, crop history, or suitability score at sample level.",
        "2. Add soil physicochemical variables such as pH, organic carbon, moisture, and nutrient measurements.",
        "3. Revisit feature engineering with a label-aware but leakage-safe protocol only after those data exist.",
        "4. Keep current outputs as the exploratory baseline for the capstone report and presentation.",
    ]
    next_steps_path.write_text("\n".join(next_steps_lines) + "\n", encoding="utf-8")

    professor_brief_lines = [
        "# Professor Brief",
        "",
        "## What has been completed",
        "",
        "- The intended 24-SRR dataset has been fully recovered and validated.",
        "- The merged microbiome dataset was split into metadata and taxonomy components.",
        "- Rank-specific phylum, genus, and species matrices were built and filtered.",
        "- Relative abundance, Hellinger, and CLR transformations were generated on rank-specific matrices.",
        "- Sample-level ecological metrics, PCA, hierarchical clustering, and pairwise similarity summaries were produced.",
        "- A reduced feature table was created for future exploratory use.",
        "",
        "## What the current analysis supports",
        "",
        "- Exploratory microbiome structure analysis",
        "- Diversity and composition summaries",
        "- Lower-dimensional feature engineering for future work",
        "",
        "## What it does not support",
        "",
        "- Crop prediction",
        "- Crop recommendation",
        "- Any supervised claim tied to agronomic outcomes",
        "",
        "## Why supervised ML remains blocked",
        "",
        "- No directly observed crop or suitability label is present.",
        "- n = 24 is still too small for the original high-dimensional feature space without a defensible target and stronger metadata.",
    ]
    professor_brief_path.write_text("\n".join(professor_brief_lines) + "\n", encoding="utf-8")

    append_log(log_path, f"Wrote sample metrics to {sample_metrics_path}")
    append_log(log_path, f"Wrote exploratory outputs to {exploratory_summary_path}, {top_taxa_path}, and {similarity_path}")
    append_log(log_path, f"Wrote reduced feature table to {reduced_table_path}")
    append_log(log_path, f"Wrote documentation files to {analysis_ready_path}, {project_status_path}, {next_steps_path}, and {professor_brief_path}")


if __name__ == "__main__":
    main()
