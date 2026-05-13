# Legacy PADataset Experiment Inventory

Generated from local ignored artifacts. This file is safe to commit because it contains metadata only, not checkpoints or raw data.

## Counts

- Run directories inventoried: 203
- Checkpoints inventoried: 617
- Generated tables inventoried: 16

## Result roots

- `results_pa_baseline`: 13
- `results_pa_cache_sweep`: 12
- `results_pa_confmanifold_coarse`: 56
- `results_pa_confmanifold_refined`: 64
- `results_pa_finalist`: 2
- `results_pa_followup`: 4
- `results_pa_osr_bank`: 48
- `results_pa_ota_btzb`: 2
- `results_pa_smoke`: 2

## Family tags observed

- `smoke_ent005_lr2e4`: 2

## Source profiles observed

- `('digital', 'pilot_noisy_torch', None, None)`: 113
- `('ota', 'ota_core_high_run01', 'ota_core_high_run01', 'high_run01')`: 4
- `(None, None, None, None)`: 86

## Next reconstruction task

Use `legacy_run_inventory.csv`, `legacy_checkpoint_inventory.csv`, and old generated leaderboard CSVs to define:

1. original digital-noisy source profile
2. old backbone family grid
3. old PA open-set folds
4. OSR evaluation settings
5. minimal reruns required for missing or ambiguous artifacts
