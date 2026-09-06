# PADataset Research Framework

> **Purpose of this README:** this is the bootstrap/context document for humans and future AI chats working in this repository. Read this file before changing code, launching a data collection, running experiments, interpreting results, or editing a paper.
>
> The repository grew from a preliminary-action (PA) RF dataset project into a reusable research framework covering deterministic waveform generation, over-the-air (OTA) acquisition, signal resplicing, feature caching, model training, open-set-recognition (OSR) experiments, result aggregation/diagnostics, and evidence-grounded, exemplar-guided paper composition.

## 0. Repository state and branch doctrine

The accepted MILCOM 2026 paper was produced from the mature repository lineage, not from the old `main` branch. As of September 2026:

- `main` is a historical/stale base and does **not** contain the complete final experiment + paper framework.
- `milcom2026-final-handin` is the immutable source snapshot for the accepted MILCOM 2026 paper.
- `research-framework` was created from `milcom2026-final-handin` and is the recommended branch for future research, documentation, new experiments, and new papers.
- `legacy/` contains old notebooks, old preprocessing code, and debug versions retained for forensic/reference use.

On Lambda, begin with:

```bash
cd ~/adamArchives/Adam/varMax/PADataset

git status --short
git fetch origin
git switch research-framework
git pull --ff-only origin research-framework
```

If `git status --short` is not clean, **do not switch branches or pull blindly**. Commit, intentionally stash, or inspect the changes first.

### Historical milestone

The repository produced the accepted IEEE MILCOM 2026 paper:

> **DQNGuard: Towards Open-World RF Preliminary-Action Detection**

The accepted-paper source lives under `papers/milcom2026/`. The accepted snapshot should remain reproducible; new research should not rewrite history on `milcom2026-final-handin`.

---

# 1. Five-minute orientation

The complete pipeline is:

```text
PA definition / experiment idea
        |
        v
protocol-specific digital waveform generation
        |
        v
deterministic dataset plan + pilot shards
        |
        v
transport-sized digital TX tapes + TX specs
        |
        v
planned OTA TX/RX campaign
        |
        v
raw OTA tape capture
        |
        v
header-aware resplicing into per-PA RF windows
        |
        v
balanced/canonical OTA bank
        |
        v
feature-cache build (.h5, normally on NVMe)
        |
        v
manifest generation
        |
        v
parallel CNN backbone training
        |
        v
saved model artifacts
        |
        v
post-training OSR evaluation (DQNGuard / VarMax / comparison heads)
        |
        v
leaderboards + diagnostics + figures/tables
        |
        v
paper evidence map + exemplar-guided composition + LaTeX build
```

The most important rule is that **raw/generated data and experiment outputs are not the source of truth by themselves**. Reproducibility comes from the combination of:

1. tracked source code,
2. deterministic dataset plans and metadata,
3. tracked manifests/configs,
4. saved run artifacts,
5. reduced result tables/diagnostics,
6. paper evidence maps and generated figure/table scripts.

---

# 2. New-chat bootstrap sequence

A fresh AI chat should not begin by guessing from filenames or from the stale `main` branch. It should do the following in order:

1. Inspect the current branch and commit:

   ```bash
   git branch --show-current
   git status --short
   git log --oneline -8
   ```

2. Confirm that the intended working branch is `research-framework` unless the user explicitly requests an historical snapshot.

3. Read:

   ```text
   README.md
   AI_HANDOFF_README.md
   docs/experiments/final_rerun_plan.md
   experiments/pa_constants.py
   experiments/pa_experiment_catalog.py
   ```

4. For data/OTA work, inspect the exact scripts that will be used before giving a command. Important directories are `core/`, `protocol/`, `tools/`, `txrx/`, and `scripts/preprocess/`.

5. For experiment work, inspect the manifest, generated JSON configs, result root, and completion artifacts before changing hyperparameters.

6. For paper work, read `papers/milcom2026/PAPER_GROUND_TRUTH.md`, `PAPER_EVIDENCE_MAP.md`, and the paper-specific handoff sections in `AI_HANDOFF_README.md` before proposing prose changes.

7. Never assume a preview image, notebook cell, stale result directory, or old branch is authoritative when a tracked manifest/config/evidence map exists.

---

# 3. Environment and machine assumptions

## 3.1 Lambda repository path

The working Linux checkout has historically been:

```text
~/adamArchives/Adam/varMax/PADataset
```

Most shell launchers default to this path through `REPO`, but it can be overridden:

```bash
export REPO=/path/to/PADataset
```

## 3.2 Python environment

The research Python environment used on Lambda has historically been:

```bash
source ~/adamArchives/venvs/DNNs/bin/activate
```

Then verify:

```bash
which python
python --version
python -c 'import torch; print(torch.__version__, torch.cuda.is_available())'
```

The exact package environment may evolve. Do not reinstall or upgrade Torch/CUDA casually on the research machine just to fix one script; first determine whether the problem is code, pathing, cache format, or environment drift.

## 3.3 MATLAB

Waveform generation, dataset planning, TX/RX tape construction, OTA capture, and resplicing are primarily MATLAB workflows.

Typical noninteractive form:

```bash
matlab -batch "cd('$HOME/adamArchives/Adam/varMax/PADataset'); pa_setup_paths; <COMMAND>;"
```

For interactive RF/SDR collection, an interactive MATLAB session is usually preferable because the TX and RX batch scripts intentionally prompt the operator.

## 3.4 GNU Parallel

The final training/evaluation system uses GNU Parallel and per-GPU file locks.

Check:

```bash
parallel --version
```

The launchers deliberately set CPU-thread environment variables to `1` inside GPU workers and use `/tmp/padataset_gpu_<id>.lock` so two jobs do not accidentally occupy the same GPU.

## 3.5 Paper tooling

For the paper workflow, useful tools include:

```bash
latexmk
pdftoppm
python3
npm            # only needed for Mathpix CLI installation
mpx            # Mathpix CLI after installation/authentication
```

---

# 4. Repository map

## Root-level current code

```text
README.md                     this document
AI_HANDOFF_README.md          detailed paper/handoff history
config/                       project configuration JSON
core/                         shared deterministic PA/data helpers
protocol/                     WiFi/Bluetooth/Zigbee waveform code
training/evaluation modules   discriminate.py, evaluate.py, etc.
prepData.py                   dataset loading / feature preprocessing
cacheBuild.py                 cache-builder CLI
build_ota_bank.m              respliced OTA -> canonical prepData bank
experiments/                   final manifest-driven experiment control plane
manifests/                     tracked run manifests + generated run configs
scripts/                       preprocess/train/eval orchestration
results*/                      generated experiment outputs; usually ignored
_runtime/                      worker logs/status; generated
_feature_cache_nvme/           generated feature caches; never source control
papers/                        paper source + evidence/exemplar composition records
docs/                          durable experiment history, inventories, diagnostics
legacy/                        historical notebooks/scripts only
tools/                         dataset/OTA utilities
txrx/                          digital tape, SDR TX/RX, capture, resplice code
```

