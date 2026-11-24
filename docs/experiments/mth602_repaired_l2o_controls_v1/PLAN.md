# MTH602 repaired L2O matched control matrix v1

Status: **FROZEN PLAN — NO EXECUTION YET**

## Scope

This plan freezes the control experiment that follows the repaired 20/20 standard-DQNGuard matrix. It reuses the exact ten competent t007 leave-two-out backbones bound in PADataset PR #54 at `f1256048b51fd863ad3fb46f9c547eff401016e7`. No backbone is retrained and no existing DQNGuard, selector, or OSR result is changed.

The scientific question is cell-by-cell: **how much does frozen standard DQNGuard improve over matched control decision heads when representation/backbone evidence is held fixed?**

## Frozen control definitions

### 1. DQN-IDS-style confidence head — matched backbone

Use the historical DQN-IDS confidence-state mechanism on the **same frozen PyTorch backbone outputs** as DQNGuard:

- state = `(P1, P1-P2, entropy)` (`softmax3`);
- DQN hyperparameters remain the repository's paper-style values: gamma 0.95, epsilon 1.0, epsilon-min 0.05, epsilon-decay 0.99, learning rate 1e-3, replay memory 2000, minibatch 32, 30 episodes, 5% anchors, training subsample 1250, centroid-update cosine threshold 0.75, DQN seed 42;
- paper-scale calibration = **625 known + 625 external-surrogate open**;
- the open calibration split is the already-frozen external surrogate for that directional cell, never the true target;
- final decision is the hard DQN action. Do **not** add DQNGuard variance/energy bands or a percentile score threshold.

This is intentionally named **DQN-IDS-style confidence head (matched backbone)**. The later historical Shreyash TensorFlow/Keras comparator used a different backbone plus a banded guard; rerunning that Keras model would violate the matched-backbone objective. It remains historical provenance, not the matched control matrix.

The current generic `--method-family dqn` path may not be used unchanged because it obtains `val_open` from the evaluated target. The implementation for this matrix must instead consume the directional evaluator's external-surrogate validation partition and assert that no target-open/test labels enter fitting.

### 2. VarMax — historical surrogate-all

Preserve the paper control exactly as **VarMax surrogate-all**:

- method family `varmax`;
- calibration mode `surrogate_all`;
- historical `smoke` sweep grid;
- temperature 1.0, energy enabled, predicted-class fitting, minimum five samples per class;
- known validation is partitioned internally by true known class into fit/guard/score subsets; each known class can serve as the pseudo-unknown candidate and all candidates compete for one selected result;
- the externally withheld surrogate is **not** VarMax calibration evidence.

For matrix alignment each directional row retains `target` and `external_surrogate` provenance because it shares a frozen leave-two-out backbone with DQNGuard. That does **not** make VarMax a surrogate-specific method. Do not relabel it as one.

## Target/test firewall

For both controls:

1. no target labels in fitting/calibration/sweep selection;
2. no target test before the method definition and calibration are frozen;
3. target test is consumed only for final directional evaluation;
4. result evidence may never change the backbone recipe/checkpoint, DQNGuard threshold policy, control definition, selector formula, retry policy, or any previously frozen result.

## Matrix

The machine-readable contract is `manifests/l2o_control_matrix_plan_v1.json`. It binds all **10 frozen backbones / 20 directional cells** to exact backbone artifact IDs, digests, candidate SHAs, and `best_model` SHA256 values.

DQN-IDS-style produces one matched external-surrogate control result for each directional cell.

VarMax also produces one target evaluation per directional cell for joinability with the frozen DQNGuard matrix, but its `surrogate_all` calibration ignores the external surrogate. The surrogate field is provenance for the leave-two-out backbone only.

## Execution gate

**Do not admit control jobs from this plan alone.** Before execution, a candidate implementation must:

- rehydrate the exact frozen artifact/checkpoint for each cell;
- expose a bounded control-evaluation request type;
- build DQN calibration from exactly 625 validation-known and up to/exactly 625 frozen external-surrogate validation samples according to the frozen cap policy, never target-open;
- invoke historical VarMax `surrogate_all` unchanged;
- record actual calibration counts and sources;
- emit `target_labels_used_for_tuning=false` and `target_test_consumed_before_final_eval=false`;
- bind output to the exact backbone artifact digest/model SHA and control-plan SHA;
- validate all 20 directional request manifests before the first admission;
- prevent duplicate admissions.

## Required final analysis

After 20/20 matched controls close, report:

- DQNGuard minus each control for every directional cell;
- aggregate mean effects and uncertainty summaries;
- target-level effects;
- unordered-pair/backbone effects;
- whether DQNGuard gains concentrate in particular frozen target/surrogate/geometry regimes.

Control outcomes are post-freeze diagnostics and cannot feed back into any recipe.
