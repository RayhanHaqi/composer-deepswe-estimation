"""Shared utilities for Composer 2.5 DeepSWE estimation pipeline."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import TheilSenRegressor

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Normalized result schema
NORMALIZED_COLUMNS = [
    "model_name",
    "model_norm",
    "effort_norm",
    "benchmark_name",
    "pass_rate",
    "cost_usd",
    "num_tasks",
    "num_completed",
    "num_failed",
    "num_errored",
    "source",
    "is_official",
    "notes",
]

COMPOSER_MODEL = "composer-2.5"
COMPOSER_CURSOR_SCORE = 63.2
COMPOSER_CURSOR_COST = 0.55

# Ratio/cost sensitivity checks — excluded from the headline central estimate.
SENSITIVITY_ONLY_METHODS = frozenset({"direct_ratio_scaling", "cost_normalized"})

CORE_LINKING_METHODS = (
    "equipercentile_mapping",
    "ols_regression",
    "robust_median_delta",
    "family_adjusted",
    "robust_regression_theil_sen",
    "knn_inverse_distance",
)

CURSORBENCH_REFERENCE_CSV = "cursorbench_3_1_reference.csv"

SANITY_TARGETS = {
    ("gpt-5.5", "xhigh"): 70.0,
    ("gpt-5.5", "high"): 62.0,
    ("claude-opus-4.8", "max"): 58.0,
    ("claude-opus-4.8", "xhigh"): 58.0,
    ("gpt-5.4", "xhigh"): 56.0,
    ("claude-opus-4.7", "max"): 54.0,
    ("claude-sonnet-4.6", "high"): 32.0,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _version_hyphens_to_dots(model: str) -> str:
    return re.sub(r"(\d)-(\d)", r"\1.\2", model.strip().lower())


def normalize_cursorbench_name(model_raw: str) -> tuple[str, str]:
    mapping: dict[str, tuple[str, str]] = {
        "GPT-5.5 Extra High": ("gpt-5.5", "xhigh"),
        "GPT-5.5 High": ("gpt-5.5", "high"),
        "GPT-5.5 Medium": ("gpt-5.5", "medium"),
        "GPT-5.5 Low": ("gpt-5.5", "low"),
        "Opus 4.8 Max": ("claude-opus-4.8", "max"),
        "Opus 4.8 Extra High": ("claude-opus-4.8", "xhigh"),
        "Opus 4.8 High": ("claude-opus-4.8", "high"),
        "Opus 4.8 Medium": ("claude-opus-4.8", "medium"),
        "Opus 4.8 Low": ("claude-opus-4.8", "low"),
        "Opus 4.7 Max": ("claude-opus-4.7", "max"),
        "Opus 4.7 Extra High": ("claude-opus-4.7", "xhigh"),
        "Opus 4.7 High": ("claude-opus-4.7", "high"),
        "Opus 4.7 Medium": ("claude-opus-4.7", "medium"),
        "Opus 4.7 Low": ("claude-opus-4.7", "low"),
        "Sonnet 4.6 Max": ("claude-sonnet-4.6", "max"),
        "Sonnet 4.6 High": ("claude-sonnet-4.6", "high"),
        "Sonnet 4.6 Medium": ("claude-sonnet-4.6", "medium"),
        "Sonnet 4.6 Low": ("claude-sonnet-4.6", "low"),
        "Gemini 3.5 Flash": ("gemini-3.5-flash", "medium"),
        "Kimi 2.6": ("kimi-k2.6", "default"),
        "Kimi 2.5": ("kimi-k2.5", "default"),
        "Composer 2.5": ("composer-2.5", "default"),
        "Composer 2": ("composer-2", "default"),
        "Fable 5 Max": ("fable-5", "max"),
        "Fable 5 Extra High": ("fable-5", "xhigh"),
        "Fable 5 High": ("fable-5", "high"),
        "Fable 5 Medium": ("fable-5", "medium"),
        "Fable 5 Low": ("fable-5", "low"),
    }
    if model_raw in mapping:
        return mapping[model_raw]
    raise ValueError(f"Unmapped CursorBench model: {model_raw}")


def normalize_deepswe_model_effort(model: str, effort: str | None) -> tuple[str, str]:
    model_norm = _version_hyphens_to_dots(model)
    effort_norm = (effort or "default").strip().lower()
    return model_norm, effort_norm


def _leaderboard_scope(grp: pd.DataFrame) -> pd.DataFrame:
    if "eval_scope" in grp.columns and (grp["eval_scope"] == "cross-bench").any():
        return grp.loc[grp["eval_scope"] == "full"].copy()
    return grp


def _task_equal_pass_rate(grp: pd.DataFrame) -> float:
    task_rates = grp.groupby("task_name")["passed"].apply(
        lambda s: s.fillna(False).astype(bool).mean()
    )
    return float(task_rates.mean() * 100.0)


def _pass_at1_rate(grp: pd.DataFrame) -> float:
    return _task_equal_pass_rate(_leaderboard_scope(grp))


def summarize_deepswe_trials(rows: list[dict[str, Any]]) -> pd.DataFrame:
    filtered = [
        r
        for r in rows
        if r.get("source") == "deep-swe" and r.get("included_in_score") is True
    ]
    if not filtered:
        raise ValueError(
            "No deep-swe trials with included_in_score=True. "
            "Check trials.json source filter."
        )

    records: list[dict[str, Any]] = []
    df = pd.DataFrame(filtered)
    for (model, effort), grp in df.groupby(["model", "reasoning_effort"], dropna=False):
        effort_val = None if pd.isna(effort) else effort
        model_norm, effort_norm = normalize_deepswe_model_effort(str(model), effort_val)
        scoped = _leaderboard_scope(grp)
        passed = scoped["passed"].fillna(False).astype(bool)
        errored = (
            scoped["errored"].fillna(False).astype(bool)
            if "errored" in scoped.columns
            else pd.Series(False, index=scoped.index)
        )
        costs = scoped["cost_usd"].dropna()
        records.append(
            {
                "model_name": f"{model_norm} [{effort_norm}]",
                "model_norm": model_norm,
                "effort_norm": effort_norm,
                "benchmark_name": "deepswe",
                "pass_rate": _pass_at1_rate(grp),
                "cost_usd": float(costs.mean()) if len(costs) else None,
                "num_tasks": int(scoped["task_name"].nunique()),
                "num_completed": int(len(scoped)),
                "num_failed": int((~passed).sum()),
                "num_errored": int(errored.sum()),
                "source": "deepswe_trials",
                "is_official": True,
                "notes": "Pass@1 equal task weight; leaderboard eval_scope=full when present",
            }
        )
    return pd.DataFrame(records)


def cursorbench_csv_to_normalized(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"model_raw", "score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path.name} missing required columns: {sorted(missing)}")

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        model_raw = str(row["model_raw"])
        model_norm, effort_norm = normalize_cursorbench_name(model_raw)
        records.append(
            {
                "model_name": model_raw,
                "model_norm": model_norm,
                "effort_norm": effort_norm,
                "benchmark_name": "cursorbench",
                "pass_rate": float(row["score"]),
                "cost_usd": float(row["avg_cost"]) if "avg_cost" in df.columns and pd.notna(row.get("avg_cost")) else None,
                "num_tasks": None,
                "num_completed": None,
                "num_failed": None,
                "num_errored": None,
                "source": "cursorbench_reference",
                "is_official": True,
                "notes": "Public CursorBench 3.1 reference row",
            }
        )
    return pd.DataFrame(records)


def generic_csv_to_normalized(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "benchmark_name" not in df.columns:
        raise ValueError(
            f"{path.name}: generic CSV must include benchmark_name column. "
            f"Found: {list(df.columns)}"
        )
    for col in NORMALIZED_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[NORMALIZED_COLUMNS].copy()


def load_trials_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    rows = data["rows"] if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"{path.name}: expected list of trial records")
    return rows


def build_overlap(normalized: pd.DataFrame) -> pd.DataFrame:
    cursor = normalized[normalized["benchmark_name"] == "cursorbench"].copy()
    deepswe = normalized[normalized["benchmark_name"] == "deepswe"].copy()
    if cursor.empty or deepswe.empty:
        raise ValueError(
            "Need both cursorbench and deepswe rows in normalized data to build overlap."
        )
    overlap = cursor.merge(
        deepswe,
        on=["model_norm", "effort_norm"],
        how="inner",
        suffixes=("_cursor", "_deepswe"),
    )
    if overlap.empty:
        raise ValueError("No overlapping model-effort pairs between benchmarks.")
    return pd.DataFrame(
        {
            "model_norm": overlap["model_norm"],
            "effort_norm": overlap["effort_norm"],
            "cursor_score": overlap["pass_rate_cursor"],
            "deepswe_score": overlap["pass_rate_deepswe"],
            "cursor_cost": overlap["cost_usd_cursor"],
            "deepswe_cost": overlap["cost_usd_deepswe"],
        }
    )


def _ols_fit_predict(
    x: np.ndarray, y: np.ndarray, x0: float
) -> tuple[float, float | None, float | None]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 2:
        pred = float(np.mean(y))
        return pred, None, None
    slope, intercept = np.polyfit(x, y, 1)
    pred = float(intercept + slope * x0)
    resid = y - (intercept + slope * x)
    dof = max(len(x) - 2, 1)
    sigma2 = float(np.sum(resid**2) / dof)
    x_bar = x.mean()
    sxx = float(np.sum((x - x_bar) ** 2))
    if sxx <= 0:
        return pred, None, None
    se = np.sqrt(sigma2 * (1.0 / len(x) + (x0 - x_bar) ** 2 / sxx))
    return pred, pred - 1.96 * se, pred + 1.96 * se


def _equipercentile(x: np.ndarray, y: np.ndarray, x0: float) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    order = np.argsort(x)
    pct = float(np.clip(np.mean(x[order] <= x0), 0.0, 1.0))
    return float(np.quantile(y[order], pct))


def _theil_sen_predict(x: np.ndarray, y: np.ndarray, x0: float) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if HAS_SKLEARN and len(x) >= 2:
        reg = TheilSenRegressor(random_state=42)
        reg.fit(x.reshape(-1, 1), y)
        return float(reg.predict(np.array([[x0]]))[0])
    slopes = []
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            if x[j] != x[i]:
                slopes.append((y[j] - y[i]) / (x[j] - x[i]))
    if not slopes:
        return float(np.mean(y))
    slope = float(np.median(slopes))
    intercept = float(np.median(y - slope * x))
    return float(intercept + slope * x0)


def _linear_equating(x: np.ndarray, y: np.ndarray, x0: float) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if np.std(x) == 0:
        return float(np.mean(y))
    return float(y.mean() + (y.std(ddof=1) / x.std(ddof=1)) * (x0 - x.mean()))


def _bayesian_ridge_predict(x: np.ndarray, y: np.ndarray, x0: float) -> tuple[float, float | None, float | None]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    if n < 2:
        return float(np.mean(y)), None, None
    xm, ym = x.mean(), y.mean()
    xc, yc = x - xm, y - ym
    sxx = float(np.dot(xc, xc))
    if sxx <= 0:
        return float(ym), None, None
    alpha = 1.0
    slope = float((sxx / (sxx + alpha)) * (np.dot(xc, yc) / sxx))
    intercept = ym - slope * xm
    resid_var = float(np.var(yc - slope * xc, ddof=1)) if n > 2 else float(np.var(yc))
    pred = intercept + slope * x0
    pred_var = resid_var * (1.0 + 1.0 / n + (x0 - xm) ** 2 / (sxx + alpha))
    se = np.sqrt(max(pred_var, 0.0))
    return float(pred), float(pred - 1.96 * se), float(pred + 1.96 * se)


def _cost_normalized_predict(
    x: np.ndarray,
    y: np.ndarray,
    x_cost: np.ndarray,
    y_cost: np.ndarray,
    x0: float,
    cost0: float,
) -> tuple[float, float]:
    """Weight overlap pairs by combined score+cost distance to Composer anchor."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x_cost = np.asarray(x_cost, dtype=float)
    y_cost = np.asarray(y_cost, dtype=float)
    cost_scale = float(np.median(y_cost / np.maximum(x_cost, 1e-6)))
    pred_cost = cost0 * cost_scale
    x_scale = float(x.std(ddof=1)) or 1.0
    c_scale = float(x_cost.std(ddof=1)) or 1.0
    dist = np.sqrt(((x - x0) / x_scale) ** 2 + ((x_cost - cost0) / c_scale) ** 2)
    weights = 1.0 / np.maximum(dist, 0.15)
    pred_pass = float(np.dot(weights, y) / weights.sum())
    return pred_pass, pred_cost