## What is current vs legacy

**Current experiment path:** use `experiments/*.py`, `scripts/train/`, `scripts/eval/`, `scripts/preprocess/`, tracked manifests, and saved run artifacts.

**Legacy experiment path:** `legacy/notebooks/pa_cnn_osr/` contains the old notebook-driven UI (`PADiscriminate`, `PAEvaluate`, etc.). Use it to recover historical behavior or rationale, not as the default way to run new science.

`docs/experiments/` contains the bridge between the two worlds: inventories, digital reconstruction, prior-chat experiment knowledge, final rerun design, committed reduced tables, and diagnostic artifacts.

---

# 5. Preliminary-action taxonomy

The final open-world RF work centers on five preliminary-action classes:

| PA | Paper name | Operational intuition |
|---|---|---|
| PA1 | Scan | discovery-like RF activity |
| PA2 | Burst | repeated short on-intervals separated by quiet gaps |
| PA3 | Sustain | persistent occupied-channel behavior |
| PA4 | Hop | frequency-agile dwell/revisit behavior |
| PA8 | Replay | repeated waveform/template behavior |

The final experiment control plane defines three useful PA universes in `experiments/pa_constants.py`:

```text
OG       = PA2, PA3, PA4, PA8
DISTINCT = PA1, PA3, PA4, PA8
MASTER   = PA1, PA2, PA3, PA4, PA8
```

Do not silently reinterpret PA numbers. There are historical WiFi generators for other PA IDs in `protocol/wifi/`; those are not automatically part of the final paper taxonomy.

---

# 6. Data generation: deterministic digital PA windows

The modern dataset-generation system deliberately separates **dataset identity** from **transport sharding**. This matters because changing the number of files/shards should not silently change random seeds or window identity.

## 6.1 Create a deterministic dataset plan

Core planner:

```text
core/pa_make_dataset_plan.m
```

It defines:

- protocol,
- SNR regime,
- dataset ID,
- PA order,
- number of windows per PA,
- number of transport shards,
- windows per segment,
- canonical global window IDs,
- canonical segment IDs/seeds.

Default scale is 10,000 windows per PA, 10 shards, 10 windows per segment.

Example in MATLAB:

```matlab
cd('~/adamArchives/Adam/varMax/PADataset')
pa_setup_paths

plan = pa_make_dataset_plan( ...
    "wifi", ...
    "high", ...
    "wifi_high_run02", ...
    'n_per_pa', 10000, ...
    'n_shards', 10, ...
    'windows_per_segment', 10, ...
    'pa_order', ["PA1","PA2","PA3","PA4","PA8"]);
```

Use a **new dataset ID** when the scientific data definition changes. Do not reuse an old ID for a different plan and hope filenames will distinguish the versions.

## 6.2 Generate protocol-specific pilot shards

Generator:

```text
tools/gen_pilot_shards.m
```

Example:

```matlab
gen_pilot_shards("wifi", plan)
```

Subset/resume example:

```matlab
gen_pilot_shards("wifi", plan, 'shards', 1:3)
```

Output layout:

```text
data/<protocol>/digital/pilot_shards/<dataset_id>/
    dataset_plan.mat
    shard_001/
        pilot_S01_PA1.mat
        pilot_S01_PA2.mat
        ...
```

Each pilot file contains RF windows (`Xsig_all`), metadata, and sometimes a schedule. Global `window_id` values are rewritten to the canonical IDs from the dataset plan.

`gen_pilot_shards` dispatches into the appropriate protocol family:

- WiFi: `protocol/wifi/` plus the PA1 generator in `tools/`
- Bluetooth: `protocol/bluetooth/`
- Zigbee: `protocol/zigbee/`

Current PA1/2/3/4/8 stream generators exist for the three protocol families.

## 6.3 Build transport-sized TX tapes

Use:

```text
txrx/build_tx_tape_shards.m
```

Example:

```matlab
build_tx_tape_shards("wifi", "wifi_high_run02")
```

Resume/subset:

```matlab
build_tx_tape_shards("wifi", "wifi_high_run02", 'shards', 1:2)
```

The implementation streams directly into v7.3 MAT files rather than retaining the entire transport tape in RAM.

Outputs:

```text
txrx/tapes/digital/<protocol>/<dataset_id>/
    tx_tape_shard_001.mat
    tx_spec_shard_001.mat
    ...
```

The TX spec contains the record index, PA IDs, window IDs, preamble/header configuration, and transport parameters needed by the receiver and resplicer.

### Never separate a TX tape from its TX spec

The `tx_spec_shard_###.mat` is not optional metadata. RX capture uses it to size the recording correctly, and resplicing uses it to map recovered RF records back to the intended PA/window identities.

---

# 7. OTA recording campaign

OTA collection is an operator-coordinated two-machine workflow. The repository is designed so both machines share the same recording plan.

## 7.1 Create a recording-session plan

Use:

```text
txrx/make_recording_session_plan_v01.m
```

Example:

```matlab
dataset_ids = struct( ...
    'wifi',      "wifi_high_run02", ...
    'bluetooth', "bluetooth_high_run02", ...
    'zigbee',    "zigbee_high_run02");

plan = make_recording_session_plan_v01( ...
    "high", dataset_ids, 10, ...
    'session_tag', "high_run02_session");
```

Optional canary recordings can be inserted at protocol-block boundaries and periodically between shards. This is useful for detecting RF-chain drift during long recording sessions.

The plan is saved under:

```text
results/recording_sessions/<session_tag>/
    recording_session_plan.mat
    recording_session_plan.txt
```

The readable `.txt` plan is extremely useful before a collection session: verify every TX tape, TX spec, intended RX output path, shard number, and protocol before touching the radios.

Expected canonical paths are:

```text
TX tape:
  txrx/tapes/digital/<protocol>/<dataset>/tx_tape_shard_###.mat

TX spec:
  txrx/tapes/digital/<protocol>/<dataset>/tx_spec_shard_###.mat

OTA RX tape:
  txrx/tapes/ota/<protocol>/<dataset>/ota_tape_shard_###.mat
```

## 7.2 Start the RX side first

RX batch runner:

```text
txrx/rx_capture_tape_batch_v01.m
```

Signature:

```matlab
rx_capture_tape_batch_v01(plan_file, ip, fc_hz, rx_gain_db, rx_ant)
```

Optional subset:

```matlab
rx_capture_tape_batch_v01(plan_file, ip, fc_hz, rx_gain_db, rx_ant, ...
    'step_ids', 1:5)
```

