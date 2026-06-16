"""Matplotlib plotting helpers for Composer DeepSWE estimation."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from common import COMPOSER_CURSOR_COST, COMPOSER_MODEL, summarize_uncertainty

COMPOSER_COLOR = "#CC0000"


def _setup_matplotlib(output_dir: Path):
    mpl_dir = output_dir / ".mplconfig"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
    import matplotlib.pyplot as plt

    return plt


def plot_cost_vs_pass_rate(
    normalized: pd.DataFrame,
    estimates: pd.DataFrame,
    out_path: Path,
) -> None:
    plt = _setup_matplotlib(out_path.parent)
    deepswe = normalized[normalized["benchmark_name"] == "deepswe"].copy()
    if deepswe.empty:
        raise ValueError("No DeepSWE rows available for cost vs pass-rate plot.")

    summary = summarize_uncertainty(estimates)
    y_mean = summary["mean_estimate_pass_rate"]
    y_lo = summary["min_estimate_pass_rate"]
    y_hi = summary["max_estimate_pass_rate"]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(
        deepswe["cost_usd"],
        deepswe["pass_rate"],
        s=50,
        alpha=0.85,
        label="Official DeepSWE (measured)",
        zorder=2,
    )
    ax.plot(
        [COMPOSER_CURSOR_COST, COMPOSER_CURSOR_COST],
        [y_lo, y_hi],
        color="black",
        linewidth=1.5,
        zorder=3,
    )
    ax.scatter(
        [COMPOSER_CURSOR_COST],
        [y_mean],
        marker="*",
        s=280,
        c=COMPOSER_COLOR,
        label=f"{COMPOSER_MODEL} estimate (unofficial)",
        zorder=4,
    )
    ax.set_xlabel("Average cost per task (USD)")
    ax.set_ylabel("Pass rate (%)")
    ax.set_title("Cost vs pass rate — DeepSWE models and Composer 2.5 estimate")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=9)
    foot = (
        "Composer x-position uses CursorBench cost proxy, not measured DeepSWE cost. "
        "Vertical bar = spread across estimation methods (not a confidence interval)."
    )
    fig.text(0.5, 0.01, foot, ha="center", fontsize=8, wrap=True)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def plot_method_estimates(estimates: pd.DataFrame, out_path: Path) -> None:
    plt = _setup_matplotlib(out_path.parent)
    df = estimates.sort_values("estimated_pass_rate")
    fig, ax = plt.subplots(figsize=(9, max(4, 0.45 * len(df) + 1)))
    y_pos = np.arange(len(df))
    ax.barh(y_pos, df["estimated_pass_rate"], color="#4C72B0", alpha=0.9)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["method_name"])
    ax.set_xlabel("Estimated DeepSWE pass rate (%)")
    ax.set_title("Composer 2.5 estimates by method")
    ax.grid(True, axis="x", alpha=0.25)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def plot_composer_vs_models(
    normalized: pd.DataFrame,
    estimates: pd.DataFrame,
    out_path: Path,
) -> None:
    plt = _setup_matplotlib(out_path.parent)
    deepswe = normalized[normalized["benchmark_name"] == "deepswe"].copy()
    if deepswe.empty:
        raise ValueError("No DeepSWE rows for model comparison chart.")

    summary = summarize_uncertainty(estimates)
    top = deepswe.nlargest(12, "pass_rate")
    labels = list(top["model_name"]) + [f"{COMPOSER_MODEL} (est.)"]
    values = list(top["pass_rate"]) + [summary["median_estimate_pass_rate"]]
    colors = ["#4C72B0"] * len(top) + [COMPOSER_COLOR]

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(labels))
    ax.barh(y_pos, values, color=colors, alpha=0.9)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Pass rate (%)")
    ax.set_title("Top DeepSWE models vs Composer 2.5 median estimate")
    ax.grid(True, axis="x", alpha=0.25)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def generate_all_plots(
    normalized: pd.DataFrame,
    estimates: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "cost_vs_pass_rate": output_dir / "cost_vs_pass_rate.png",
        "method_estimates": output_dir / "method_estimates.png",
        "composer_vs_models": output_dir / "composer_vs_models.png",
    }
    plot_cost_vs_pass_rate(normalized, estimates, paths["cost_vs_pass_rate"])
    plot_method_estimates(estimates, paths["method_estimates"])
    plot_composer_vs_models(normalized, estimates, paths["composer_vs_models"])
    return paths
