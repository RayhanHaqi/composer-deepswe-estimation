# composer-deepswe-estimation

**Unofficial, reproducible estimate of Composer 2.5 on DeepSWE-style coding-agent benchmarks**

## What this is

This repository provides a reproducible, unofficial **linking estimate** of Composer 2.5 DeepSWE Pass@1 using:

- public **CursorBench 3.1** reference scores (Composer anchor: **63.2%**, **$0.55**/task cost proxy)
- public **DeepSWE** `trials.json` recomputed to Pass@1
- **n≈14** overlapping model-effort pairs evaluated on both benchmarks
- eight transparent linking methods (six **core** methods for the headline central estimate)

The committed snapshot in [`results/pinned/`](results/pinned/) matches the headline numbers below.

## What this is not

- **Not** an official DeepSWE benchmark submission or leaderboard entry
- **Not** a measured Composer 2.5 DeepSWE score (Composer has **no** public DeepSWE trials in `trials.json`)
- **Not** a confidence interval — method spread summarizes assumption disagreement across linking methods
- **Not** measured DeepSWE cost for Composer — chart x-position uses a CursorBench cost proxy

## Key result (pinned snapshot)

When the committed `trials.json` and CursorBench reference are used, the linking pipeline yields approximately:

| Statistic | Estimated DeepSWE Pass@1 |
| --- | ---: |
| Central estimate (core 6 methods; chart star) | ~58.1% |
| Median across all methods | ~57.6% |
| Mean across all methods | ~55.8% |
| Method spread (min–max, all 8 methods) | ~48.0% – 62.2% |
| Conservative anchor (`robust_median_delta`) | ~52.3% |

*Core methods exclude `direct_ratio_scaling` and `cost_normalized` (ratio/cost sensitivity checks). Method spread is sensitivity disagreement across all eight methods — not a confidence interval.*

![Composer 2.5 DeepSWE estimate (unofficial)](figures/composer_deepswe_estimate.png)

*Official DeepSWE model points from `trials.json` (Pass@1). Red star = unofficial Composer 2.5 **central estimate** (mean of six core linking methods, ~58.1%). Vertical bar = **method spread** min–max across all eight methods (~48.0%–62.2%) — not a confidence interval. Composer x-position uses a CursorBench cost proxy.*

> **Disclaimer:** These are **estimates** from cross-benchmark linking (n≈14 overlap pairs). Composer has no public DeepSWE trials. Method spread is **not** a confidence interval. See [limitations.md](limitations.md).

| Method | Estimated DeepSWE Pass@1 |
| --- | ---: |
| `cost_normalized` | 48.0% |
| `direct_ratio_scaling` | 49.6% |
| `robust_median_delta` | 52.3% |
| `ols_regression` | 57.3% |
| `equipercentile_mapping` | 57.8% |
| `family_adjusted` | 57.9% |
| `robust_regression_theil_sen` | 61.3% |
| `knn_inverse_distance` | 62.2% |

*Per-method assumptions: [methodology.md](methodology.md). Re-run `bash scripts/run_full.sh` to refresh from your local artifacts; compare to `results/pinned/`.*

## Leave-one-out validation (diagnostic)

`scripts/loo_validation.py` holds out each overlap pair and tests whether the remaining pairs recover that model's DeepSWE score from its CursorBench score. This is **diagnostic only** — it does not validate Composer directly.

See [`results/pinned/loo_validation_summary.json`](results/pinned/loo_validation_summary.json) for the committed diagnostic summary (n=14 held-out overlap pairs). Mean absolute error ranges from **4.6 pp** (`robust_regression_theil_sen`) to **9.2 pp** (`family_adjusted`). This measures overlap-pair recovery only — not Composer estimate accuracy.

Regenerate locally with `python scripts/loo_validation.py` after `bash scripts/run_full.sh`; compare to the pinned snapshot.

## Source provenance

| Artifact | Path | Notes |
| --- | --- | --- |
| DeepSWE trials | `data/raw/trials.json` | SHA-256 in [`data/raw/MANIFEST.json`](data/raw/MANIFEST.json) |
| CursorBench 3.1 reference | `data/raw/cursorbench_3_1_reference.csv` | [`data/raw/CURSORBENCH_SOURCE.md`](data/raw/CURSORBENCH_SOURCE.md) |
| Pinned headline outputs | `results/pinned/` | Committed snapshot for README numbers and LOO diagnostics |

CursorBench upstream: [cursor.com/cursorbench](https://cursor.com/cursorbench) (see `CURSORBENCH_SOURCE.md`). Refresh CursorBench and DeepSWE artifacts deliberately, then rerun the pipeline and update pinned outputs.

## Repository structure

```text
composer-deepswe-estimation/
  README.md
  methodology.md
  limitations.md
  requirements.txt
  requirements-lock.txt
  scripts/
    parse_results.py
    estimate_composer.py
    plot_results.py
    generate_report.py
    loo_validation.py
    common.py
  data/raw/
  data/processed/
  results/
    pinned/               # committed headline snapshot
  figures/
  tests/
  .github/workflows/ci.yml
```

## Setup

```bash
git clone https://github.com/RayhanHaqi/composer-deepswe-estimation.git
cd composer-deepswe-estimation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For exact reproduction, prefer the pinned versions in `requirements-lock.txt`.

## Reproduce the headline numbers

Requirements:

- `data/raw/cursorbench_3_1_reference.csv` (included)
- `data/raw/trials.json` (included; refresh from DeepSWE if needed)
- Python dependencies from `requirements.txt`

```bash
bash scripts/run_full.sh
python scripts/loo_validation.py
```

Compare `results/summary.json` to `results/pinned/summary.json`. Artifact fingerprints: `data/raw/MANIFEST.json`.

### Quick synthetic smoke test

```bash
bash scripts/run_example.sh
pytest -q
```

Or use the Makefile:

```bash
make test
make example
make full
make validate
```

## Outputs

- `results/` — regenerated local outputs (gitignored except README)
- `results/pinned/` — **committed** snapshot used for README headline numbers; update intentionally after artifact refresh
- `figures/composer_deepswe_estimate.png` — README chart (tracked)
- `reports/composer_deepswe_estimate.md` — generated report (gitignored)

## Limitations

See [limitations.md](limitations.md) for benchmark mismatch, cost proxy issues, small overlap, and non-official status.

## Citation

If you use this work, cite the repository and clearly label results as **unofficial estimates**, not official DeepSWE scores.

```bibtex
@misc{composer_deepswe_estimation2026,
  title  = {composer-deepswe-estimation: Unofficial Composer 2.5 DeepSWE Linking Analysis},
  author = {Rayhan Haqi},
  year   = {2026},
  url    = {https://github.com/RayhanHaqi/composer-deepswe-estimation},
  note   = {Unofficial estimate; not an official DeepSWE submission}
}
```

## License

MIT — see [LICENSE](LICENSE).
