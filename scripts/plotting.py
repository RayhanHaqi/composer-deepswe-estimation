"""Matplotlib plotting helpers for Composer DeepSWE estimation."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from common import COMPOSER_CURSOR_COST, COMPOSER_MODEL, filter_core_methods, summarize_uncertainty

COMPOSER_COLOR = "#CC0000"
# Warm parchment cream (Claude / editorial tone — visibly off-white on GitHub README)
CHART_BG_COLOR = "#EFE6D8"
CHART_GRID_COLOR = "#C8BBA8"
CHART_LABEL_BG = "#F7F1E8"
CHART_SPINE_COLOR = "#BFB3A2"
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


def _setup_matplotlib(output_dir: Path):
    mpl_dir = output_dir / ".mplconfig"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
    import matplotlib.pyplot as plt

    return plt


def _configure_readme_chart_style(plt) -> None:
    """Force cream background through matplotlib rcParams (not just axis patches)."""
    plt.rcParams.update(
        {
            "figure.facecolor": CHART_BG_COLOR,
            "axes.facecolor": CHART_BG_COLOR,
            "savefig.facecolor": CHART_BG_COLOR,
            "savefig.edgecolor": CHART_BG_COLOR,
        }
    )


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


def _format_effort_tag(effort_norm: str) -> str:
    if effort_norm == "default":
        return ""
    return f"[{effort_norm}]"


def _format_full_model_effort(model_norm: str, effort_norm: str) -> str:
    tag = _format_effort_tag(effort_norm)
    if not tag:
        return model_norm
    return f"{model_norm} {tag}"


def _tiered_effort_annotate_map(deepswe: pd.DataFrame) -> dict[tuple[str, str], str]:
    effort_counts = deepswe.groupby("model_norm").size()
    multi_effort_models = {str(model) for model, count in effort_counts.items() if count > 1}
    annotate: dict[tuple[str, str], str] = {}
    for model, grp in deepswe.groupby("model_norm", sort=False):
        model_str = str(model)
        if model_str not in multi_effort_models:
            continue
        ranked = grp.copy()
        ranked["_effort_rank"] = ranked["effort_norm"].astype(str).map(_effort_sort_key)
        top_effort = str(ranked.loc[ranked["_effort_rank"].idxmin(), "effort_norm"])
        for _, row in ranked.iterrows():
            effort = str(row["effort_norm"])
            key = (model_str, effort)
            if effort == top_effort:
                annotate[key] = _format_full_model_effort(model_str, effort)
            else:
                annotate[key] = _format_effort_tag(effort) or effort
    return annotate


def _low_score_model_annotate_map(
    deepswe: pd.DataFrame,
    *,
    min_score: float = 0.0,
    max_score: float = 30.0,
    skip_keys: set[tuple[str, str]] | None = None,
) -> dict[tuple[str, str], str]:
    skip_keys = skip_keys or set()
    annotate: dict[tuple[str, str], str] = {}
    for _, row in deepswe.iterrows():
        score = float(row["pass_rate"])
        if score <= min_score or score > max_score:
            continue
        key = (str(row["model_norm"]), str(row["effort_norm"]))
        if key in skip_keys:
            continue
        annotate[key] = _format_full_model_effort(str(row["model_norm"]), str(row["effort_norm"]))
    return annotate


def _chart_label_map(deepswe: pd.DataFrame) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str], float]]:
    labels = _tiered_effort_annotate_map(deepswe)
    labels[("gpt-5.4", "xhigh")] = _format_full_model_effort("gpt-5.4", "xhigh")
    labels[("claude-sonnet-4.6", "high")] = _format_full_model_effort("claude-sonnet-4.6", "high")
    low_score_labels = _low_score_model_annotate_map(deepswe, skip_keys=set(labels))
    labels.update(low_score_labels)
    font_sizes = {key: 8.0 for key in low_score_labels}
    font_sizes[("claude-sonnet-4.6", "high")] = 8.0
    return labels, font_sizes


def _chart_annotate_offsets() -> dict[tuple[str, str], tuple[float, float]]:
    return {
        ("claude-opus-4.8", "medium"): (0, -14),
        ("qwen3.7-max", "default"): (6, -4),
    }


def _chart_estimate_bounds(estimates: pd.DataFrame) -> tuple[float, float, float]:
    """Star = core-method mean; bar = min–max across all linking methods."""
    core = filter_core_methods(estimates)
    y_mean = float(core["estimated_pass_rate"].mean())
    y_lo = float(estimates["estimated_pass_rate"].min())
    y_hi = float(estimates["estimated_pass_rate"].max())
    return y_mean, y_lo, y_hi


def _plot_deepswe_model_points(
    ax,
    deepswe: pd.DataFrame,
    *,
    point_size: float = 60,
    annotate: dict[tuple[str, str], str] | None = None,
    annotate_fontsize: float = 9,
    annotate_offsets: dict[tuple[str, str], tuple[float, float]] | None = None,
    annotate_fontsizes: dict[tuple[str, str], float] | None = None,
) -> None:
    annotate = annotate or {}
    annotate_offsets = annotate_offsets or {}
    annotate_fontsizes = annotate_fontsizes or {}
    label_bbox = dict(
        boxstyle="round,pad=0.25",
        facecolor=CHART_LABEL_BG,
        edgecolor=CHART_SPINE_COLOR,
        alpha=0.98,
    )
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
        for _, row in subset.iterrows():
            key = (str(row["model_norm"]), str(row["effort_norm"]))
            if key not in annotate:
                continue
            xytext = annotate_offsets.get(key, (6, 6))
            ha = "center" if xytext[0] == 0 else "left"
            va = "top" if xytext[1] < 0 else "bottom"
            fontsize = annotate_fontsizes.get(key, annotate_fontsize)
            ax.annotate(
                annotate[key],
                (row["cost_usd"], row["pass_rate"]),
                textcoords="offset points",
                xytext=xytext,
                fontsize=fontsize,
                color=color,
                ha=ha,
                va=va,
                bbox=label_bbox,
                zorder=6,
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
    label_offset_x: float = 0,
) -> None:
    xlim = ax.get_xlim()
    cap = abs(xlim[1] - xlim[0]) * cap_fraction
    ax.plot([x, x], [y_lo, y_hi], color="black", linewidth=linewidth, zorder=3)
    ax.plot([x - cap, x + cap], [y_lo, y_lo], color="black", linewidth=linewidth, zorder=3)
    ax.plot([x - cap, x + cap], [y_hi, y_hi], color="black", linewidth=linewidth, zorder=3)
    if label_range:
        for y_val, y_off, va in ((y_lo, -8, "top"), (y_hi, 8, "bottom")):
            ax.annotate(
                f"{y_val:.1f}%",
                (x, y_val),
                textcoords="offset points",
                xytext=(label_offset_x, y_off),
                fontsize=label_fontsize,
                ha="center",
                va=va,
                zorder=6,
            )


def plot_readme_chart(
    normalized: pd.DataFrame,
    estimates: pd.DataFrame,
    out_path: Path,
) -> None:
    """Primary publication chart for README — matches the wide annotated scatter style."""
    plt = _setup_matplotlib(out_path.parent)
    _configure_readme_chart_style(plt)
    deepswe = normalized[normalized["benchmark_name"] == "deepswe"].copy()
    if deepswe.empty:
        raise ValueError("No DeepSWE rows available for README chart.")

    plot_df = _chart_deepswe_df(deepswe)
    effort_labels, label_fontsizes = _chart_label_map(plot_df)
    y_mean, y_lo, y_hi = _chart_estimate_bounds(estimates)

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor(CHART_BG_COLOR)
    ax.set_facecolor(CHART_BG_COLOR)
    _plot_deepswe_model_points(
        ax,
        plot_df,
        point_size=70,
        annotate=effort_labels,
        annotate_fontsize=11,
        annotate_offsets=_chart_annotate_offsets(),
        annotate_fontsizes=label_fontsizes,
    )

    ax.set_xlabel("Average cost per task (USD)", fontsize=14, color="#2A241C")
    ax.set_ylabel("DeepSWE Pass@1 (%)", fontsize=14, color="#2A241C")
    ax.set_title(
        "Composer 2.5 estimated from CursorBench 3.1 → DeepSWE",
        fontsize=16,
        color="#1A1612",
    )
    ax.tick_params(labelsize=12, colors="#3A342C")
    ax.grid(True, alpha=0.55, color=CHART_GRID_COLOR, linewidth=0.9)
    for spine in ax.spines.values():
        spine.set_color(CHART_SPINE_COLOR)
    ax.margins(x=0.04, y=0.06)
    ax.invert_xaxis()
    _format_dollar_xaxis(ax)

    cost_min = float(plot_df["cost_usd"].min())
    cost_max = float(plot_df["cost_usd"].max())
    span = max(cost_max - cost_min, 1.0)
    ax.set_xlim(cost_max + span * 0.06, max(0.0, cost_min - span * 0.22))

    _plot_composer_range_marker(
        ax,
        COMPOSER_CURSOR_COST,
        y_lo,
        y_hi,
        linewidth=2.0,
        label_range=True,
        label_fontsize=11,
        label_offset_x=6,
    )
    ax.scatter([COMPOSER_CURSOR_COST], [y_mean], marker="*", s=420, c=COMPOSER_COLOR, zorder=5)
    ax.annotate(
        "Composer 2.5",
        (COMPOSER_CURSOR_COST, y_mean),
        textcoords="offset points",
        xytext=(-14, -2),
        fontsize=12,
        color=COMPOSER_COLOR,
        ha="right",
        va="bottom",
    )
    ax.annotate(
        f"({y_mean:.1f}%)",
        (COMPOSER_CURSOR_COST, y_mean),
        textcoords="offset points",
        xytext=(-14, -6),
        fontsize=12,
        color="#000000",
        ha="right",
        va="top",
    )
    ax.annotate(
        "CursorBench cost proxy",
        (COMPOSER_CURSOR_COST, y_mean),
        textcoords="offset points",
        xytext=(-14, -22),
        fontsize=9,
        color="#666666",
        ha="right",
        va="top",
    )

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.10)
    fig.text(
        0.5,
        0.02,
        "← more expensive     cheaper →",
        fontsize=9,
        ha="center",
        va="bottom",
        color="#6B6258",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out_path,
        dpi=160,
        bbox_inches="tight",
        facecolor=CHART_BG_COLOR,
        edgecolor=CHART_BG_COLOR,
        transparent=False,
    )
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
