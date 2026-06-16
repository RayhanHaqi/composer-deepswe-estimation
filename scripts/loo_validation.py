#!/usr/bin/env python3
"""Leave-one-out validation on overlap pairs for linking methods."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import numpy as np
import pandas as pd

from common import (
    COMPOSER_CURSOR_COST,
    CORE_LINKING_METHODS,
    build_overlap,
    ensure_parent,
    predict_linking_at_anchor,
    repo_root,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Leave-one-out validation on overlap model-effort pairs"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=repo_root() / "data" / "processed" / "normalized_results.csv",
        help="Normalized results CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root() / "results",
        help="Directory for loo_validation.csv and summary JSON",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=repo_root() / "figures",
        help="Directory for loo_validation_errors.png",
    )
    return parser.parse_args()


def run_loo_validation(overlap: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    n = len(overlap)
    min_pairs_note = "n_remaining < 2" if n <= 2 else ""

    for idx, held in overlap.iterrows():
        train = overlap.drop(index=idx).reset_index(drop=True)
        cursor_score = float(held["cursor_score"])
        actual = float(held["deepswe_score"])
        cursor_cost = (
            float(held["cursor_cost"])
            if pd.notna(held["cursor_cost"])
            else COMPOSER_CURSOR_COST
        )

        if len(train) < 2:
            preds = {m: float("nan") for m in CORE_LINKING_METHODS}
            note = min_pairs_note or "insufficient training pairs"
        else:
            preds = predict_linking_at_anchor(
                train,
                cursor_score,
                cursor_cost,
                methods=CORE_LINKING_METHODS,
            )
            note = ""

        for method_name, predicted in preds.items():
            if np.isnan(predicted):
                abs_err = float("nan")
                signed_err = float("nan")
                row_note = note or "method failed or insufficient data"
            else:
                abs_err = abs(predicted - actual)
                signed_err = predicted - actual
                row_note = ""
            rows.append(
                {
                    "model_norm": held["model_norm"],
                    "effort_norm": held["effort_norm"],
                    "cursor_score": cursor_score,
                    "actual_deepswe_score": actual,
                    "predicted_deepswe_score": predicted,
                    "absolute_error": abs_err,
                    "signed_error": signed_err,
                    "method_name": method_name,
                    "note": row_note,
                }
            )
    return pd.DataFrame(rows)


def summarize_loo(loo_df: pd.DataFrame) -> dict:
    summary: dict = {
        "pair_count": int(loo_df[["model_norm", "effort_norm"]].drop_duplicates().shape[0]),
        "method_count": len(CORE_LINKING_METHODS),
        "disclaimer": (
            "Diagnostic only: tests recovery of held-out overlap DeepSWE scores. "
            "Does not prove Composer 2.5 estimate correctness."
        ),
        "methods": {},
    }
    for method in CORE_LINKING_METHODS:
        sub = loo_df.loc[loo_df["method_name"] == method]
        valid = sub["absolute_error"].dropna()
        summary["methods"][method] = {
            "n_valid": int(len(valid)),
            "mean_absolute_error": float(valid.mean()) if len(valid) else None,
            "median_absolute_error": float(valid.median()) if len(valid) else None,
            "rmse": float(np.sqrt(np.mean(sub["signed_error"].dropna() ** 2)))
            if len(valid)
            else None,
            "mean_signed_error": float(sub["signed_error"].dropna().mean())
            if len(valid)
            else None,
        }
    return summary


def plot_loo_errors(loo_df: pd.DataFrame, output_path: Path) -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib.pyplot as plt

    methods = list(CORE_LINKING_METHODS)
    data = []
    labels = []
    for method in methods:
        errs = loo_df.loc[loo_df["method_name"] == method, "absolute_error"].dropna()
        if len(errs):
            data.append(errs.to_numpy())
            labels.append(method.replace("_", "\n"))

    if not data:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#EFE6D8")
    ax.set_ylabel("Absolute error (percentage points)")
    ax.set_title("Leave-one-out validation: held-out DeepSWE score recovery")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    ensure_parent(output_path)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    if not args.input.is_file():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 1

    normalized = pd.read_csv(args.input)
    try:
        overlap = build_overlap(normalized)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    loo_df = run_loo_validation(overlap)
    summary = summarize_loo(loo_df)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "loo_validation.csv"
    json_path = args.output_dir / "loo_validation_summary.json"
    loo_df.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    fig_path = args.figures_dir / "loo_validation_errors.png"
    args.figures_dir.mkdir(parents=True, exist_ok=True)
    plot_loo_errors(loo_df, fig_path)

    print(f"Wrote {csv_path} ({len(loo_df)} rows)")
    print(f"Wrote {json_path}")
    print(f"Wrote {fig_path}")
    for method, stats in summary["methods"].items():
        mae = stats["mean_absolute_error"]
        mae_s = f"{mae:.2f}" if mae is not None else "n/a"
        print(f"  {method}: MAE={mae_s} pp (n={stats['n_valid']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