The script explicitly expects the receiver to be armed **before** the corresponding TX step begins.

## 7.3 Run the matching TX step

TX batch runner:

```text
txrx/tx_stream_tape_batch_v01.m
```

Signature:

```matlab
tx_stream_tape_batch_v01(plan_file, ip, fc_hz, gain_db, tx_ant)
```

It loads the same session plan, prompts before each step, calls `tx_stream_tape`, and writes per-step TX logs.

## 7.4 RF settings are site-specific inputs

Do not copy old IP addresses, gains, antenna IDs, center frequencies, or physical placement from a prior campaign without checking the current radios and the current experiment plan. The batch APIs deliberately require those values as inputs.

Historical MILCOM experiments used 2.4-GHz OTA hardware, but the README intentionally treats hardware parameters as **experiment configuration**, not universal repository constants.

## 7.5 Session logs

TX and RX batch runners write per-step logs under the recording-session result tree. Keep these when diagnosing:

- missing captures,
- wrong shard pairing,
- SDR underflow/overflow,
- gain mistakes,
- incorrect protocol/tape selection,
- an interrupted campaign.

---

# 8. OTA resplicing: raw tape -> per-PA windows

A raw OTA tape is not ready for model training. The transmitted record structure contains start sync, window preambles, headers, payloads, and guards. Resplicing recovers the payload windows and associates them with the TX-spec identities.

## 8.1 Canonical simple resplicer

The final OTA bank workflow is aligned with:

```text
txrx/rx_resplice_tape_simple.m
```

Usage example:

```matlab
rx_resplice_tape_simple("bluetooth", "high_run02", 1, ...
    'seed_k', 1800000)
```

It supports operator seed/fallback anchors and recovery options because long SDR recordings can suffer frame-scale slips.

Output layout:

```text
data/<protocol>/ota/spliced/simple/<protocol>_<dataset>/shard_###/
    ota_rx_PA1.mat
    ota_rx_PA2.mat
    ...

results/<protocol>/ota/rx_resplice_simple/<protocol>_<dataset>/shard_###/
    ...diagnostics...
```

PNG generation is optional and should normally be limited; it is useful for spot-checking recovered windows, not for replacing quantitative validation.

## 8.2 Session-plan batch resplicer

There is also:

```text
txrx/rx_resplice_tape_batch_v01.m
```

This consumes a session plan and writes a `spliced/v05/...` staging layout. It is useful for plan-driven batch processing. The final core-bank scripts historically consume the canonical `spliced/simple/...` layout, so **do not assume a staging layout is already the final training source**. Verify/promote the intended data definition explicitly.

## 8.3 Visual/structural checks before banking

Before building a canonical bank:

- verify that expected PA files exist,
- compare recovered counts with TX specs,
- inspect representative spectrograms,
- check metadata/window IDs,
- investigate suspicious high-confidence class confusions rather than hiding them,
- quarantine known-bad banks instead of overwriting evidence.

Useful tools include:

```text
tools/eval_ota_quick_v01.m
tools/find_top_ota_windows_v01.m
tools/make_png_pairs_from_spliced_v01.m
tools/quarantine_banks.py
```

---

# 9. Canonical OTA bank construction

`build_ota_bank.m` converts respliced OTA windows into the format consumed by `prepData.py`.

Example:

```matlab
summary = build_ota_bank("ota_core_high_run02", 1:10, ...
    'bt_shards', 1:10, ...
    'zb_shards', 1:10, ...
    'run_suffix', "high_run02", ...
    'pas', ["PA2","PA3","PA4","PA8"], ...
    'mode', "balanced");
```

Output layout:

```text
data/<protocol>/ota/<bank_name>/
    <bank_name>__shard_###__PA2.mat
    <bank_name>__shard_###__PA3.mat
    ...
```

The bank files are prepData-native tensors with labels/protocol/window/shard/source metadata.

### Balanced mode

The bank builder can balance the selected count per PA across protocols by taking the minimum available count. This was important for avoiding a protocol with more surviving windows from dominating the model.

### PA1 special handling in the final MILCOM pipeline

PA1 was acquired/processed on a different shard structure from the preexisting PA2/3/4/8 core bank. The final solution was **not** to perform a slow monolithic serial merge.

The working strategy was:

1. keep the established core bank for PA2/3/4/8,
2. map PA1 spliced shards into the core-shard namespace,
3. create small PA1 `part_*_of_*` bank files in parallel with `pa1_core_split_part_bank_v01.m`,
4. let `cacheBuild.py` consume those part files directly.

This split-part path is a validated optimization and should be preserved unless there is a scientific reason to redesign it.

---

# 10. Feature caching / preprocessing

Training directly from large MAT files repeatedly is expensive. The final system builds HDF5 feature caches on fast storage and trains from those caches.

## 10.1 Current final cache convention

The final experiment constants point to:

```text
_feature_cache_nvme/
  len16384/
    norm/
      ota__ota_core_high_run01__high_run01/
```

For new data, use a new source/dataset/noise namespace rather than mixing content under the historical path.

## 10.2 Generic cache builder

CLI:

```text
cacheBuild.py
```

Important arguments:

```text
--data-root
--cache-root
--cache-len
--normalize / --no-normalize
--source-type
--source-name
--dataset-tag
--noise-tag
--manifest-path       preferred when available
--source-glob
--force
```

Example shape:

```bash
python cacheBuild.py \
  --data-root "$PWD/data" \
  --cache-root "$PWD/_feature_cache_nvme/len16384/norm/ota__ota_core_high_run02__high_run02" \
  --cache-len 16384 \
  --normalize \
  --source-type ota \
  --source-name ota_core_high_run02 \
  --dataset-tag ota_core_high_run02 \
  --noise-tag high_run02 \
  --source-glob 'wifi/ota/ota_core_high_run02/*.mat'
```

Note: `cacheBuild.py` has a generic CLI default of `8192`, while the **final manifest experiment system explicitly uses `16384`**. Do not infer the experimental cache length from the CLI default.

## 10.3 Final unified MILCOM preprocessing script

For reproducing the accepted final source structure, the most mature orchestrator is:

```text
scripts/preprocess/run_unified_core_splitpa1_cache_v03.sh
```

It performs:

- input prechecks,
- core-label relabeling,
- parallel PA1 split-bank creation,
- stale PA1 cache cleanup,
- parallel feature-cache creation,
- count verification.

Historical defaults include:

```text
protocols      wifi bluetooth zigbee
core bank      ota_core_high_run01
noise tag      high_run01
core shards    1..20
PA1 dataset    pa1_run01
parts/core     2
cache length   16384
```

Run it only when those inputs are actually the intended source definition. For a new campaign, copy/adapt parameters or expose them as environment variables rather than overwriting the old corpus.

Example controlled override:

