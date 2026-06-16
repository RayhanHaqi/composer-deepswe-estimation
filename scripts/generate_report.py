#!/usr/bin/env python3
"""Generate a Markdown report for Composer 2.5 DeepSWE estimation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import pandas as pd

from common import COMPOSER_MODEL, ensure_parent, repo_root, summarize_uncertainty


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Composer DeepSWE estimation report")
    parser.add_argument(
        "--input",
        type=Path,
        default=repo_root() / "data" / "processed" / "normalized_results.csv",
        help="Normalized results CSV",
    )
    parser.add_argument(
        "--estimates",
        type=Path,
        default=repo_root() / "results" / "estimates.csv",
        help="Method estimates CSV",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=repo_root() / "results" / "summary.json",
        help="Summary JSON from estimate_composer.py",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=repo_root() / "figures",
        help="Directory containing plot PNGs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root() / "reports" / "composer_deepswe_estimate.md",
        help="Output Markdown report path",
    )
    return parser.parse_args()


def _df_markdown(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except ImportError:
        cols = list(df.columns)
        lines = [
            "| " + " | ".join(cols) + " |",
            "| " + " | ".join("---" for _ in cols) + " |",
        ]
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        return "\n".join(lines)


def build_report(
    normalized: pd.DataFrame,
    estimates: pd.DataFrame,
    summary: dict,
    figures_dir: Path,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    med = summary["median_estimate_pass_rate"]
    lo = summary["min_estimate_pass_rate"]
    hi = summary["max_estimate_pass_rate"]
    mean = summary["mean_estimate_pass_rate"]
    n_overlap = summary.get("overlap_pair_count", "n/a")
    cursor_score = summary.get("composer_cursorbench_score", "n/a")

    bench_counts = normalized["benchmark_name"].value_counts().to_dict()
    figure_names = [
        "cost_vs_pass_rate.png",
        "method_estimates.png",
        "composer_vs_models.png",
    ]
    figure_lines = []
    for name in figure_names:
        rel = figures_dir / name
        if rel.is_file():
            figure_lines.append(f"![{name}](../figures/{name})")
        else:
            figure_lines.append(f"_(Figure not found: `figures/{name}` — run plot_results.py)_")

    method_table = estimates[
        ["method_name", "estimated_pass_rate", "estimated_cost_usd", "assumptions"]
    ].copy()
    method_table["estimated_pass_rate"] = method_table["estimated_pass_rate"].map(
        lambda v: f"{float(v):.1f}%"
    )

    lines = [
        "# Composer 2.5 DeepSWE estimate (unofficial)",
        "",
        f"_Generated: {ts}_",
        "",
        "> **Disclaimer:** This is an unofficial, reproducible **estimate**, not an official "
        "DeepSWE benchmark submission. Composer 2.5 has no public DeepSWE trials. "
        "Figures and ranges describe method disagreement, not formal confidence intervals.",
        "",
        "## Summary",
        "",
        f"Composer 2.5 scores **{cursor_score}%** on CursorBench 3.1 (public reference) but "
        f"has **no measured DeepSWE Pass@1**. Linking **{n_overlap}** overlapping model-effort "
        f"pairs yields a DeepSWE pass-rate estimate cluster with **median {med:.1f}%**, "
        f"**mean {mean:.1f}%**, and **method spread {lo:.1f}–{hi:.1f}%** "
        f"({summary['method_count']} methods).",
        "",
        "## Data sources",
        "",
        f"- Normalized rows by benchmark: `{bench_counts}`",
        "- DeepSWE rows: recomputed from public `trials.json` when provided (Pass@1, equal task weight).",
        "- CursorBench rows: public CursorBench 3.1 reference table in `data/raw/`.",
        "- Composer cost on charts uses a **CursorBench cost proxy**, not measured DeepSWE spend.",
        "",
        "## Estimation methods",
        "",
        _df_markdown(method_table),
        "",
        "## Estimated range",
        "",
        f"| Statistic | Pass rate (%) |",
        f"| --- | ---: |",
        f"| Minimum across methods | {lo:.1f} |",
        f"| Maximum across methods | {hi:.1f} |",
        f"| Mean across methods | {mean:.1f} |",
        f"| Median across methods | {med:.1f} |",
        "",
        summary.get(
            "uncertainty_note",
            "Method spread is not a formal confidence interval.",
        ),
        "",
        "## Caveats",
        "",
        "- Small overlap sets make linking fragile; one outlier pair can move several methods.",
        "- CursorBench and DeepSWE use different harnesses and task mixes.",
        "- Effort labels are aligned heuristically between leaderboards.",
        "- Do not treat the estimate as an official Composer 2.5 DeepSWE score.",
        "",
        "## Figures",
        "",
        *figure_lines,
        "",
        "## Reproducibility",
        "",
        "From the repository root:",
        "",
        "```bash",
        "python scripts/parse_results.py --input-dir data/raw --output data/processed/normalized_results.csv",
        "python scripts/estimate_composer.py --input data/processed/normalized_results.csv --output-dir results/",
        "python scripts/plot_results.py --input data/processed/normalized_results.csv --estimates results/estimates.csv --output-dir figures/",
        "python scripts/generate_report.py --input data/processed/normalized_results.csv --output reports/composer_deepswe_estimate.md",
        "```",
        "",
        "See `methodology.md` and `limitations.md` for full context.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    for path, label in (
        (args.input, "input"),
        (args.estimates, "estimates"),
    ):
        if not path.is_file():
            print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
            return 1

    normalized = pd.read_csv(args.input)
    estimates = pd.read_csv(args.estimates)

    if args.summary.is_file():
        summary = json.loads(args.summary.read_text(encoding="utf-8"))
    else:
        summary = summarize_uncertainty(estimates)

    report = build_report(normalized, estimates, summary, args.figures_dir)
    ensure_parent(args.output)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
