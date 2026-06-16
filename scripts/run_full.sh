#!/usr/bin/env bash
# Run the full pipeline with public CursorBench + local DeepSWE trials.json (from repo root).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
TRIALS="${1:-data/raw/trials.json}"
if [[ ! -f "$TRIALS" ]]; then
  echo "ERROR: trials.json not found at $TRIALS" >&2
  echo "Download: curl -L -o data/raw/trials.json https://deepswe.datacurve.ai/artifacts/trials.json" >&2
  exit 1
fi
python scripts/parse_results.py --files data/raw/cursorbench_3_1_reference.csv "$TRIALS" --output data/processed/normalized_results.csv
python scripts/estimate_composer.py --input data/processed/normalized_results.csv --output-dir results/
python scripts/plot_results.py --input data/processed/normalized_results.csv --estimates results/estimates.csv --output-dir figures/
python scripts/generate_report.py --input data/processed/normalized_results.csv --output reports/composer_deepswe_estimate.md
echo "Full pipeline complete. See results/summary.json"
