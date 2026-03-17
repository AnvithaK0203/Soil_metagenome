#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PROJECT_ROOT}/.wsl_venv/bin/python"
FINAL_LOG="${PROJECT_ROOT}/logs/wsl_recovery/finalize_after_last_srr.log"
TARGET_SRR="${1:-SRR33963317}"

mkdir -p "${PROJECT_ROOT}/logs/wsl_recovery"
exec > >(tee -a "${FINAL_LOG}") 2>&1

echo "[finalize] started at $(date -u --iso-8601=seconds)"
echo "[finalize] waiting for ${TARGET_SRR} recovery processes to finish"

while ps -eo cmd | grep -E "run_remaining_disk_truth_recovery|wsl_recover_missing_srrs|${TARGET_SRR}|/usr/lib/kraken2/classify" | grep -v grep >/dev/null; do
  ts="$(date -u --iso-8601=seconds)"
  kraken_size="$(stat -c%s "kraken_out/${TARGET_SRR}.kraken" 2>/dev/null || echo 0)"
  report_size="$(stat -c%s "kraken_out/${TARGET_SRR}.report" 2>/dev/null || echo 0)"
  echo "[finalize] ${ts} waiting: kraken_size=${kraken_size} report_size=${report_size}"
  sleep 120
done

echo "[finalize] recovery process for ${TARGET_SRR} is no longer running"

"${PYTHON_BIN}" scripts/clean_data.py
"${PYTHON_BIN}" scripts/execute_srr_recovery.py
"${PYTHON_BIN}" scripts/disk_truth_reaudit.py
"${PYTHON_BIN}" scripts/rebuild_final_dataset.py
"${PYTHON_BIN}" scripts/inspect_datasets.py
"${PYTHON_BIN}" scripts/reassess_feasibility.py

echo "[finalize] rebuilt manifests and final reports at $(date -u --iso-8601=seconds)"
