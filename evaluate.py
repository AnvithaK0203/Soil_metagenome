"""Summarize model evaluation artifacts when they exist."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import add_standard_args, append_log, default_project_root, ensure_parent, make_log_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_args(parser, "evaluate.log")
    parser.add_argument(
        "--metrics-file",
        default="outputs/model_metrics.json",
        help="Expected metrics file produced by a future modeling run.",
    )
    args = parser.parse_args()

    project_root = default_project_root() if args.input_root is None else Path(args.input_root).expanduser().resolve()
    output_dir = project_root if args.output_dir is None else Path(args.output_dir).expanduser().resolve()
    log_path = make_log_path(project_root, args.log_file, "evaluate.log")
    metrics_path = project_root / args.metrics_file
    report_path = output_dir / "outputs" / "evaluation_summary.md"
    ensure_parent(report_path)

    if not metrics_path.exists():
        report_path.write_text(
            "\n".join(
                [
                    "# Evaluation Summary",
                    "",
                    "No model evaluation was generated in this recovery pass because the modeling gate did not pass.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        append_log(log_path, "No evaluation metrics were present; wrote a no-evaluation summary.")
        return

    report_path.write_text(
        "\n".join(
            [
                "# Evaluation Summary",
                "",
                f"A metrics file exists at `{metrics_path}` and should be reviewed manually.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    append_log(log_path, f"Metrics file detected at {metrics_path}")


if __name__ == "__main__":
    main()
