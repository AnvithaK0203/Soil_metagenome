"""Template for future metadata integration.

Future workflow -- not yet executable until real metadata and labels are added.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


CLUSTER_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = CLUSTER_ROOT / "data"
EXPECTED_METADATA_COLUMNS = [
    "sample",
    "soil_pH",
    "nitrogen_mg_kg",
    "phosphorus_mg_kg",
    "potassium_mg_kg",
    "moisture_percent",
    "temperature_c",
    "known_crop_outcome",
    "crop_grown",
    "crop_suitability_label",
]


def validate_metadata_schema(frame: pd.DataFrame) -> list[str]:
    return [column for column in EXPECTED_METADATA_COLUMNS if column not in frame.columns]


def main() -> None:
    metadata_path = DATA_DIR / "future_metadata_template.csv"
    if not metadata_path.exists():
        raise SystemExit(
            "Future workflow -- not yet executable until real metadata and labels are added. "
            "Expected template: cluster_2_future_supervised_modeling/data/future_metadata_template.csv"
        )
    frame = pd.read_csv(metadata_path)
    missing = validate_metadata_schema(frame)
    if missing:
        raise SystemExit(f"Metadata template is missing required columns: {', '.join(missing)}")
    raise SystemExit(
        "Schema check passed, but supervised metadata merging remains blocked until the blank template is replaced "
        "with real sample-level measurements and observed crop outcomes."
    )


if __name__ == "__main__":
    main()
