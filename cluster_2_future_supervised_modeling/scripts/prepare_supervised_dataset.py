"""Template gate for future supervised-dataset assembly.

Future workflow -- not yet executable until real metadata and labels are added.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


CLUSTER_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = CLUSTER_ROOT / "data"
REQUIRED_TARGET_COLUMNS = ["known_crop_outcome", "crop_grown", "crop_suitability_label"]


def main() -> None:
    merged_template = DATA_DIR / "future_merged_table_template.csv"
    if not merged_template.exists():
        raise SystemExit(
            "Future workflow -- not yet executable until real metadata and labels are added. "
            "Expected template: cluster_2_future_supervised_modeling/data/future_merged_table_template.csv"
        )
    frame = pd.read_csv(merged_template)
    observed_targets = [column for column in REQUIRED_TARGET_COLUMNS if column in frame.columns and frame[column].notna().any()]
    if not observed_targets:
        raise SystemExit(
            "Supervised dataset preparation is blocked. No directly observed crop target is populated in the merged template."
        )
    raise SystemExit(
        "A real target column has been detected, but this template script is only a scaffold. Replace it with a leakage-safe "
        "dataset builder before training any model."
    )


if __name__ == "__main__":
    main()
