# OTA banks and feature caches

Read this to convert recovered OTA windows into labeled banks, build multi-domain
features, or inspect a cache before training/evaluation. Begin with the
[repository README](../../README.md); upstream inputs come from
[OTA capture and resplicing](../../txrx/CONTEXT.md). This stage prepares data;
training splits and OSR calibration are defined by the experiment code.

## Source ownership and formats

| Source | Role |
|---|---|
| [build_ota_bank.m](../../build_ota_bank.m) | Respliced windows → per-protocol, per-shard, per-PA bank files |
| [pa_relabel_bank_labels_v01.m](../../core/pa_relabel_bank_labels_v01.m) | Rewrite bank labels using PA tokens in ordinary bank filenames |
| [pa1_core_split_part_bank_v01.m](../../pa1_core_split_part_bank_v01.m) | Insert separately captured PA1 as parts in the core bank |
| [manifestBuild.py](../../manifestBuild.py) | Enumerate bank files and provenance in JSON |
| [cacheBuild.py](../../cacheBuild.py) | CLI for building/reusing HDF5 features |
| [prepData.py](../../prepData.py) | Input layout, transforms, pooling, cache schema and loading |
| [pa_audit_feature_cache.py](../../experiments/pa_audit_feature_cache.py) | Read first/last feature slices and detect unreadable/nonfinite files |
| [run_unified_core_splitpa1_cache_v03.sh](run_unified_core_splitpa1_cache_v03.sh) | Existing destructive PA1 rebuild/relabel/cache orchestration |

Respliced MAT files hold complex `Xrx_all[W,N]`, `meta_rx` and `rx_cfg`. Banks
contain real-valued I/Q `X[N,2,W]` in MATLAB, labels `y[N,1]`, and `proto[N,1]`.
They also retain window/shard/record/source IDs where produced by the builder.
MATLAB v7.3 files are HDF5; their axes can appear reversed to `h5py`. The Python
loader locates the size-two I/Q axis and treats the smaller remaining axis as
the sample axis. Check its inferred sample count against label lengths when
introducing a different layout; this heuristic is not a general tensor schema.

## Label invariants

| Behavior | Global PA label |
|---|---:|
| PA1 Scan | 0 |
| PA2 Burst | 1 |
| PA3 Sustain | 2 |
| PA4 Hop | 3 |
| PA8 Replay | 4 |

Protocol labels are WiFi=0, Bluetooth=1, Zigbee=2. These global labels differ from
the contiguous known-class labels an experiment may construct for a fold.

`build_ota_bank` assigns labels by the caller's `pas` order. Its default four-PA
order assigns PA2=0, which is incompatible with the global five-PA convention
above. A Burst-only bank also initially assigns PA2=0. Relabel such banks before
caching. Cached labels are copies: changing a bank afterward does not update
an existing cache.

## Build a bank from the WiFi Burst example

Use the MATLAB path setup in [PA generation](../../protocol/CONTEXT.md), with the
repository root as current directory. This continues the captured and respliced
`wifi_burst_context01` example. It is a small pipeline check, not a five-class
training or paper-reproduction dataset.

```matlab
bank_name = "ota_burst_context01";
bank_dir = fullfile(pa_root(), 'data', 'wifi', 'ota', bank_name);
assert(~isfolder(bank_dir), 'Choose a new bank name; inspect existing outputs first.');
summary = build_ota_bank(bank_name, 1, ...
    'run_suffix', "burst_context01", 'protocols', "wifi", ...
    'pas', "PA2", 'mode', "all", 'chunk_n', 8, ...
    'delete_spliced_after_write', false);
pa_relabel_bank_labels_v01("wifi", bank_name, ...
    ["PA1","PA2","PA3","PA4","PA8"]);
bank_file = fullfile(bank_dir, 'ota_burst_context01__shard_001__PA2.mat');
L = load(bank_file, 'y', 'proto');
assert(~isempty(L.y) && all(L.y(:) == 1) && all(L.proto(:) == 0));
whos('-file', char(bank_file))
```

`run_suffix` resolves to `<protocol>_<suffix>` beneath
`data/<protocol>/ota/spliced/simple/`. Bank outputs are
`data/<protocol>/ota/<bank_name>/<bank_name>__shard_###__<PA>.mat`.
The builder can overwrite existing bank files. Keeping a fresh bank name also
prevents stale files from earlier selections entering a later manifest.