def _family_adjusted_delta(overlap: pd.DataFrame) -> tuple[float, str]:
    overlap = overlap.copy()
    overlap["delta"] = overlap["deepswe_score"] - overlap["cursor_score"]

    def family_median(prefix: str) -> float | None:
        mask = overlap["model_norm"].str.startswith(prefix)
        if not mask.any():
            return None
        return float(overlap.loc[mask, "delta"].median())

    scenarios = {
        "gpt_like": family_median("gpt-5"),
        "opus_like": family_median("claude-opus-4."),
        "sonnet_like": family_median("claude-sonnet-4.6"),
        "all_family_average": float(overlap["delta"].median()),
    }
    gpt = scenarios["gpt_like"]
    opus = scenarios["opus_like"]
    if gpt is not None and opus is not None:
        delta = float(np.median([gpt, opus]))
        ref = f"median of gpt_like ({gpt:+.1f}pp) and opus_like ({opus:+.1f}pp)"
    else:
        delta = scenarios["all_family_average"]
        ref = "all-family median"
    fam_notes = "; ".join(
        f"{k}={v:+.1f}pp" for k, v in scenarios.items() if v is not None and k != "all_family_average"
    )
    return delta, f"{ref}. Reference family medians: {fam_notes}."


def predict_linking_at_anchor(
    overlap: pd.DataFrame,
    cursor_score: float,
    cursor_cost: float,
    *,
    methods: tuple[str, ...] | None = None,
) -> dict[str, float]:
    """Return per-method DeepSWE pass-rate predictions at a CursorBench anchor."""
    if overlap.empty:
        raise ValueError("Overlap table is empty.")

    x = overlap["cursor_score"].to_numpy(dtype=float)
    y = overlap["deepswe_score"].to_numpy(dtype=float)
    x_cost = overlap["cursor_cost"].to_numpy(dtype=float)
    y_cost = overlap["deepswe_cost"].to_numpy(dtype=float)
    x0 = float(cursor_score)
    cost0 = float(cursor_cost)

    all_methods = {
        "direct_ratio_scaling": lambda: float(
            x0 * np.mean(y / np.maximum(x, 1e-6))
        ),
        "equipercentile_mapping": lambda: _equipercentile(x, y, x0),
        "ols_regression": lambda: _ols_fit_predict(x, y, x0)[0],
        "robust_median_delta": lambda: x0 + float(np.median(y - x)),
        "cost_normalized": lambda: _cost_normalized_predict(x, y, x_cost, y_cost, x0, cost0)[0],
        "family_adjusted": lambda: x0 + _family_adjusted_delta(overlap)[0],
        "robust_regression_theil_sen": lambda: _theil_sen_predict(x, y, x0),
        "knn_inverse_distance": lambda: _knn_inverse_distance_predict(x, y, x0),
    }

    selected = methods or tuple(all_methods.keys())
    preds: dict[str, float] = {}
    for name in selected:
        if name not in all_methods:
            raise KeyError(f"Unknown linking method: {name}")
        if len(x) < 2 and name in {"ols_regression", "robust_regression_theil_sen"}:
            preds[name] = float("nan")
            continue
        if len(x) < 3 and name == "knn_inverse_distance":
            preds[name] = float("nan")
            continue
        try:
            preds[name] = float(all_methods[name]())
        except Exception:
            preds[name] = float("nan")
    return preds


