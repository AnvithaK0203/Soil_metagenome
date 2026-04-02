"""Utilities for microbiome matrix preparation and exploratory analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from common import infer_column_category, rank_prefix

STRUCTURAL_FEATURES = ["U|unclassified", "R|root", "R1|cellular organisms"]
RANK_PREFIX_MAP = {
    "phylum": "P",
    "genus": "G",
    "species": "S",
}


@dataclass(frozen=True)
class MatrixSummary:
    matrix_name: str
    original_feature_count: int
    nonzero_feature_count: int
    prevalence_ge_2_count: int
    prevalence_ge_3_count: int
    mean_abundance_threshold: float
    abundance_threshold_count: int


def load_final_merged_dataset(project_root: Path) -> pd.DataFrame:
    return pd.read_csv(project_root / "processed_data" / "final_merged_dataset_preview.csv")


def metadata_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in frame.columns if infer_column_category(column) != "microbial_feature"]


def feature_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in frame.columns if infer_column_category(column) == "microbial_feature"]


def split_metadata_and_taxonomy(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metadata = frame[metadata_columns(frame)].copy()
    taxonomy = pd.concat([frame[["sample"]].copy(), frame[feature_columns(frame)].copy()], axis=1)
    return metadata, taxonomy


def exact_rank_columns(columns: list[str], level: str) -> list[str]:
    prefix = f"{RANK_PREFIX_MAP[level]}|"
    return [column for column in columns if column.startswith(prefix)]


def feature_frame(matrix: pd.DataFrame) -> pd.DataFrame:
    features = [column for column in matrix.columns if column != "sample"]
    data = matrix[features].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return data


def with_sample(sample_series: pd.Series, feature_data: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([sample_series.reset_index(drop=True), feature_data.reset_index(drop=True)], axis=1)


def drop_features(matrix: pd.DataFrame, columns_to_drop: list[str]) -> pd.DataFrame:
    keep = ["sample"] + [column for column in matrix.columns if column != "sample" and column not in columns_to_drop]
    return matrix[keep].copy()


def prevalence_counts(data: pd.DataFrame) -> pd.Series:
    return (data > 0).sum(axis=0)


def filter_by_prevalence(
    matrix: pd.DataFrame,
    min_prevalence: int,
    mean_abundance_threshold: float = 0.0,
) -> tuple[pd.DataFrame, MatrixSummary]:
    data = feature_frame(matrix)
    sample = matrix[["sample"]].copy()

    nonzero_keep = data.sum(axis=0) > 0
    data_nonzero = data.loc[:, nonzero_keep]

    prevalence = prevalence_counts(data_nonzero)
    prev_keep = prevalence >= min_prevalence
    data_prev = data_nonzero.loc[:, prev_keep]

    if mean_abundance_threshold > 0:
        abundance_keep = data_prev.mean(axis=0) >= mean_abundance_threshold
    else:
        abundance_keep = pd.Series(True, index=data_prev.columns)
    data_final = data_prev.loc[:, abundance_keep]

    summary = MatrixSummary(
        matrix_name="",
        original_feature_count=int(data.shape[1]),
        nonzero_feature_count=int(data_nonzero.shape[1]),
        prevalence_ge_2_count=int((prevalence >= 2).sum()),
        prevalence_ge_3_count=int((prevalence >= 3).sum()),
        mean_abundance_threshold=float(mean_abundance_threshold),
        abundance_threshold_count=int(data_final.shape[1]),
    )
    return with_sample(sample["sample"], data_final), summary


def close_composition(data: pd.DataFrame) -> pd.DataFrame:
    row_sums = data.sum(axis=1).replace(0, np.nan)
    closed = data.div(row_sums, axis=0).fillna(0.0)
    return closed


def hellinger_transform(relative_abundance: pd.DataFrame) -> pd.DataFrame:
    return np.sqrt(relative_abundance)


def clr_transform(relative_abundance: pd.DataFrame, pseudocount: float = 1e-6) -> pd.DataFrame:
    adjusted = relative_abundance + pseudocount
    adjusted = adjusted.div(adjusted.sum(axis=1), axis=0)
    log_values = np.log(adjusted)
    geometric_mean = log_values.mean(axis=1)
    return log_values.sub(geometric_mean, axis=0)


def shannon_index(relative_abundance: pd.DataFrame) -> pd.Series:
    values = relative_abundance.to_numpy(copy=True)
    positive = values > 0
    safe = np.where(positive, values, 1.0)
    shannon = -(values * np.log(safe)).sum(axis=1)
    return pd.Series(shannon, index=relative_abundance.index)


def simpson_index(relative_abundance: pd.DataFrame) -> pd.Series:
    values = relative_abundance.to_numpy(copy=True)
    simpson = 1.0 - np.square(values).sum(axis=1)
    return pd.Series(simpson, index=relative_abundance.index)


def richness(data: pd.DataFrame) -> pd.Series:
    return (data > 0).sum(axis=1)


def pielou_evenness(shannon: pd.Series, richness_values: pd.Series) -> pd.Series:
    denominator = np.log(richness_values.replace(0, np.nan))
    evenness = shannon.div(denominator).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    evenness = evenness.where(richness_values > 1, 0.0)
    return evenness


def dominant_taxon(relative_abundance: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    taxon = relative_abundance.idxmax(axis=1)
    abundance = relative_abundance.max(axis=1)
    return taxon, abundance


def taxon_summary(relative_abundance: pd.DataFrame, level: str) -> pd.DataFrame:
    prevalence = (relative_abundance > 0).sum(axis=0)
    summary = pd.DataFrame(
        {
            "taxonomic_level": level,
            "taxon": relative_abundance.columns,
            "prevalence_count": prevalence.values,
            "prevalence_fraction": prevalence.values / len(relative_abundance),
            "mean_relative_abundance": relative_abundance.mean(axis=0).values,
            "median_relative_abundance": relative_abundance.median(axis=0).values,
            "max_relative_abundance": relative_abundance.max(axis=0).values,
        }
    )
    return summary.sort_values(["mean_relative_abundance", "prevalence_count"], ascending=[False, False]).reset_index(drop=True)


def rank_level_counts(columns: list[str]) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for column in columns:
        prefix = rank_prefix(column) or "unknown"
        counts[prefix] = counts.get(prefix, 0) + 1
    return pd.DataFrame(
        sorted(counts.items(), key=lambda item: item[0]),
        columns=["rank_prefix", "feature_count"],
    )
