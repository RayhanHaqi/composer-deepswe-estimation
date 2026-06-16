"""Tests for model/effort normalization helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from common import normalize_cursorbench_name, normalize_deepswe_model_effort  # noqa: E402


def test_normalize_cursorbench_composer():
    model_norm, effort_norm = normalize_cursorbench_name("Composer 2.5")
    assert model_norm == "composer-2.5"
    assert effort_norm == "default"


def test_normalize_deepswe_version_hyphens():
    model_norm, effort_norm = normalize_deepswe_model_effort("gpt-5-5", "xhigh")
    assert model_norm == "gpt-5.5"
    assert effort_norm == "xhigh"


def test_normalize_deepswe_default_effort():
    model_norm, effort_norm = normalize_deepswe_model_effort("claude-opus-4.8", None)
    assert model_norm == "claude-opus-4.8"
    assert effort_norm == "default"
