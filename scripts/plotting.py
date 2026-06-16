"""Matplotlib plotting helpers for Composer DeepSWE estimation."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from common import COMPOSER_CURSOR_COST, COMPOSER_MODEL, summarize_uncertainty

COMPOSER_COLOR = "#CC0000"
CHART_SCORE_FLOOR_MODEL = "gemini-3-flash-preview"
README_CHART_NAME = "composer_deepswe_estimate.png"

DEEPSWE_MODEL_COLORS: dict[str, str] = {
    "gpt-5.5": "#1a9e55",
    "gpt-5.4": "#2ecc71",
    "gpt-5.4-mini": "#82e0aa",
    "claude-opus-4.8": "#e67e22",
    "claude-opus-4.7": "#d35400",
    "claude-opus-4.6": "#f39c12",
    "claude-sonnet-4.6": "#e59866",
    "claude-haiku-4.5": "#f5b041",
    "gemini-3.5-flash": "#2980b9",
    "gemini-3.1-pro-preview": "#5dade2",
    "gemini-3-flash-preview": "#85c1e9",
    "kimi-k2.6": "#e74c3c",
    "qwen3.7-max": "#5dade2",
    "qwen3.6-plus": "#48c9b0",
    "minimax-m3": "#e91e8c",
    "minimax-m2.7": "#f48fb1",
    "glm-5.1": "#16a085",
    "grok-build-0.1": "#1f618d",
    "deepseek-v4-pro": "#8e44ad",
    "mimo-v2.5-pro": "#7d6608",
}

EFFORT_ORDER = {"max": 0, "xhigh": 1, "high": 2, "medium": 3, "low": 4, "default": 5}

_FALLBACK_COLORS = [
    "#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b3",
    "#937860", "#da8bc3", "#8c8c8c", "#ccb974", "#64b5cd",
]

METHOD_LABELS = {
    "direct_ratio_scaling": "Direct ratio",
    "linear_interpolation": "Equipercentile",
    "ols_regression": "OLS regression",
    "robust_median_ratio": "Median delta",
    "cost_normalized": "Cost-weighted",
    "family_adjusted": "Family-adjusted",
    "robust_regression_theil_sen": "Theil-Sen",
    "knn_inverse_distance": "kNN (k=3)",
}


def _setup_matplotlib(output_dir: Path):
    mpl_dir = output_dir / ".mplconfig"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
    import matplotlib.pyplot as plt

    return plt


def _model_color(model_norm: str) -> str:
    if model_norm in DEEPSWE_MODEL_COLORS:
        return DEEPSWE_MODEL_COLORS[model_norm]
    return _FALLBACK_COLORS[abs(hash(model_norm)) % len(_FALLBACK_COLORS)]


def _effort_sort_key(effort: str) -> int:
    return EFFORT_ORDER.get(str(effort).lower(), 99)


def _format_dollar_xaxis(ax) -> None:
    def _fmt(val: float, _pos: int) -> str:
        if abs(val - round(val)) < 1e-6:
            return f"${int(round(val))}"
        return f"${val:.1f}"

    ax.xaxis.set_major_formatter(FuncFormatter(_fmt))


def _chart_deepswe_df(deepswe: pd.DataFrame) -> pd.DataFrame:
    flash = deepswe.loc[deepswe["model_norm"] == CHART_SCORE_FLOOR_MODEL]
    if flash.empty:
        return deepswe.copy()
    floor = float(flash.iloc[0]["pass_rate"])
    return deepswe.loc[deepswe["pass_rate"] >= floor - 1e-9].copy()


def _plot_deepswe_model_points(ax, deepswe: pd.DataFrame, *, point_size: float = 60) -> None:
    for model_norm, grp in deepswe.groupby("model_norm", sort=False):
        color = _model_color(str(model_norm))
        subset = grp.copy()
        subset["_effort_rank"] = subset["effort_norm"].astype(str).map(_effort_sort_key)
        subset = subset.sort_values(["cost_usd", "_effort_rank"])
        if len(subset) > 1:
            ax.plot(
                subset["cost_usd"],
                subset["pass_rate"],
                linestyle="--",
                color=color,
                alpha=0.75,
                linewidth=1.4,
                zorder=1,
            )
        ax.scatter(
            subset["cost_usd"],
            subset["pass_rate"],
            s=point_size,
            c=[color],
            alpha=0.92,
            edgecolors="white",
            linewidths=0.6,
            zorder=2,
        )


def _plot_composer_range_marker(
    ax,
    x: float,
    y_lo: float,
    y_hi: float,
    *,
    linewidth: float = 1.6,
    cap_fraction: float = 0.01,
    label_range: bool = False,
    label_fontsize: float = 9,
) -> None:
    xlim = ax.get_xlim()
    cap = abs(xlim[1] - xlim[0]) * cap_fraction
    ax.plot([x, x], [y_lo, y_hi], color="black", linewidth=linewidth, zorder=3)
    ax.plot([x - cap, x + cap], [y_lo, y_lo], color="black", linewidth=linewidth, zorder=3)
    ax.plot([x - cap, x + cap], [y_hi, y_hi], color="black", linewidth=linewidth, zorder=3)
    if label_range:
        for y_val in (y_lo, y_hi):
            ax.annotate(
                f"{y_val:.1f}%",
                (x, y_val),
                textcoords="offset points",
                xytext=(-10, 0),
                fontsize=label_fontsize,
                ha="right",
                va="center",
                zorder=6,
            )


def plot_readme_chart(
    normalized: pd.DataFrame,
    estimates: pd.DataFrame,
    out_path: Path,
) -> None:
    """Primary publication chart for README and reports."""
    plt = _setup_matplotlib(out_path.parent)
    deepswe = normalized[normalized["benchmark_name"] == "deepswe"].copy()
    if deepswe.empty:
        raise ValueError("No DeepSWE rows available for README chart.")

    plot_df = _chart_deepswe_df(deepswe)
    summary = summarize_uncertainty(estimates)
    y_mean = summary["mean_estimate_pass_rate"]
    y_lo = summary["min_estimate_pass_rate"]
    y_hi = summary["max_estimate_pass_rate"]

    fig = plt.figure(figsize=(19, 10))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 0.55], wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    ax_tbl = fig.add_subplot(gs[0, 1])
    ax_tbl.axis("off")

    _plot_deepswe_model_points(ax, plot_df, point_size=60)

    ax.set_xlabel("Average cost per task (USD)", fontsize=11)
    ax.set_ylabel("DeepSWE Pass@1 (%)\n(equal task weight; full eval scope)", fontsize=11, labelpad=10)
    ax.set_title(
        "Composer 2.5 estimated from CursorBench 3.1 → DeepSWE benchmark linking",
        fontsize=14,
        pad=12,
    )
    ax.grid(True, alpha=0.25)
    ax.margins(x=0.04, y=0.06)
    ax.invert_xaxis()
    _format_dollar_xaxis(ax)
    _plot_composer_range_marker(
        ax, COMPOSER_CURSOR_COST, y_lo, y_hi, label_range=True, label_fontsize=9
    )
    ax.scatter([COMPOSER_CURSOR_COST], [y_mean], marker="*", s=320, c=COMPOSER_COLOR, zorder=5)
    ax.annotate(
        "CursorBench cost proxy",
        xy=(COMPOSER_CURSOR_COST, y_mean),
        xytext=(-10, -32),
        textcoords="offset points",
        fontsize=9,
        color=COMPOSER_COLOR,
        ha="right",
        va="top",
        arrowprops={"arrowstyle": "->", "color": COMPOSER_COLOR, "lw": 0.9},
    )

    from matplotlib.lines import Line2D

    ax.legend(
        handles=[
            Line2D(
                [0], [0], marker="o", color="w", markerfacecolor="#666666",
                markersize=8, label="Official DeepSWE (per model)",
            ),
            Line2D([0], [0], linestyle="--", color="#666666", label="Effort variants"),
            Line2D(
                [0], [0], marker="*", color="w", markerfacecolor=COMPOSER_COLOR,
                markersize=14, label="Composer 2.5 (unofficial estimate)",
            ),
        ],
        loc="upper left",
        fontsize=10,
    )

    table_data = [
        [
            METHOD_LABELS.get(str(row["method_name"]), str(row["method_name"])),
            f"{row['estimated_pass_rate']:.1f}",
        ]
        for _, row in estimates.iterrows()
    ]
    table = ax_tbl.table(
        cellText=table_data,
        colLabels=["Method", "Est. %"],
        cellLoc="left",
        colLoc="left",
        loc="center",
        colWidths=[0.74, 0.26],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.55)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cccccc")
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#f2f2f2")

    foot = textwrap.fill(
        "Official DeepSWE points from trials.json (Pass@1). Composer 2.5 has no DeepSWE trials; "
        "star = linked estimate from CursorBench overlap. Composer x-axis uses CursorBench cost proxy. "
        "Vertical bar = spread across linking methods, not a confidence interval.",
        width=120,
    )
    fig.text(0.07, 0.03, foot, fontsize=9, ha="left", va="bottom")
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.12, top=0.92, wspace=0.18)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120, facecolor="white")
    plt.close(fig)


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
    ax.plot([COMPOSER_CURSOR_COST, COMPOSER_CURSOR_COST], [y_lo, y_hi], color="black", linewidth=1.5, zorder=3)
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
    fig.tight_layout()
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
        "readme_chart": output_dir / README_CHART_NAME,
        "cost_vs_pass_rate": output_dir / "cost_vs_pass_rate.png",
        "method_estimates": output_dir / "method_estimates.png",
        "composer_vs_models": output_dir / "composer_vs_models.png",
    }
    plot_readme_chart(normalized, estimates, paths["readme_chart"])
    plot_cost_vs_pass_rate(normalized, estimates, paths["cost_vs_pass_rate"])
    plot_method_estimates(estimates, paths["method_estimates"])
    plot_composer_vs_models(normalized, estimates, paths["composer_vs_models"])
    return paths
