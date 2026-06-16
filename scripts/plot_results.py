#!/usr/bin/env python3
"""Generate matplotlib figures for Composer DeepSWE estimation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import pandas as pd

from common import repo_root
from plotting import generate_all_plots


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot Composer DeepSWE estimation figures")
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
        help="Method estimates CSV from estimate_composer.py",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root() / "figures",
        help="Directory for PNG outputs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for path, label in ((args.input, "input"), (args.estimates, "estimates")):
        if not path.is_file():
            print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
            return 1

    normalized = pd.read_csv(args.input)
    estimates = pd.read_csv(args.estimates)
    if "estimated_pass_rate" not in estimates.columns:
        print("ERROR: estimates CSV missing estimated_pass_rate column", file=sys.stderr)
        return 1

    try:
        paths = generate_all_plots(normalized, estimates, args.output_dir)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for name, path in paths.items():
        print(f"Wrote {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