For a multi-protocol bank, explicitly select protocols and use the positional
WiFi shard list plus `bt_shards` and `zb_shards`. An empty shard list discovers
all available shard directories; it does not mean “none.” Default `balanced`
mode subsamples each PA to the minimum available count across selected protocols.
It does not guarantee equal counts across different PAs. `all` mode retains all
available records. Compare the printed counts with intended coverage before
continuing; absent PA files can otherwise lead to incomplete selections.

## Build a manifest and a pooled feature cache

Return to Bash at the repository root in the existing `(DNNs)` environment.
The Python feature builder imports NumPy, SciPy, PyTorch and h5py. No training
job is launched by these commands.

```bash
cd ~/adamArchives/Adam/varMax/PADataset
export PA_CACHE_LEN=16384
export PA_CACHE_ROOT="$PWD/_feature_cache_nvme/len${PA_CACHE_LEN}/norm/ota_burst_context01"
python manifestBuild.py \
  --data-root "$PWD/data" \
  --source-type ota --source-name ota_burst_context01 \
  --protocols wifi --require-nonempty \
  --dataset-tag ota_burst_context01 --noise-tag burst_context01 \
  --out "$PWD/results/manifests/ota_burst_context01.json"
python cacheBuild.py \
  --data-root "$PWD/data" --cache-root "$PA_CACHE_ROOT" \
  --cache-len "$PA_CACHE_LEN" --normalize \
  --source-type ota --source-name ota_burst_context01 \
  --dataset-tag ota_burst_context01 --noise-tag burst_context01 \
  --manifest-path "$PWD/results/manifests/ota_burst_context01.json"
```

The manifest is a JSON list of records with `path`, `protocol_name`, `source_type`,
`source_name`, `dataset_tag` and `noise_tag`. Discovery is the immediate
`data/<protocol>/<source_type>/<source_name>/*.mat` directory, not a recursive
search. `--require-nonempty` checks each selected protocol, not every PA/shard.
Review the manifest for unwanted files and missing expected coverage. Rebuilding
a manifest replaces that JSON file; preserve it when recording a run's inputs.

`--manifest-path` takes precedence over `--source-glob`. Each manifest row's
provenance contributes to the generated cache filename. One HDF5 file is built
per bank source record. Use a separate cache root for every different feature
length, normalization choice or source revision: filenames alone do not enforce
all those distinctions.

## What the feature builder computes

Each raw I/Q window is transformed at its original length, normalized if enabled,
and then reduced channel-wise using PyTorch `adaptive_avg_pool1d` to length L.
It does not first pool I/Q and then compute the other representations.

| Channels, in order | Representation | With normalization enabled |
|---|---|---|
| 0–1 | I and Q | `tanh` |
| 2–3 | Real and imaginary FFT of complex I/Q | `tanh` |
| 4–5 | Type-II, orthonormal DCT of I and Q separately | `tanh` |
| 6–7 | Complex magnitude and phase | Magnitude `tanh`, phase `sin` |

Normalization here is not fitted z-score normalization. The resulting `Xfeat`
is float32 `[N,8,L]`; N is the number of windows, eight is the feature-channel
count, and L is pooled window length. HDF5 also holds `y_pa`, `proto`, `y_joint`,
optional sample metadata, and attributes including `cache_len`, `normalize` and
source identity. The loader consumes `Xfeat` directly without repooling it.

Cache length is a provenance field, not a manuscript constant. Earlier
PADataset work evaluated multiple pooled lengths, including 8,192 and
16,384. The surviving final OTA/DQNGuard experiment lineage uses
**L=16,384**. The late manuscript/figure statement of 8,192 does not
have corresponding surviving rerun provenance and is retained as a
manuscript-provenance conflict.

The example above therefore defaults to 16,384. If deliberately
evaluating another pooled length, use a separate cache root and record
the actual HDF5 `Xfeat` shape and `cache_len` attribute with the run.
Never infer experimental length from a paper sentence, directory name,
or checkpoint compatibility alone.

## Inspect before training or evaluation

This reads headers and labels, not full feature tensors. It verifies this
specific Burst example, including its global PA label:

