# DQNGuard calibration and evaluation

Read this to evaluate a saved PA backbone with DQNGuard, choose a calibration
regime, or interpret its unknown decision. First read the
[experiment framework](../CONTEXT.md) for run/config lifecycle and the
[backbone context](BACKBONE.md) for logits, embeddings and class mapping.

## Source and scientific role

| Source | Responsibility |
|---|---|
| [dqn_osr.py](../../dqn_osr.py), `BandedGuardDQNOSR` | Confidence DQN, predicted-class bands, combined score and hard decision |
| [pa_eval_dqn_guard_surrogate_open.py](../pa_eval_dqn_guard_surrogate_open.py) | PyTorch run loading, calibration selection, known-budget threshold and evaluation CSV |
| [evaluate.py](../../evaluate.py) | Known/open evaluation bundle and backbone evidence collection |
| [osr_core.py](../../osr_core.py) | Backbone loading and OSR metrics |
| [pa_eval_shreyash_keras_dqn_guard.py](../pa_eval_shreyash_keras_dqn_guard.py) | Separate adapted DQN-IDS Keras backbone plus guard evaluation |

DQNGuard is an RF evidence/triage layer over a closed-set PA backbone. Known PA
outputs can support downstream precursor reasoning; rejected windows are
candidates for later label-making and behavior discovery. This is not the whole
QR-CWoS system. The evaluator described here writes aggregate results, not a
persistent unknown-window discovery pool or an attack-chain prediction.

## Calibration and decision mechanics

The dedicated evaluator constructs a `softmax3` DQN confidence state from maximum
softmax probability, top-two probability gap and entropy. Its factory fixes the
DQN seed at 42, CPU fitting, 30 episodes, anchor fraction 0.05 and up to 1,250
training states. The CLI's `--device cuda` controls backbone inference; it does
not move this DQN factory to GPU. Fitting uses the supplied known/open calibration
states. It is an offline calibration procedure, not deployment-time continual RL.

The three-stage interpretation maps to code as follows:

1. **Predicted-class conditional calibration:** known calibration windows are
   grouped by the backbone's predicted class. Each class gets 5th–95th percentile
   bands for probability gap, logit variance and energy. With fewer than five
   samples in a predicted group, fitting falls back to its true-class group,
   then to the pooled known calibration values.
2. **Guard evidence:** each value outside its class band receives a nonnegative
   distance divided by band width (floored at `1e-8`). The guard score averages
   the gap, variance and energy distances. The combined unknown score is
   `Q(unknown) - Q(known) + band_weight * mean_band_distance`; the factory's
   `band_weight` is 1. Higher means more unknown-like.
3. **Known-only operating threshold:** in `score_threshold` mode, the evaluator
   uses the `(1-beta)` percentile of known calibration scores. At beta=0.05 this
   is the 95th percentile. Scores greater than or equal to the cutoff are rejected.

Variance here is variance of absolute logits; energy is positive
`T*logsumexp(logits/T)`. These are not interchangeable with variance of the
256-value embedding or a negative-energy convention. Class bands are fitted
using known calibration only. Open calibration affects DQN fitting; it does not
select the final known-only percentile cutoff.

## Choose the decision mode explicitly

| Mode | Actual decision |
|---|---|
| `--decision-mode hard` | Accept only if the DQN selects known and the selected hard band rule passes |
| `--decision-mode score_threshold` | Replace the hard decision with a cutoff on the combined continuous score |

The default decision mode is `hard`, and default `--max-known-reject-cal` is
0.25. The 5% workflow requires both `--decision-mode score_threshold` and
`--max-known-reject-cal 0.05`; setting the budget alone does not activate it.

`--mode var_energy` selects a variance-and-energy **hard acceptance rule**.
It does not remove probability-gap distance from the continuous score. Other
supported hard-band modes are `all`, `two_of_three`, and `any`. Do not infer a
two-term score merely from the name `var_energy`.

