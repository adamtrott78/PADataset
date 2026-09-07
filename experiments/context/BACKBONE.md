# PA backbone models and evidence interface

Read this for architecture, training-loss interpretation, checkpoint loading,
or extracting classifier evidence for an OSR method. The
[experiment framework](../CONTEXT.md) owns manifests, launchers and run lifecycle;
the [preprocessing context](../../scripts/preprocess/CONTEXT.md) owns feature
construction, normalization, global PA labels and cache validation.

## Source and boundaries

| Source | Role |
|---|---|
| [discriminate.py](../../discriminate.py) | PyTorch model, losses, training, checkpoints and post-training evaluation |
| [prepData.py](../../prepData.py) | Cached tensors, class filtering, fold mapping and data loaders |
| [evaluate.py](../../evaluate.py) | Closed-set metrics and confidence diagnostics |
| [osr_core.py](../../osr_core.py) | Backbone reload and split/payload API consumed by decision layers |
| [pa_train_one.py](../pa_train_one.py) | Single PyTorch training worker |
| [train_shreyash_keras_pa_stream.py](../train_shreyash_keras_pa_stream.py) | Separate streaming RF adaptation of the DQN-IDS CNN |
| [train_shreyash_keras_pa_one.py](../train_shreyash_keras_pa_one.py) | Earlier in-memory Keras training path |

The closed-set backbone emits evidence over its known classes. It does not itself
produce a calibrated unknown decision, an ATT&CK/EW technique label, or an
attack-chain prediction. An unknown input can still receive a high-confidence
closed-set prediction; rejection belongs to the downstream decision layer.

## PyTorch architecture and tensor contracts

`ModulationClassifierReduced` consumes `[B,8,L]`, where B is batch size, eight
channels are the ordered IQ/FFT/DCT/polar stack, and L is pooled window length.
Use L=8192 for the author-confirmed paper setting. Do not confuse the cache's
average pooling with the pooling inside each convolutional branch.

| Stage | Operation | Output per window |
|---|---|---|
| Eight independent branches | One input channel per branch; weights are not shared across branches | Eight branch outputs |
| Each branch | Conv1d 1→32 (kernel 5, stride 1, padding 2); 32→64 and 64→128 (kernel 3, stride 2, padding 1) | Downsampled sequence |
| After each convolution | BatchNorm and LeakyReLU with slope 0.1 | Same channel count |
| Branch pooling | AdaptiveAvgPool1d(1), then flatten | 128 values |
| Concatenation | Eight × 128 | 1024 values |
| MLP | Linear 1024→1024→512→256; LeakyReLU and configured dropout after each layer | 256 values |
| Classifier | Linear 256→K | K logits for the fold's known classes |

`forward(x)` returns logits. `forward(x, return_features=True)` returns logits
and the **256-value MLP embedding**. `extract_features(x)` instead returns the
**1024-value branch concatenation**. The shared OSR collector uses the former,
so `SplitOutputs.features` is `[N,256]`. A change between these representations
changes the method input and must be deliberate.

`input_len` is stored as model/checkpoint metadata; `forward` does not enforce it.
Adaptive branch pooling permits multiple input lengths without changing the
classifier weight shapes. Successful checkpoint loading therefore cannot prove
that the original input length was 8192. Inspect actual cache shape and run
provenance as described in the preprocessing context.

## Training objective and model selection

The PyTorch training loss is:

`cross_entropy + lambda_center * center_loss + entropy_loss_weight * entropy`.

Cross-entropy supports label smoothing and optional balanced class weights.
Center loss is mean-squared distance from the 256-value embedding to its learned
class center. Entropy is the mean softmax entropy; a positive coefficient
penalizes high entropy, encouraging sharper predictions. Do not describe its sign
as encouraging uncertainty. Adam jointly optimizes model and center parameters;
optional gradient clipping covers both. `scheduler_name="cosine"` refers to
learning-rate scheduling, not a cosine-similarity loss.

Read the saved effective config for actual coefficients. The reference profile
uses label smoothing 0.1, center weight 0.1 and entropy weight 0.05; those are
profile choices, not universal constants. Training-loss components are recorded
separately in `history.json`. Validation classifier loss uses the evaluation
routine's cross-entropy, so it is not the same composite objective as training.

The [framework context](../CONTEXT.md) defines split and held-out-target semantics.
In `known_only` selection, the configured known-validation metric determines
the best checkpoint. In `open_conf` selection, balanced known/open validation
streams are required, and `open_conf_selection_metric` determines selection.
The reference uses `dqn_proxy_expanded5`. These proxy scores are backbone
diagnostics, not a completed DQNGuard calibration or test OSR score. Withheld
target validation can affect model selection even though target examples do not
enter the backbone's gradient-training set. Post-training evaluation reloads
`best_model.pt`; it does not automatically report the final epoch instead.

## Train or inspect an existing run

Use the reviewed configuration and GPU launcher in the
[framework workflow](../CONTEXT.md). There is no need to call `discriminate.py`
as an invented training CLI. The actual worker interface is
`python experiments/pa_train_one.py --cfg <config.json>`, with GPU coordination
provided by its shell wrapper. Class names and output width come from the fold's
data mapping; never infer them from the global five-class list alone.

Run from the repository root in `(DNNs)`. This CPU example loads the completed
framework demonstration run and predicts one cached window. It performs no
training and writes no outputs. It assumes that run actually exists; replace
the path when inspecting another run.

