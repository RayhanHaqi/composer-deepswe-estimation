# Methodology

This document explains how Composer 2.5 DeepSWE performance is **estimated** in this repository.

## What is being estimated?

We estimate **DeepSWE Pass@1 (%)** for **Composer 2.5** on the public DeepSWE task suite, even though Composer 2.5 does **not** appear in public DeepSWE trial artifacts.

The estimate answers a narrow question:

> If models that appear on both CursorBench 3.1 and DeepSWE follow a stable cross-benchmark relationship, where would Composer 2.5 likely fall on a DeepSWE-style pass-rate axis?

This is **not** a measured DeepSWE score.

## Why estimation is needed

- Composer 2.5 has a public **CursorBench 3.1** reference row.
- Composer 2.5 has **no** public DeepSWE trials in `trials.json`.
- Direct measurement would require running the official DeepSWE harness, which this repo does not do.

Estimation links benchmarks through **overlap pairs**: models with the same normalized name and reasoning-effort label on both leaderboards.

## Data used

| Source | Role | Official? |
| --- | --- | --- |
| `cursorbench_3_1_reference.csv` | CursorBench 3.1 pass rate and cost proxy | Public reference table |
| `trials.json` | DeepSWE rollouts recomputed to Pass@1 | Public DeepSWE artifact (included in repo) |
| `example_model_results.csv` | Synthetic pipeline test only | **Not real** |

### DeepSWE Pass@1 definition

For each model + reasoning effort:

1. Filter rollouts to `source=deep-swe` and `included_in_score=true`.
2. When `eval_scope=cross-bench` exists, keep `eval_scope=full` only (leaderboard scope).
3. Per task, compute pass rate across rollouts.
4. Average task pass rates with **equal task weight**.

This follows the filtering and aggregation rules implemented in `scripts/common.py` (`deep-swe` source, `included_in_score=true`, full eval scope when cross-bench rows exist, equal task weight). Re-run the pipeline after `trials.json` updates to confirm scores still match your artifact.

## Estimation methods

Each method takes overlap pairs `(cursor_score, deepswe_score)` and predicts DeepSWE pass rate at Composer's CursorBench anchor (default **63.2%**).

| Method | Idea | Main assumption |
| --- | --- | --- |
| `direct_ratio_scaling` | Multiply Composer score by mean pass-rate ratio | Ratio is stable across models |
| `equipercentile_mapping` | Equipercentile mapping | Score distributions align by percentile |
| `ols_regression` | Linear fit `deepswe ~ cursor` | Linear link on overlap |
| `robust_median_delta` | Composer + median(Cursor→DeepSWE gap) | Median gap is representative |
| `cost_normalized` | Scale pass/cost and cost ratios | Cost structure transfers to Composer |
| `family_adjusted` | Family-specific median gap | Composer behaves like its model family |
| `robust_regression_theil_sen` | Theil-Sen robust line | Outlier pairs should be down-weighted |
| `knn_inverse_distance` | k=3 neighbors on Cursor score | Local neighborhood predicts Composer |

Methods are **correlated sensitivity checks**, not independent estimators.

### Central estimate vs method spread

- **Central estimate** — mean of six **core** linking methods (`equipercentile_mapping`, `ols_regression`, `robust_median_delta`, `family_adjusted`, `robust_regression_theil_sen`, `knn_inverse_distance`). This is the red star on the README chart (~58.1% with current artifacts).
- **Sensitivity-only methods** — `direct_ratio_scaling` and `cost_normalized` stress ratio/cost assumptions and are excluded from the central estimate.
- **Method spread** — min and max across **all eight** methods (currently ~48.0%–62.2%). This summarizes assumption disagreement, not statistical precision.

## Final range

For each method we record `estimated_pass_rate`. The published range is:

- **Central estimate** — mean across core methods (headline point estimate)
- **Minimum** and **maximum** across all methods (method spread)
- **Mean** and **median** across all methods
- **Method count**

We label this **method spread**. It is **not** a formal confidence interval unless a method supplies a statistically justified interval (e.g., OLS approximate predictive bounds in `estimates.csv`).

## Uncertainty representation

- **Method spread** communicates disagreement between linking assumptions.
- Optional per-method intervals (when present) are documented in `notes` and must not be over-interpreted with n≈14 overlap pairs.
- **Leave-one-out validation** (`scripts/loo_validation.py`) holds out each overlap pair and asks whether the remaining pairs recover that model's DeepSWE score from its CursorBench score. This is a **diagnostic** check on linking assumptions among overlap models — not proof that the Composer 2.5 estimate is correct.

## Leave-one-out validation

For each overlap model-effort pair:

1. Remove that pair from the overlap set.
2. Fit each core linking method on the remaining pairs.
3. Predict the held-out model's DeepSWE pass rate from its CursorBench score.
4. Compare predicted vs actual DeepSWE score and summarize error metrics.

Outputs: `results/loo_validation.csv`, `results/loo_validation_summary.json`, `figures/loo_validation_errors.png` (regenerated locally). Committed snapshot: `results/pinned/loo_validation.csv`, `results/pinned/loo_validation_summary.json`.

This tests **internal consistency** of linking methods on models that appear on both benchmarks. It does **not** validate Composer 2.5 directly (Composer is not in the overlap set) and must not be read as a confidence interval for the headline estimate.

## What would improve the estimate

1. **Official Composer 2.5 DeepSWE trials** — replaces estimation entirely.
2. **Larger overlap** — more models evaluated on both benchmarks under matched harness settings.
3. **Matched cost accounting** — measured DeepSWE spend for Composer, not CursorBench proxy.
4. **Version pinning** — explicit Composer build, harness commit, and trial artifact fingerprints in every report.
5. **External validation** — LOO validation is included as an internal diagnostic on existing overlap pairs. Future model-effort rows that were not available when designing the methods would provide a stronger external check.

## Reproducibility

Run from repository root:

```bash
pip install -r requirements.txt
bash scripts/run_full.sh
```

See `data/raw/MANIFEST.json` for the pinned `trials.json` fingerprint. See `README.md` for example-data workflows.