```bash
CORE_BANK=ota_core_high_run02 \
CORE_NOISE=high_run02 \
DATASET_SUFFIX=pa1_run02 \
CACHE_LEN=16384 \
SPLIT_JOBS=16 \
CACHE_JOBS=16 \
bash scripts/preprocess/run_unified_core_splitpa1_cache_v03.sh
```

Before doing this, inspect the script and make sure its core-shard/PA1-shard mapping is still correct for the new campaign.

## 10.4 Cache validation

Useful current utilities:

```text
experiments/pa_audit_feature_cache.py
experiments/pa_preflight_cache_dataset.py
scripts/preprocess/pipeline_status.sh
```

A missing or stale `.h5` should be treated as a data-preparation problem, not patched by changing training code.

---

# 11. Final model-training architecture

The mature experiment system is manifest-driven and non-notebook-based.

Core pieces:

```text
experiments/pa_constants.py
experiments/pa_experiment_catalog.py
experiments/pa_make_train_manifest.py
experiments/pa_train_one.py
scripts/train/run_pa_train_parallel.sh
discriminate.py
prepData.py
```

## 11.1 What a training run is

A manifest row points to a JSON config. `pa_train_one.py` loads that config and calls:

```python
discriminate.run_experiment(...)
```

A non-timestamped training run is considered complete only if these files exist:

```text
config.json
best_model.pt
final_model.pt
history.json
summary.json
```

The wrapper then writes:

```text
train_complete.json
```

On failure it attempts to write:

```text
train_error.json
```

This artifact-based completion rule is what makes sweeps resumable.

## 11.2 Final family grid

The retained family comparisons in `experiments/pa_constants.py` include:

```text
ref_ent005_lr2e4
ref_ent005_lr5e4
ref_noent_lr5e4
ref_ls000_noent_lr5e4
```

The final baseline configuration uses, among other settings:

```text
cache_len                 16384
source_type               ota
source_name               ota_core_high_run01
split_mode                open_pa
open_val_frac             0.15
require_true_val_open     true
lambda_center             0.1
scheduler                  cosine
early_stopping_mode       open_conf
model_selection_metric    val_macro_f1
open_conf metric          dqn_proxy_expanded5
default full epochs       60
default patience           10
```

These are the accepted-project defaults, **not immutable universal truths**. A new research project may change them, but changes should be explicit in a new family/run-group definition so historical runs remain interpretable.

## 11.3 Generate a manifest

Smoke test first:

```bash
python experiments/pa_make_train_manifest.py \
  --run-group smoke_functional \
  --out manifests/smoke_functional.tsv \
  --gpus 0,1
```

Main historical OTA matrix:

```bash
python experiments/pa_make_train_manifest.py \
  --run-group ota_primary_matrix \
  --out manifests/ota_primary_matrix.tsv \
  --gpus 0,1
```

The manifest generator creates:

```text
manifests/<name>.tsv
manifests/configs/<name>/<run_name>.json
```

The TSV contains at least:

```text
run_name
paper_set
family_tag
unknown_pa
seed
gpu
cfg_path
save_root
```

Always inspect the manifest and several generated JSON files before launching dozens of runs.

## 11.4 Preflight before a real sweep

Minimum checks:

```bash
git status --short
nvidia-smi
head -5 manifests/ota_primary_matrix.tsv
python experiments/pa_preflight_cache_dataset.py --help
```

Also verify the configured cache root actually exists and corresponds to the intended OTA bank.

## 11.5 Parallel training

Launcher:

```bash
JOBS=2 bash scripts/train/run_pa_train_parallel.sh manifests/ota_primary_matrix.tsv
```

The launcher:

- reads the TSV using GNU Parallel,
- assigns each row to its declared GPU,
- sets `CUDA_VISIBLE_DEVICES`,
- serializes access to each GPU with `flock`,
- writes worker logs to `_runtime/train_workers/`,
- stops soon after a worker failure,
- safely skips already-complete runs unless explicitly overridden.

Do not remove the GPU lock just to make a run “go faster.” Increase concurrency only when GPU IDs, VRAM, CPU threads, storage bandwidth, and manifest assignments support it.

## 11.6 Monitor training

Useful scripts:

```text
scripts/train/pa_dashboard.sh
scripts/train/pa_tqdm_watch.sh
scripts/train/watch_pa_train.sh
scripts/train/pa_trainctl.sh
experiments/pa_dashboard.py
experiments/pa_render_run_status.py
```

The intended workflow is to inspect artifacts/status rather than infer progress from a single terminal window.

---

# 12. Reducing training outputs into a leaderboard

Raw run directories are too verbose for reasoning across an experiment family. Reduce `summary.json` files into a single CSV:

```bash
python experiments/pa_reduce_train_summaries.py \
  --results-root results_pa_ota_primary \
  --out results/ota_primary_train_leaderboard.csv
```

This adds `summary_path` and `run_dir` provenance to every row.

For durable scientific history, selected reduced outputs and validation notes can be committed under:

```text
docs/experiments/run_results/
```

Large checkpoints, caches, raw run directories, and generated tensors should remain outside Git unless there is a compelling reason to version a small artifact.

---

# 13. OSR evaluation from saved backbone artifacts

Training the closed-set PA backbone is only one stage. The accepted project’s central scientific question is open-world routing: preserve known PA recognition while rejecting held-out behavior under controlled calibration assumptions.

Important code:

```text
osr_core.py
varmax_osr.py
dqn_osr.py
experiments/pa_make_osr_eval_manifest.py
experiments/pa_eval_osr_one.py
scripts/eval/run_pa_osr_eval_parallel.sh
experiments/pa_reduce_osr_summaries.py
```

## 13.1 Make an OSR manifest from the training leaderboard

```bash
python experiments/pa_make_osr_eval_manifest.py \
  --train-leaderboard results/ota_primary_train_leaderboard.csv \
  --out manifests/ota_primary_osr.tsv \
  --gpus 0,1 \
  --checkpoint best_model \
  --modes oracle,surrogate_all \
  --sweep-grid full \
  --out-root results_pa_osr_eval
```

The OSR manifest contains:

```text
run_name
run_dir
checkpoint
gpu
modes
sweep_grid
out_dir
```

## 13.2 Run evaluation in parallel

```bash
JOBS=2 bash scripts/eval/run_pa_osr_eval_parallel.sh manifests/ota_primary_osr.tsv
```

The launcher uses the same per-GPU lock discipline as training.

## 13.3 Reduce OSR results

```bash
python experiments/pa_reduce_osr_summaries.py \
  --results-root results_pa_osr_eval \
  --out results/ota_primary_osr_leaderboard.csv
```

Important reported fields include known-OSR macro F1, unknown F1/recall, OSR macro F1, calibration mode, threshold/percentile selections, and feasibility flags.

