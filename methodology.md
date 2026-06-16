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
| `trials.json` (user download) | DeepSWE rollouts recomputed to Pass@1 | Public DeepSWE artifact |
| `example_model_results.csv` | Synthetic pipeline test only | **Not real** |

### DeepSWE Pass@1 definition

For each model + reasoning effort:

1. Filter rollouts to `source=deep-swe` and `included_in_score=true`.
2. When `eval_scope=cross-bench` exists, keep `eval_scope=full` only (leaderboard scope).
3. Per task, compute pass rate across rollouts.
4. Average task pass rates with **equal task weight**.

This matches the public DeepSWE leaderboard definition in our validation checks.

## Estimation methods

Each method takes overlap pairs `(cursor_score, deepswe_score)` and predicts DeepSWE pass rate at Composer's CursorBench anchor (default **63.2%**).

| Method | Idea | Main assumption |
| --- | --- | --- |
| `direct_ratio_scaling` | Multiply Composer score by mean pass-rate ratio | Ratio is stable across models |
| `linear_interpolation` | Equipercentile mapping | Score distributions align by percentile |
| `ols_regression` | Linear fit `deepswe ~ cursor` | Linear link on overlap |
| `robust_median_ratio` | Composer + median(Cursor→DeepSWE gap) | Median gap is representative |
| `cost_normalized` | Scale pass/cost and cost ratios | Cost structure transfers to Composer |
| `family_adjusted` | Family-specific median gap | Composer behaves like its model family |
| `robust_regression_theil_sen` | Theil-Sen robust line | Outlier pairs should be down-weighted |
| `knn_inverse_distance` | k=3 neighbors on Cursor score | Local neighborhood predicts Composer |

Methods are **correlated sensitivity checks**, not independent estimators.

## Final range

For each method we record `estimated_pass_rate`. The published range is:

- **Minimum** across methods
- **Maximum** across methods
- **Mean** and **median** across methods
- **Method count**

We label this **method spread**. It is **not** a formal confidence interval unless a method supplies a statistically justified interval (e.g., OLS approximate predictive bounds in `estimates.csv`).

## Uncertainty representation

- **Method spread** communicates disagreement between linking assumptions.
- Optional per-method intervals (when present) are documented in `notes` and must not be over-interpreted with n≈14 overlap pairs.
- Leave-one-out sensitivity can be added in future work; not required for the minimal pipeline.

## What would improve the estimate

1. **Official Composer 2.5 DeepSWE trials** — replaces estimation entirely.
2. **Larger overlap** — more models evaluated on both benchmarks under matched harness settings.
3. **Matched cost accounting** — measured DeepSWE spend for Composer, not CursorBench proxy.
4. **Version pinning** — explicit Composer build, harness commit, and trial artifact fingerprints in every report.
5. **Held-out validation** — reserve overlap pairs to score linking error.

## Reproducibility

Run from repository root:

```bash
pip install -r requirements.txt
python scripts/parse_results.py --files data/raw/cursorbench_3_1_reference.csv data/raw/trials.json
python scripts/estimate_composer.py
python scripts/plot_results.py
python scripts/generate_report.py
```

See `README.md` for example-data and full-data workflows.
