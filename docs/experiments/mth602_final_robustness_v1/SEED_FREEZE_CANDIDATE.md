# MTH602 Final Robustness Seed Freeze Candidate v1

Status: **PROPOSED / NOT AUTHORIZED FOR SCIENTIFIC ADMISSION**

This candidate closes the missing design needed to execute the durable
`mth602-final-multisurrogate-dqnguard-v1` robustness stage without mixing
partition variance and training/model variance.

## Why this change is required

The frozen robustness budget is 5 partition seeds x 10 backbone
training/model seeds x 10 canonical leave-two-out pairs. The existing trainer
uses one legacy `seed` for all of the following:

- dataset split construction;
- model/Python/NumPy/PyTorch RNG;
- DataLoader order.

That makes the two planned variance axes inseparable. This candidate introduces
explicit `partition_seed` and `training_seed` fields while retaining the
legacy `seed` fallback for old manifests.

## Proposed exact seed identities

These values are proposed before any multi-seed result exists:

- partition seeds: `[0, 1, 2, 3, 4]`
- training/model seeds: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`

The already-frozen seed-0 backbone matrix may count as cell
`partition_seed=0, training_seed=0` only when its recipe and artifact identity
match the final robustness contract exactly.

The numeric labels are intentionally simple seed identifiers. Independence is
provided by separate RNG roles, not by making the integers numerically distant.

## RNG ownership

`partition_seed` controls:

- train/validation/test partition construction;
- open-set partitioning;
- deterministic calibration-subset selection used by the standard DQNGuard
  evaluator.

`training_seed` controls:

- Python / NumPy / PyTorch model RNG;
- CUDA RNG;
- deterministic DataLoader ordering/worker RNG.

## DQN policy

The standard DQNGuard evaluator already uses fixed `seed=42`. The main 5x10
factorial therefore keeps **DQN seed 42** exactly, so DQN initialization does
not become an unplanned third factorial axis.

A separate DQN-seed sensitivity experiment is deferred and is not part of this
candidate or the 5x10 budget.

## Frozen scientific invariants

This candidate does not change:

- t007 recipe or HPO selection;
- known-only checkpoint selection;
- frozen standard-DQNGuard band/threshold semantics;
- Rule A/B/C definitions;
- DQN-IDS-style matched-control definition;
- VarMax matched-control definition;
- target-test firewall;
- retry policy.

No target/test/OSR result may change seed identities, recipes, checkpoints,
thresholds, controls, selectors, or retry decisions.

## Planned identities

Backbone identity:

`(canonical_pair, partition_seed, training_seed)`

Directional OSR identity:

`(target, surrogate, partition_seed, training_seed)`

This yields 50 backbone replications per canonical pair, 500 total backbone
cells, followed by two frozen directional OSR evaluations per backbone.

## Admission gate

No scientific jobs may be admitted from this candidate until:

1. the exact numeric seed lists are explicitly accepted;
2. the candidate implementation is validated;
3. the exact accepted candidate SHA is bound in durable task state;
4. immutable manifests are generated from the accepted plan;
5. admissions use only the existing bounded scientific paths.

No merge authority is implied.
