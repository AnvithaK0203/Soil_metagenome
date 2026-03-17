#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

LOG_DIR="logs/wsl_recovery"
RUN_LOG_DIR="${LOG_DIR}/runs"
QUARANTINE_DIR="${LOG_DIR}/quarantine"
FASTQ_DIR="raw_data/recovered_fastq"
SRA_CACHE_DIR="raw_data/recovered_sra_cache"
SRA_TMP_DIR="raw_data/recovered_sra_tmp"
KRAKEN_DB_DIR="kraken_db/minikraken2_v2_8GB_201904_UPDATE"
KRAKEN_OUT_DIR="kraken_out"
SUMMARY_CSV="${LOG_DIR}/run_recovery_status.csv"
MASTER_LOG="${LOG_DIR}/wsl_recovery_master.log"

mkdir -p "${LOG_DIR}" "${RUN_LOG_DIR}" "${QUARANTINE_DIR}" "${FASTQ_DIR}" "${SRA_CACHE_DIR}" "${SRA_TMP_DIR}" "${KRAKEN_OUT_DIR}" "kraken_db"

TOTAL_THREADS="$(nproc 2>/dev/null || echo 4)"
DEFAULT_THREADS="$(( TOTAL_THREADS * 8 / 10 ))"
if [ "${DEFAULT_THREADS}" -lt 1 ]; then
  DEFAULT_THREADS=1
fi
if [ "${TOTAL_THREADS}" -gt 1 ] && [ "${DEFAULT_THREADS}" -ge "${TOTAL_THREADS}" ]; then
  DEFAULT_THREADS="$(( TOTAL_THREADS - 1 ))"
fi
THREADS="${KRAKEN_THREADS:-${DEFAULT_THREADS}}"
DOWNLOAD_THREADS="${RECOVERY_IO_THREADS:-${THREADS}}"
USE_MEMORY_MAPPING="${KRAKEN_USE_MEMORY_MAPPING:-1}"
KRAKEN_EXTRA_ARGS=()
if [ "${USE_MEMORY_MAPPING}" = "1" ]; then
  KRAKEN_EXTRA_ARGS+=(--memory-mapping)
fi

log_msg() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "${MASTER_LOG}"
}

run_log_path() {
  printf '%s/%s.log' "${RUN_LOG_DIR}" "$1"
}

log_run() {
  local srr="$1"
  shift
  local message="$*"
  local stamp
  stamp="$(date -Iseconds)"
  printf '[%s] %s\n' "${stamp}" "${message}" | tee -a "${MASTER_LOG}" >> "$(run_log_path "${srr}")"
}

write_status_header() {
  python3 - "${SUMMARY_CSV}" <<'PY'
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
fieldnames = [
    "srr_id",
    "overall_status",
    "download_status",
    "classification_status",
    "expected_fastq_files",
    "local_fastq_paths",
    "report_path",
    "kraken_path",
    "threads_used",
    "started_at",
    "completed_at",
    "notes",
]
rows = []
if path.exists():
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({key: row.get(key, "") for key in fieldnames})
with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
PY
}

