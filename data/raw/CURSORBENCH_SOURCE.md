# CursorBench 3.1 reference provenance

This file documents the public CursorBench reference table used to anchor Composer 2.5.

| Field | Value |
| --- | --- |
| Path | `data/raw/cursorbench_3_1_reference.csv` |
| SHA-256 | `604a0e35efc046aa4163b4c8035adb62975ee180d2f73ad4cda3c3aa8b4894f9` |
| Size (bytes) | 1603 |
| Captured date | 2026-06-17 |
| Capture method | Manually transcribed / curated reference table (not an automated export in this repo) |
| Upstream URL | TODO: add exact upstream URL |

## Composer 2.5 anchor row

The linking pipeline reads Composer 2.5 from this table:

- **Pass rate:** 63.2%
- **Cost proxy:** $0.55 per task (`avg_cost` column)

Composer has **no** public DeepSWE trials; this CursorBench row is the only public anchor for Composer in this analysis.

## Refresh policy

CursorBench leaderboard values can change upstream. This repository does **not** auto-sync CursorBench.

If the upstream CursorBench 3.1 table changes:

1. Update `data/raw/cursorbench_3_1_reference.csv` deliberately.
2. Recompute SHA-256 and update this file and `MANIFEST.json`.
3. Re-run `bash scripts/run_full.sh` and refresh `results/pinned/` if headline numbers change.
