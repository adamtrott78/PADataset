# Stage 03 — Architecture C Implementation Candidate

This implementation follows the frozen Stage 01/02 contracts.

Files:
- `multisurrogate_dqnguard.py`
- `experiments/pa_eval_multisurrogate_dqnguard.py`
- `tests/test_multisurrogate_dqnguard.py`

Key behavior:
- requires a backbone selected with `early_stopping_mode=known_only`;
- partitions known validation deterministically into disjoint fit/guard/norm/threshold/pseudo roles;
- fits one DQN from known-fit + pooled internal pseudo-open evidence;
- fits predicted-class deterministic bands from known-guard only;
- derives one surrogate-specific guard weighting from each pseudo-open slice;
- normalizes each guard against known-norm empirical CDF;
- max-aggregates normalized guard evidence using the predeclared OR-like rule;
- adds that guard score to the single DQN margin;
- selects one final threshold from known-threshold only at the 95th percentile;
- emits the frozen Stage 02 result-record schema.

The candidate intentionally refuses historical `open_conf` backbone runs for
new architecture-C evaluation because that checkpoint-selection regime can use
withheld-target validation.

Execution remains gated until Workspace Shell is rebound to this exact candidate
SHA and a matching known-only four-class backbone is prepared for a target fold.

Backbone freeze for the first real fold:
- target fold is fixed a priori to PA2/Burst by task order, not target metrics;
- config: `manifests/configs/mth602_stage03/archC_backbone_knownonly_unkPA2_c16384_seed0.json`;
- `pas` contains PA1/PA2/PA3/PA4/PA8 and `unknown_pas=[PA2]`, yielding four known classes;
- `cache_len=16384` and the authoritative `ota_core_high_run01/high_run01` cache lineage are preserved;
- `early_stopping_mode=known_only` with `model_selection_metric=val_macro_f1`;
- `open_val_frac=0.0`, balanced open validation disabled, and
  `quarantine_target_until_test=true`, so target-open examples are not
  iterated before the frozen checkpoint is selected.