```bash
python - <<'PY'
import os
from pathlib import Path
import h5py
import numpy as np
root = Path(os.environ['PA_CACHE_ROOT'])
L = int(os.environ['PA_CACHE_LEN'])
files = sorted(root.glob('*.h5'))
assert files, f'No cache files in {root}'
for path in files:
    with h5py.File(path, 'r') as f:
        shape = f['Xfeat'].shape
        assert len(shape) == 3 and shape[0] > 0 and shape[1:] == (8, L), (path, shape)
        assert int(f.attrs['cache_len']) == L and int(f.attrs['normalize']) == 1
        for key in ['y_pa', 'proto', 'y_joint']:
            assert f[key].shape == (shape[0],), (path, key)
        assert np.all(f['y_pa'][:] == 1), path
        assert np.all(f['proto'][:] == 0), path
        print(path.name, shape, f.attrs['source_path'])
PY
python experiments/pa_audit_feature_cache.py --cache-root "$PA_CACHE_ROOT"
```

For a full corpus, replace the Burst-only label checks with expected PA/protocol
coverage and compare source identities and file counts with the manifest. The
existing audit reads first and last feature slices for finiteness/readability.
It does not check every tensor value, require a nonempty directory, enforce
the intended pooled length, or prove every file was fully written. A successful audit is one check,
not a substitute for coverage and provenance checks.

Existing cache files are skipped unless `--force` is passed. A failed build can
leave a partial file that a later ordinary invocation skips. Use a fresh cache
root after a failed build or changed source; `--force` deliberately replaces
existing cache files and should not be used while training/evaluation reads them.


## Historical BUH production orchestration

`legacy/preprocessing/buh_pipeline/` is historical in interface and path
assumptions, but it is not merely abandoned prototype code. Surviving
scripts, runtime logs, worker logs, and later recovery tools establish the
architecture that operated the large OTA preprocessing campaign.

The main historical control path was:

`run_buh.sh`
→ transient `systemd-run --user` service
→ `buh_orchestrate.sh`
→ artifact-derived status queues
→ capture
→ parallel resplice
→ parallel banking
→ PA1 integration/relabeling
→ parallel cache construction.

The archived sources include:

| Historical source | Operational role |
|---|---|
| [run_buh.sh](../../legacy/preprocessing/buh_pipeline/run_buh.sh) | Starts a transient user-systemd unit and follows it with `journalctl` |
| [buh_orchestrate.sh](../../legacy/preprocessing/buh_pipeline/buh_orchestrate.sh) | Runs stage transitions, GNU Parallel worker pools, logging and final summary |
| [pipeline_status_buh.sh](../../legacy/preprocessing/buh_pipeline/pipeline_status_buh.sh) | Classifies protocol/dataset/shard artifacts into next-action queues |
| [buh.txt](../../legacy/preprocessing/buh_pipeline/buh.txt) | Historical operator notes for journal/log/process monitoring |

The important design principle is **artifact-driven orchestration**. A shard
was classified from outputs actually present: TX tape/spec, OTA tape,
spliced PA files, bank files, cache files, and stranded temporary artifacts.
Queues such as CAPTURE, RESPLICE, BANK, CACHE, and BLOCKED represented the
next missing operation. This is more reliable than assuming a stage
completed because its command had once been launched.

`buh_orchestrate.sh` also used separate worker pools for resplicing, banking,
and caching and retained GNU Parallel joblogs plus per-stage logs.
`run_buh.sh` used a transient user-systemd service so a long operation could
survive terminal fragility while remaining observable through
`journalctl`.

### Why the pipeline became workerized

Workerization was a throughput and resource-utilization optimization, not a
change to the scientific preprocessing definition. Resplicing, banking,
and especially feature-cache construction took extremely long when
performed serially. Lambda's large RAM and compute capacity made it much
faster to split independent shards or files into concurrent workers than
to leave the machine underutilized.

Parallel execution may change scheduling, logging, and recovery behavior;
it must not silently change the per-record signal transformation, labels,
cache schema, or provenance. Parallelize only units with independent
mutation boundaries, control per-worker CPU math threads where appropriate,
and verify expected artifacts after the pool finishes.

### Evolution from bulk orchestration to surgical recovery

Later scripts made the operational unit progressively smaller and recovery
increasingly explicit:

- `run_unified_core_splitpa1_cache_v01.sh`, `v02`, and `v03` iterated on
  five-class PA1/core integration, prechecks, relabeling, concurrent cache
  construction, and verification.
- `run_filemax_core_cache_v01.sh` moved cache construction toward one
  independent task per source MAT file so a much larger rolling worker pool
  could occupy the machine.
