# MTH602 L2O HPO Pilot v2

## Purpose

Provide a deterministic, target-blind HPO controller for the three canonical leave-two-out backbones that missed the written competence gate:

- PA2-PA3
- PA2-PA8
- PA3-PA8

The controller reuses the existing trusted `train_backbone` GPU operation. It does not add or widen workflow authority.

## Selection contract

Only known-validation evidence may affect candidate ranking or promotion.

Competency gate:

- validation macro-F1 >= 0.95
- minimum known-class validation F1 >= 0.90

True target labels and all final/test/OSR metrics are forbidden from HPO selection.

## Deterministic candidate sequence

`experiments/l2o_hpo_generate.py` maps `(candidate_seed, trial_index, hyperparameter_name)` through SHA-256 to a fixed parameter value. The same trial index therefore means the same hyperparameter vector across all weak canonical pairs.

Default candidate seed: `6022026`.

Screen candidates are consumed in fixed waves of 8. A later wave never changes earlier candidate identities.

## Resource ladder

The repository's reviewed HPO space remains authoritative:

- screen: up to 96 candidates, 8 epochs
- refine: up to 24 candidates, 24 epochs
- finalist: up to 6 candidates, 60 epochs

Pilot controller policy:

1. screen 8 candidates per unresolved pair;
2. rank using known validation only;
3. promote top 2 per pair to refine;
4. promote best refined candidate to finalist;
5. freeze a pair only when a terminal finalist clears both competency thresholds;
6. otherwise consume the next deterministic screen wave until the reviewed budget is exhausted.

## Immediate OSR pilot

After a pair freezes, run known-test once and then both standard-DQNGuard directional OSR evaluations.

These target-open results are an exploratory resource-allocation gate only. They must never choose new hyperparameters for that pair.

Frozen H1 practical-effect gate:

- mean two-direction delta Unknown-F1 >= +0.05 versus current repaired baseline;
- neither direction regresses by more than 0.02;
- known-reject budget remains satisfied.

## Ledger

`experiments/l2o_hpo_ledger.py` provides fail-closed state transitions. Once a pair is frozen—and especially after target-open evaluation—the controller cannot silently register or substitute another trial.

## Validation

`tests/test_l2o_hpo_controller.py` verifies:

- deterministic shared candidate vectors;
- topology/quarantine invariants;
- promotion preserves parameters;
- ranker rejects target/test/OSR metrics;
- min-class feasibility rule;
- final competency gate;
- immutable freeze after target-open evaluation.
