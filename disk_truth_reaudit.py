"""Re-audit SRR status from on-disk truth and write disk-first validation tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path, normalize_sample_id

EXPECTED_SRRS = [
    "SRR12376372",
    "SRR13342225",
    "SRR13396075",
    "SRR13396103",
    "SRR1825760",
    "SRR23183348",
    "SRR23183349",
    "SRR23183368",
    "SRR26201959",
    "SRR26201960",
    "SRR26201961",
    "SRR33853917",
    "SRR33963317",
    "SRR33963318",
    "SRR33963319",
    "SRR33963320",
    "SRR33963321",
    "SRR33963322",
    "SRR33963323",
    "SRR33963324",
    "SRR5365029",
    "SRR8468865",
    "SRR9093167",
    "SRR9830591",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "disk_truth_reaudit.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "disk_truth_reaudit.log")

    srr_path = output_dir / "srr_audit_report.csv"
    remote_path = output_dir / "outputs" / "remote_run_metadata.csv"
    validation_csv_path = output_dir / "outputs" / "kraken_disk_validation.csv"
    fastq_check_path = output_dir / "outputs" / "missing_srr_fastq_check.csv"
    report_path = output_dir / "outputs" / "disk_truth_reaudit_report.md"
    for path in (validation_csv_path, fastq_check_path, report_path):
        ensure_parent(path)

    if srr_path.exists():
        srr_df = pd.read_csv(srr_path)
    else:
        srr_df = pd.DataFrame({"srr_id": EXPECTED_SRRS})
    if remote_path.exists():
        remote_df = pd.read_csv(remote_path)
    else:
        remote_df = pd.DataFrame({"srr_id": EXPECTED_SRRS})

    srr_df["srr_id"] = srr_df["srr_id"].map(normalize_sample_id)
    remote_df["srr_id"] = remote_df.get("srr_id", remote_df.get("run_accession", pd.Series(EXPECTED_SRRS))).map(normalize_sample_id)

    base = pd.DataFrame({"srr_id": EXPECTED_SRRS})
    base = base.merge(remote_df, on="srr_id", how="left", suffixes=("", "_remote"))
    base = base.merge(
        srr_df[[col for col in srr_df.columns if col in {"srr_id", "sample_accession", "study_accession", "experiment_accession", "library_layout", "fastq_ftp", "fastq_bytes"}]],
        on="srr_id",
        how="left",
        suffixes=("", "_audit"),
    )

    validation_rows: list[dict[str, object]] = []
    for srr in EXPECTED_SRRS:
        report_path_disk = project_root / "kraken_out" / f"{srr}.report"
        kraken_path_disk = project_root / "kraken_out" / f"{srr}.kraken"
        fastq_paths = sorted((project_root / "raw_data" / "recovered_fastq").glob(f"{srr}*.fastq.gz"))
        report_exists = report_path_disk.exists()
        kraken_exists = kraken_path_disk.exists()
        report_nonempty = report_exists and report_path_disk.stat().st_size > 0
        kraken_nonempty = kraken_exists and kraken_path_disk.stat().st_size > 0
        validated_complete = report_nonempty and kraken_nonempty
        if validated_complete:
            state = "validated_complete"
            notes = ""
        elif fastq_paths and kraken_nonempty and not report_nonempty:
            state = "classification_in_progress"
            notes = "FASTQ files are present and Kraken output is growing, but the non-empty report file is not complete yet."
        elif fastq_paths and not kraken_exists and not report_exists:
            state = "downloaded_not_classified"
            notes = "FASTQ files are present on disk, but Kraken output files are not present yet."
        elif fastq_paths or kraken_exists or report_exists:
            state = "partial_local_artifacts"
            notes = "Some local recovery artifacts exist, but the validated Kraken report/output pair is incomplete."
        else:
            state = "missing_completely_locally"
            notes = "No local FASTQ files or validated Kraken outputs are present on disk."
        validation_rows.append(
            {
                "srr_id": srr,
                "report_path": report_path_disk.relative_to(project_root).as_posix() if report_exists else "",
                "report_exists": report_exists,
                "report_nonempty": report_nonempty,
                "kraken_path": kraken_path_disk.relative_to(project_root).as_posix() if kraken_exists else "",
                "kraken_exists": kraken_exists,
                "kraken_nonempty": kraken_nonempty,
                "local_fastq_count": len(fastq_paths),
                "local_fastq_paths": ";".join(path.relative_to(project_root).as_posix() for path in fastq_paths),
                "validated_complete": validated_complete,
                "disk_truth_state": state,
                "notes": notes,
            }
        )

    validation_df = pd.DataFrame(validation_rows)
    validation_df.to_csv(validation_csv_path, index=False)

    merged = base.merge(validation_df, on="srr_id", how="left")
    missing_df = merged[~merged["validated_complete"]].copy()
    missing_df["local_fastq_presence"] = missing_df["local_fastq_count"].fillna(0).astype(int).gt(0).map({True: "present", False: "absent"})
    missing_df["status"] = missing_df["disk_truth_state"]
    missing_df["notes"] = missing_df["notes"].fillna("Needs disk-truth review.")
    missing_columns = [
        "srr_id",
        "disk_truth_state",
        "local_fastq_presence",
        "local_fastq_paths",
        "fastq_ftp",
        "fastq_bytes",
        "library_layout",
        "sample_accession",
        "study_accession",
        "experiment_accession",
        "status",
        "notes",
    ]
    for column in missing_columns:
        if column not in missing_df.columns:
            missing_df[column] = ""
    missing_df[missing_columns].to_csv(fastq_check_path, index=False)

    complete_ids = validation_df.loc[validation_df["validated_complete"], "srr_id"].tolist()
    in_progress_ids = validation_df.loc[validation_df["disk_truth_state"] == "classification_in_progress", "srr_id"].tolist()
    pending_ids = validation_df.loc[validation_df["disk_truth_state"] == "downloaded_not_classified", "srr_id"].tolist()
    partial_ids = validation_df.loc[validation_df["disk_truth_state"] == "partial_local_artifacts", "srr_id"].tolist()
    missing_ids = validation_df.loc[validation_df["disk_truth_state"] == "missing_completely_locally", "srr_id"].tolist()
    report_lines = [
        "# Disk-Truth Re-Audit Report",
        "",
        "## What was found",
        "",
        f"- Expected SRRs: {len(EXPECTED_SRRS)}",
        f"- Validated complete SRRs on disk: {len(complete_ids)}",
        f"- Classification currently in progress: {len(in_progress_ids)}",
        f"- Downloaded but not yet classified: {len(pending_ids)}",
        f"- Partial local artifacts requiring review: {len(partial_ids)}",
        f"- Missing completely locally: {len(missing_ids)}",
        "",
        "## Validated complete SRRs",
        "",
        *[f"- `{srr}`" for srr in complete_ids],
        "",
        "## Classification In Progress",
        "",
        *([f"- `{srr}`" for srr in in_progress_ids] or ["- none"]),
        "",
        "## Downloaded But Not Yet Classified",
        "",
        *([f"- `{srr}`" for srr in pending_ids] or ["- none"]),
        "",
        "## Partial Local Artifacts",
        "",
        *([f"- `{srr}`" for srr in partial_ids] or ["- none"]),
        "",
        "## Missing completely locally",
        "",
        *([f"- `{srr}`" for srr in missing_ids] or ["- none"]),
        "",
        "## Rule applied",
        "",
        "- A run is counted as processed only if both `.report` and `.kraken` exist on disk and are non-empty.",
        "- CSV-only derived rows without supporting Kraken artifacts are not counted as processed.",
        "- In-progress and partial states are reported from on-disk FASTQ and Kraken artifacts only.",
        "",
        "## Files written",
        "",
        "- `outputs/kraken_disk_validation.csv`",
        "- `outputs/missing_srr_fastq_check.csv`",
        "- `outputs/disk_truth_reaudit_report.md`",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    append_log(log_path, f"Wrote {validation_csv_path}")
    append_log(log_path, f"Wrote {fastq_check_path}")
    append_log(log_path, f"Wrote {report_path}")


if __name__ == "__main__":
    main()
