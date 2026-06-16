#!/usr/bin/env python3
"""Estimate Composer 2.5 DeepSWE performance from normalized benchmark data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import pandas as pd

from common import (
    COMPOSER_CURSOR_COST,
    COMPOSER_CURSOR_SCORE,
    COMPOSER_MODEL,
    build_overlap,
    ensure_parent,
    estimate_composer_methods,
    repo_root,
    summarize_uncertainty,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate Composer 2.5 DeepSWE pass rate from normalized results"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=repo_root() / "data" / "processed" / "normalized_results.csv",
        help="Normalized results CSV from parse_results.py",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root() / "results",
        help="Directory for estimates.csv and summary.json",
    )
    parser.add_argument(
        "--composer-score",
        type=float,
        default=COMPOSER_CURSOR_SCORE,
        help="Composer CursorBench anchor score (%%)",
    )
    parser.add_argument(
        "--composer-cost",
        type=float,
        default=COMPOSER_CURSOR_COST,
        help="Composer CursorBench cost proxy (USD per task)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.is_file():
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        return 1

    normalized = pd.read_csv(args.input)
    required = {"benchmark_name", "model_norm", "effort_norm", "pass_rate"}
    missing = required - set(normalized.columns)
    if missing:
        print(
            f"ERROR: input missing required columns: {sorted(missing)}",
            file=sys.stderr,
        )
        return 1

    composer_rows = normalized[
        (normalized["model_norm"] == COMPOSER_MODEL)
        & (normalized["benchmark_name"] == "cursorbench")
    ]
    composer_score = args.composer_score
    composer_cost = args.composer_cost
    if not composer_rows.empty:
        composer_score = float(composer_rows.iloc[0]["pass_rate"])
        cost_val = composer_rows.iloc[0].get("cost_usd")
        if pd.notna(cost_val):
            composer_cost = float(cost_val)

    try:
        overlap = build_overlap(normalized)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    estimates = estimate_composer_methods(
        overlap,
        composer_cursor_score=composer_score,
        composer_cursor_cost=composer_cost,
    )
    summary = summarize_uncertainty(estimates)
    summary["composer_model"] = COMPOSER_MODEL
    summary["composer_cursorbench_score"] = composer_score
    summary["composer_cost_proxy_usd"] = composer_cost
    summary["overlap_pair_count"] = int(len(overlap))
    summary["disclaimer"] = (
        "Unofficial estimate. Composer 2.5 has no DeepSWE trials in public artifacts."
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    overlap_path = args.output_dir / "overlap_pairs.csv"
    estimates_path = args.output_dir / "estimates.csv"
    summary_path = args.output_dir / "summary.json"

    overlap.to_csv(overlap_path, index=False)
    estimates.to_csv(estimates_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"Overlap pairs: {len(overlap)} → {overlap_path}")
    print(f"Method estimates: {len(estimates)} → {estimates_path}")
    print(
        f"Summary: central={summary['core_mean_estimate_pass_rate']:.1f}% "
        f"median={summary['median_estimate_pass_rate']:.1f}% "
        f"mean_all={summary['mean_estimate_pass_rate']:.1f}% "
        f"spread={summary['min_estimate_pass_rate']:.1f}–"
        f"{summary['max_estimate_pass_rate']:.1f}% "
        f"({summary['method_count']} methods)"
    )
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
