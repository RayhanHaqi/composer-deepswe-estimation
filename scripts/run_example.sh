#!/usr/bin/env bash
# Run the full pipeline on synthetic example data (from repo root).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python scripts/parse_results.py --files data/raw/example_model_results.csv --output data/processed/normalized_results.csv
python scripts/estimate_composer.py --input data/processed/normalized_results.csv --output-dir results/
python scripts/plot_results.py --input data/processed/normalized_results.csv --estimates results/estimates.csv --output-dir figures/
python scripts/generate_report.py --input data/processed/normalized_results.csv --output reports/composer_deepswe_estimate.md
echo "Example pipeline complete."
