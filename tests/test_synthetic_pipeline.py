"""End-to-end synthetic pipeline smoke tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_synthetic_pipeline_commands(tmp_path: Path):
    normalized = tmp_path / "normalized.csv"
    out_dir = tmp_path / "results"
    fig_dir = tmp_path / "figures"
    report = tmp_path / "report.md"
    py = sys.executable

    _run(
        [
            py,
            "scripts/parse_results.py",
            "--files",
            "data/raw/example_model_results.csv",
            "--output",
            str(normalized),
        ]
    )
    assert normalized.is_file()
    df = pd.read_csv(normalized)
    assert "benchmark_name" in df.columns
    assert set(df["benchmark_name"]) == {"cursorbench", "deepswe"}

    _run(
        [
            py,
            "scripts/estimate_composer.py",
            "--input",
            str(normalized),
            "--output-dir",
            str(out_dir),
        ]
    )
    assert (out_dir / "estimates.csv").is_file()
    assert (out_dir / "summary.json").is_file()
    estimates = pd.read_csv(out_dir / "estimates.csv")
    assert len(estimates) == 8

    _run(
        [
            py,
            "scripts/plot_results.py",
            "--input",
            str(normalized),
            "--estimates",
            str(out_dir / "estimates.csv"),
            "--output-dir",
            str(fig_dir),
        ]
    )

    _run(
        [
            py,
            "scripts/generate_report.py",
            "--input",
            str(normalized),
            "--estimates",
            str(out_dir / "estimates.csv"),
            "--summary",
            str(out_dir / "summary.json"),
            "--figures-dir",
            str(fig_dir),
            "--output",
            str(report),
        ]
    )
    assert report.is_file()
