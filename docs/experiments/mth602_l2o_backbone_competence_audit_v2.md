# MTH602 canonical backbone competence/stability audit v2

Source: the 10 frozen canonical Track-A backbone artifacts. The audit reads each artifact's `summary.json`, `history.json`, and best-checkpoint `val_stats`. It does **not** use target-open OSR metrics for training decisions.

## Competency result

The written gate is validation macro-F1 >= 0.95 and minimum known-class validation F1 >= 0.90.

- **PA2-PA3** fails both: macro 0.9254; min-class 0.8788 (PA4).
- **PA2-PA8** fails macro only: macro 0.9433; min-class 0.9095 (PA4).
- **PA3-PA8** fails both: macro 0.8966; min-class 0.8258 (PA1).

The other seven pass both best-checkpoint thresholds.

## Stability observation

Best-checkpoint competence hides substantial epoch instability in several pairs. Examples:

- PA1-PA4: max adjacent validation macro-F1 drop ~0.833; 16 epochs below 0.80.
- PA2-PA4: max adjacent drop ~0.716; tail-5 mean only ~0.628 despite a perfect best checkpoint.
- PA3-PA4: max adjacent drop ~0.833; 6 epochs below 0.80.
- PA1-PA3: 10 epochs below 0.80 despite a near-perfect best checkpoint.

Therefore epoch stability remains a meaningful diagnostic. The initial weak-pair pilot still uses the already-frozen 0.95/0.90 competence gate. After the immediate standard-DQNGuard OSR pilot, the program may freeze a stability-aware uniform full-matrix qualification rule using only known-validation trajectories.

Machine-readable evidence: `docs/experiments/mth602_l2o_backbone_competence_audit_v2.json`.