def _knn_inverse_distance_predict(x: np.ndarray, y: np.ndarray, x0: float, k: int = 3) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) == 0:
        return float("nan")
    dist = np.abs(x - x0)
    order = np.argsort(dist)[: min(k, len(x))]
    eps = 1e-6
    w = 1.0 / np.maximum(dist[order], eps)
    return float(np.dot(w, y[order]) / w.sum())


def estimate_composer_methods(
    overlap: pd.DataFrame,
    *,
    composer_cursor_score: float = COMPOSER_CURSOR_SCORE,
    composer_cursor_cost: float = COMPOSER_CURSOR_COST,
) -> pd.DataFrame:
    if overlap.empty:
        raise ValueError("Overlap table is empty; cannot estimate Composer 2.5.")

    x = overlap["cursor_score"].to_numpy(dtype=float)
    y = overlap["deepswe_score"].to_numpy(dtype=float)
    x_cost = overlap["cursor_cost"].to_numpy(dtype=float)
    y_cost = overlap["deepswe_cost"].to_numpy(dtype=float)
    x0 = composer_cursor_score
    cost0 = composer_cursor_cost

    preds = predict_linking_at_anchor(overlap, x0, cost0)
    ratio = y / np.maximum(x, 1e-6)
    median_ratio = float(np.median(y - x))
    pred_pass, pred_cost = _cost_normalized_predict(x, y, x_cost, y_cost, x0, cost0)
    cost_scale = float(np.median(y_cost / np.maximum(x_cost, 1e-6)))
    delta, fam_note = _family_adjusted_delta(overlap)
    _, lo, hi = _ols_fit_predict(x, y, x0)
    interval_note = ""
    if lo is not None and hi is not None:
        interval_note = f" OLS approximate 95% predictive interval: {lo:.1f}–{hi:.1f}%."

    rows: list[dict[str, Any]] = [
        {
            "method_name": "direct_ratio_scaling",
            "estimated_pass_rate": preds["direct_ratio_scaling"],
            "estimated_cost_usd": cost0,
            "assumptions": "DeepSWE/CursorBench pass-rate ratio is stable across overlap pairs.",
            "notes": f"Mean ratio={np.mean(ratio):.4f} applied to Composer CursorBench {x0:.1f}%.",
        },
        {
            "method_name": "equipercentile_mapping",
            "estimated_pass_rate": preds["equipercentile_mapping"],
            "estimated_cost_usd": cost0,
            "assumptions": "Equipercentile mapping between CursorBench and DeepSWE score distributions.",
            "notes": "Equipercentile equating on overlap pairs.",
        },
        {
            "method_name": "ols_regression",
            "estimated_pass_rate": preds["ols_regression"],
            "estimated_cost_usd": cost0,
            "assumptions": "Linear relationship deepswe_score ~ cursor_score on overlap.",
            "notes": f"Ordinary least squares on n={len(x)} pairs.{interval_note}",
            "lower_interval_optional": lo,
            "upper_interval_optional": hi,
        },
        {
            "method_name": "robust_median_delta",
            "estimated_pass_rate": preds["robust_median_delta"],
            "estimated_cost_usd": cost0,
            "assumptions": "Median Cursor→DeepSWE gap is representative for Composer.",
            "notes": f"Composer CursorBench + median delta ({median_ratio:+.2f} pp).",
        },
        {
            "method_name": "cost_normalized",
            "estimated_pass_rate": pred_pass,
            "estimated_cost_usd": pred_cost,
            "assumptions": (
                "Overlap models near Composer in both CursorBench score and cost are most informative; "
                "DeepSWE cost scales via median cost ratio."
            ),
            "notes": (
                "Inverse-distance weighted DeepSWE pass rate on normalized (score, cost) distance; "
                f"cost uses median deepswe/cursor ratio ({cost_scale:.3f})."
            ),
        },
        {
            "method_name": "family_adjusted",
            "estimated_pass_rate": preds["family_adjusted"],
            "estimated_cost_usd": cost0,
            "assumptions": "Composer behaves like frontier GPT/Opus families on cross-benchmark shift.",
            "notes": f"Composer CursorBench + family-adjusted delta ({delta:+.2f} pp). {fam_note}",
        },
        {
            "method_name": "robust_regression_theil_sen",
            "estimated_pass_rate": preds["robust_regression_theil_sen"],
            "estimated_cost_usd": cost0,
            "assumptions": "Robust linear fit reduces influence of outlier overlap pairs.",
            "notes": "Theil-Sen regression (sklearn if available).",
        },
        {
            "method_name": "knn_inverse_distance",
            "estimated_pass_rate": preds["knn_inverse_distance"],
            "estimated_cost_usd": cost0,
            "assumptions": "Nearest CursorBench neighbors (k=3) predict Composer DeepSWE score.",
            "notes": "Sensitivity upper bound when Composer sits among top-tier Cursor rows.",
        },
    ]

    return pd.DataFrame(rows)


