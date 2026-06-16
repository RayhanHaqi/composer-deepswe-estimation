# Pinned results snapshot

This directory contains a **committed snapshot** of pipeline outputs used for README headline numbers.

Regenerated local outputs live in `results/` (gitignored). After refreshing DeepSWE `trials.json` or the CursorBench reference CSV:

1. Run `bash scripts/run_full.sh`
2. Run `python scripts/loo_validation.py` (optional diagnostic)
3. Compare `results/summary.json` to this directory
4. Copy updated files here intentionally if headline numbers change

Files:

- `summary.json` — central estimate, method spread, overlap count
- `estimates.csv` — per-method Composer DeepSWE pass-rate estimates
- `overlap_pairs.csv` — matched CursorBench ↔ DeepSWE pairs used for linking
- `loo_validation.csv` — per-pair, per-method held-out recovery errors
- `loo_validation_summary.json` — committed LOO diagnostic summary (mean absolute error by method)
