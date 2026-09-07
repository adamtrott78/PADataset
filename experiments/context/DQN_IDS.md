# DQN-IDS architecture adapted to RF

Read this to train, recover or evaluate the RF-adapted DQN-IDS comparator.
The [experiment framework](../CONTEXT.md) owns data/config preparation; the
[backbone context](BACKBONE.md) describes its architecture alongside the PyTorch
backbone. Use the [preprocessing context](../../scripts/preprocess/CONTEXT.md)
to validate cache shape, PA coverage and global-to-fold labels.

## Lineage and source ownership

Per the author, this comparator copies the peer's DQN-IDS model for CICIDS2017
and UNSW as closely as practical, adapting it to RF signals. TensorFlow/Keras
identifies its implementation, not an unrelated scientific baseline. It is
nevertheless a separate backbone from the eight-branch PyTorch classifier.
Document both backbone and decision layer when naming a comparison.

| Source | Responsibility |
|---|---|
| [train_shreyash_keras_pa_stream.py](../train_shreyash_keras_pa_stream.py) | Current streaming training, callbacks, checkpoints, diagnostic outputs |
| [train_shreyash_keras_pa_one.py](../train_shreyash_keras_pa_one.py) | Earlier in-memory training path; not interchangeable with the streaming CLI |
| [pa_eval_shreyash_keras_dqn_guard.py](../pa_eval_shreyash_keras_dqn_guard.py) | Keras reload, logit reconstruction, external-surrogate banded guard |
| [dqn_osr.py](../../dqn_osr.py) | Shared confidence DQN and banded guard |
| [pa_eval_osr_one.py](../pa_eval_osr_one.py) | Separate DQN decision-layer experiments on PyTorch checkpoints |

The dedicated Keras evaluator adds `BandedGuardDQNOSR` and a known-only score
threshold. It is not a pure confidence DQN on the shared PyTorch backbone.
Conversely, general `--method-family dqn` evaluation does not load Keras models.
The paper-facing name “DQN-IDS-style head” needs this implementation distinction
when tracing a result; a method label alone cannot establish backbone identity.

## Training contract

The streaming adapter converts cached `[8,L]` windows into `[L,8]` for Keras,
inferring L from actual input. The code comment mentioning 16384 is not a shape
constraint. Use 8192 for the author-confirmed paper setting and verify the actual
cache; historical exploratory paths/configs at 16384 are not the final paper run.

The model uses Conv1D filters 8/24/32 with kernel 3, ReLU, BatchNorm and max pooling;
global average pooling; a 48-unit dense layer, ReLU and dropout 0.5; then a
K-class softmax. Convolution/dense kernels use L2=0.005. The compiled loss is
categorical cross-entropy plus entropy with coefficient 1, plus Keras
regularization losses. Positive entropy weight penalizes uncertainty.
Balanced training-class weights are passed to fitting.

Adam starts at learning rate 1e-5 with clipnorm=1. Known-validation loss selects
`best_model.keras`, drives early stopping (patience 10), and reduces learning
rate (factor 0.5, patience 5, minimum 1e-7). PyTorch config values for optimizer,
entropy coefficient and checkpoint-selection metrics do not replace this recipe.

CLI defaults are 500 epochs, training batch 500 and prediction batch 512;
`--epochs` and `--batch-size` override these, not the JSON's similarly named
fields. `--data-root` defaults to `data` and overrides the setup root.
The trainer copies the input JSON to its output directory without recording all
CLI overrides there. Preserve the full command and printed effective settings.

## Train one execution-check run

Use the already reviewed full five-PA, three-protocol cache and example config
created in the framework context. The external surrogate PA1 must exist in that
cache while remaining outside the selected backbone classes. These commands
create a separate Keras config/run. Run in the existing `(DNNs)` environment,
which must provide TensorFlow/Keras as well as the shared PyTorch/data dependencies.

```bash
cd ~/adamArchives/Adam/varMax/PADataset
export PA_KERAS_CFG="manifests/configs/context_keras01/context_keras_unkPA2_c8192_seed0.json"
export PA_KERAS_RUN="results_pa_context_keras01/context_keras_unkPA2_c8192_seed0"
python - <<'PY'
import json
import os
import subprocess
from pathlib import Path
source = Path('manifests/configs/context_train01/context_og_ref_unkPA2_c8192_seed0.json')
cfg = json.loads(source.read_text())
assert cfg['split_mode'] == 'open_pa' and cfg['unknown_pas'] == ['PA2']
assert set(cfg['pas']) == {'PA2', 'PA3', 'PA4', 'PA8'}
assert cfg['cache_len'] == 8192 and cfg['skip_cache_build']
out = Path(os.environ['PA_KERAS_RUN'])
target = Path(os.environ['PA_KERAS_CFG'])
assert not out.exists() and not target.exists(), 'Choose fresh names.'
cfg['run_name'] = out.name
cfg['source_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(cfg, indent=2) + '\n')
print('Known PA3/PA4/PA8; target PA2; external surrogate PA1')
PY
CUDA_VISIBLE_DEVICES=0 python experiments/train_shreyash_keras_pa_stream.py \
  --cfg "$PA_KERAS_CFG" --out-dir "$PA_KERAS_RUN" --data-root data \
  --epochs 1 --batch-size 128 --predict-batch-size 128 \
  --epoch-metric-every 1
```

Use an available GPU; this command does not acquire the shared launcher's lock.
Replace `--data-root data` if the data setup requires another root. This is a
one-epoch execution check, not the final training recipe or a performance result.
It still traverses the selected data. For research training, use a fresh run and
deliberately choose the CLI epoch/batch settings.

