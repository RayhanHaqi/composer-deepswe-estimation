# Raw data

Place input files here. Supported formats:

| Format | Typical file | Notes |
| --- | --- | --- |
| CSV | `cursorbench_3_1_reference.csv` | Public CursorBench 3.1 reference (included) |
| CSV | `example_model_results.csv` | **Synthetic** pipeline test data (included) |
| JSON | `trials.json` | DeepSWE public trials artifact (not committed — download below) |
| JSON | `tasks.json` | DeepSWE task metadata (optional; for report context) |
| JSONL | `*.jsonl` | One trial record per line (same schema as trials.json rows) |

## Download DeepSWE artifacts

If you do not already have local copies (e.g. from the sibling `deepswe/` workspace):

```bash
curl -L -o data/raw/trials.json https://deepswe.datacurve.ai/artifacts/trials.json
curl -L -o data/raw/tasks.json https://deepswe.datacurve.ai/artifacts/tasks.json
```

Or symlink from an existing checkout:

```bash
ln -sf /path/to/deepswe/trials.json data/raw/trials.json
ln -sf /path/to/deepswe/tasks.json data/raw/tasks.json
```

`trials.json` is ~22 MB and is listed in `.gitignore`. Do not commit private logs or local workspace paths.

## Synthetic vs real data

- Files prefixed with `example_` are **synthetic** and only test the pipeline.
- `cursorbench_3_1_reference.csv` contains **public reference** leaderboard numbers.
- Recomputed DeepSWE scores come from your local `trials.json` copy.

Never mix synthetic and real outputs without labeling the run in your report.