- `run_filemax_core_cache_resume_v01.sh` reconstructs unfinished work from
  prior `FILECACHE DONE` records, excludes confirmed source stems, removes
  partial/unconfirmed H5 outputs for pending stems, and launches only the
  remaining file-level tasks.
- `run_missing_h5_cache_v01.sh` independently enumerates expected source
  files and schedules only sources whose corresponding H5 artifact is
  absent.

The reusable recovery pattern is:

preserve logs and partial-run evidence
→ derive the expected work universe
→ identify completed work from authoritative artifacts and verified
  completion records
→ rebuild only missing or untrusted independent units
→ inspect worker/joblog failures
→ verify final coverage.

Do not respond to one failed worker by deleting a complete multi-hour
preprocessing tree and starting from zero.

### Historical BUH is not the future one-click command

Do not execute the archived BUH scripts unchanged merely because they were
production-used. They encode historical dataset names, shard geometry,
cache settings, path assumptions, and capture policies. Their status-script
path and capture-gate values also reflect the historical runtime and should
be reconciled against currently tracked source before reuse.

For a future journal collection, preserve the proven architecture rather
than the literal old command: use a reviewed tracked manifest/wrapper around
current generation, same-host capture, resplice, bank, and cache owners;
make status artifact-driven; use worker pools for independent expensive
stages; log START/DONE/ERROR identities; make reruns skip verified work;
and validate the wrapper on a small pilot before scaling.

## Incremental PA1 integration into the existing core


PA1 records the project's first large **incremental corpus extension**.
The original PA2/PA3/PA4/PA8 corpus had already been generated,
transmitted, captured, respliced, banked, and cached before PA1 was added.
Reprocessing every valid older PA was prohibitively expensive, so PA1 was
acquired and processed separately and then integrated downstream into the
existing core.

This history explains the otherwise unusual split/part machinery below.
It also provides a future-journal pattern: adding a new PA does not
inherently require recapturing every old PA. Generate, capture, resplice,
and bank the new behavior under its own provenance-preserving collection;
adapt physical partitioning only as required by the existing loader/cache
contract; preserve one semantic label; audit the combined mapping; then
build a clean combined experiment view.


The existing PA1 split helper maps five PA1 acquisition shards to twenty core
shards: acquisition shard = `floor((core_shard-1)/4)+1`; each core shard selects
a 500-window ID interval. Parts divide recovered records within that interval;
missing captures mean a part need not contain its nominal count. A matching
historical-layout example is:

```matlab
% Requires wifi_pa1_run01 source shard 1 and a deliberately selected core bank.
% Replaces this part file if it already exists.
pa1_core_split_part_bank_v01("wifi", "pa1_run01", 1, 1, 1, 2, ...
    "ota_core_high_run01", 8);
```

This writes `...__shard_001__PA1__part_01_of_02.mat` with global PA1 label zero.
The general relabel helper only recognizes filenames ending `__PAx.mat`; it
does not accept these part suffixes. Relabel ordinary core files before inserting
parts, as the historical orchestration does. Verify real window IDs: the split
helper can synthesize positional IDs when metadata lacks them.

`run_unified_core_splitpa1_cache_v03.sh` deletes/rebuilds PA1 outputs, relabels
banks and launches parallel workers. Its default cache length is 16384, and its
relabel call hardcodes all three protocols even when `PROTOCOLS` is overridden.
It is not a status/resume command or the fresh-bank example above. Likewise,
[quarantine_banks.py](../../tools/quarantine_banks.py) moves files by default;
it is not a read-only validator. Inspect these mutation boundaries before use.

## Validation scope and next stage

The documented interfaces were checked against source at
`954ccd8f8f1630419b0179ba608ae84ce3e5a063` (unchanged preprocessing code from the
earlier audited commit). MATLAB banking and real cache construction were not
executed during documentation authoring. Keep source/configuration, bank/manifest
identity, actual cache shape and normalization together in run provenance.

Bank MATs, feature HDF5 files, generated manifests and audit logs are artifacts
often ignored by Git; absence from GitHub does not establish absence on Lambda.
After validation, proceed to the experiment entry points in
[experiments/](../../experiments/) for training configuration, folds and
evaluation. Changing pooled length for a new experiment requires an explicitly
matching cache and effective run configuration, not just a renamed directory.
