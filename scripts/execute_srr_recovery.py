"""Recover remote SRR metadata, update manifests, and document extraction blockers."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path, normalize_sample_id

ENA_FILEREPORT_URL = "https://www.ebi.ac.uk/ena/portal/api/filereport"
ENA_SAMPLE_XML_URL = "https://www.ebi.ac.uk/ena/browser/api/xml/{accession}"
RAW_PATTERNS = ("*.fastq", "*.fastq.gz", "*.fq", "*.fq.gz", "*.sra")
PROCESSED_REPORT_GLOB = "*.report"
RUN_FIELDS = [
    "run_accession",
    "sample_accession",
    "secondary_sample_accession",
    "study_accession",
    "experiment_accession",
    "library_layout",
    "library_source",
    "scientific_name",
    "fastq_ftp",
    "fastq_md5",
    "fastq_bytes",
    "sample_title",
]
SELECTED_ATTRIBUTE_KEYS = [
    "collection_date",
    "geo_loc_name",
    "lat_lon",
    "env_broad_scale",
    "env_local_scale",
    "env_medium",
    "depth",
    "elev",
    "soil_type",
    "host",
    "host_disease",
    "isolation_source",
    "sample_type",
    "organism",
]


def normalize_tag(tag: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", tag.strip().lower()).strip("_")


def request_run_metadata(session: requests.Session, srr_id: str) -> dict[str, str]:
    response = session.get(
        ENA_FILEREPORT_URL,
        params={
            "accession": srr_id,
            "result": "read_run",
            "fields": ",".join(RUN_FIELDS),
        },
        timeout=90,
    )
    response.raise_for_status()
    lines = [line for line in response.text.splitlines() if line.strip()]
    if len(lines) < 2:
        return {"run_accession": srr_id}
    reader = csv.DictReader(lines, delimiter="\t")
    return next(reader)


def request_sample_attributes(session: requests.Session, sample_accession: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    response = session.get(ENA_SAMPLE_XML_URL.format(accession=sample_accession), timeout=90)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    sample = root.find(".//SAMPLE")
    if sample is None:
        return {}, []

    wide: dict[str, str] = {}
    long_rows: list[dict[str, str]] = []
    title = sample.findtext("./TITLE", default="")
    scientific_name = sample.findtext("./SAMPLE_NAME/SCIENTIFIC_NAME", default="")
    if title:
        wide["sample_title"] = title
    if scientific_name:
        wide["scientific_name"] = scientific_name

    for attribute in sample.findall(".//SAMPLE_ATTRIBUTE"):
        tag = normalize_tag(attribute.findtext("TAG", default=""))
        value = attribute.findtext("VALUE", default="").strip()
        if not tag or not value:
            continue
        if tag in wide and value not in wide[tag].split(" | "):
            wide[tag] = wide[tag] + " | " + value
        elif tag not in wide:
            wide[tag] = value
        long_rows.append(
            {
                "sample_accession": sample_accession,
                "attribute_tag": tag,
                "attribute_value": value,
            }
        )
    return wide, long_rows


def split_fastq_urls(value: str) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return []
    urls = [part.strip() for part in value.split(";") if part.strip()]
    return ["https://" + url.removeprefix("ftp://") if not url.startswith("http") else url for url in urls]


def url_basename(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def sum_fastq_bytes(value: str) -> int:
    if not isinstance(value, str) or not value.strip():
        return 0
    total = 0
    for part in value.split(";"):
        part = part.strip()
        if not part:
            continue
        try:
            total += int(part)
        except ValueError:
            continue
    return total


def detect_local_raw(project_root: Path) -> dict[str, list[str]]:
    raw_map: dict[str, list[str]] = {}
    for pattern in RAW_PATTERNS:
        for path in project_root.rglob(pattern):
            match = re.search(r"(SRR\d+)", path.name)
            if not match:
                continue
            raw_map.setdefault(match.group(1), []).append(path.relative_to(project_root).as_posix())
    return raw_map


def detect_local_processed(project_root: Path) -> dict[str, list[str]]:
    processed_map: dict[str, list[str]] = {}

    report_dir = project_root / "kraken_out"
    if report_dir.exists():
        for report_path in report_dir.glob(PROCESSED_REPORT_GLOB):
            kraken_path = report_path.with_suffix(".kraken")
            if not report_path.is_file() or report_path.stat().st_size == 0:
                continue
            if not kraken_path.is_file() or kraken_path.stat().st_size == 0:
                continue
            sample = normalize_sample_id(report_path.stem)
            processed_map.setdefault(sample, []).extend(
                [
                    report_path.relative_to(project_root).as_posix(),
                    kraken_path.relative_to(project_root).as_posix(),
                ]
            )

    taxonomy_path = project_root / "processed_data" / "current_best_taxonomy_matrix.csv"
    if taxonomy_path.exists():
        try:
            taxonomy_df = pd.read_csv(taxonomy_path, usecols=["sample"])
        except Exception:
            taxonomy_df = pd.DataFrame(columns=["sample"])
        for sample in taxonomy_df.get("sample", pd.Series(dtype=str)).dropna().astype(str).map(normalize_sample_id):
            if sample in processed_map:
                processed_map[sample].append(taxonomy_path.relative_to(project_root).as_posix())

    for sample, paths in processed_map.items():
        deduped: list[str] = []
        seen: set[str] = set()
        for path in paths:
            if path in seen:
                continue
            deduped.append(path)
            seen.add(path)
        processed_map[sample] = deduped

    return processed_map


def read_recovery_status(project_root: Path) -> dict[str, dict[str, str]]:
    status_path = project_root / "logs" / "wsl_recovery" / "run_recovery_status.csv"
    if not status_path.exists():
        return {}
    try:
        status_df = pd.read_csv(status_path)
    except Exception:
        return {}
    if "srr_id" not in status_df.columns:
        return {}
    status_df["srr_id"] = status_df["srr_id"].map(normalize_sample_id)
    return {
        row["srr_id"]: {key: "" if pd.isna(value) else str(value) for key, value in row.items()}
        for row in status_df.to_dict(orient="records")
    }


def wsl_status() -> tuple[bool, str]:
    try:
        process = subprocess.run(["wsl", "-l", "-v"], capture_output=True, text=True, check=False, timeout=60)
    except Exception as exc:  # pragma: no cover - environment specific
        return False, f"WSL unavailable: {exc}"
    output = (process.stdout or "") + (process.stderr or "")
    if process.returncode == 0 and "Ubuntu" in output:
        return True, output.replace("\x00", "").strip()
    return False, output.replace("\x00", "").strip()


def recommended_blocker(run_info: dict[str, Any], has_wsl: bool) -> str:
    if run_info.get("fastq_ftp"):
        if has_wsl:
            return (
                "Public FASTQ files are available, but the missing runs are not yet classified locally. "
                "Use the generated WSL recovery script to provision Kraken2 plus the MiniKraken database "
                "before downloading and classifying the missing samples."
            )
        return (
            "Public FASTQ files are available, but native Windows Kraken2 recovery is not provisioned in the workspace."
        )
    return "No public FASTQ endpoint was recovered from ENA for this run."


def build_https_download_command(srr_id: str, urls: list[str]) -> str:
    if not urls:
        return ""
    commands = [f"curl -L '{url}' -o raw_data/recovered_fastq/{url_basename(url)}" for url in urls]
    return " && ".join(commands)


def build_wsl_command(srr_id: str, urls: list[str]) -> str:
    if len(urls) == 1:
        download_clause = f"wget -c '{urls[0]}' -O raw_data/recovered_fastq/{url_basename(urls[0])}"
        input_clause = f"raw_data/recovered_fastq/{url_basename(urls[0])}"
        paired_clause = ""
    elif len(urls) >= 2:
        download_clause = " && ".join(
            [f"wget -c '{url}' -O raw_data/recovered_fastq/{url_basename(url)}" for url in urls[:2]]
        )
        input_clause = (
            f"raw_data/recovered_fastq/{url_basename(urls[0])} raw_data/recovered_fastq/{url_basename(urls[1])}"
        )
        paired_clause = "--paired "
    else:
        return ""
    return (
        f"wget -c https://genome-idx.s3.amazonaws.com/kraken/minikraken2_v2_8GB_201904.tgz -O kraken_db/minikraken2_v2_8GB_201904.tgz && "
        f"tar -xzf kraken_db/minikraken2_v2_8GB_201904.tgz -C kraken_db && "
        f"{download_clause} && "
        f"kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 4 {paired_clause}{input_clause} "
        f"--report kraken_out/{srr_id}.report --output kraken_out/{srr_id}.kraken"
    )


def write_wsl_recovery_script(project_root: Path, missing_rows: list[dict[str, Any]]) -> Path:
    preferred_path = project_root / "scripts" / "wsl_recover_missing_srrs.sh"
    ensure_parent(preferred_path)
    script_path = preferred_path
    if preferred_path.exists():
        try:
            existing_text = preferred_path.read_text(encoding="utf-8")
        except Exception:
            existing_text = ""
        if "validate_fastq_file() {" in existing_text and "recover_downloads()" in existing_text:
            script_path = project_root / "scripts" / "wsl_recover_missing_srrs_autogen.sh"
            ensure_parent(script_path)
        else:
            previous_path = preferred_path.with_suffix(".previous.sh")
            shutil.copy2(preferred_path, previous_path)
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "sudo apt-get update",
        "sudo apt-get install -y kraken2 wget pigz",
        "mkdir -p raw_data/recovered_fastq kraken_db kraken_out",
        "if [ ! -d kraken_db/minikraken2_v2_8GB_201904_UPDATE ]; then",
        "  wget -c https://genome-idx.s3.amazonaws.com/kraken/minikraken2_v2_8GB_201904.tgz -O kraken_db/minikraken2_v2_8GB_201904.tgz",
        "  tar -xzf kraken_db/minikraken2_v2_8GB_201904.tgz -C kraken_db",
        "fi",
        "",
    ]
    for row in missing_rows:
        urls = split_fastq_urls(row.get("fastq_ftp", ""))
        if not urls:
            continue
        lines.append(f"echo 'Recovering {row['srr_id']}'")
        for url in urls[:2]:
            lines.append(f"wget -c '{url}' -O raw_data/recovered_fastq/{url_basename(url)}")
        if len(urls) >= 2:
            lines.append(
                f"kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 4 --paired "
                f"raw_data/recovered_fastq/{url_basename(urls[0])} raw_data/recovered_fastq/{url_basename(urls[1])} "
                f"--report kraken_out/{row['srr_id']}.report --output kraken_out/{row['srr_id']}.kraken"
            )
        else:
            lines.append(
                f"kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 4 "
                f"raw_data/recovered_fastq/{url_basename(urls[0])} "
                f"--report kraken_out/{row['srr_id']}.report --output kraken_out/{row['srr_id']}.kraken"
            )
        lines.append("")
    script_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return script_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "execute_srr_recovery.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "execute_srr_recovery.log")
    srr_report_path = output_dir / "srr_audit_report.csv"
    sample_manifest_path = output_dir / "processed_data" / "sample_manifest.csv"
    extraction_manifest_path = output_dir / "outputs" / "extraction_manifest.csv"
    remote_run_path = output_dir / "outputs" / "remote_run_metadata.csv"
    remote_attr_long_path = output_dir / "outputs" / "remote_sample_attributes_long.csv"
    remote_meta_path = output_dir / "cleaned_data" / "remote_sample_metadata.csv"
    report_path = output_dir / "docs" / "srr_recovery_execution_report.md"
    for path in (
        srr_report_path,
        sample_manifest_path,
        extraction_manifest_path,
        remote_run_path,
        remote_attr_long_path,
        remote_meta_path,
        report_path,
    ):
        ensure_parent(path)

    audit_df = pd.read_csv(project_root / "srr_audit_report.csv")
    base_audit_columns = [
        "srr_id",
        "expected_or_detected",
        "local_raw_presence",
        "local_processed_presence",
        "metadata_presence",
        "status",
        "evidence_source",
        "notes",
    ]
    audit_df = audit_df[[column for column in base_audit_columns if column in audit_df.columns]].copy()
    audit_df["srr_id"] = audit_df["srr_id"].map(normalize_sample_id)
    expected_ids = sorted(audit_df["srr_id"].unique())
    original_processed_lookup = audit_df.set_index("srr_id")["local_processed_presence"].to_dict()

    raw_map = detect_local_raw(project_root)
    processed_map = detect_local_processed(project_root)
    recovery_status_map = read_recovery_status(project_root)
    has_wsl, wsl_detail = wsl_status()
    append_log(log_path, f"Detected WSL availability: {has_wsl}")

    session = requests.Session()
    session.headers.update({"User-Agent": "AnvithaProjectRecovery/1.0"})

    run_rows: list[dict[str, Any]] = []
    attribute_rows: list[dict[str, str]] = []
    sample_rows: list[dict[str, Any]] = []

    for srr_id in expected_ids:
        run_info = request_run_metadata(session, srr_id)
        sample_accession = run_info.get("sample_accession") or ""
        sample_wide: dict[str, str] = {}
        sample_long: list[dict[str, str]] = []
        if sample_accession:
            sample_wide, sample_long = request_sample_attributes(session, sample_accession)
        attribute_rows.extend(sample_long)

        run_urls = split_fastq_urls(run_info.get("fastq_ftp", ""))
        run_bytes = sum_fastq_bytes(run_info.get("fastq_bytes", ""))
        run_rows.append(
            {
                "srr_id": srr_id,
                **run_info,
                "remote_fastq_total_bytes": run_bytes,
                "remote_fastq_url_count": len(run_urls),
            }
        )
        sample_rows.append(
            {
                "srr_id": srr_id,
                **{
                    key: sample_wide.get(key, "")
                    for key in sorted((set(sample_wide) | set(SELECTED_ATTRIBUTE_KEYS)) - {"sample_title", "scientific_name"})
                },
            }
        )

    run_df = pd.DataFrame(run_rows)
    sample_df = pd.DataFrame(sample_rows)
    if attribute_rows:
        pd.DataFrame(attribute_rows).to_csv(remote_attr_long_path, index=False)
    run_df.to_csv(remote_run_path, index=False)
    sample_df.to_csv(remote_meta_path, index=False)

    local_meta = pd.read_csv(project_root / "cleaned_data" / "sample_metadata_observed.csv")
    local_meta["sample"] = local_meta["sample"].map(normalize_sample_id)

    enriched = audit_df.merge(run_df, left_on="srr_id", right_on="srr_id", how="left").merge(
        sample_df, left_on="srr_id", right_on="srr_id", how="left"
    )
    enriched["local_raw_presence"] = enriched["srr_id"].map(lambda s: "present" if raw_map.get(s) else "absent")
    enriched["local_raw_paths"] = enriched["srr_id"].map(lambda s: ";".join(raw_map.get(s, [])))
    enriched["local_processed_presence"] = enriched["srr_id"].map(lambda s: "present" if processed_map.get(s) else "absent")
    enriched["local_processed_paths"] = enriched["srr_id"].map(lambda s: ";".join(processed_map.get(s, [])))
    enriched["remote_run_metadata_available"] = enriched["run_accession"].notna() & (enriched["run_accession"] != "")
    enriched["remote_sample_metadata_available"] = enriched["sample_accession"].notna() & (enriched["sample_accession"] != "")
    enriched["remote_fastq_available"] = enriched["fastq_ftp"].notna() & (enriched["fastq_ftp"] != "")
    enriched["remote_fastq_total_bytes"] = enriched["remote_fastq_total_bytes"].fillna(0).astype("int64")
    enriched["recovery_attempt_status"] = enriched.apply(
        lambda row: recovery_status_map.get(row["srr_id"], {}).get(
            "overall_status",
            (
                "local_processed_present"
                if row["local_processed_presence"] == "present"
                else "metadata_recovered_processing_blocked"
                if row["remote_fastq_available"]
                else "missing_remote_fastq"
            ),
        ),
        axis=1,
    )
    in_progress_statuses = {
        "classification_running",
        "downloading",
        "downloaded_not_classified",
        "partially_downloaded",
        "classification_partial",
    }
    enriched["status"] = enriched.apply(
        lambda row: (
            "processed_with_metadata"
            if row["local_processed_presence"] == "present" and row["metadata_presence"] == "present"
            else "processed_no_metadata"
            if row["local_processed_presence"] == "present"
            else "recovery_in_progress_with_metadata"
            if row["recovery_attempt_status"] in in_progress_statuses
            and (row["metadata_presence"] == "present" or bool(row["remote_sample_metadata_available"]))
            else "recovery_in_progress_no_metadata"
            if row["recovery_attempt_status"] in in_progress_statuses
            else "missing_processing_with_metadata"
            if row["metadata_presence"] == "present" or bool(row["remote_sample_metadata_available"])
            else "missing_processing_no_metadata"
        ),
        axis=1,
    )
    enriched["still_missing"] = enriched["local_processed_presence"].eq("absent")
    enriched["blocked"] = enriched.apply(
        lambda row: row["still_missing"] and row["recovery_attempt_status"] not in in_progress_statuses,
        axis=1,
    )
    enriched["blocked_reason"] = enriched.apply(
        lambda row: recommended_blocker(row, has_wsl) if row["blocked"] else "",
        axis=1,
    )
    enriched["recovered_now"] = enriched.apply(
        lambda row: (
            "recovered_and_classified"
            if row["local_processed_presence"] == "present"
            and row["recovery_attempt_status"] in {"completed", "skipped_already_complete"}
            else "metadata_only"
            if row["local_processed_presence"] != "present"
            and row["recovery_attempt_status"] not in in_progress_statuses
            and bool(row["remote_sample_metadata_available"])
            else "in_progress"
            if row["recovery_attempt_status"] in in_progress_statuses
            else "no"
        ),
        axis=1,
    )
    enriched["recommended_execution_environment"] = "WSL Ubuntu 24.04" if has_wsl else "Linux environment required"
    enriched["https_download_command"] = enriched.apply(
        lambda row: build_https_download_command(row["srr_id"], split_fastq_urls(row.get("fastq_ftp", ""))),
        axis=1,
    )
    enriched["wsl_kraken2_command"] = enriched.apply(
        lambda row: build_wsl_command(row["srr_id"], split_fastq_urls(row.get("fastq_ftp", ""))),
        axis=1,
    )
    enriched["notes"] = enriched.apply(
        lambda row: (
            "Validated on-disk Kraken report/output files are present for this SRR."
            if row["local_processed_presence"] == "present"
            else "Local FASTQ files are present and Kraken2 classification is actively running."
            if row["recovery_attempt_status"] == "classification_running"
            else "Local FASTQ files are present, but validated Kraken outputs are not complete yet."
            if row["local_raw_presence"] == "present"
            else "Remote metadata is available, but no validated local FASTQ or Kraken outputs exist on disk."
            if bool(row["remote_sample_metadata_available"])
            else "Expected SRR from project evidence, but no validated local FASTQ or Kraken outputs exist on disk."
        ),
        axis=1,
    )

    srr_report_columns = [
        "srr_id",
        "expected_or_detected",
        "local_raw_presence",
        "local_processed_presence",
        "metadata_presence",
        "status",
        "remote_run_metadata_available",
        "remote_sample_metadata_available",
        "remote_fastq_available",
        "remote_fastq_total_bytes",
        "sample_accession",
        "secondary_sample_accession",
        "study_accession",
        "experiment_accession",
        "library_layout",
        "library_source",
        "scientific_name",
        "recovery_attempt_status",
        "recovered_now",
        "still_missing",
        "blocked",
        "blocked_reason",
        "evidence_source",
        "local_raw_paths",
        "local_processed_paths",
        "notes",
    ]
    enriched[srr_report_columns].to_csv(srr_report_path, index=False)

    manifest = enriched.rename(columns={"srr_id": "sample"}).merge(local_meta, on="sample", how="left", suffixes=("", "_local"))
    manifest = manifest.rename(
        columns={
            "BioSample": "biosample_local",
            "Collection_Date": "collection_date_local",
            "sample_title": "sample_title_remote",
            "scientific_name": "scientific_name_remote",
            "geo_loc_name": "geo_loc_name_remote",
            "lat_lon": "lat_lon_remote",
            "env_medium": "env_medium_remote",
            "env_local_scale": "env_local_scale_remote",
            "collection_date": "collection_date_remote",
            "env_broad_scale": "env_broad_scale_remote",
            "depth": "depth_remote",
            "elev": "elev_remote",
            "soil_type": "soil_type_remote",
            "host": "host_remote",
            "host_disease": "host_disease_remote",
            "isolation_source": "isolation_source_remote",
            "sample_type": "sample_type_remote",
            "organism": "organism_remote",
        }
    )
    for key in SELECTED_ATTRIBUTE_KEYS:
        remote_key = f"{key}_remote"
        if remote_key not in manifest.columns:
            manifest[remote_key] = ""
    manifest["resolved_geo_loc_name"] = manifest["geo_loc_name_local"].where(
        manifest["geo_loc_name_local"].notna() & (manifest["geo_loc_name_local"] != ""),
        manifest.get("geo_loc_name_remote", ""),
    )
    manifest["resolved_lat_lon"] = manifest["lat_lon_local"].where(
        manifest["lat_lon_local"].notna() & (manifest["lat_lon_local"] != ""),
        manifest.get("lat_lon_remote", ""),
    )
    manifest["resolved_env_medium"] = manifest["env_medium_local"].where(
        manifest["env_medium_local"].notna() & (manifest["env_medium_local"] != ""),
        manifest.get("env_medium_remote", ""),
    )
    manifest["resolved_env_local_scale"] = manifest["env_local_scale_local"].where(
        manifest["env_local_scale_local"].notna() & (manifest["env_local_scale_local"] != ""),
        manifest.get("env_local_scale_remote", ""),
    )
    manifest["resolved_collection_date"] = manifest["collection_date_local"].where(
        manifest["collection_date_local"].notna() & (manifest["collection_date_local"] != ""),
        manifest.get("collection_date_remote", ""),
    )
    manifest["has_local_metadata"] = manifest["metadata_presence"].eq("present")
    manifest["has_remote_metadata"] = manifest["remote_sample_metadata_available"]
    manifest["has_local_taxonomy"] = manifest["local_processed_presence"].eq("present")
    manifest.to_csv(sample_manifest_path, index=False)

    extraction = enriched[
        [
            "srr_id",
            "local_raw_presence",
            "local_processed_presence",
            "local_processed_paths",
            "sample_accession",
            "study_accession",
            "experiment_accession",
            "library_layout",
            "library_source",
            "fastq_ftp",
            "fastq_md5",
            "fastq_bytes",
            "remote_fastq_total_bytes",
            "recovery_attempt_status",
            "recovered_now",
            "still_missing",
            "blocked",
            "blocked_reason",
            "recommended_execution_environment",
            "https_download_command",
            "wsl_kraken2_command",
        ]
    ].copy()
    extraction["checkpoint_status"] = extraction["local_processed_presence"].map(
        lambda value: "classified" if value == "present" else "not_started"
    )
    extraction.to_csv(extraction_manifest_path, index=False)

    missing_df = enriched[enriched["still_missing"]].copy()
    script_path = write_wsl_recovery_script(project_root, missing_df.to_dict(orient="records"))
    total_missing_bytes = int(missing_df["remote_fastq_total_bytes"].sum())
    processed_count = int((enriched["local_processed_presence"] == "present").sum())
    metadata_count = int((enriched["metadata_presence"] == "present").sum())
    missing_count = len(missing_df)
    if missing_count == 0:
        blocked_lines = [
            "- No expected SRRs remain missing from local processed outputs in this recovery pass.",
            "- Windows-native Kraken2 is still not provisioned in the workspace, but WSL-based recovery has already produced the required local outputs.",
        ]
        next_step_lines = [
            "- Freeze the verified biological recovery state and rebuild downstream analytical datasets from the recovered SRR set.",
            "- Keep supervised modeling blocked unless a directly observed target is added later.",
        ]
        missing_section = ["None"]
    else:
        blocked_lines = [
            "- No raw FASTQ or SRA files for the missing runs are present in the current project snapshot.",
            "- The missing SRRs have not been classified locally in this pass.",
            "- Native Windows Kraken2 processing is not provisioned in the workspace; WSL is available but the Kraken2 database and downloads were not executed in this pass.",
        ]
        next_step_lines = [
            f"- Run the WSL recovery helper to download and classify the missing {missing_count} SRRs if full biological completeness is still required.",
            f"- Otherwise continue with the currently available {processed_count} processed SRRs as an exploratory-only local dataset.",
        ]
        missing_section = [", ".join(missing_df["srr_id"].tolist())]
    report_lines = [
        "# SRR Recovery Execution Report",
        "",
        "## What was found",
        "",
        f"- Expected SRRs audited: {len(enriched)}",
        f"- Local processed SRRs still present: {processed_count}",
        f"- Local metadata-merged SRRs still present: {metadata_count}",
        f"- Missing processed SRRs: {missing_count}",
        f"- Missing processed compressed FASTQ volume advertised by ENA: {round(total_missing_bytes / 1024 / 1024 / 1024, 2)} GB",
        "",
        "## What was executed",
        "",
        "- Queried ENA run metadata for all expected SRRs.",
        "- Queried ENA sample XML records to recover richer sample attributes.",
        "- Re-scanned the project snapshot for raw FASTQ and SRA files.",
        "- Rebuilt the SRR audit, sample manifest, and extraction manifest with remote recovery context.",
        "",
        "## What changed",
        "",
        "- Added remote sample accession, study accession, experiment accession, layout, and public FASTQ URLs for the expected SRRs.",
        "- Added remote sample metadata fields such as collection date and geo-location where available.",
        f"- Generated a WSL recovery helper at `{script_path.relative_to(project_root).as_posix()}`.",
        "",
        "## What remains blocked or uncertain",
        "",
        *blocked_lines,
        "",
        "## What files were created or updated",
        "",
        "- `srr_audit_report.csv`",
        "- `processed_data/sample_manifest.csv`",
        "- `outputs/extraction_manifest.csv`",
        "- `outputs/remote_run_metadata.csv`",
        "- `outputs/remote_sample_attributes_long.csv`",
        "- `cleaned_data/remote_sample_metadata.csv`",
        "- `scripts/wsl_recover_missing_srrs.sh`",
        "",
        "## What the next immediate step is",
        "",
        *next_step_lines,
        "",
        "## Missing SRRs",
        "",
        *missing_section,
        "",
        "## WSL Availability",
        "",
        "```text",
        wsl_detail or "Unavailable",
        "```",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    append_log(log_path, f"Updated {srr_report_path}")
    append_log(log_path, f"Updated {sample_manifest_path}")
    append_log(log_path, f"Updated {extraction_manifest_path}")


if __name__ == "__main__":
    main()