`--smoke-n` takes the first N dataset indices before sequence shuffling, not a
stratified sample. It may omit classes and cause balanced-class-weight fitting
to fail. It also limits several final predictions, while per-epoch diagnostics
have a separate `--epoch-metric-n` cap. Do not assume it bounds all work equally.
The sequence uses the config seed for shuffling, but this trainer does not
explicitly seed TensorFlow model initialization; that seed alone does not
establish fully deterministic training.

## Inspect or recover an interrupted run

| Artifact | Meaning |
|---|---|
| `config.json` | Copied input config; retain CLI overrides separately |
| `latest_model.keras`, `latest_epoch.json` | Latest checkpoint and completed-epoch counter |
| `best_model.keras` | Lowest known-validation-loss checkpoint |
| `keras_history.csv` | Epoch training/validation history |
| `keras_backup/` | Keras BackupAndRestore state |
| `epoch_osr_metrics.csv`, `epoch_osr_metrics.jsonl` | Periodic confidence/anchor diagnostics |
| `final_model.keras` | Saved model after fitting and callback restoration; not necessarily last-epoch weights |
| `softmax_outputs.npz`, `summary.json`, `train_complete.json` | Post-fit predictions, metrics and successful completion |

Target-open validation is used for anchor diagnostics, not the known-validation
loss monitor. If unavailable, those diagnostics fall back to target test data;
inspect `anchor_source` and avoid using test-derived diagnostics for tuning.
Post-fit outputs explicitly reload `best_model.keras`.

To continue an interrupted run, preserve its existing source, config, command
and artifacts; check checkpoint/counter consistency first. Then repeat the
training command with `--resume` and the intended **total** `--epochs` value.
For example, after an interrupted 50-epoch job with 12 completed epochs, use
`--epochs 50 --resume`, not 38. Keep other settings identical.

Resume loads latest if present, otherwise best, and reads the epoch counter from
`latest_epoch.json` or the number of CSV history rows. If neither model exists,
`--resume` starts a new model. The best-checkpoint fallback may represent an
earlier epoch than the latest counter. State files and checkpoint saves are
separate callbacks; they are not an atomic snapshot. BackupAndRestore also
participates, while new EarlyStopping/ReduceLROnPlateau callbacks are created.
Do not claim exact uninterrupted continuation solely because loading succeeded.

There is no general skip-completed or reject-nonempty-directory guard. Startup
rewrites `config.json` even on resume. Use fresh directories for new experiments
and never use a changed config with an existing run without preserving provenance.

## Evaluate the Keras backbone with the guard

After successful training, use its config and an explicit Keras model path.
The following continues the example; pick a fresh evaluation output directory.

```bash
export PA_KERAS_OSR_OUT="results_pa_context_keras_osr01/og_PA2_surPA1_budget005"
python - <<'PY'
import os
from pathlib import Path
run = Path(os.environ['PA_KERAS_RUN'])
assert all((run / p).is_file() for p in ['config.json', 'best_model.keras', 'train_complete.json'])
assert not Path(os.environ['PA_KERAS_OSR_OUT']).exists(), 'Choose a fresh output directory.'
PY
CUDA_VISIBLE_DEVICES=0 python experiments/pa_eval_shreyash_keras_dqn_guard.py \
  --run-dir "$PA_KERAS_RUN" --model-file "$PA_KERAS_RUN/best_model.keras" \
  --out-dir "$PA_KERAS_OSR_OUT" --surrogate-open-pa PA1 \
  --known-cap 625 --open-cap 625 --max-known-reject-cal 0.05 \
  --batch-size 128 --data-root data
```

For another saved run, verify target, surrogate and known-class disjointness,
cache shape and class order before evaluating. The model path is consumed as
supplied; it is not automatically relative to `--run-dir`. The evaluator loads
the custom entropy loss from the streaming trainer. It requires the named
`softmax` layer, reconstructing logits as `features @ W + b` from its 48-value
input. It does not derive logits by taking log probabilities.

Unlike the dedicated PyTorch evaluator, this CLI always uses score thresholding;
there are no `--decision-mode`, `--mode`, `--device` or `--checkpoint` flags.
GPU visibility is controlled externally. Its fixed guard uses CPU DQN fitting,
seed 42, softmax3 states and var/energy hard bands, then replaces the hard
decision with the combined-score cutoff. The score still includes gap-band
distance. The known-only 95th-percentile cutoff is selected after DQN fitting
with known plus surrogate calibration; it is not a known-only fitting procedure.
See [DQNGuard](DQNGUARD.md) for the score and budget interpretation.

Calibration caps apply after full evidence collection. Zero means uncapped,
not an empty split. The output is one `osr_summary.csv`; there is no evaluator
completion JSON or serialized fitted guard. Check exit status, target/surrogate,
actual calibration counts, measured rejection and unknown/OSR metrics. Reuse
overwrites the CSV. The method-name string hardcodes `PA1surrogate` even if another
surrogate is requested; use `surrogate_open_pa` and the recorded command to
resolve that naming discrepancy.

## Distinguish a pure DQN decision-layer experiment

The general PyTorch evaluator supports
`--method-family dqn --modes paper` with a PyTorch `best_model.pt`.
It fits `DQNOSR` using known and true-target-open validation and applies its hard
known/unknown action, without the Keras backbone or known-budget cutoff.
Modes `paper`, `paper_mixed`, `cicids`, and `cicids_mixed` use the same factory;
their names do not load those datasets. General guard modes are another variant.
Do not substitute these commands for the dedicated Keras comparator above.

Interfaces checked against source at
`5541d7635bef987ee6d56b0d6b91521b1e439371`. Examples were checked statically;
TensorFlow training, checkpoint recovery and OSR were not executed during authoring.
