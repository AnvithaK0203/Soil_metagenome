"""Create cleaned derivatives and rebuild the taxonomy matrix from validated Kraken reports only."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, make_log_path, normalize_sample_id


FILES_TO_CLEAN = [
    ("taxonomy_kraken2_minikraken.csv", "taxonomy_kraken2_minikraken_subset_clean.csv"),
    ("taxonomy_kraken2_minikraken (1).csv", "taxonomy_kraken2_minikraken_superset_clean.csv"),
    ("Optimized_Taxonomy_ML.csv", "optimized_taxonomy_ml_clean.csv"),
]

SPECIAL_RANK_LOOKUP = {
    "Bacteria": "D",
    "Archaea": "D",
    "Eukaryota": "D",
    "Viruses": "D",
}


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if "sample" in frame.columns:
        frame["sample"] = frame["sample"].map(normalize_sample_id)
        frame = frame.drop_duplicates(subset=["sample"], keep="first")
        frame = frame.sort_values("sample").reset_index(drop=True)
    return frame


def suffix_lookup(columns: list[str]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    collisions: set[str] = set()
    for column in columns:
        if column == "sample" or "|" not in column:
            continue
        _, _, suffix = column.partition("|")
        suffix = suffix.strip()
        if suffix in lookup and lookup[suffix] != column:
            collisions.add(suffix)
        else:
            lookup[suffix] = column
    for suffix in collisions:
        lookup.pop(suffix, None)
    return lookup


def infer_report_column(rank_code: str, name: str, last_major_rank: str | None, suffix_map: dict[str, str]) -> str:
    stripped_name = name.strip()
    if stripped_name in suffix_map:
        return suffix_map[stripped_name]
    if re.fullmatch(r"\d+", rank_code):
        prefix = last_major_rank or "R"
        return f"{prefix}{rank_code}|{stripped_name}"
    if rank_code:
        return f"{rank_code}|{stripped_name}"
    if stripped_name in SPECIAL_RANK_LOOKUP:
        return f"{SPECIAL_RANK_LOOKUP[stripped_name]}|{stripped_name}"
    return f"X|{stripped_name}"


def parse_kraken_report(report_path: Path, suffix_map: dict[str, str]) -> dict[str, float | str]:
    sample = normalize_sample_id(report_path.stem)
    row: dict[str, float | str] = {"sample": sample}
    last_major_rank = "R"
    for line in report_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        percent_text, _, _, rank_code, _, raw_name = parts[:6]
        name = raw_name.strip()
        if not name:
            continue
        try:
            percent = float(percent_text.strip())
        except ValueError:
            continue
        column = infer_report_column(rank_code.strip(), name, last_major_rank, suffix_map)
        row[column] = percent
        major_match = re.match(r"^([A-Z])\d*$", column.split("|", 1)[0])
        if major_match:
            last_major_rank = major_match.group(1)
    return row


def load_recovered_reports(project_root: Path, base_columns: list[str]) -> pd.DataFrame:
    suffix_map = suffix_lookup(base_columns)
    report_dir = project_root / "kraken_out"
    rows: list[dict[str, float | str]] = []
    if not report_dir.exists():
        return pd.DataFrame()

    for report_path in sorted(report_dir.glob("*.report")):
        kraken_path = report_path.with_suffix(".kraken")
        if not report_path.is_file() or report_path.stat().st_size == 0:
            continue
        if not kraken_path.is_file() or kraken_path.stat().st_size == 0:
            continue
        rows.append(parse_kraken_report(report_path, suffix_map))

    if not rows:
        return pd.DataFrame()

    recovered = pd.DataFrame(rows).fillna(0.0)
    return clean_frame(recovered)


def combine_taxonomy_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    usable = [frame.copy() for frame in frames if not frame.empty]
    if not usable:
        return pd.DataFrame(columns=["sample"])

    ordered_columns: list[str] = ["sample"]
    seen = {"sample"}
    for frame in usable:
        for column in frame.columns:
            if column in seen:
                continue
            ordered_columns.append(column)
            seen.add(column)

    aligned = []
    for frame in usable:
        working = frame.copy()
        for column in ordered_columns:
            if column not in working.columns:
                working[column] = 0.0 if column != "sample" else ""
        working = working[ordered_columns]
        aligned.append(working)

    combined = pd.concat(aligned, ignore_index=True)
    combined["sample"] = combined["sample"].map(normalize_sample_id)
    combined = combined.drop_duplicates(subset=["sample"], keep="last")
    combined = combined.sort_values("sample").reset_index(drop=True)
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "clean_data.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "clean_data.log")
    cleaned_dir = output_dir / "cleaned_data"
    processed_dir = output_dir / "processed_data"
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    best_local_taxonomy = pd.DataFrame()

    for source_name, target_name in FILES_TO_CLEAN:
        source_path = project_root / source_name
        if not source_path.exists():
            continue
        df = pd.read_csv(source_path)
        cleaned = clean_frame(df)
        target_path = cleaned_dir / target_name
        cleaned.to_csv(target_path, index=False)
        append_log(log_path, f"Wrote cleaned dataset {target_path}")

        if source_name == "taxonomy_kraken2_minikraken (1).csv":
            best_local_taxonomy = cleaned.copy()

    recovered_reports = load_recovered_reports(project_root, best_local_taxonomy.columns.tolist())
    if not recovered_reports.empty:
        recovered_path = processed_dir / "recovered_kraken_taxonomy_rows.csv"
        recovered_reports.to_csv(recovered_path, index=False)
        append_log(log_path, f"Wrote recovered taxonomy rows {recovered_path}")

    # Disk truth takes precedence over teammate-derived CSVs: the authoritative
    # current taxonomy matrix must come only from validated on-disk Kraken outputs.
    combined_taxonomy = combine_taxonomy_frames([recovered_reports])
    processed_path = processed_dir / "current_best_taxonomy_matrix.csv"
    combined_taxonomy.to_csv(processed_path, index=False)
    append_log(log_path, f"Wrote disk-truth validated taxonomy matrix {processed_path}")


if __name__ == "__main__":
    main()
