# Shared experiment framework

Read this to prepare a run, schedule training/evaluation, find artifacts, or
understand completion and rerun behavior. Start at the [root README](../README.md).
Inputs must satisfy the [bank/cache context](../scripts/preprocess/CONTEXT.md).
Load method implementation details only for the decision layer you are using.

For architecture, losses, checkpoint loading and the classifier evidence API,
continue to the [backbone context](context/BACKBONE.md).

## Conceptual model and source ownership

A backbone learns the selected known PA classes. An OSR method operates on its
outputs and uses a specified calibration regime to decide whether to reject a
window as unknown. Training, model selection, calibration, and held-out testing
are distinct operations. A training fold's withheld target is not automatically
the class supplied as a surrogate during calibration.

| Source | Responsibility |
|---|---|
| [pa_constants.py](pa_constants.py), [pa_experiment_catalog.py](pa_experiment_catalog.py) | PA subsets, source profiles, families and named run groups |
| [pa_make_train_manifest.py](pa_make_train_manifest.py) | Catalog/grid → JSON configs and training TSV |
| [pa_train_one.py](pa_train_one.py), [discriminate.py](../discriminate.py) | One PyTorch backbone training run and completion checks |
| [prepData.py](../prepData.py) | Cached data selection and splits |
| [run_pa_train_parallel.sh](../scripts/train/run_pa_train_parallel.sh) | GPU assignment, locks, worker logs |
| [pa_make_osr_eval_manifest.py](pa_make_osr_eval_manifest.py) | Selected training summaries → evaluation TSV |
| [pa_eval_osr_one.py](pa_eval_osr_one.py) | General VarMax/DQN evaluator |
| [run_pa_osr_eval_parallel.sh](../scripts/eval/run_pa_osr_eval_parallel.sh) | General evaluation workers; defaults to VarMax |
| [pa_reduce_train_summaries.py](pa_reduce_train_summaries.py), [pa_reduce_osr_summaries.py](pa_reduce_osr_summaries.py) | Discover and concatenate saved summaries |

Relevant method entry points are
[pa_eval_dqn_guard_surrogate_open.py](pa_eval_dqn_guard_surrogate_open.py) for
DQNGuard, [varmax_osr.py](../varmax_osr.py) for VarMax, and
[dqn_osr.py](../dqn_osr.py) for confidence/guard implementations. The separate
[Keras evaluator](pa_eval_shreyash_keras_dqn_guard.py) uses a model adapted from
the peer's DQN-IDS architecture for RF inputs. It is a distinct backbone track;
do not apply PyTorch checkpoint commands to its `.keras` files or equate every
comparator with a pure confidence head on the same backbone.

## Configuration, folds and source boundaries

| Paper-set identifier | Selected global PAs |
|---|---|
| OG | PA2, PA3, PA4, PA8 |
| DISTINCT | PA1, PA3, PA4, PA8 |
| MASTER | PA1, PA2, PA3, PA4, PA8 |

In `split_mode="open_pa"`, `unknown_pas` identifies the withheld target within
`pas`; the remaining classes form the backbone's known set. For example,
OG/target PA2 gives known PA3/PA4/PA8. PA1 is outside that backbone set and can
serve as an external surrogate in the dedicated DQNGuard workflow. The cache
must contain any external surrogate the evaluator will later request.

Default data splits are shuffled windows within PA classes, with 70% training,
15% validation and the remainder test for the ordinary class split. These are
not acquisition-session or shard-grouped splits. Open-class splitting and
balanced validation selection also depend on the saved config. The target is
excluded from backbone gradient training, but `early_stopping_mode="open_conf"`
can use target validation evidence for checkpoint selection. In the reference
profile, `open_conf_selection_metric="dqn_proxy_expanded5"` controls that choice;
the simultaneous `model_selection_metric="val_macro_f1"` field does not override
the active open-confidence selection path.

Use 8,192 pooled length for the author-confirmed paper setting. Historical
catalog defaults, names and exploratory configs include 16,384. Effective JSON
and actual cache shape must agree; changing a name or CLI flag is insufficient.

## Prepare one explicit configuration

Run commands from the repository root in the existing `(DNNs)` environment.
This example uses an already validated **full OTA core cache**, including the
three protocols and five PAs. The upstream Burst-only demonstration cache is
insufficient. Set `PA_EXPERIMENT_CACHE` to your actual verified 8,192 cache root;
the path below is a placeholder to replace, not a known local artifact location.