## 13.4 Diagnostic exports

The repository contains utilities for analyzing why a model or OSR rule fails, not just whether a scalar metric is low:

```text
experiments/export_highconf_open_impostors.py
experiments/export_bank_spectrogram_impostors.py
experiments/export_osr_selection_provenance.py
experiments/plot_osr_confusion_matrices.py
experiments/plot_osr_confusion_montage_clean.py
```

Notable committed examples live under:

```text
docs/experiments/run_diagnostics/
```

Use these to distinguish:

- a genuinely difficult RF behavior,
- a mislabeled/stale data source,
- a representation failure,
- an operating-threshold failure,
- a surrogate-calibration failure,
- a bookkeeping/provenance error.

---

# 14. The final rerun plan and how to design future experiment families

Read:

```text
docs/experiments/final_rerun_plan.md
```

The final MILCOM rerun program intentionally stopped treating “rerun everything” as scientific rigor. It reused recovered legacy evidence and concentrated compute on the questions that were still unresolved under the final OTA data definition.

The documented final groups include:

```text
smoke_functional
legacy_digital_recovered           metadata/reference only
legacy_digital_bridge_rerun        optional
ota_primary_matrix                 mandatory core comparison
ota_master_context                 full five-PA context
ota_protocol_ablation              after primary selection
osr_eval_matrix                    post-training OSR evaluation
```

For new research, follow the same design principle:

1. state the scientific question,
2. define the smallest run group that answers it,
3. encode it in `pa_experiment_catalog.py`,
4. generate configs/manifests rather than launching ad-hoc commands,
5. smoke test,
6. run the matrix,
7. reduce results,
8. inspect failure modes,
9. only then expand the grid.

A run name should encode enough provenance to be interpretable, but the **JSON config is the authoritative record**.

---

# 15. Results organization and provenance discipline

The project uses three levels of result persistence.

## Level 1: heavy generated artifacts (normally local only)

Examples:

```text
results_pa_*/<run>/best_model.pt
results_pa_*/<run>/final_model.pt
_feature_cache_nvme/**/*.h5
data/**/*.mat
txrx/tapes/**/*.mat
_runtime/**/*.log
```

These are necessary to run/reproduce locally but are too large/noisy for ordinary Git history.

## Level 2: reduced experiment products

Examples:

```text
results/*.csv
results/*.json
leaderboards
OSR summaries
selected confusion matrices
```

These are the bridge from compute to interpretation.

## Level 3: durable research record

Commit carefully selected artifacts under:

```text
docs/experiments/run_results/
docs/experiments/run_diagnostics/
docs/experiments/run_incidents/
```

This is where future researchers/chats can understand what happened without possessing terabytes of raw data.

### Run incidents are scientific metadata

When a real run failed due to a family/config/data mismatch, the project preserved incident writeups rather than silently deleting the evidence. Continue that practice. A reproducibility record should explain unusual exclusions and reruns.

---

# 16. Legacy experiment recovery

The repository underwent a major cleanup/migration from notebook-centric experimentation to the final manifest-driven system.

Historical sources are intentionally retained under:

```text
legacy/
docs/experiments/legacy_*
docs/experiments/dqn_review/
```

Useful documents include:

```text
docs/experiments/legacy_digital_reconstruction.md
docs/experiments/legacy_prior_chat_experiment_knowledge.md
docs/experiments/legacy_run_inventory.csv
docs/experiments/legacy_checkpoint_inventory.csv
docs/experiments/legacy_generated_table_inventory.csv
```

Use them when the question is:

- “What did the old experiment actually test?”
- “Why was this family kept/dropped?”
- “Can the new runner reproduce a historical conclusion?”
- “Which old checkpoint generated this table?”

Do **not** make the old notebooks the default execution path again.

---

# 17. Paper composition system

The repository also contains a reusable research-paper engineering workflow. The accepted MILCOM paper is both a finished artifact and an example of how to turn experiment evidence into a polished IEEE paper.

## 17.1 Paper root

```text
papers/milcom2026/
```

Primary source:

```text
main.tex
sections/
references.bib
```

The section layout is:

```text
0-abstract.tex
1-intro.tex
2-related.tex
3-methodology.tex
4-experiments.tex
5-results.tex
6-discussion.tex
7-conclusion.tex
```

## 17.2 Ground truth before prose

Before editing scientific claims, read:

```text
papers/milcom2026/PAPER_GROUND_TRUTH.md
papers/milcom2026/PAPER_EVIDENCE_MAP.md
papers/milcom2026/HANDIN_MANIFEST.md
```

The paper process deliberately separated:

- what the repository/results **prove**,
- what the paper **claims**,
- what future work **proposes**.

Do not rewrite prose in a way that erases those boundaries.

## 17.3 Build the paper

```bash
cd ~/adamArchives/Adam/varMax/PADataset/papers/milcom2026
make
```

or explicitly:

```bash
latexmk -pdf -interaction=nonstopmode -file-line-error -synctex=1 \
  -outdir=build main.tex
```

Expected PDF:

```text
build/main.pdf
```

Watch mode:

```bash
make watch
```

## 17.4 Render pages for visual review

```bash
rm -rf build/page_previews
mkdir -p build/page_previews
pdftoppm -png -r 220 build/main.pdf build/page_previews/page
```

Page images were repeatedly used to catch problems invisible in raw LaTeX: figure scale, blank space, section breaks, table readability, bad line wrapping, stale build output, and column balance.

A browser preview can be served locally if useful:

```bash
python3 -m http.server 8123
```

## 17.5 Generated figures and tables

Do not manually edit generated output if the repository contains a generator.

Examples from MILCOM:

```text
papers/milcom2026/figures/target_surrogate_matrix/make_target_surrogate_matrix.py
papers/milcom2026/tables/main_results/make_main_results_table.py
```

The hero figure has its own tracked design/comparative history under:

```text
papers/milcom2026/composition/aspects/hero_figure/
```

## 17.6 The paper-composition method that was actually used

The final DQNGuard manuscript was **not** produced by mechanically executing the early comparative-analysis framework in `papers/milcom2026/composition/` or by forcing every reference paper through a large scorecard. Those files record an exploratory plan from an earlier stage. They are useful historical provenance, but they are **not the workflow a future chat should copy**.

The method that survived into the final paper was simpler and more effective:

1. establish the scientific ground truth and claim boundaries first;
2. build a technically complete evidence-driven draft;
3. curate several kinds of real papers, each for a specific reason;
4. analyze useful papers individually and extract transferable heuristics;
5. synthesize those heuristics into section-level writing rules;
6. revise the manuscript in targeted passes;
7. score/audit the whole paper against the same standards used to judge the exemplars;
8. spend the remaining page budget on the prose changes with the largest clarity gain;
9. finish with a human read-through plus mechanical build/reference checks.

