"""Reassess scientific feasibility after the latest recovery pass."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import add_standard_args, append_log, default_project_root, infer_column_category, make_log_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "reassess_feasibility.log")
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "reassess_feasibility.log")

    srr_path = project_root / "srr_audit_report.csv"
    manifest_path = project_root / "processed_data" / "sample_manifest.csv"
    final_dataset_path = project_root / "processed_data" / "final_merged_dataset_preview.csv"

    srr_df = pd.read_csv(srr_path)
    manifest_df = pd.read_csv(manifest_path)
    final_df = pd.read_csv(final_dataset_path)

    expected_count = len(srr_df)
    processed_count = int((srr_df["local_processed_presence"] == "present").sum())
    metadata_local_count = int((srr_df["metadata_presence"] == "present").sum())
    metadata_remote_count = int(srr_df["remote_sample_metadata_available"].fillna(False).sum())
    missing_processed_count = int(srr_df["still_missing"].fillna(False).sum())

    label_cols = [col for col in final_df.columns if infer_column_category(col) == "label_candidate"]
    microbe_cols = [col for col in final_df.columns if infer_column_category(col) == "microbial_feature"]
    metadata_cols = [col for col in final_df.columns if infer_column_category(col) == "metadata"]

    if label_cols:
        label_status = f"Observed label columns detected: {', '.join(label_cols)}"
    else:
        label_status = "No directly observed crop or suitability label column exists after reconstruction."

    if missing_processed_count == 0:
        missing_lines = [
            "- All expected SRRs now have local processed outputs in this recovery pass.",
            "- A directly observed crop label is still absent.",
            "- Even with full local SRR processing, the metadata remains insufficient for supervised crop prediction.",
        ]
        next_step_lines = [
            "- Freeze the biological recovery as complete and continue only with exploratory microbiome plus metadata analysis unless primary label data is added.",
        ]
        cannot_claim_lines = [
            "- It still cannot claim crop prediction or crop recommendation readiness.",
            "- It still cannot claim a validated soil health index.",
        ]
        final_status_missing_claim = "- Missing locally processed SRRs: 0"
        final_status_next_step = "- Treat the current dataset as exploratory only unless a defensible observed target is added."
        rebuild_phase_2_lines = [
            "- Biological SRR recovery is complete for the expected local run set in this snapshot.",
            "- Re-merge taxonomy outputs only from validated processed files and preserve the current manifests as the recovery baseline.",
        ]
        modeling_risk_lines = [
            f"- The current ratio of {len(microbe_cols)} microbial features to {processed_count} processed samples is not appropriate for confident prediction.",
            "- Full SRR recovery improves completeness, but the dataset is still too small and label-poor for predictive claims.",
        ]
        incomplete_extraction_lines = [
            "- 0 expected SRRs still lack local processed outputs.",
            "- Biological recovery is complete for the expected SRR list recovered from the local project evidence.",
        ]
        modeling_gate_line = "- Do not train a crop or suitability model until a directly observed target exists and the feature space is reduced to a defensible scale."
    else:
        missing_lines = [
            f"- {missing_processed_count} expected SRRs are still not classified locally.",
            "- No observed crop label has been recovered.",
            "- Missing SRRs may materially change the taxonomic distribution and any downstream interpretation.",
        ]
        next_step_lines = [
            f"- Either complete WSL-based Kraken2 recovery for the missing {missing_processed_count} SRRs or freeze the project scope to exploratory microbiome plus metadata analysis.",
        ]
        cannot_claim_lines = [
            "- It still cannot claim full SRR completeness.",
            "- It still cannot claim crop prediction or crop recommendation readiness.",
            "- It still cannot claim a validated soil health index.",
        ]
        final_status_missing_claim = f"- Missing locally processed SRRs: {missing_processed_count}"
        final_status_next_step = (
            f"- Treat the current dataset as exploratory only unless the missing {missing_processed_count} SRRs are processed and a defensible observed target is added."
        )
        rebuild_phase_2_lines = [
            "- Use the generated WSL recovery helper to download and classify the remaining missing SRRs if full dataset recovery is required.",
            "- Re-merge taxonomy outputs only after the remaining runs are classified.",
        ]
        modeling_risk_lines = [
            f"- The current ratio of {len(microbe_cols)} microbial features to {processed_count} processed samples is not appropriate for confident prediction.",
            "- Missing SRRs mean the observed microbiome distribution is incomplete.",
        ]
        incomplete_extraction_lines = [
            f"- {missing_processed_count} expected SRRs still lack local processed outputs.",
            "- Full biological completeness now depends on WSL-based download and Kraken2 classification or an equivalent Linux workflow.",
        ]
        modeling_gate_line = "- Do not train a crop or suitability model until a directly observed target exists and the missing SRRs are processed."

    feasibility_lines = [
        "# Post-Recovery Feasibility Report",
        "",
        "## What was found",
        "",
        f"- Expected SRRs: {expected_count}",
        f"- Locally processed SRRs: {processed_count}",
        f"- Locally metadata-merged SRRs: {metadata_local_count}",
        f"- SRRs with remote sample metadata recovered from ENA: {metadata_remote_count}",
        f"- Missing processed SRRs: {missing_processed_count}",
        f"- Final merged preview rows: {len(final_df)}",
        f"- Microbial feature columns in the final merged preview: {len(microbe_cols)}",
        f"- Metadata columns in the final merged preview: {len(metadata_cols)}",
        "",
        "## Scientific Answers",
        "",
        "- One sample is currently defined as one SRR sequencing run.",
        f"- Label status: {label_status}",
        f"- Sample size sufficiency: {processed_count} processed samples is too small for defensible crop prediction.",
        "- Metadata sufficiency: remote metadata enrichment improves context, but it still does not supply a validated crop target or full soil chemistry.",
        "- Leakage risk: high if any label were inferred from accession, study, geography, or sample title rather than observed field measurements.",
        f"- High-dimensionality risk: {len(microbe_cols)} microbial features over {processed_count} processed samples remains severely underpowered.",
        "- Crop prediction ambition: still too ambitious for the current recovered state.",
        "",
        "## Decision",
        "",
        "- Crop prediction: not scientifically justified.",
        "- Crop recommendation: not scientifically justified.",
        "- Soil health index development: only as a cautious exploratory prototype after feature aggregation, not as a validated index.",
        "- Exploratory analysis only: justified.",
        "- Proof-of-concept baseline only: possible only after a real observed target exists.",
        "",
        "## What remains blocked or uncertain",
        "",
        *missing_lines,
        "",
        "## What the next immediate step is",
        "",
        *next_step_lines,
    ]
    (output_dir / "outputs" / "post_recovery_feasibility_report.md").write_text(
        "\n".join(feasibility_lines) + "\n", encoding="utf-8"
    )

    final_status_lines = [
        "# Final Project Status Summary",
        "",
        "## What the project can claim now",
        "",
        f"- The project now has a reproducible recovery toolkit running in a local `.venv`.",
        f"- A best-available local Kraken2 feature matrix exists for {processed_count} SRR sequencing runs.",
        f"- Remote ENA metadata was recovered for {metadata_remote_count} expected SRRs.",
        "- A final sample-level merged preview dataset has been rebuilt with explicit provenance columns.",
        "",
        "## What the project cannot claim now",
        "",
        *cannot_claim_lines,
        "",
        "## ML Feasibility",
        "",
        "- Supervised ML remains blocked because no valid observed crop or suitability target exists.",
        "- The processed sample count remains too small relative to the microbial feature space for strong predictive claims.",
        "",
        "## SRR Recovery Status",
        "",
        f"- Expected SRRs: {expected_count}",
        f"- Locally processed SRRs: {processed_count}",
        f"- Locally metadata-merged SRRs: {metadata_local_count}",
        f"- Remotely metadata-enriched SRRs: {metadata_remote_count}",
        final_status_missing_claim,
        "",
        "## Best Next Step",
        "",
        final_status_next_step,
    ]
    (output_dir / "final_project_status_summary.md").write_text("\n".join(final_status_lines) + "\n", encoding="utf-8")

    assumptions_lines = [
        "# Assumptions and Risks",
        "",
        "## Assumptions",
        "",
        "- One row remains one SRR sequencing run unless a later consolidation manifest proves otherwise.",
        "- ENA metadata is treated as secondary provenance and not a replacement for primary local lab metadata.",
        "",
        "## Scientific Uncertainties",
        "",
        "- No validated crop target or suitability label is present after reconstruction.",
        "- Soil physicochemical features remain absent in the local dataset.",
        "",
        "## Leakage Risks",
        "",
        "- Sample titles, geography, accession IDs, and study identifiers could become leakage proxies if used as targets or as near-target features.",
        "",
        "## Modeling Risks",
        "",
        *modeling_risk_lines,
        "",
        "## Small-Sample Risks",
        "",
        "- Any model trained now would be unstable and proof-of-concept only.",
        "",
        "## Incomplete Extraction Risks",
        "",
        *incomplete_extraction_lines,
    ]
    (output_dir / "assumptions_and_risks.md").write_text("\n".join(assumptions_lines) + "\n", encoding="utf-8")

    rebuild_plan_lines = [
        "# Project Rebuild Plan",
        "",
        "## Phase 1 - Freeze Current Evidence",
        "",
        "- Preserve the current root snapshot and the regenerated recovery outputs.",
        "",
        "## Phase 2 - Complete Missing SRR Processing",
        "",
        *rebuild_phase_2_lines,
        "",
        "## Phase 3 - Metadata and Label Intake",
        "",
        "- Seek primary crop, soil chemistry, and agronomic label sources before any supervised modeling.",
        "- Keep ENA-derived metadata as context only unless validated against primary project records.",
        "",
        "## Phase 4 - Exploratory Analysis",
        "",
        "- Prioritize descriptive microbiome profiling, diversity metrics, and defensible feature aggregation.",
        "",
        "## Phase 5 - Modeling Gate",
        "",
        modeling_gate_line,
    ]
    (output_dir / "project_rebuild_plan.md").write_text("\n".join(rebuild_plan_lines) + "\n", encoding="utf-8")

    model_no_go_lines = [
        "# Baseline Modeling Status",
        "",
        "Baseline modeling remains blocked after the post-recovery reassessment.",
        "",
        "- No directly observed crop or suitability target is present.",
        f"- Only {processed_count} SRRs are processed locally, with {missing_processed_count} still missing.",
        f"- The feature space remains very high-dimensional ({len(microbe_cols)} microbial features).",
        "- The project is currently defensible as exploratory analysis, not predictive modeling.",
    ]
    (output_dir / "outputs" / "model_no_go_report.md").write_text("\n".join(model_no_go_lines) + "\n", encoding="utf-8")

    append_log(log_path, "Updated feasibility reports and no-go status.")


if __name__ == "__main__":
    main()
