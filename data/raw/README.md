# Raw data

Place input files here. Supported formats:

| Format | Typical file | Notes |
| --- | --- | --- |
| CSV | `cursorbench_3_1_reference.csv` | Public CursorBench 3.1 reference (included) |
| CSV | `example_model_results.csv` | **Synthetic** pipeline test data (included) |
| JSON | `trials.json` | DeepSWE public trials artifact (**included** in repo, ~22 MB) |
| JSON | `tasks.json` | DeepSWE task metadata (optional; for report context) |
| JSONL | `*.jsonl` | One trial record per line (same schema as trials.json rows) |

## Refresh DeepSWE artifacts

`trials.json` is committed for one-step reproducibility. To update when DeepSWE publishes new rollouts:

```bash
curl -L -o data/raw/trials.json https://deepswe.datacurve.ai/artifacts/trials.json
```

`tasks.json` is optional and not committed. Download if needed:

```bash
curl -L -o data/raw/tasks.json https://deepswe.datacurve.ai/artifacts/tasks.json
```

Do not commit private logs or local workspace paths.

## Artifact manifest

Pinned upstream fingerprints live in [`MANIFEST.json`](MANIFEST.json) (SHA-256, size, source URL, dates).

CursorBench provenance details: [`CURSORBENCH_SOURCE.md`](CURSORBENCH_SOURCE.md).

The committed `trials.json` is the public artifact from [DeepSWE](https://deepswe.datacurve.ai/data). Verify upstream terms before redistributing beyond this research repo.

## Synthetic vs real data

- Files prefixed with `example_` are **synthetic** and only test the pipeline.
- `cursorbench_3_1_reference.csv` contains **public reference** leaderboard numbers.
- Recomputed DeepSWE scores come from `data/raw/trials.json` (included).

Never mix synthetic and real outputs without labeling the run in your report.
