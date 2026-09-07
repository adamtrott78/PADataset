> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../../experiments/CONTEXT.md).

# Catalog tiny smoke incident: existing run directory

## Run

- manifest: `manifests/catalog_tiny_smoke.tsv`
- run: `og_smoke_ent005_lr2e4_unkPA2_c16384_seed0`
- output root: `results_pa_final_smoke`
- observed: 2026-05-13 11:56

## Root cause

The worker refused to overwrite an existing non-empty run directory:

`results_pa_final_smoke/og_smoke_ent005_lr2e4_unkPA2_c16384_seed0`

The directory contained stale artifacts from a previous partial smoke attempt, including `train_progress.json`.

## Interpretation

This was not a GPU failure and not a cache failure. The dashboard correctly reported `ERROR`, but the stale progress file made the display look like the run failed mid-epoch.

## Fix

For debug reruns only, delete the stale run directory or use a unique run name/output root.

For production runs, keep overwrite protection enabled.
