#!/usr/bin/env python3
"""Parse raw benchmark files into a normalized results table."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import pandas as pd

from common import (
    CURSORBENCH_REFERENCE_CSV,
    NORMALIZED_COLUMNS,
    cursorbench_csv_to_normalized,
    ensure_parent,
    generic_csv_to_normalized,
    load_trials_json,
    repo_root,
    summarize_deepswe_trials,
)


def discover_raw_files(input_dir: Path) -> list[Path]:
    patterns = ("*.json", "*.jsonl", "*.csv")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(input_dir.glob(pattern)))
    return files


def parse_jsonl_trials(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                import json

                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no}: invalid JSONL — {exc}") from exc
    return rows


def load_raw_file(path: Path) -> pd.DataFrame:
    name = path.name.lower()
    if name == "trials.json" or (name.endswith(".json") and "trial" in name):
        rows = load_trials_json(path)
        return summarize_deepswe_trials(rows)
    if name.endswith(".jsonl"):
        rows = parse_jsonl_trials(path)
        return summarize_deepswe_trials(rows)
    if "cursorbench" in name or name == CURSORBENCH_REFERENCE_CSV:
        return cursorbench_csv_to_normalized(path)
    if name.startswith("example_"):
        return generic_csv_to_normalized(path)
    if name.endswith(".csv"):
        try:
            return generic_csv_to_normalized(path)
        except ValueError:
            return cursorbench_csv_to_normalized(path)
    raise ValueError(f"Unsupported file type: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load raw benchmark files and write normalized_results.csv"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=repo_root() / "data" / "raw",
        help="Directory containing raw json/jsonl/csv files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root() / "data" / "processed" / "normalized_results.csv",
        help="Output normalized CSV path",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        type=Path,
        help="Optional explicit file list (overrides directory scan)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    if args.files:
        raw_files = [p.resolve() for p in args.files]
    else:
        if not input_dir.is_dir():
            print(f"ERROR: input directory not found: {input_dir}", file=sys.stderr)
            return 1
        raw_files = discover_raw_files(input_dir)

    if not raw_files:
        print(
            f"ERROR: no raw files found in {input_dir}. "
            "Add CSV/JSON files or pass --files.",
            file=sys.stderr,
        )
        return 1

    frames: list[pd.DataFrame] = []
    for path in raw_files:
        if not path.is_file():
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            return 1
        print(f"Parsing {path.name} ...")
        try:
            frames.append(load_raw_file(path))
        except Exception as exc:
            print(f"ERROR parsing {path}: {exc}", file=sys.stderr)
            return 1

    combined = pd.concat(frames, ignore_index=True)
    for col in NORMALIZED_COLUMNS:
        if col not in combined.columns:
            combined[col] = None
    combined = combined[NORMALIZED_COLUMNS]

    ensure_parent(args.output)
    combined.to_csv(args.output, index=False)
    print(f"Wrote {len(combined)} rows to {args.output}")
    print(f"  benchmarks: {combined['benchmark_name'].value_counts().to_dict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