def filter_core_methods(estimates: pd.DataFrame) -> pd.DataFrame:
    """Core linking methods used for the headline central estimate (chart star)."""
    return estimates[~estimates["method_name"].isin(SENSITIVITY_ONLY_METHODS)].copy()


def summarize_uncertainty(estimates: pd.DataFrame) -> dict[str, Any]:
    scores = estimates["estimated_pass_rate"].dropna().to_numpy(dtype=float)
    costs = estimates["estimated_cost_usd"].dropna().to_numpy(dtype=float)
    core = filter_core_methods(estimates)
    core_scores = core["estimated_pass_rate"].dropna().to_numpy(dtype=float)
    return {
        "min_estimate_pass_rate": float(np.min(scores)),
        "max_estimate_pass_rate": float(np.max(scores)),
        "mean_estimate_pass_rate": float(np.mean(scores)),
        "median_estimate_pass_rate": float(np.median(scores)),
        "core_mean_estimate_pass_rate": float(np.mean(core_scores)),
        "method_count": int(len(scores)),
        "core_method_count": int(len(core_scores)),
        "min_estimate_cost_usd": float(np.min(costs)) if len(costs) else None,
        "max_estimate_cost_usd": float(np.max(costs)) if len(costs) else None,
        "mean_estimate_cost_usd": float(np.mean(costs)) if len(costs) else None,
        "uncertainty_label": "method_spread",
        "uncertainty_note": (
            "Min/max across methods summarize method disagreement, not a formal "
            "confidence interval unless a method provides a statistically justified interval."
        ),
    }