```bash
python - <<'PY'
from pathlib import Path
import h5py
import torch
from osr_core import load_backbone_run

run_dir = 'results_pa_context_train01/context_og_ref_unkPA2_c8192_seed0'
handle = load_backbone_run(run_dir, 'best_model', device='cpu')
assert handle.checkpoint['input_len'] == handle.config['cache_len'] == 8192
assert len(handle.class_names) == handle.num_classes
cache_files = sorted(Path(handle.config['cache_root']).expanduser().glob('*.h5'))
assert cache_files, 'No feature caches at saved path'
with h5py.File(cache_files[0], 'r') as f:
    assert f['Xfeat'].shape[1:] == (8, 8192)
    x = torch.from_numpy(f['Xfeat'][0:1]).float()
with torch.no_grad():
    logits, features = handle.model(x, return_features=True)
    probs = logits.softmax(dim=1)
assert logits.shape == (1, handle.num_classes)
assert features.shape == (1, 256)
assert torch.isfinite(logits).all() and torch.isfinite(features).all()
pred = int(probs.argmax(dim=1).item())
print('Checkpoint epoch:', handle.checkpoint['epoch'])
print('Known class order:', handle.class_names)
print('Closed-set prediction:', handle.class_names[pred])
print('Probabilities:', probs.tolist())
PY
```

The selected window may come from a class outside the known set. This command
demonstrates the evidence interface; its printed prediction is not an accuracy
measurement or an unknown-rejection decision. `load_backbone_run` calls `eval()`,
disabling dropout and using BatchNorm running statistics for inference.

Checkpoints contain `model_state_dict`, `num_classes`, `input_len`, `epoch`,
`class_names`, configuration and selection/evaluation metadata. The run-level
`config.json` is also required by `load_backbone_run`. Keep both together.
The checkpoint writer does not save optimizer, scheduler or learned center-loss
state, so these `.pt` files are not complete resumable training snapshots.
Only use checkpoint tags that exist; early stopping can leave epoch milestone
files absent. The framework documents completion and partial-directory behavior.

## Extract evidence for a decision layer

For an existing `handle`, the Python API is:

```python
from osr_core import extract_backbone_outputs
split = extract_backbone_outputs(
    handle, 'val_known', batch_size=16, num_workers=0, pin_memory=False,
)
print(split.logits.shape, split.features.shape, split.probs.shape)
```

This traverses the entire selected split and retains its outputs in memory.
It expects an `open_pa` run and accepts `val_known`, `test_known`, or `test_open`.
It rebuilds the data bundle from saved settings; verify `skip_cache_build=True`
and cache provenance if the task must only consume existing caches. Do not
invent a `val_open` argument to this API: dedicated evaluators construct the
additional calibration streams they require. `build_backbone_payload` can
collect several supported splits in one data-bundle construction.

Each `SplitOutputs` holds `y_true`, logits, 256-value features, probabilities,
closed predictions and optional sample metadata. Probabilities in the shared
collector use ordinary softmax of logits. Global PA labels are mapped to the
fold's contiguous known-class indices; open labels use the data layer's unknown
sentinel. Use `handle.class_names` and payload metadata to interpret predictions.
Calibration algorithms determine which splits may influence fitted parameters;
do not substitute test outputs merely because the API makes them available.

The confidence helper in `evaluate.py` supplies maximum softmax probability,
top-two probability gap, entropy, positive `T*logsumexp(logits/T)` energy, and
variance of absolute logits. These definitions are implementation-specific:
do not silently switch to negative energy or feature variance when discussing
that helper. Method-specific modules must still be checked for their own scoring
definitions and thresholds.

## Adapted DQN-IDS backbone boundary

Per the author's account, the comparator copies the peer's DQN-IDS model for
CICIDS2017/UNSW as closely as practical and adapts it to RF signal input. The
local implementation is a TensorFlow/Keras CNN, separate from the eight-branch
PyTorch backbone. This is its technical lineage, not an assertion that tabular
network-flow data and the RF representation are interchangeable.

Its input is transposed to `[B,L,8]`. The CNN uses Conv1D filters 8→24→32 with
kernel size 3, ReLU, BatchNorm and max pooling; global average pooling precedes
a 48-unit dense feature layer, ReLU/dropout 0.5 and a K-class softmax. The recipe
uses L2 regularization and categorical cross-entropy plus entropy. Preserve its
own hyperparameters and `.keras` loading/custom-loss conventions when reproducing
this track rather than inheriting PyTorch settings.

The streaming trainer exposes `--resume`; the PyTorch worker does not offer an
equivalent capability. Keras lifecycle and calibration details are in the
[DQN-IDS adaptation context](DQN_IDS.md). The inspected comparator evaluator adds a banded
guard to this Keras backbone; document backbone identity and decision-layer
identity separately when interpreting the manuscript's “DQN-IDS-style head.”

## Validation scope

Architecture, checkpoint fields and API examples were checked against source at
`71e7f533f2e15d0f78114d8ad2131d646cdd44a3`. Example syntax was checked without
loading user checkpoints or running training/inference during documentation
authoring. For a changed model, validate input/output shapes, class order,
checkpoint reload, and the embedding consumed by OSR before launching a matrix.
Retain checkpoints, config, source version, cache identity and split seed as
one provenance chain; generated summaries cannot replace that information.