```bash
cd ~/adamArchives/Adam/varMax/PADataset
export PA_EXPERIMENT_CACHE="/absolute/path/to/verified/8192/core/cache"
python - <<'PY'
import csv
import json
import os
import subprocess
from pathlib import Path

cache = Path(os.environ['PA_EXPERIMENT_CACHE']).expanduser().resolve()
assert cache.is_dir() and any(cache.glob('*.h5')), cache
template = Path('manifests/configs/ota_primary_matrix/og_ref_ent005_lr2e4_unkPA2_c16384_seed0.json')
cfg = json.loads(template.read_text())
run_name = 'context_og_ref_unkPA2_c8192_seed0'
save_root = 'results_pa_context_train01'
cfg_path = Path('manifests/configs/context_train01') / (run_name + '.json')
manifest = Path('manifests/context_train01.tsv')
assert not cfg_path.exists() and not manifest.exists(), 'Choose new example names or inspect existing definitions.'
assert not (Path(save_root) / run_name).exists(), 'Run directory already exists.'
cfg.update({
    'run_name': run_name, 'save_root': save_root,
    'cache_len': 8192, 'cache_root': str(cache),
    'epochs': 1, 'early_stopping_patience': 1,
    'skip_cache_build': True, 'force_rebuild_cache': False,
    'use_timestamped_run_dir': False, 'overwrite_existing_run': False,
    'run_group': 'manual_context_example',
    'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
})
cfg_path.parent.mkdir(parents=True, exist_ok=True)
cfg_path.write_text(json.dumps(cfg, indent=2) + '\n')
row = dict(run_name=run_name, paper_set=cfg['paper_set'],
           family_tag=cfg['family_tag'], unknown_pa='PA2', seed=cfg['seed'],
           gpu='0', cfg_path=str(cfg_path), save_root=save_root)
with manifest.open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(row), delimiter='\t')
    writer.writeheader()
    writer.writerow(row)
print(cfg_path.read_text())
print('Manifest:', manifest)
PY
```

This writes a new config and one-row TSV, not a training run. Review the printed
configuration and perform the cache checks in the preprocessing context before
launching. The one-epoch setting is an execution check, not the paper's training
recipe or a meaningful performance comparison. Other template settings are
retained deliberately; changes to source identity, PA selection or normalization
require reviewing those fields too. Recording Git HEAD does not capture dirty
working-tree changes; preserve their diff/source snapshot in run provenance.

## Catalog-generated matrices

Use `python experiments/pa_make_train_manifest.py --help` to see current choices.
To inspect named groups without creating a manifest:

```bash
python - <<'PY'
from experiments.pa_experiment_catalog import RUN_GROUPS
for name, group in RUN_GROUPS.items():
    print(name, group)
PY
```

The generator accepts `--run-group` or `--grid`, comma-separated `--paper-sets`,
`--unknowns`, `--families`, `--seeds`, `--gpus`, and `--protocols` (`all` is special).
`--out manifests/NAME.tsv` also writes configs under `manifests/configs/NAME/`.
Its output columns match the explicit TSV above. Use new output names to preserve
existing definitions. Generation can overwrite matching config/manifest files.

Important override order: a run group replaces paper sets, save root and seeds;
`--families` can replace its family list. Source-profile overrides are applied
after base configuration, and the OTA profile replaces `cache_root` even when
`--cache-root` was supplied. Generated cache length and `c16384` names are also
fixed by current code. There is no generator `--cache-len` flag. Review/amend the
generated JSON, run names and TSV together before using an 8,192 cache, following
the explicit-configuration pattern above. Metadata-only `no_rerun` groups and
unresolved `top_selected` families cannot be launched directly.

An existing manifest filename does not establish an identically named catalog
run group. In particular, do not invent `--run-group l2o_surrogate_matrix` from
the L2O filenames; those definitions and launchers follow a separate workflow.

## Train and monitor

The supported shared launcher needs GNU Parallel, `flock`, and the active Python
environment. Confirm the example's GPU 0 assignment is appropriate before use.
For a different checkout, `REPO="$PWD"` overrides the launcher's Lambda default.

```bash
REPO="$PWD" JOBS=1 bash scripts/train/run_pa_train_parallel.sh manifests/context_train01.tsv
```

The worker sets `CUDA_VISIBLE_DEVICES` from the TSV `gpu` column, caps CPU math
threads, and takes `/tmp/padataset_gpu_<gpu>.lock` without waiting. A busy lock
fails with exit 99; it is not a GPU queue. GNU Parallel stops launching new jobs
after a failure while already-running jobs finish. Concurrent launchers sharing
these locks coordinate, but unrelated jobs need not honor them. `JOBS` controls
worker concurrency, not the number of GPUs visible to each worker.

