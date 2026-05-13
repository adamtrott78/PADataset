# Catalog tiny smoke validation

## Purpose

Validate that the new experiment catalog path can generate a manifest, create config JSON, launch a training worker, update dashboard progress, complete training/evaluation, and reduce results.

## Manifest

- `manifests/catalog_tiny_smoke.tsv`

## Run

- run group: `smoke_functional`
- paper set: `OG`
- unknown PA: `PA2`
- family: `smoke_ent005_lr2e4`
- seed: `0`
- GPU: `1`
- epochs: `1`
- batch size: `2`
- output root: `results_pa_final_smoke`

## Result artifact

- `docs/experiments/run_results/catalog_tiny_smoke_leaderboard.csv`

## Notes

This validates the catalog-driven manifest path. The actual checkpoint artifacts remain local and are intentionally not committed.