The key distinction is **reference relevance is not the same as exemplar value**. A paper can be essential technical lineage but a poor writing model; another paper can be technically distant but an excellent model for problem framing, page economy, a figure, a results narrative, or claim boundaries.

### A. Start from evidence, not style

Before polishing prose, read:

```text
papers/milcom2026/PAPER_GROUND_TRUTH.md
papers/milcom2026/PAPER_EVIDENCE_MAP.md
papers/milcom2026/HANDIN_MANIFEST.md
```

The first draft should be generated from the actual method, run artifacts, reduced results, figures/tables, and known system boundaries. Lock down:

- what the experiments prove,
- what they do not prove,
- the paper's main claim,
- the paper's secondary/diagnostic findings,
- the role of the proposed method inside the larger operational system,
- which claims require citations.

For DQNGuard, this prevented the prose from drifting into a claim that the work solved the full QR-CWoS response loop. The paper evaluates an RF open-set sensing/decision layer that can feed downstream reasoning; it does not claim to implement the whole downstream system.

### B. Build a role-based paper library

The successful reference search used three overlapping groups.

**1. Direct technical sources and lineage.** These are papers we actually cite or rely on for definitions, predecessors, baselines, or technical language. For DQNGuard this included the varMax lineage, DQN-IDS, prior RF open-set work, multi-domain RF/EMS work, and foundational OSR/OOD/calibration papers. These sources control technical accuracy first; they are writing exemplars only when they are also well composed.

**2. Close venue/domain exemplars.** Select short MILCOM/IEEE RF, spectrum, communications, and security papers that resemble the target audience and page budget. Use them to learn six-page pacing, first-page economy, experimental exposition, figure/table density, and results narration. The DQNGuard searches deliberately added polished RF/MILCOM-style papers after the initial citation set because the citation set alone did not cover these communication problems.

**3. Award-recognized or unusually polished exemplars.** Add a small number of exceptionally well written systems/security papers. Some may have verified awards or recognition; others may be included simply because their composition is unusually strong. Even when the technical topic is more distant, use these for problem framing, operational stakes, evidence chains, discussion structure, and claim-boundary discipline -- not for importing unrelated technical assumptions or their longer-page layout.

Representative recorded DQNGuard examples included Baye et al. varMax and Wei et al. multi-domain EMS as close MILCOM models; Scheirer, Bendale/Boult, Guo, and Liu for technical OSR/OOD/calibration precision; and polished systems/security papers such as ZMap, Foreshadow, Carlini/Wagner, DolphinAttack, and Spectre for selected rhetorical lessons. Additional RF-style searches included papers such as Searchlight, SpecForce, spectrum-sensing/security work, Stitching the Spectrum, and HyperAdv. **Do not assume every historical candidate must be reused for a new paper. Choose papers that fill the new paper's actual communication gaps.**

A useful lightweight role vocabulary is:

```text
TECHNICAL_LINEAGE
VENUE_STYLE_MODEL
PROBLEM_FRAMING_MODEL
METHOD_EXPOSITION_MODEL
EXPERIMENT_DESIGN_MODEL
RESULTS_NARRATIVE_MODEL
FIGURE_MODEL
TABLE_MODEL
CLAIM_BOUNDARY_MODEL
LAB_CONTINUITY
```

These are tags, not a mandatory scoring system.

### C. Ingest only the papers worth close reading

Reference infrastructure:

```text
papers/milcom2026/reference_notes/
```

Reusable processing pipeline:

```text
papers/milcom2026/tools/process_reference_papers.sh
```

Install/login once if needed:

```bash
npm install -g @mathpix/mpx-cli
mpx login
```

Then process selected PDFs:

```bash
MATHPIX_CMD='mpx convert "{pdf}" "{out}"' \
  bash papers/milcom2026/tools/process_reference_papers.sh
```

The processing package can contain:

```text
<paper>.pdf
<paper>.mmd
images/contact_sheet.png
images/pages/*.png
manifest.json
process.log
```

Use the original PDF/page images for layout, visual hierarchy, figures/tables, and exact appearance. Use Mathpix Markdown for semantic/section analysis. Mathpix is never the authoritative source for exact publication text.

### D. Analyze each useful paper individually

Do **not** begin with a rigid `our section vs. exemplar A vs. exemplar B vs. exemplar C` matrix. Read each useful paper on its own terms and record only what transfers.

For each paper, answer:

- Why is this paper in the library?
- Which section/artifact does it teach us about?
- What does it do unusually well?
- What concrete structural or rhetorical heuristic can be extracted?
- What should **not** transfer because the domain, claims, page length, or evaluation differs?

Examples of the kind of heuristic we actually wanted:

- turn the operational problem into a crisp failure mode quickly;
- make a narrow component important by locating it clearly inside a larger system;
- use one readable pipeline figure rather than decorative architecture clutter;
- describe evaluation conditions before asking the reader to interpret scores;
- narrate why a result happens and what tradeoff it represents, not only which number wins;
- state what the method does **not** decide so the contribution remains credible;
- use venue exemplars for density/page economy and technical papers for definitions/lineage, rather than pretending one paper can model everything.

The output is a small set of **transferable heuristics**, not a large comparative-analysis report.

### E. Synthesize heuristics before rewriting

Once several papers have been analyzed, combine repeated lessons into rules for the current paper. For a short IEEE/MILCOM paper, the DQNGuard process converged on a communication package roughly like:

- an operational first-page hook and explicit failure mode;
- one central pipeline/system figure;
- compact methodology that follows the pipeline in reader order;
- a clearly separated experimental-design section;
- one main comparison table plus one diagnostic figure/matrix;
- results prose that explains the operating-point tradeoff and mechanisms;
- a discussion that states implications, limitations, and the boundary of the component;
- a short conclusion with no new claims.

Section-specific lessons should be derived from the current exemplar set, not copied blindly from this historical list.

### F. Revise in targeted passes, then score the whole paper

Apply the synthesized heuristics to the manuscript **without changing scientific truth**. Prefer targeted section/paragraph rewrites over uncontrolled paper-wide regeneration. Preserve terminology and advisor/lab framing when they are technically correct.

After a coherent draft exists, perform the same kind of quality review used on the reference papers. The DQNGuard final passes repeatedly evaluated the paper as a reviewer would, including:

- problem framing and significance,
- novelty/contribution clarity,
- technical correctness,
- method explanation,
- experimental rigor and fairness,
- results narrative and claim/evidence alignment,
- limitations and claim boundaries,
- abstract quality,
- figure/table usefulness and readability,
- page economy,
- overall readability / reviewer effort.

The purpose of scoring is diagnostic: identify the weakest reviewer-facing dimension and fix that next. Do not optimize a synthetic total score at the expense of scientific correctness.