record_status() {
  local srr="$1"
  local overall_status="$2"
  local download_status="$3"
  local classification_status="$4"
  local expected_fastq_files="$5"
  local local_fastq_paths="$6"
  local report_path="$7"
  local kraken_path="$8"
  local threads_used="$9"
  local started_at="${10}"
  local completed_at="${11}"
  local notes="${12}"
  python3 - "${SUMMARY_CSV}" "${srr}" "${overall_status}" "${download_status}" "${classification_status}" "${expected_fastq_files}" "${local_fastq_paths}" "${report_path}" "${kraken_path}" "${threads_used}" "${started_at}" "${completed_at}" "${notes}" <<'PY'
import csv
import sys
from pathlib import Path

(
    summary,
    srr,
    overall_status,
    download_status,
    classification_status,
    expected_fastq_files,
    local_fastq_paths,
    report_path,
    kraken_path,
    threads_used,
    started_at,
    completed_at,
    notes,
) = sys.argv[1:]

fieldnames = [
    "srr_id",
    "overall_status",
    "download_status",
    "classification_status",
    "expected_fastq_files",
    "local_fastq_paths",
    "report_path",
    "kraken_path",
    "threads_used",
    "started_at",
    "completed_at",
    "notes",
]
path = Path(summary)
rows = []
if path.exists():
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({key: row.get(key, "") for key in fieldnames})
rows = [row for row in rows if row["srr_id"] != srr]
rows.append(
    {
        "srr_id": srr,
        "overall_status": overall_status,
        "download_status": download_status,
        "classification_status": classification_status,
        "expected_fastq_files": expected_fastq_files,
        "local_fastq_paths": local_fastq_paths,
        "report_path": report_path,
        "kraken_path": kraken_path,
        "threads_used": threads_used,
        "started_at": started_at,
        "completed_at": completed_at,
        "notes": notes,
    }
)
rows = sorted(rows, key=lambda row: row["srr_id"])
with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
PY
}

file_size_bytes() {
  stat -c '%s' "$1"
}

quarantine_file() {
  local srr="$1"
  local path="$2"
  local reason="$3"
  if [ ! -e "${path}" ]; then
    return 0
  fi
  local target_dir="${QUARANTINE_DIR}/${srr}"
  mkdir -p "${target_dir}"
  local base
  base="$(basename "${path}")"
  local target="${target_dir}/${base}.$(date +%Y%m%dT%H%M%S).${reason}"
  mv "${path}" "${target}"
  log_run "${srr}" "Quarantined ${path} -> ${target} (${reason})"
}

validate_fastq_file() {
  local path="$1"
  local expected_bytes="$2"
  if [ ! -f "${path}" ] || [ ! -s "${path}" ]; then
    return 1
  fi
  local actual_bytes
  actual_bytes="$(file_size_bytes "${path}")"
  if [ -n "${expected_bytes}" ] && [ "${actual_bytes}" -ne "${expected_bytes}" ]; then
    return 2
  fi
  if ! gzip -t "${path}" >/dev/null 2>&1; then
    return 3
  fi
  return 0
}

validate_kraken_outputs() {
  local report="$1"
  local out="$2"
  local srr="$3"
  if [ ! -s "${report}" ] || [ ! -s "${out}" ]; then
    return 1
  fi
  if ! grep -q "${srr}" "${out}"; then
    return 2
  fi
  return 0
}

