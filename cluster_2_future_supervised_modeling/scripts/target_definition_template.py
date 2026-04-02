"""Template checks for future target definition.

Future workflow -- not yet executable until real metadata and labels are added.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


CLUSTER_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = CLUSTER_ROOT / "data"
ACCEPTABLE_TARGETS = {
    "known_crop_outcome": "Observed crop outcome measured after sampling.",
    "crop_grown": "Observed crop actually grown at or after the sampled location and time.",
    "crop_suitability_label": "Externally curated suitability label from a defined agronomic protocol.",
}


def main() -> None:
    template_path = DATA_DIR / "future_metadata_template.csv"
    if not template_path.exists():
        raise SystemExit("Future workflow -- metadata template not found.")
    frame = pd.read_csv(template_path)
    populated = [column for column in ACCEPTABLE_TARGETS if column in frame.columns and frame[column].notna().any()]
    if not populated:
        raise SystemExit(
            "No observed target is populated. Do not create labels from geography, accession ID, or unsupervised cluster membership."
        )
    raise SystemExit(
        "A candidate target column is populated. Review target leakage, class balance, and observation protocol before enabling "
        "any supervised workflow."
    )


if __name__ == "__main__":
    main()
