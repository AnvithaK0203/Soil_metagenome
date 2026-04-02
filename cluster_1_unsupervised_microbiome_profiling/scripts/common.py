"""Shared helpers for the project recovery scripts."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SRR_PATTERN = re.compile(r"SRR\d+")
TEXT_EXTENSIONS = {".md", ".txt", ".csv", ".tsv", ".py", ".ipynb", ".json", ".yaml", ".yml", ".log"}


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_project_root(path: str | None = None) -> Path:
    if path:
        return Path(path).expanduser().resolve()
    return default_project_root()


def resolve_output_dir(project_root: Path, path: str | None = None) -> Path:
    if path:
        output_dir = Path(path).expanduser()
        if not output_dir.is_absolute():
            output_dir = project_root / output_dir
        return output_dir.resolve()
    return project_root


def add_standard_args(parser: argparse.ArgumentParser, log_name: str) -> None:
    parser.add_argument("--input-root", default=None, help="Project root to audit.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write outputs into. Defaults to the project root.",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help=f"Optional log file path. Defaults to logs/{log_name}.",
    )


def make_log_path(project_root: Path, value: str | None, log_name: str) -> Path:
    if value:
        log_path = Path(value).expanduser()
        if not log_path.is_absolute():
            log_path = project_root / log_path
        return log_path.resolve()
    return (project_root / "logs" / log_name).resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_log(log_path: Path, message: str) -> None:
    ensure_parent(log_path)
    stamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def iter_files(root: Path, extensions: Iterable[str] | None = None) -> list[Path]:
    allowed = {ext.lower() for ext in extensions} if extensions else None
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if allowed is not None and path.suffix.lower() not in allowed:
            continue
        paths.append(path)
    return sorted(paths)


def read_text_like(path: Path) -> str:
    if path.suffix.lower() == ".ipynb":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return path.read_text(encoding="utf-8", errors="ignore")
        chunks: list[str] = []
        for cell in data.get("cells", []):
            chunks.append("".join(cell.get("source", [])))
            for output in cell.get("outputs", []):
                text = output.get("text")
                if text:
                    chunks.append("".join(text))
                data_block = output.get("data", {})
                plain_text = data_block.get("text/plain")
                if plain_text:
                    chunks.append("".join(plain_text))
        return "\n".join(chunks)
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_srr_ids(text: str) -> list[str]:
    return sorted(set(SRR_PATTERN.findall(text)))


def infer_column_category(column_name: str) -> str:
    name = column_name.strip()
    lowered = name.lower()
    metadata_tokens = (
        "geo_loc_name",
        "lat_lon",
        "env_medium",
        "env_local_scale",
        "collection_date",
        "env_broad_scale",
        "depth",
        "elev",
        "soil_type",
        "host",
        "isolation_source",
    )
    if lowered.startswith("candidate_label_"):
        return "other"
    if any(
        token in lowered
        for token in (
            "source_file",
            "recovery_attempt_status",
            "local_processed_presence",
            "has_local_",
            "has_remote_",
            "still_missing",
            "blocked",
            "row_unit",
            "checkpoint_status",
        )
    ):
        return "provenance"
    if lowered in {"sample", "biosample", "run", "accession"} or lowered.endswith("_id"):
        return "id"
    if "|" in name:
        return "microbial_feature"
    if any(token in lowered for token in ("crop", "label", "target", "class", "suitability")):
        return "label_candidate"
    if any(token in lowered for token in metadata_tokens) or lowered in {"country", "state", "district"}:
        return "metadata"
    return "other"


def infer_column_description(column_name: str) -> str:
    category = infer_column_category(column_name)
    if category == "id":
        return "Identifier column for the sample or accession."
    if category == "label_candidate":
        return "Potential supervised-learning label or grouping variable."
    if category == "metadata":
        return "Observed contextual metadata carried with the sample."
    if category == "provenance":
        return "Provenance or workflow status column added during recovery."
    if category == "microbial_feature":
        if "|" in column_name:
            rank, _, label = column_name.partition("|")
            return f"Taxonomic abundance feature at rank '{rank}' for '{label}'."
        return "Microbial abundance feature."
    return "Unclassified column carried from the source dataset."


def rank_prefix(column_name: str) -> str | None:
    if "|" not in column_name:
        return None
    prefix = column_name.split("|", 1)[0]
    return prefix or None


def normalize_sample_id(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()
