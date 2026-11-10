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