Logs are under `_runtime/train_workers/`: an aggregate log, GNU Parallel joblog,
and per-run logs. If scheduling more than one job, check row GPU assignment and
joblog failures; do not assume every scheduled row ran successfully.

The underlying single-run interface is
`python experiments/pa_train_one.py --cfg <repository-relative-config.json>`
with optional `--data-root`. Direct invocation does not acquire the wrapper's
GPU lock. TSV config paths must be repository-relative because the wrapper
prepends `REPO`; avoid tabs, newlines and shell metacharacters in manifest fields.

For the example, the run directory is
`results_pa_context_train01/context_og_ref_unkPA2_c8192_seed0/`.

| Artifact | Meaning |
|---|---|
| `config.json` | Saved effective run configuration |
| `best_model.pt`, `final_model.pt` | Selected and final PyTorch checkpoints |
| `history.json`, `summary.json` | Training history and run metrics |
| `train_complete.json` | Written by a successful new worker after artifact checks |
| `train_error.json` | Worker failure record where a deterministic run path is available |

The training worker skips an existing deterministic run when the first five
files exist. This check does not require/recreate `train_complete.json`, compare
the requested config, or validate file contents. Some specialized launchers do
require the marker, so their completion decisions can differ. Inspect the files
before interpreting either outcome. The trainer normally refuses a nonempty
partial directory; `--no-skip-existing` is not checkpoint-resume support. Preserve
failed outputs and choose a new run name for a deliberate rerun. Re-running a
matrix skips complete runs but does not automatically repair partial ones.

## Reduce summaries and run general OSR evaluation

After successful training, collect just this example's output root:

```bash
python experiments/pa_reduce_train_summaries.py \
  --results-root results_pa_context_train01 \
  --out results/context_train01_leaderboard.csv
```

Inspect the CSV before constructing an evaluation manifest. Require valid
`run_name`/`run_dir`, the intended config/checkpoint, and no error rows. For this
single-run example the expected training row count is one. Then:

```bash
python experiments/pa_make_osr_eval_manifest.py \
  --train-leaderboard results/context_train01_leaderboard.csv \
  --out manifests/context_osr01.tsv --gpus 0 \
  --checkpoint best_model --modes surrogate_all --sweep-grid smoke \
  --out-root results_pa_context_osr01
REPO="$PWD" JOBS=1 bash scripts/eval/run_pa_osr_eval_parallel.sh manifests/context_osr01.tsv
python experiments/pa_reduce_osr_summaries.py \
  --results-root results_pa_context_osr01 \
  --out results/context_osr01_leaderboard.csv
```

This shared evaluation launcher runs **VarMax**: it does not pass `--method-family`
and the evaluator defaults to `varmax`. `surrogate_all` here means VarMax's
internal calibration regime, not DQNGuard with an external Scan surrogate.
`smoke` is an evaluator sweep-grid size, not a guarantee of paper settings.
The general evaluator also accepts `--method-family dqn` or `both` when called
directly; the manifest schema has no method-family field. DQNGuard uses its
dedicated entry point and calibration options instead of this generic recipe.

Evaluation TSV columns are `run_name`, `run_dir`, `checkpoint`, `gpu`, `modes`,
`sweep_grid`, `out_dir`. Paths consumed by the shared wrapper are repository-relative.
Worker logs default to `_runtime/osr_eval_workers/`. Evaluation output directories
contain `osr_progress.json`, `osr_summary.csv` and `osr_complete.json` on success,
or an error record on failure. Reusing an output directory reruns evaluation and
can replace artifacts; there is no general skip-complete check here. Choose
distinct output roots for changed modes, checkpoints or methods to prevent collisions.

## Results authority, validation and further context

Reducers search one directory level for `*/summary.json` or `*/osr_summary.csv`.
They concatenate results and can retain parse-error rows. They do not verify
matrix completeness or compute scientifically valid means/stds across seeds and
folds. Compare expected manifest identities with successful run outputs, reject
errors and duplicates, and preserve method/calibration identity before aggregation.

Generated leaderboards, progress records, runtime logs and indexes describe
specific executions; they do not override code or intended workflow. Conversely,
a stale directory name is not evidence of actual cache shape. Retain source
commit/diff, reviewed config, cache/manifest provenance, seed, withheld class,
checkpoint, evaluator options, logs and summary together. Large outputs may exist
only on Lambda through ignored directories or symlinks.

These contracts were checked against source at
`9eb7bcb80bb0ae9b5976f0e243cc6e5326fcbef3`; example shell/Python syntax and CLI
options were checked without launching training or OSR. A successful one-epoch
workflow checks execution, not research validity. Backbone details are covered in
the linked context. Method and result-analysis contexts are added separately;
until then, use the source links above for those details.
