"""Tests for linking method names and core formulas."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from common import (  # noqa: E402
    CORE_LINKING_METHODS,
    build_overlap,
    estimate_composer_methods,
    predict_linking_at_anchor,
)


def _synthetic_overlap() -> pd.DataFrame:
    normalized = pd.read_csv(ROOT / "data" / "raw" / "example_model_results.csv")
    return build_overlap(normalized)


def test_old_method_names_absent():
    estimates = estimate_composer_methods(_synthetic_overlap(), composer_cursor_score=58.0)
    names = set(estimates["method_name"])
    assert "linear_interpolation" not in names
    assert "robust_median_ratio" not in names
    assert "equipercentile_mapping" in names
    assert "robust_median_delta" in names


def test_all_expected_methods_returned():
    estimates = estimate_composer_methods(_synthetic_overlap(), composer_cursor_score=58.0)
    assert len(estimates) == 8
    for name in CORE_LINKING_METHODS:
        assert name in set(estimates["method_name"])


def test_method_outputs_finite_on_synthetic():
    estimates = estimate_composer_methods(_synthetic_overlap(), composer_cursor_score=58.0)
    rates = estimates["estimated_pass_rate"].to_numpy(dtype=float)
    assert np.all(np.isfinite(rates))


def test_robust_median_delta_formula():
    overlap = _synthetic_overlap()
    x0 = 58.0
    preds = predict_linking_at_anchor(overlap, x0, 1.0, methods=("robust_median_delta",))
    expected = x0 + float(np.median(overlap["deepswe_score"] - overlap["cursor_score"]))
    assert abs(preds["robust_median_delta"] - expected) < 1e-9


def test_equipercentile_mapping_exists():
    overlap = _synthetic_overlap()
    preds = predict_linking_at_anchor(overlap, 58.0, 1.0, methods=("equipercentile_mapping",))
    assert np.isfinite(preds["equipercentile_mapping"])