### G. Treat the page limit as an information budget

The final DQNGuard paper reached six pages through both compression **and later decompression**. This is important: once the draft fits, do not assume shorter prose is better.

For every substantial pass:

1. compile;
2. verify the actual page count;
3. render every page;
4. inspect section flow, columns, figures/tables, whitespace, and line wrapping.

When space is scarce, triage prose by **clarity improvement per added line**. The final process explicitly inventoried compressed passages, estimated how much each compression hurt comprehension, estimated the line cost of restoring clarity, and spent remaining space on the highest-value fixes first. Conversely, when the paper overflowed, compression targeted lower-value/redundant prose before cutting necessary explanation.

Do not fill space merely because it exists. Use available lines only when they reduce ambiguity, lower reviewer effort, strengthen claim/evidence flow, or restore an important limitation/definition. DQNGuard's final layout intentionally used most of the six-page budget and placed the conclusion cleanly in the final column, but that exact column placement is historical, not a universal rule.

### H. Run a hostile/low-effort-reader clarity pass

Before submission, read the paper as if the reviewer is skeptical, rushed, or looking for an easy misunderstanding. Every major claim should be difficult to misread.

Check especially:

- acronyms are expanded before first use;
- specialized terms are defined before they carry argumentative weight;
- the reader can state the task, method input/output, calibration/evaluation regime, and operating constraint without reverse-engineering them;
- baseline comparisons are fair and described consistently;
- figures/tables are referenced explicitly and near the relevant prose;
- the abstract tells the same story as the body;
- limitations prevent overclaiming without obscuring the contribution.

This pass is where DQNGuard's abstract, acronym setup, compressed prose, and several reviewer-risk ambiguities received late improvements.

### I. Finish with human and mechanical verification

The last pass is not another rewrite. It is a proofread and reproducibility check.

For DQNGuard the finalization loop included:

- a human line-by-line read-through;
- checking exact experimental constants against the repository/figures;
- checking acronym definitions and terminology;
- checking figure/table references and captions;
- checking citations and claim boundaries;
- rebuilding from the intended LaTeX source;
- confirming the PDF is exactly within the page limit;
- rendering the final PDF and visually reviewing every page;
- guarding against stale preview/build paths;
- committing the successful state before Overleaf/export/submission.

### Writing doctrine

The desired style is:

- technically precise,
- easy to audit,
- explicit about assumptions,
- rhetorically clear,
- concise but not compressed into ambiguity,
- grounded in experiment outputs,
- guided by excellent real papers rather than generic AI style,
- written so a skeptical reviewer can recover the paper's logic with minimal effort.

Avoid:

- hype,
- vague “AI paper” phrasing,
- unsupported generalization,
- copying exemplar wording or technical assumptions,
- claiming a full system when only one layer/component was evaluated,
- using the old comparative-analysis scorecards/CA rounds as mandatory procedure,
- rewriting an entire paper to solve one local prose issue.

### Historical warning: old composition-framework documents

The following files preserve the earlier, more elaborate comparative-analysis idea:

```text
papers/milcom2026/reference_notes/PAPER_COMPOSITION_FRAMEWORK.md
papers/milcom2026/reference_notes/REFERENCE_LIBRARY_FRAMEWORK.md
papers/milcom2026/composition/comparative_revision_plan.md
papers/milcom2026/composition/ASPECT_REGISTRY.md
```

Keep them for provenance. **Do not treat them as the current paper-writing algorithm.** If they conflict with this README, this README reflects the later/final DQNGuard process and takes precedence.

---

# 18. Creating a new paper from this framework

Do not overwrite `papers/milcom2026/` for a new venue/project.

Recommended pattern:

```text
papers/<venue_or_project>/
    main.tex
    sections/
    figures/
    tables/
    references.bib
    PAPER_GROUND_TRUTH.md
    PAPER_EVIDENCE_MAP.md
    composition/
    reference_notes/
    tools/
```

Then reuse the concepts, not the historical claims:

- evidence maps,
- generated figure/table scripts,
- Mathpix/reference-paper ingestion,
- page rendering,
- role-based exemplar selection and synthesized writing heuristics,
- reviewer-style scoring/audits,
- page-budget clarity triage,
- final build verification,
- clean Overleaf export.

A new paper should get a new ground-truth file tied to its actual run manifests and result roots.

---

# 19. Git discipline

## 19.1 Before work

```bash
git status --short
git branch --show-current
git log --oneline -5
```

## 19.2 Use targeted staging

Prefer:

```bash
git add README.md
git add experiments/pa_experiment_catalog.py manifests/<new_manifest>.tsv
git add papers/<project>/sections/3-methodology.tex
```

Avoid habitual:

```bash
git add .
```

The repository contains generated artifacts, local diagnostics, and large files that should not be swept into a commit accidentally.

## 19.3 Commit by semantic unit

Good commit boundaries:

```text
Add run group for PA protocol ablation
Fix PA1 core-shard mapping and cache verification
Add OSR surrogate-selection diagnostics
Document LEAF paper review ingestion workflow
Revise methodology using exemplar-derived heuristics
```

## 19.4 Preserve accepted-paper history

Do future work on `research-framework` or a branch from it. Do not rewrite `milcom2026-final-handin` just because a future experiment uses similar code.

---

# 20. Generated-data / Git hygiene

The repository intentionally ignores most heavy/generated research data. Typical local-only categories include:

- `data/` contents,
- raw digital/OTA tapes,
- feature caches,
- HDF5 tensors,
- model checkpoints,
- large result roots,
- worker logs,
- paper build products,
- temporary archives.

Tracked exceptions exist for small metadata/specification artifacts that are necessary for reproducibility. Check `.gitignore` before inventing a new convention.

If a future chat is unsure whether a file should be committed, ask:

> Can this artifact be regenerated deterministically from tracked code/config/metadata, and is it too large/noisy to review in Git?

If yes, it probably belongs outside normal Git history. Commit the generator/config/reduced evidence instead.

---

# 21. Failure modes and recovery checklist

## “The code I expect is missing.”

First check the branch. `main` is not the mature final framework.

```bash
git branch --show-current
git fetch origin
git branch -a
```

## “Training says data/cache is missing.”

Do not weaken data validation to bypass it. Inspect:

```text
experiments/pa_constants.py
manifest JSON config
cache_root
source_name / dataset_tag / noise_tag
experiments/pa_preflight_cache_dataset.py
experiments/pa_audit_feature_cache.py
```

## “A GPU worker says gpu_lock_busy.”

Another PADataset worker owns that GPU lock, or a stale process needs investigation.

Inspect:

```bash
nvidia-smi
pgrep -af 'pa_train_one|pa_eval_osr_one|python'
ls -l /tmp/padataset_gpu_*.lock
```

Do not blindly delete locks while a process is active.