build_candidate_urls() {
  local primary_url="$1"
  local candidates=("${primary_url}")
  if [[ "${primary_url}" == https://ftp.sra.ebi.ac.uk/* ]]; then
    local suffix="${primary_url#https://ftp.sra.ebi.ac.uk}"
    candidates+=("ftp://ftp.sra.ebi.ac.uk${suffix}" "http://ftp.sra.ebi.ac.uk${suffix}")
  elif [[ "${primary_url}" == ftp://ftp.sra.ebi.ac.uk/* ]]; then
    local suffix="${primary_url#ftp://ftp.sra.ebi.ac.uk}"
    candidates+=("https://ftp.sra.ebi.ac.uk${suffix}")
  fi
  printf '%s\n' "${candidates[@]}" | awk '!seen[$0]++'
}

ensure_prereqs() {
  log_msg "Validating WSL bioinformatics prerequisites"
  log_msg "Detected OS: $(grep '^PRETTY_NAME=' /etc/os-release | cut -d= -f2- | tr -d '\"')"
  log_msg "Project root: ${PROJECT_ROOT}"
  log_msg "Logical CPUs detected: ${TOTAL_THREADS}"
  log_msg "Kraken2 threads selected: ${THREADS}"
  log_msg "I/O helper threads selected: ${DOWNLOAD_THREADS}"
  log_msg "Kraken2 memory mapping enabled: ${USE_MEMORY_MAPPING}"
  log_msg "Free disk on project volume: $(df -h "${PROJECT_ROOT}" | awk 'NR==2 {print $4 " free of " $2}')"

  local missing_tools=()
  for tool in kraken2 wget pigz prefetch fasterq-dump python3 gzip; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
      missing_tools+=("${tool}")
    fi
  done

  if [ "${#missing_tools[@]}" -gt 0 ]; then
    log_msg "Installing missing packages for: ${missing_tools[*]}"
    apt-get update >> "${MASTER_LOG}" 2>&1
    DEBIAN_FRONTEND=noninteractive apt-get install -y kraken2 wget pigz sra-toolkit python3 >> "${MASTER_LOG}" 2>&1
  else
    log_msg "All required command-line tools are already available."
  fi

  if [ ! -d "${KRAKEN_DB_DIR}" ]; then
    log_msg "Kraken2 database missing; downloading MiniKraken2."
    wget -c https://genome-idx.s3.amazonaws.com/kraken/minikraken2_v2_8GB_201904.tgz -O kraken_db/minikraken2_v2_8GB_201904.tgz >> "${MASTER_LOG}" 2>&1
    tar -xzf kraken_db/minikraken2_v2_8GB_201904.tgz -C kraken_db >> "${MASTER_LOG}" 2>&1
  fi

  if [ ! -d "${KRAKEN_DB_DIR}" ]; then
    log_msg "Kraken2 database path is still missing after setup: ${KRAKEN_DB_DIR}"
    return 1
  fi

  log_msg "Kraken2 executable: $(command -v kraken2)"
  log_msg "Kraken2 database verified at ${KRAKEN_DB_DIR}"
  return 0
}

prepare_existing_file() {
  local srr="$1"
  local path="$2"
  if [ -f "${path}" ] && [ ! -s "${path}" ]; then
    quarantine_file "${srr}" "${path}" "zero_byte"
  fi
}

download_one_file() {
  local srr="$1"
  local output_path="$2"
  local expected_bytes="$3"
  local primary_url="$4"
  local run_log
  run_log="$(run_log_path "${srr}")"

  prepare_existing_file "${srr}" "${output_path}"

  if validate_fastq_file "${output_path}" "${expected_bytes}"; then
    log_run "${srr}" "Reusing existing validated FASTQ ${output_path}"
    return 0
  fi

  if [ -f "${output_path}" ] && [ -s "${output_path}" ]; then
    log_run "${srr}" "Existing FASTQ ${output_path} is incomplete or unvalidated; attempting resumable download."
  fi

  local attempted_any=0
  while IFS= read -r candidate_url; do
    attempted_any=1
    for attempt in 1 2 3; do
      log_run "${srr}" "Download attempt ${attempt} for ${output_path} using ${candidate_url}"
      if wget -c --tries=1 --timeout=60 --read-timeout=60 --retry-connrefused "${candidate_url}" -O "${output_path}" >> "${run_log}" 2>&1; then
        if validate_fastq_file "${output_path}" "${expected_bytes}"; then
          log_run "${srr}" "Validated ${output_path} after ${candidate_url}"
          return 0
        fi
        log_run "${srr}" "Downloaded ${output_path} from ${candidate_url} but validation failed; retrying."
      else
        local rc=$?
        log_run "${srr}" "Download attempt ${attempt} failed for ${candidate_url} with exit code ${rc}"
      fi
      prepare_existing_file "${srr}" "${output_path}"
      sleep "$(( attempt * 5 ))"
    done
  done < <(build_candidate_urls "${primary_url}")

  if [ "${attempted_any}" -eq 0 ]; then
    log_run "${srr}" "No candidate URLs could be generated for ${output_path}"
  fi
  return 1
}

compress_sra_fastqs() {
  local srr="$1"
  local source_dir="$2"
  shift 2
  local targets=("$@")
  for target in "${targets[@]}"; do
    local base
    base="$(basename "${target}" .gz)"
    local raw_path="${source_dir}/${base}"
    if [ ! -s "${raw_path}" ]; then
      return 1
    fi
    pigz -p "${DOWNLOAD_THREADS}" -c "${raw_path}" > "${target}"
    rm -f "${raw_path}"
    log_run "${srr}" "Compressed ${raw_path} -> ${target}"
  done
  return 0
}

sra_toolkit_fallback() {
  local srr="$1"
  local layout="$2"
  shift 2
  local expected_paths=("$@")
  local sra_dir="${SRA_CACHE_DIR}/${srr}"
  local tmp_dir="${SRA_TMP_DIR}/${srr}"
  rm -rf "${tmp_dir}"
  mkdir -p "${tmp_dir}"

  log_run "${srr}" "Attempting SRA Toolkit fallback via prefetch/fasterq-dump"
  if ! prefetch --max-size u --output-directory "${SRA_CACHE_DIR}" "${srr}" >> "$(run_log_path "${srr}")" 2>&1; then
    log_run "${srr}" "prefetch failed for ${srr}"
    return 1
  fi

  if ! fasterq-dump --threads "${DOWNLOAD_THREADS}" --outdir "${tmp_dir}" --split-files "${sra_dir}" >> "$(run_log_path "${srr}")" 2>&1; then
    log_run "${srr}" "fasterq-dump failed for ${srr}"
    return 1
  fi

  if [ "${layout}" = "single" ]; then
    local single_raw="${tmp_dir}/${srr}.fastq"
    if [ ! -s "${single_raw}" ] && [ -s "${tmp_dir}/${srr}_1.fastq" ]; then
      single_raw="${tmp_dir}/${srr}_1.fastq"
    fi
    if [ ! -s "${single_raw}" ]; then
      log_run "${srr}" "SRA fallback did not produce a single-end FASTQ for ${srr}"
      return 1
    fi
    pigz -p "${DOWNLOAD_THREADS}" -c "${single_raw}" > "${expected_paths[0]}"
    rm -f "${single_raw}"
  else
    if ! compress_sra_fastqs "${srr}" "${tmp_dir}" "${expected_paths[@]}"; then
      log_run "${srr}" "SRA fallback did not produce the expected paired FASTQ set for ${srr}"
      return 1
    fi
  fi

  rm -rf "${tmp_dir}"
  log_run "${srr}" "SRA Toolkit fallback completed for ${srr}"
  return 0
}

recover_downloads() {
  local srr="$1"
  local layout="$2"
  shift 2
  local -a urls=("$1" "$2")
  shift 2
  local -a bytes=("$1" "$2")
  shift 2
  local -a paths=("$1" "$2")
  shift 2 || true

  local expected_file_count=1
  if [ "${layout}" = "paired" ]; then
    expected_file_count=2
  fi

  local i
  for (( i=0; i<expected_file_count; i++ )); do
    if ! download_one_file "${srr}" "${paths[$i]}" "${bytes[$i]}" "${urls[$i]}"; then
      if ! sra_toolkit_fallback "${srr}" "${layout}" "${paths[@]:0:${expected_file_count}}"; then
        return 1
      fi
      break
    fi
  done

  for (( i=0; i<expected_file_count; i++ )); do
    if ! validate_fastq_file "${paths[$i]}" "${bytes[$i]}"; then
      return 1
    fi
  done

  return 0
}

run_kraken_paired() {
  local srr="$1"
  local r1="$2"
  local r2="$3"
  local report="${KRAKEN_OUT_DIR}/${srr}.report"
  local out="${KRAKEN_OUT_DIR}/${srr}.kraken"

  if validate_kraken_outputs "${report}" "${out}" "${srr}"; then
    log_run "${srr}" "Skipping Kraken2 classification; validated outputs already exist."
    return 0
  fi

  if [ -e "${report}" ] || [ -e "${out}" ]; then
    log_run "${srr}" "Existing Kraken2 outputs did not validate; quarantining partial artifacts before rerun."
    quarantine_file "${srr}" "${report}" "kraken_report_invalid"
    quarantine_file "${srr}" "${out}" "kraken_output_invalid"
  fi
  log_run "${srr}" "Running Kraken2 paired classification with ${THREADS} threads"
  if ! kraken2 --db "${KRAKEN_DB_DIR}" --threads "${THREADS}" "${KRAKEN_EXTRA_ARGS[@]}" --paired "${r1}" "${r2}" --report "${report}" --output "${out}" >> "$(run_log_path "${srr}")" 2>&1; then
    log_run "${srr}" "Kraken2 classification failed for ${srr}"
    return 1
  fi

  if ! validate_kraken_outputs "${report}" "${out}" "${srr}"; then
    log_run "${srr}" "Kraken2 outputs failed validation for ${srr}"
    return 1
  fi

  return 0
}

run_kraken_single() {
  local srr="$1"
  local fq="$2"
  local report="${KRAKEN_OUT_DIR}/${srr}.report"
  local out="${KRAKEN_OUT_DIR}/${srr}.kraken"

  if validate_kraken_outputs "${report}" "${out}" "${srr}"; then
    log_run "${srr}" "Skipping Kraken2 classification; validated outputs already exist."
    return 0
  fi

  if [ -e "${report}" ] || [ -e "${out}" ]; then
    log_run "${srr}" "Existing Kraken2 outputs did not validate; quarantining partial artifacts before rerun."
    quarantine_file "${srr}" "${report}" "kraken_report_invalid"
    quarantine_file "${srr}" "${out}" "kraken_output_invalid"
  fi
  log_run "${srr}" "Running Kraken2 single-end classification with ${THREADS} threads"
  if ! kraken2 --db "${KRAKEN_DB_DIR}" --threads "${THREADS}" "${KRAKEN_EXTRA_ARGS[@]}" "${fq}" --report "${report}" --output "${out}" >> "$(run_log_path "${srr}")" 2>&1; then
    log_run "${srr}" "Kraken2 classification failed for ${srr}"
    return 1
  fi

  if ! validate_kraken_outputs "${report}" "${out}" "${srr}"; then
    log_run "${srr}" "Kraken2 outputs failed validation for ${srr}"
    return 1
  fi

  return 0
}

completed_before_run() {
  local srr="$1"
  local layout="$2"
  shift 2
  local -a paths=("$1" "$2")
  shift 2
  local -a bytes=("$1" "$2")
  shift 2
  local report="${KRAKEN_OUT_DIR}/${srr}.report"
  local out="${KRAKEN_OUT_DIR}/${srr}.kraken"

  if [ "${layout}" = "paired" ]; then
    validate_fastq_file "${paths[0]}" "${bytes[0]}" || return 1
    validate_fastq_file "${paths[1]}" "${bytes[1]}" || return 1
  else
    validate_fastq_file "${paths[0]}" "${bytes[0]}" || return 1
  fi

  validate_kraken_outputs "${report}" "${out}" "${srr}"
}

process_paired() {
  local srr="$1"
  local url1="$2"
  local url2="$3"
  local bytes1="$4"
  local bytes2="$5"
  local fq1="${FASTQ_DIR}/${srr}_1.fastq.gz"
  local fq2="${FASTQ_DIR}/${srr}_2.fastq.gz"
  local report="${KRAKEN_OUT_DIR}/${srr}.report"
  local out="${KRAKEN_OUT_DIR}/${srr}.kraken"
  local started_at completed_at
  started_at="$(date -Iseconds)"

  if completed_before_run "${srr}" "paired" "${fq1}" "${fq2}" "${bytes1}" "${bytes2}"; then
    completed_at="$(date -Iseconds)"
    record_status "${srr}" "skipped_already_complete" "validated_present" "validated_present" "2" "${fq1};${fq2}" "${report}" "${out}" "${THREADS}" "${started_at}" "${completed_at}" "Validated pre-existing FASTQ and Kraken2 outputs."
    log_run "${srr}" "Pre-run validation shows ${srr} is already complete."
    return 0
  fi

  log_run "${srr}" "Starting paired recovery for ${srr}"
  record_status "${srr}" "running" "in_progress" "not_started" "2" "${fq1};${fq2}" "${report}" "${out}" "${THREADS}" "${started_at}" "" "Recovery started; validating or downloading FASTQ files."
  if ! recover_downloads "${srr}" "paired" "${url1}" "${url2}" "${bytes1}" "${bytes2}" "${fq1}" "${fq2}"; then
    completed_at="$(date -Iseconds)"
    record_status "${srr}" "download_failed" "failed" "not_started" "2" "${fq1};${fq2}" "${report}" "${out}" "${THREADS}" "${started_at}" "${completed_at}" "FASTQ recovery failed after URL retries and SRA Toolkit fallback."
    log_run "${srr}" "FASTQ recovery failed for ${srr}"
    return 1
  fi

  record_status "${srr}" "classification_running" "validated_present" "running" "2" "${fq1};${fq2}" "${report}" "${out}" "${THREADS}" "${started_at}" "" "FASTQ validation passed; Kraken2 classification in progress."
  if ! run_kraken_paired "${srr}" "${fq1}" "${fq2}"; then
    completed_at="$(date -Iseconds)"
    record_status "${srr}" "classification_failed" "validated_present" "failed" "2" "${fq1};${fq2}" "${report}" "${out}" "${THREADS}" "${started_at}" "${completed_at}" "Kraken2 classification failed or outputs did not validate."
    return 1
  fi

  completed_at="$(date -Iseconds)"
  record_status "${srr}" "completed" "validated_present" "completed" "2" "${fq1};${fq2}" "${report}" "${out}" "${THREADS}" "${started_at}" "${completed_at}" "Downloaded, validated, and classified successfully."
  log_run "${srr}" "Completed paired recovery for ${srr}"
  return 0
}

process_single() {
  local srr="$1"
  local url1="$2"
  local bytes1="$3"
  local fq1="${FASTQ_DIR}/${srr}_1.fastq.gz"
  local report="${KRAKEN_OUT_DIR}/${srr}.report"
  local out="${KRAKEN_OUT_DIR}/${srr}.kraken"
  local started_at completed_at
  started_at="$(date -Iseconds)"

  if completed_before_run "${srr}" "single" "${fq1}" "" "${bytes1}" ""; then
    completed_at="$(date -Iseconds)"
    record_status "${srr}" "skipped_already_complete" "validated_present" "validated_present" "1" "${fq1}" "${report}" "${out}" "${THREADS}" "${started_at}" "${completed_at}" "Validated pre-existing FASTQ and Kraken2 outputs."
    log_run "${srr}" "Pre-run validation shows ${srr} is already complete."
    return 0
  fi

  log_run "${srr}" "Starting single-end recovery for ${srr}"
  record_status "${srr}" "running" "in_progress" "not_started" "1" "${fq1}" "${report}" "${out}" "${THREADS}" "${started_at}" "" "Recovery started; validating or downloading FASTQ files."
  if ! recover_downloads "${srr}" "single" "${url1}" "" "${bytes1}" "" "${fq1}" ""; then
    completed_at="$(date -Iseconds)"
    record_status "${srr}" "download_failed" "failed" "not_started" "1" "${fq1}" "${report}" "${out}" "${THREADS}" "${started_at}" "${completed_at}" "FASTQ recovery failed after URL retries and SRA Toolkit fallback."
    log_run "${srr}" "FASTQ recovery failed for ${srr}"
    return 1
  fi

  record_status "${srr}" "classification_running" "validated_present" "running" "1" "${fq1}" "${report}" "${out}" "${THREADS}" "${started_at}" "" "FASTQ validation passed; Kraken2 classification in progress."
  if ! run_kraken_single "${srr}" "${fq1}"; then
    completed_at="$(date -Iseconds)"
    record_status "${srr}" "classification_failed" "validated_present" "failed" "1" "${fq1}" "${report}" "${out}" "${THREADS}" "${started_at}" "${completed_at}" "Kraken2 classification failed or outputs did not validate."
    return 1
  fi

  completed_at="$(date -Iseconds)"
  record_status "${srr}" "completed" "validated_present" "completed" "1" "${fq1}" "${report}" "${out}" "${THREADS}" "${started_at}" "${completed_at}" "Downloaded, validated, and classified successfully."
  log_run "${srr}" "Completed single-end recovery for ${srr}"
  return 0
}

pre_run_summary() {
  local completed=()
  local pending=()
  local zero_bytes=()
  local pairs=(
    "SRR12376372|paired|1611011798|1601499526"
    "SRR13342225|single|68319394|0"
    "SRR13396075|paired|17835622|19440313"
    "SRR13396103|single|68667967|0"
    "SRR1825760|single|10956806|0"
    "SRR23183348|paired|12914335|15673000"
    "SRR23183349|paired|7382003|9220251"
    "SRR23183368|paired|8392576|10944642"
    "SRR26201959|paired|46580083|48428890"
    "SRR26201960|paired|48657892|50483930"
    "SRR26201961|paired|88697488|92303192"
    "SRR33853917|paired|1388638284|1413550410"
    "SRR33963317|paired|4748173695|5307862583"
  )
  local entry srr layout bytes1 bytes2 fq1 fq2
  for entry in "${pairs[@]}"; do
    IFS='|' read -r srr layout bytes1 bytes2 <<< "${entry}"
    fq1="${FASTQ_DIR}/${srr}_1.fastq.gz"
    fq2="${FASTQ_DIR}/${srr}_2.fastq.gz"
    if [ -f "${fq1}" ] && [ ! -s "${fq1}" ]; then
      zero_bytes+=("${fq1}")
    fi
    if [ "${layout}" = "paired" ]; then
      if completed_before_run "${srr}" "paired" "${fq1}" "${fq2}" "${bytes1}" "${bytes2}"; then
        completed+=("${srr}")
      else
        pending+=("${srr}")
      fi
    else
      if completed_before_run "${srr}" "single" "${fq1}" "" "${bytes1}" ""; then
        completed+=("${srr}")
      else
        pending+=("${srr}")
      fi
    fi
  done

  log_msg "Restart summary:"
  log_msg "  Completed before this run: ${#completed[@]} (${completed[*]:-none})"
  log_msg "  Pending at restart: ${#pending[@]} (${pending[*]:-none})"
  log_msg "  Zero-byte placeholders detected: ${#zero_bytes[@]} (${zero_bytes[*]:-none})"
  if [ "${#pending[@]}" -gt 0 ]; then
    log_msg "  Restart point: ${pending[0]}"
  fi
}

run_queue() {
  local failures=0

  if should_run_srr "SRR12376372"; then process_paired "SRR12376372" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR123/072/SRR12376372/SRR12376372_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR123/072/SRR12376372/SRR12376372_2.fastq.gz" "1611011798" "1601499526" || failures=$((failures + 1)); fi
  if should_run_srr "SRR13342225"; then process_single "SRR13342225" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR133/025/SRR13342225/SRR13342225.fastq.gz" "68319394" || failures=$((failures + 1)); fi
  if should_run_srr "SRR13396075"; then process_paired "SRR13396075" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR133/075/SRR13396075/SRR13396075_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR133/075/SRR13396075/SRR13396075_2.fastq.gz" "17835622" "19440313" || failures=$((failures + 1)); fi
  if should_run_srr "SRR13396103"; then process_single "SRR13396103" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR133/003/SRR13396103/SRR13396103.fastq.gz" "68667967" || failures=$((failures + 1)); fi
  if should_run_srr "SRR1825760"; then process_single "SRR1825760" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR182/000/SRR1825760/SRR1825760.fastq.gz" "10956806" || failures=$((failures + 1)); fi
  if should_run_srr "SRR23183348"; then process_paired "SRR23183348" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR231/048/SRR23183348/SRR23183348_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR231/048/SRR23183348/SRR23183348_2.fastq.gz" "12914335" "15673000" || failures=$((failures + 1)); fi
  if should_run_srr "SRR23183349"; then process_paired "SRR23183349" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR231/049/SRR23183349/SRR23183349_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR231/049/SRR23183349/SRR23183349_2.fastq.gz" "7382003" "9220251" || failures=$((failures + 1)); fi
  if should_run_srr "SRR23183368"; then process_paired "SRR23183368" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR231/068/SRR23183368/SRR23183368_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR231/068/SRR23183368/SRR23183368_2.fastq.gz" "8392576" "10944642" || failures=$((failures + 1)); fi
  if should_run_srr "SRR26201959"; then process_paired "SRR26201959" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR262/059/SRR26201959/SRR26201959_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR262/059/SRR26201959/SRR26201959_2.fastq.gz" "46580083" "48428890" || failures=$((failures + 1)); fi
  if should_run_srr "SRR26201960"; then process_paired "SRR26201960" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR262/060/SRR26201960/SRR26201960_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR262/060/SRR26201960/SRR26201960_2.fastq.gz" "48657892" "50483930" || failures=$((failures + 1)); fi
  if should_run_srr "SRR26201961"; then process_paired "SRR26201961" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR262/061/SRR26201961/SRR26201961_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR262/061/SRR26201961/SRR26201961_2.fastq.gz" "88697488" "92303192" || failures=$((failures + 1)); fi
  if should_run_srr "SRR33853917"; then process_paired "SRR33853917" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR338/017/SRR33853917/SRR33853917_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR338/017/SRR33853917/SRR33853917_2.fastq.gz" "1388638284" "1413550410" || failures=$((failures + 1)); fi
  if should_run_srr "SRR33963317"; then process_paired "SRR33963317" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR339/017/SRR33963317/SRR33963317_1.fastq.gz" "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR339/017/SRR33963317/SRR33963317_2.fastq.gz" "4748173695" "5307862583" || failures=$((failures + 1)); fi

  return "${failures}"
}

should_run_srr() {
  local srr="$1"
  if [ -z "${ONLY_SRRS:-}" ]; then
    return 0
  fi
  case ",${ONLY_SRRS}," in
    *,"${srr}",*) return 0 ;;
    *) return 1 ;;
  esac
}

summarize_results() {
  python3 - "${SUMMARY_CSV}" <<'PY'
import csv
import sys
from collections import Counter
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("No run recovery status CSV found.")
    sys.exit(0)

with path.open("r", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

counter = Counter(row.get("overall_status", "") for row in rows)
print("Recovery queue summary:")
for key in sorted(counter):
    print(f"  {key}: {counter[key]}")
pending = [row["srr_id"] for row in rows if row.get("overall_status") not in {"completed", "skipped_already_complete"}]
print(f"  remaining_noncomplete: {len(pending)}")
if pending:
    print(f"  pending_ids: {', '.join(pending)}")
PY
}

write_status_header
if ! ensure_prereqs; then
  log_msg "Prerequisite validation failed. Aborting recovery queue."
  exit 1
fi
pre_run_summary
run_queue
queue_failures=$?
summarize_results | tee -a "${MASTER_LOG}"
if [ "${queue_failures}" -gt 0 ]; then
  log_msg "Recovery queue finished with ${queue_failures} SRR-level failures that require review."
  exit 1
fi
log_msg "Recovery queue finished without SRR-level failures."
