"""Consistency checks for headline estimate taxonomy."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from common import SENSITIVITY_ONLY_METHODS, filter_core_methods, summarize_uncertainty  # noqa: E402


def _fixture_estimates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "method_name": [
                "cost_normalized",
                "direct_ratio_scaling",
                "robust_median_ratio",
                "ols_regression",
                "linear_interpolation",
                "family_adjusted",
                "robust_regression_theil_sen",
                "knn_inverse_distance",
            ],
            "estimated_pass_rate": [48.0, 49.6, 52.3, 57.3, 57.8, 57.9, 61.3, 62.2],
            "estimated_cost_usd": [0.68, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55],
        }
    )


def test_core_methods_exclude_sensitivity_only():
    estimates = _fixture_estimates()
    core = filter_core_methods(estimates)
    assert set(core["method_name"]) == set(estimates["method_name"]) - SENSITIVITY_ONLY_METHODS
    assert len(core) == 6


def test_summary_separates_core_mean_from_all_method_mean():
    summary = summarize_uncertainty(_fixture_estimates())
    assert summary["core_method_count"] == 6
    assert summary["method_count"] == 8
    assert abs(summary["core_mean_estimate_pass_rate"] - 58.1) < 0.15
    assert abs(summary["mean_estimate_pass_rate"] - 55.8) < 0.15
    assert summary["min_estimate_pass_rate"] == 48.0
    assert summary["max_estimate_pass_rate"] == 62.2