The budget is a calibration operating point, not a guaranteed test rejection
bound. Percentile interpolation, finite samples and tied scores can make even
calibration rejection differ from exactly 0.05. For example, rejecting 32 of
625 known calibration windows gives 0.0512. Report measured calibration and test
rejection separately.

## Fixed Scan-surrogate evaluation

Use a completed run whose backbone excludes both the target and the intended
surrogate from gradient training. For the framework's OG/PA2 example, the known
classes are PA3/PA4/PA8, the target is PA2, and external surrogate PA1 is added
only for the dedicated calibration stream. The underlying cache must include
that PA1 data and the correct global labels.

Run from the repository root in `(DNNs)`. This example consumes the completed
framework demonstration run, which is a one-epoch execution check rather than
a paper-performance reproduction. Replace its run path for a research evaluation.
Choose a new output directory for each changed configuration or calibration.

```bash
cd ~/adamArchives/Adam/varMax/PADataset
export PA_GUARD_RUN="results_pa_context_train01/context_og_ref_unkPA2_c8192_seed0"
export PA_GUARD_OUT="results_pa_context_dqnguard01/og_PA2_surPA1_budget005"
python - <<'PY'
import json
import os
from pathlib import Path
run = Path(os.environ['PA_GUARD_RUN'])
cfg = json.loads((run / 'config.json').read_text())
assert cfg['split_mode'] == 'open_pa'
assert cfg['unknown_pas'] == ['PA2']
assert set(cfg['pas']) == {'PA2', 'PA3', 'PA4', 'PA8'}
assert cfg['cache_len'] == 8192 and cfg['skip_cache_build']
assert (run / 'best_model.pt').is_file()
assert not Path(os.environ['PA_GUARD_OUT']).exists(), 'Choose a fresh output directory.'
print('Known: PA3/PA4/PA8; target: PA2; external surrogate: PA1')
PY
```

After this precheck succeeds and the linked cache checks confirm actual shape
and PA coverage, launch on the intended free GPU (0 in this example):

```bash
CUDA_VISIBLE_DEVICES=0 python experiments/pa_eval_dqn_guard_surrogate_open.py \
  --run-dir "$PA_GUARD_RUN" --checkpoint best_model \
  --out-dir "$PA_GUARD_OUT" --surrogate-open-pa PA1 \
  --mode var_energy --decision-mode score_threshold \
  --max-known-reject-cal 0.05 --known-cap 625 --open-cap 625 \
  --device cuda --batch-size 128 --num-workers 0
```

This direct evaluator does not acquire the shared launcher's GPU lock. The
general VarMax launcher is not a substitute for this command. `--known-cap`
caps known calibration with class stratification; `--open-cap` caps surrogate
calibration without stratification. Caps use deterministic offsets from the
backbone seed and apply after backbone outputs have been collected: lowering
them does not bound all feature extraction or inference memory.

There is no `--held-out` flag here. The saved run configuration determines the
target. The surrogate builder appends the requested surrogate to its data
selection and takes its open-validation stream. Verify target/surrogate/known
disjointness yourself; the CLI does not enforce the whole experimental design.

## Target–Surrogate Matrix

For validating completed pair coverage and rendering the paper matrix, use the
[results and analysis workflow](RESULTS.md).

For five PAs there are twenty ordered target/surrogate pairs with distinct
classes. Each cell requires a matching trained backbone with the other three
PAs as known classes. In its saved config, `pas` contains those three plus the
target, `unknown_pas` contains the target, and the surrogate is absent from
`pas`. The evaluator subsequently retrieves surrogate calibration windows from
the cache. Reusing a backbone that trained on the surrogate changes the regime.

The existing [L2O manifest](../../manifests/l2o_surrogate_matrix_gpu0.tsv) records
`run_name`, `gpu`, `cfg_path`, `target_unknown`, `surrogate_open`, `known_pas`.
These are different columns from the shared training TSV. Existing L2O names and
configs include exploratory 16384 settings; do not treat them as the final 8192
paper snapshot without tracing their provenance.

