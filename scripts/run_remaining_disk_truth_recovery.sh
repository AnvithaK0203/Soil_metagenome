#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PROJECT_ROOT}/.wsl_venv/bin/python"
RUNNER="${PROJECT_ROOT}/scripts/wsl_recover_missing_srrs.sh"
THREADS="${KRAKEN_THREADS:-12}"
IO_THREADS="${RECOVERY_IO_THREADS:-4}"
USE_MEMORY_MAPPING="${KRAKEN_USE_MEMORY_MAPPING:-1}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BATCH_LOG="${PROJECT_ROOT}/logs/wsl_recovery/batch_resume_${TIMESTAMP}.log"

mkdir -p "${PROJECT_ROOT}/logs/wsl_recovery"

exec > >(tee -a "${BATCH_LOG}") 2>&1

echo "[batch] started at $(date -u --iso-8601=seconds)"
echo "[batch] project_root=${PROJECT_ROOT}"
echo "[batch] runner=${RUNNER}"
echo "[batch] python=${PYTHON_BIN}"
echo "[batch] kraken_threads=${THREADS}"
echo "[batch] io_threads=${IO_THREADS}"
echo "[batch] memory_mapping=${USE_MEMORY_MAPPING}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "[batch] missing WSL python environment at ${PYTHON_BIN}" >&2
  exit 1
fi
if [[ ! -x "${RUNNER}" ]]; then
  echo "[batch] missing recovery runner at ${RUNNER}" >&2
  exit 1
fi

mapfile -t QUEUE < <(
  "${PYTHON_BIN}" - <<'PY'
import pandas as pd
srr = pd.read_csv("srr_audit_report.csv")
missing = srr.loc[srr["still_missing"].fillna(False), "srr_id"].tolist()
for srr_id in missing:
    print(srr_id)
PY
)

echo "[batch] remaining queue count=${#QUEUE[@]}"
if [[ "${#QUEUE[@]}" -eq 0 ]]; then
  echo "[batch] no missing SRRs remain"
  exit 0
fi
printf '[batch] queue=%s\n' "${QUEUE[*]}"

validate_srr() {
  local srr="$1"
  local report_path="${PROJECT_ROOT}/kraken_out/${srr}.report"
  local kraken_path="${PROJECT_ROOT}/kraken_out/${srr}.kraken"
  shopt -s nullglob
  local fastqs=("${PROJECT_ROOT}"/raw_data/recovered_fastq/${srr}*.fastq.gz)
  shopt -u nullglob

  if [[ ! -s "${report_path}" ]]; then
    echo "[batch] validation failed for ${srr}: missing or empty report ${report_path}" >&2
    return 1
  fi
  if [[ ! -s "${kraken_path}" ]]; then
    echo "[batch] validation failed for ${srr}: missing or empty kraken output ${kraken_path}" >&2
    return 1
  fi
  if [[ "${#fastqs[@]}" -lt 1 ]]; then
    echo "[batch] validation failed for ${srr}: no FASTQ files found" >&2
    return 1
  fi
  if ! grep -q "${srr}" "${kraken_path}"; then
    echo "[batch] validation failed for ${srr}: kraken output does not contain expected SRR id" >&2
    return 1
  fi
  gzip -t "${fastqs[@]}"
  echo "[batch] validation passed for ${srr}: ${#fastqs[@]} FASTQ file(s)"
}

refresh_manifests() {
  "${PYTHON_BIN}" scripts/clean_data.py
  "${PYTHON_BIN}" scripts/execute_srr_recovery.py
  "${PYTHON_BIN}" scripts/disk_truth_reaudit.py
}

show_counts() {
  "${PYTHON_BIN}" - <<'PY'
import pandas as pd
srr = pd.read_csv("srr_audit_report.csv")
processed = int((srr["local_processed_presence"] == "present").sum())
missing = int(srr["still_missing"].fillna(False).sum())
print(f"[batch] counts processed_present={processed} still_missing={missing}")
PY
}

failures=0
for srr in "${QUEUE[@]}"; do
  echo
  echo "[batch] ===== ${srr} ====="
  status=0
  ONLY_SRRS="${srr}" \
  KRAKEN_THREADS="${THREADS}" \
  RECOVERY_IO_THREADS="${IO_THREADS}" \
  KRAKEN_USE_MEMORY_MAPPING="${USE_MEMORY_MAPPING}" \
  "${RUNNER}" || status=$?

  if validate_srr "${srr}"; then
    refresh_manifests
    show_counts
  else
    echo "[batch] ${srr} remains incomplete after runner exit_code=${status}" >&2
    failures=$((failures + 1))
  fi
done

echo
echo "[batch] final summary"
show_counts
if [[ "${failures}" -gt 0 ]]; then
  echo "[batch] failures=${failures}" >&2
  exit 1
fi
echo "[batch] finished cleanly"
