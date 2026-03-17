"""Create resumable extraction manifests and command files for the expected SRRs."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path


def expected_srrs_from_notebook(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return sorted(set(re.findall(r"SRR\d+", text)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "reconstruct_extraction.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "reconstruct_extraction.log")

    srr_audit_path = project_root / "srr_audit_report.csv"
    notebook_path = project_root / "Anvitha.ipynb"
    manifest_path = output_dir / "outputs" / "extraction_manifest.csv"
    ps1_path = output_dir / "scripts" / "run_missing_srr_recovery.ps1"
    sh_path = output_dir / "scripts" / "run_missing_srr_recovery.sh"
    notes_path = output_dir / "docs" / "extraction_recovery_notes.md"
    ensure_parent(manifest_path)
    ensure_parent(ps1_path)
    ensure_parent(sh_path)
    ensure_parent(notes_path)

    expected = expected_srrs_from_notebook(notebook_path)
    audit = pd.read_csv(srr_audit_path)
    by_srr = {row["srr_id"]: row for row in audit.to_dict(orient="records")}

    rows: list[dict[str, str]] = []
    missing_srrs: list[str] = []
    for srr_id in expected:
        row = by_srr.get(srr_id, {})
        processed = row.get("local_processed_presence", "absent")
        raw = row.get("local_raw_presence", "absent")
        if processed == "present":
            checkpoint = "classified"
        elif raw == "present":
            checkpoint = "raw_downloaded"
        else:
            checkpoint = "not_started"
            missing_srrs.append(srr_id)

        rows.append(
            {
                "srr_id": srr_id,
                "planned_classifier": "kraken2",
                "local_raw_presence": raw,
                "local_processed_presence": processed,
                "checkpoint_status": checkpoint,
                "kraken2_command": (
                    f"prefetch {srr_id} -O sra && "
                    f"fasterq-dump sra/{srr_id}/{srr_id}.sra -O raw_fastq --split-files -e 4 --temp tmp_sra && "
                    f"pigz -f raw_fastq/{srr_id}*.fastq && "
                    f"kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 2 "
                    f"--paired raw_fastq/{srr_id}_1.fastq.gz raw_fastq/{srr_id}_2.fastq.gz "
                    f"--report kraken_out/{srr_id}.report --output kraken_out/{srr_id}.kraken"
                ),
                "metaphlan_command": (
                    f"metaphlan raw_fastq/{srr_id}_1.fastq.gz,raw_fastq/{srr_id}_2.fastq.gz "
                    f"--input_type fastq --db_dir metaphlan_db "
                    f"-x mpa_vJan25_CHOCOPhlAnSGB_202503 --nproc 1 --mapout metaphlan_mapout/{srr_id}.bowtie2.bz2 "
                    f"-o metaphlan_out/{srr_id}_profile.tsv"
                ),
                "notes": row.get("notes", ""),
            }
        )

    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "srr_id",
                "planned_classifier",
                "local_raw_presence",
                "local_processed_presence",
                "checkpoint_status",
                "kraken2_command",
                "metaphlan_command",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    ps1_lines = [
        "$ErrorActionPreference = 'Stop'",
        "$missing = @(" + ", ".join(f"'{item}'" for item in missing_srrs) + ")",
        "foreach ($srr in $missing) {",
        "  Write-Host \"Recovering $srr\"",
        "  prefetch $srr -O sra",
        "  fasterq-dump \"sra/$srr/$srr.sra\" -O raw_fastq --split-files -e 4 --temp tmp_sra",
        "  Get-ChildItem \"raw_fastq/$srr*.fastq\" | ForEach-Object { pigz -f $_.FullName }",
        "  kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 2 --paired raw_fastq/${srr}_1.fastq.gz raw_fastq/${srr}_2.fastq.gz --report kraken_out/${srr}.report --output kraken_out/${srr}.kraken",
        "}",
    ]
    ps1_path.write_text("\n".join(ps1_lines) + "\n", encoding="utf-8")

    sh_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "missing=(" + " ".join(missing_srrs) + ")",
        "for srr in \"${missing[@]}\"; do",
        "  echo \"Recovering ${srr}\"",
        "  prefetch \"${srr}\" -O sra",
        "  fasterq-dump \"sra/${srr}/${srr}.sra\" -O raw_fastq --split-files -e 4 --temp tmp_sra",
        "  pigz -f raw_fastq/${srr}*.fastq",
        "  kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 2 --paired raw_fastq/${srr}_1.fastq.gz raw_fastq/${srr}_2.fastq.gz --report kraken_out/${srr}.report --output kraken_out/${srr}.kraken",
        "done",
    ]
    sh_path.write_text("\n".join(sh_lines) + "\n", encoding="utf-8")

    notes_path.write_text(
        "\n".join(
            [
                "# Extraction Recovery Notes",
                "",
                "- Kraken2 is the primary supported route because the notebook shows MetaPhlAn failed before successful outputs were produced.",
                "- The local snapshot contains no raw FASTQ or SRA files, so extraction is not complete in the current folder.",
                "- The generated command files are resumable templates and still require the SRA Toolkit, pigz, and Kraken2 databases to be installed.",
            ]
        ),
        encoding="utf-8",
    )

    append_log(log_path, f"Wrote extraction manifest to {manifest_path}")


if __name__ == "__main__":
    main()