For each reviewed cell, use the same dedicated command above, replacing
`--run-dir` with its completed backbone directory, `--surrogate-open-pa` with
the cell's surrogate, and `--out-dir` with a unique cell directory. Check saved
config against that row before launching. Preserve the threshold mode, budget,
caps and seed policy across comparisons. Track all twenty successful cell
identities, not merely twenty files, before producing a matrix.

The recovered Lambda-only `run_l2o_dqnguard_eval_manifest.sh` automates those
calls as `bash run_l2o_dqnguard_eval_manifest.sh MANIFEST.tsv GPU_ID`.
It is not yet tracked on the inspected `research-framework` branch; the direct
evaluator above is the available GitHub entry point. That local wrapper:

- uses its positional GPU for every row and ignores the row's GPU column;
- hardcodes the Lambda checkout/environment and `results_pa_ota_l2o` run root;
- skips runs lacking `best_model.pt` or `train_complete.json`;
- skips output directories containing `osr_summary.csv`, without validating it;
- runs sequentially and acquires no shared GPU lock.

Do not launch the same full manifest on two GPUs through that wrapper and expect
automatic partitioning. Source recovery and matrix-wide execution instructions
must preserve these distinctions when the wrapper is added to GitHub.

## Target-open diagnostics: current CLI limitation

Conceptually, target-open diagnostic calibration uses labeled target validation
examples while still excluding them from backbone gradient training. This is a
different assumption from fixed-surrogate calibration and must be labeled as such.

The CLI offers `--mix-true-open` and `--surrogate-frac`, but the current endpoint
behavior prevents a faithful target-only recipe via fraction zero. `cap_split`
returns the entire input for a cap of zero. Therefore
`--mix-true-open --surrogate-frac 0.0` retains the full surrogate split and
concatenates capped target validation, rather than removing surrogate examples.
At fraction one, a zero target cap similarly retains the target split. Surrogate
data is constructed before either branch. Small rounded allocations can also
reach zero. Historical `oracle_trueopen` launcher names do not override this code.

This helper behavior was confirmed using five dummy rows and cap zero, which
returned all five. Do not advertise those endpoint commands as pure target-only
or pure-surrogate diagnostics. A corrected implementation and provenance review
are required before that claim; this documentation migration does not modify
the experimental algorithm. Interior mixtures with positive caps still need
their actual sample counts checked.

## Outputs, validation and reproducibility

The dedicated PyTorch evaluator writes one `osr_summary.csv` in `--out-dir` and
prints metrics. It does not write the general evaluator's `osr_complete.json`,
serialize the fitted DQN/bands, or save per-window unknown-pool artifacts.
Successful completion is the process exit plus a valid summary matching the
requested run and settings. Reusing its directory overwrites the summary.

Inspect target/surrogate identity, `decision_mode`, `max_known_reject_cal`,
`score_threshold`, actual calibration counts, `threshold_known_reject_cal`, and
known test rejection. Evaluate unknown precision/recall/F1, OSR macro F1/accuracy
and unknown AUROC together; rank quality and operating-point performance differ.
`threshold_open_recall_cal` is diagnostic and does not choose the cutoff.

Record the source version, saved backbone config/checkpoint, actual cache shape,
full evaluator command and stdout alongside results. The known-only threshold
description applies to cutoff selection, not to the entire DQN fitting or
backbone-selection history. Surrogate usefulness is target-dependent; a good
surrogate for one PA is not a universal unknown-behavior proxy.

Interfaces were checked against source at
`d9944bae6e1a046e10b0d8aa6f7f2413bd467557`. Shell/Python examples and the isolated
zero-cap helper were checked without running any research data, model fitting,
or OSR evaluation. Historical paper-run identity remains separate from this
current executable contract.