## “The sweep was interrupted.”

The final training wrapper skips runs that already have the required completion artifacts. Regenerate/inspect the same manifest and relaunch; do not create a second ambiguous result tree unless the configuration changed.

## “A run directory exists but is incomplete.”

Check the required artifacts and `train_error.json`. An existing directory is not equivalent to a completed run.

## “The OTA model suddenly confuses one PA with another.”

Treat this as a possible data/provenance problem before tuning the network. Use the high-confidence impostor/spectrogram/provenance tools and verify bank labels/source files.

## “The paper preview changed but the PDF did not.”

Rebuild explicitly and check timestamps/path. During MILCOM finalization, stale preview/build paths caused false alarms. Verify the actual `build/main.pdf`, page count, and rendered page images before submission.

## “Mathpix Markdown has weird hyphens/characters.”

Mathpix is an analysis representation, not authoritative publication text. Use it to understand structure/equations and compare papers; use the source PDF/LaTeX for exact final wording where necessary.

---

# 22. Reproducibility checklist for a new experiment

Before declaring a new result publishable, be able to answer **yes** to all of the following:

- [ ] The working branch/commit is recorded.
- [ ] The source OTA/digital dataset has a unique, meaningful identity.
- [ ] Dataset planning seeds/window IDs are deterministic.
- [ ] TX tape and TX spec correspond to the same plan.
- [ ] OTA recording logs are preserved.
- [ ] Respliced windows were validated before banking.
- [ ] The canonical bank source and label mapping are documented.
- [ ] Cache namespace/length/normalization are explicit.
- [ ] Every run has a tracked/generated JSON config.
- [ ] A manifest defines the sweep rather than shell-history memory.
- [ ] A smoke test succeeded before the full sweep.
- [ ] Completed runs contain the required artifacts.
- [ ] Training summaries were reduced into a provenance-preserving leaderboard.
- [ ] OSR evaluation was performed from saved checkpoints under explicit calibration modes.
- [ ] Important failures/confusions were diagnosed, not discarded.
- [ ] Paper figures/tables are generated from named result sources.
- [ ] Paper claims are traceable through an evidence map.
- [ ] Large raw/generated artifacts remain separate from reviewable Git history.

---

# 23. Command cookbook

## Enter project

```bash
cd ~/adamArchives/Adam/varMax/PADataset
source ~/adamArchives/venvs/DNNs/bin/activate
git switch research-framework
```

## Inspect repository state

```bash
git status --short
git log --oneline -8
```

## Generate training manifest

```bash
python experiments/pa_make_train_manifest.py \
  --run-group ota_primary_matrix \
  --out manifests/ota_primary_matrix.tsv \
  --gpus 0,1
```

## Launch training

```bash
JOBS=2 bash scripts/train/run_pa_train_parallel.sh manifests/ota_primary_matrix.tsv
```

## Reduce training summaries

```bash
python experiments/pa_reduce_train_summaries.py \
  --results-root results_pa_ota_primary \
  --out results/ota_primary_train_leaderboard.csv
```

## Build OSR manifest

```bash
python experiments/pa_make_osr_eval_manifest.py \
  --train-leaderboard results/ota_primary_train_leaderboard.csv \
  --out manifests/ota_primary_osr.tsv \
  --gpus 0,1 \
  --checkpoint best_model \
  --modes oracle,surrogate_all \
  --sweep-grid full \
  --out-root results_pa_osr_eval
```

## Launch OSR evaluation

```bash
JOBS=2 bash scripts/eval/run_pa_osr_eval_parallel.sh manifests/ota_primary_osr.tsv
```

## Reduce OSR summaries

```bash
python experiments/pa_reduce_osr_summaries.py \
  --results-root results_pa_osr_eval \
  --out results/ota_primary_osr_leaderboard.csv
```

## Build accepted MILCOM paper

```bash
cd ~/adamArchives/Adam/varMax/PADataset/papers/milcom2026
make
```

## Render paper pages

```bash
rm -rf build/page_previews
mkdir -p build/page_previews
pdftoppm -png -r 220 build/main.pdf build/page_previews/page
```

## Process a reference paper library through Mathpix

```bash
cd ~/adamArchives/Adam/varMax/PADataset
MATHPIX_CMD='mpx convert "{pdf}" "{out}"' \
  bash papers/milcom2026/tools/process_reference_papers.sh
```

---

# 24. Where to read next

If the task is **new experiments**:

```text
docs/experiments/final_rerun_plan.md
experiments/pa_experiment_catalog.py
experiments/pa_constants.py
experiments/pa_make_train_manifest.py
experiments/pa_train_one.py
```

If the task is **OTA collection / preprocessing**:

```text
core/pa_make_dataset_plan.m
tools/gen_pilot_shards.m
txrx/build_tx_tape_shards.m
txrx/make_recording_session_plan_v01.m
txrx/tx_stream_tape_batch_v01.m
txrx/rx_capture_tape_batch_v01.m
txrx/rx_resplice_tape_simple.m
build_ota_bank.m
scripts/preprocess/run_unified_core_splitpa1_cache_v03.sh
cacheBuild.py
```

If the task is **understanding historical experiments**:

```text
docs/experiments/legacy_digital_reconstruction.md
docs/experiments/legacy_prior_chat_experiment_knowledge.md
docs/experiments/legacy_run_inventory.csv
docs/experiments/legacy_checkpoint_inventory.csv
legacy/
```

If the task is **paper composition**:

```text
README.md                                   # Section 17 is the current method
AI_HANDOFF_README.md                         # history/context; Section 17 overrides older composition recipes
papers/milcom2026/PAPER_GROUND_TRUTH.md
papers/milcom2026/PAPER_EVIDENCE_MAP.md
papers/milcom2026/HANDIN_MANIFEST.md
papers/milcom2026/reference_notes/          # actual source/exemplar artifacts
```

Historical note: `PAPER_COMPOSITION_FRAMEWORK.md`, `REFERENCE_LIBRARY_FRAMEWORK.md`, and `papers/milcom2026/composition/` preserve the earlier formal comparative-analysis experiment. They are useful provenance but are **not** the workflow a new chat should follow; Section 17 of this README takes precedence.

---

# 25. Final operating principle

This repository works best when each stage leaves enough structured evidence for the next stage to be audited independently.

Do not treat it as a pile of scripts where the answer lives in somebody's terminal history. Treat it as a research system:

- plans define data,
- metadata defines identity,
- manifests define experiments,
- artifacts define completion,
- reduced tables define comparisons,
- diagnostics explain failures,
- evidence maps constrain claims,
- exemplars improve communication,
- Git commits preserve decisions.

That is the framework that took the project from raw RF waveform generation through OTA experiments to an accepted MILCOM paper, and it is the framework future projects should reuse.
