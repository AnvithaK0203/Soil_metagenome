"""Audit expected versus locally represented SRR accessions."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pandas as pd

from common import (
    SRR_PATTERN,
    TEXT_EXTENSIONS,
    add_standard_args,
    append_log,
    default_project_root,
    ensure_parent,
    extract_srr_ids,
    iter_files,
    make_log_path,
    normalize_sample_id,
    read_text_like,
)


def load_sample_set(path: Path) -> set[str]:
    df = pd.read_csv(path)
    for candidate in ("sample", "Sample", "run", "SRR"):
        if candidate in df.columns:
            return {normalize_sample_id(value) for value in df[candidate].dropna()}
    return set()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "audit_srrs.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "audit_srrs.log")
    output_path = output_dir / "srr_audit_report.csv"
    ensure_parent(output_path)

    all_mentions: dict[str, set[str]] = defaultdict(set)
    notebook_expected: set[str] = set()
    for path in iter_files(project_root, TEXT_EXTENSIONS):
        text = read_text_like(path)
        ids = extract_srr_ids(text)
        if not ids:
            continue
        relative = path.relative_to(project_root).as_posix()
        for srr_id in ids:
            all_mentions[srr_id].add(relative)
        if path.name == "Anvitha.ipynb":
            notebook_expected.update(ids)

    raw_patterns = ["*.sra", "*.fastq", "*.fastq.gz", "*.fq", "*.fq.gz"]
    raw_present: dict[str, list[str]] = defaultdict(list)
    for pattern in raw_patterns:
        for path in project_root.rglob(pattern):
            match = SRR_PATTERN.search(path.name)
            if match:
                raw_present[match.group()].append(path.relative_to(project_root).as_posix())

    processed_files = [
        project_root / "taxonomy_kraken2_minikraken.csv",
        project_root / "taxonomy_kraken2_minikraken (1).csv",
        project_root / "Optimized_Taxonomy_ML.csv",
    ]
    processed_sources: dict[str, list[str]] = defaultdict(list)
    metadata_sources: dict[str, list[str]] = defaultdict(list)
    for path in processed_files:
        if not path.exists():
            continue
        sample_set = load_sample_set(path)
        for sample_id in sample_set:
            processed_sources[sample_id].append(path.relative_to(project_root).as_posix())
        if path.name == "Optimized_Taxonomy_ML.csv":
            for sample_id in sample_set:
                metadata_sources[sample_id].append(path.relative_to(project_root).as_posix())

    universe = sorted(set(all_mentions) | set(processed_sources) | set(metadata_sources) | set(raw_present))
    rows: list[dict[str, str]] = []
    for srr_id in universe:
        expected_flag = "expected" if srr_id in notebook_expected else "detected"
        local_raw = "present" if raw_present.get(srr_id) else "absent"
        local_processed = "present" if processed_sources.get(srr_id) else "absent"
        metadata_presence = "present" if metadata_sources.get(srr_id) else "absent"

        if local_processed == "present" and metadata_presence == "present":
            status = "processed_with_metadata"
        elif local_processed == "present":
            status = "processed_no_metadata"
        elif expected_flag == "expected":
            status = "expected_missing_processed"
        else:
            status = "detected_only"

        evidence_parts: list[str] = []
        if all_mentions.get(srr_id):
            evidence_parts.append("mentions=" + ";".join(sorted(all_mentions[srr_id])))
        if processed_sources.get(srr_id):
            evidence_parts.append("processed=" + ";".join(sorted(processed_sources[srr_id])))
        if metadata_sources.get(srr_id):
            evidence_parts.append("metadata=" + ";".join(sorted(metadata_sources[srr_id])))
        if raw_present.get(srr_id):
            evidence_parts.append("raw=" + ";".join(sorted(raw_present[srr_id])))

        notes = ""
        if srr_id in {"SRR12376372", "SRR33853917", "SRR33963317"} and metadata_presence == "absent":
            notes = "Present in current best taxonomy table but absent from derived 10-sample ML table."
        elif status == "expected_missing_processed":
            notes = "Mentioned in the notebook target list but not represented in current local processed files."

        rows.append(
            {
                "srr_id": srr_id,
                "expected_or_detected": expected_flag,
                "local_raw_presence": local_raw,
                "local_processed_presence": local_processed,
                "metadata_presence": metadata_presence,
                "status": status,
                "evidence_source": " | ".join(evidence_parts),
                "notes": notes,
            }
        )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "srr_id",
                "expected_or_detected",
                "local_raw_presence",
                "local_processed_presence",
                "metadata_presence",
                "status",
                "evidence_source",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    append_log(log_path, f"Wrote {len(rows)} SRR rows to {output_path}")


if __name__ == "__main__":
    main()
