# Corrected L2O Target–Surrogate Matrix v1

## Purpose
Repair the published 20-cell Target–Surrogate experiment without changing DQNGuard. The historical matrix used one-epoch backbones and allowed true target-open validation evidence to influence checkpoint selection.

## Per-cell taxonomy
For ordered pair (target T, surrogate S), T != S: backbone gradients use the other three PAs; T is held out until final open test; S is absent from backbone taxonomy and loaded later by the unchanged surrogate-open DQNGuard evaluator.

## Frozen baseline
Preserve lr=2e-4, weight_decay=0, center=0.1, label_smoothing=0.1, entropy_weight=0.05, dropout=0.3, cosine scheduler, cache_len=16384 and batch_size=8. Corrections: epochs=60, patience=10, open_val_frac=0, known-only checkpoint selection, target quarantine, strict_tf32 deterministic profile.

## Competency gate / HPO escalation
Never use final test performance to decide retuning. A cell passes the baseline backbone gate when known-validation macro-F1 >= 0.95 and minimum known-class validation F1 >= 0.90. Failing cells enter known-only HPO. Final known-test is evaluated only after the recipe is frozen.

## Decision-layer invariance
For the backbone-repair comparison, keep the existing surrogate-open DQNGuard implementation unchanged. Any DQNGuard modification is a separate method experiment.

## Required evidence
Retain exact SHA/config/checkpoint, best epoch, validation macro/per-class F1, final known-test macro-F1/confusion, DQNGuard unknown F1, OSR macro-F1, known reject rate, AUROC, target/surrogate IDs, seed and partition provenance.

## Seed policy
Seed0 is the paired first pass, not a robustness claim. Later replication must separate partition seed from model/training seed.
