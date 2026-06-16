# Processed data

`parse_results.py` writes `normalized_results.csv` here.

Schema columns:

- `model_name`, `model_norm`, `effort_norm`
- `benchmark_name` (`cursorbench` or `deepswe`)
- `pass_rate`, `cost_usd`
- `num_tasks`, `num_completed`, `num_failed`, `num_errored` (nullable)
- `source`, `is_official`, `notes`

Missing fields are allowed as empty cells.
