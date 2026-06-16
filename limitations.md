# Limitations

Read this before citing any number from this repository.

## Non-official status

- This repository publishes an **unofficial estimate**.
- It is **not** a DeepSWE benchmark submission.
- Composer 2.5 has **not** been officially scored on DeepSWE in the public artifacts used here.

## Benchmark mismatch

CursorBench 3.1 and DeepSWE differ in:

- Task sets and difficulty
- Agent harness and tooling
- Evaluation timeouts and retry policies
- Scoring details beyond headline pass rate

Linking assumes these differences are absorbable from a small overlap set. That assumption often fails for some model families.

## Model and version ambiguity

- "Composer 2.5" must be tied to a specific product build and evaluation date.
- CursorBench and DeepSWE rows may not reflect the same model snapshot.
- Reasoning-effort labels are aligned heuristically (`max`, `xhigh`, `high`, etc.).

## Hidden evaluation differences

Public leaderboards may round scores, filter tasks, or change scope without this repo immediately reflecting those changes. We recompute DeepSWE from `trials.json`, but CursorBench reference rows are static CSV unless you update them.

## Cost accounting limitations

- DeepSWE costs come from trial rollouts.
- Composer's chart position uses a **CursorBench cost proxy** ($0.55/task in the reference table).
- Cost-normalized methods inherit this mismatch.

## Selection bias

Overlap pairs are not a random sample of all models. They skew toward frontier models that appear on both leaderboards. Composer extrapolation from this set may not generalize.

## Small overlap fragility

With roughly **14** overlap pairs, one outlier (e.g., GPT-5.5 [xhigh] scoring higher on DeepSWE than CursorBench) can move several methods. Treat wide method spread as a warning, not precision.

## Synthetic example data

`example_model_results.csv` is for **pipeline testing only**. Never present example outputs as real benchmark results.

## Reproducibility limits

- `trials.json` updates when DeepSWE publishes new rollouts; refresh with the command in `data/raw/README.md`.
- This repo commits a pinned copy of the public DeepSWE `trials.json` (~22 MB) for one-step reproduction. Fingerprint: `data/raw/MANIFEST.json`.
- Recomputed numbers may drift after refresh unless you update the manifest and README tables.
- The committed artifact is the public DeepSWE download. Check [deepswe.datacurve.ai/data](https://deepswe.datacurve.ai/data) for upstream terms before redistributing or citing the bundled file.

## How to cite responsibly

Prefer language such as:

> "Unofficial estimate (~58% DeepSWE Pass@1 central estimate from six core linking methods; mean across all eight methods ~56%; method spread 48.0–62.2%) derived from CursorBench↔DeepSWE linking; not a measured DeepSWE score."

Avoid language such as:

> "Composer 2.5 scores X% on DeepSWE."

unless X comes from official DeepSWE trials you provide.
