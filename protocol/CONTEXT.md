# PA waveform generation

Read this for generating digital preliminary-action (PA) windows, changing a
waveform, or planning a new protocol collection. Start at the [root README](../README.md)
for repository-wide research boundaries. Continue to [OTA capture](../txrx/CONTEXT.md)
to turn digital windows into measured RF data.

## Purpose and ownership

A PA is precursor RF behavior, not a final ATT&CK/EW technique label. The paper's
five behaviors are PA1 Scan, PA2 Burst, PA3 Sustain, PA4 Hop and PA8 Replay.
Protocol names accepted by the planner are `wifi`, `bluetooth` and `zigbee`.
The planner defaults to **PA2/PA3/PA4/PA8**, so a default call does not create the
five-class corpus. Explicitly include PA1 when that is the intended collection.

| Source | Role |
|---|---|
| [pa_make_dataset_plan.m](../core/pa_make_dataset_plan.m) | Dataset identity, canonical window/segment IDs, shard tasks |
| [gen_pilot_shards.m](../tools/gen_pilot_shards.m) | Configuration loading, protocol/PA dispatch, pilot MAT writing |
| [starter.json](../config/starter.json) | Configuration actually loaded by that generator |
| [protocol/wifi](wifi/), [bluetooth](bluetooth/), [zigbee](zigbee/) | Protocol waveform implementations |
| [tools/pa_gen_windows_pa1_stream.m](../tools/pa_gen_windows_pa1_stream.m) | Shared location of the WiFi PA1 generator |
| [pa_protocol_roots.m](../core/pa_protocol_roots.m) | Canonical generated paths |
| [pa_root.m](../core/pa_root.m) | Derives the repository root from the source location |

The orchestration spans `core/`, `tools/` and `protocol/`; there is no
`txrx_tools/data_generation/` entry point in this implementation.

## Environment and path setup

Use the existing MATLAB installation with the protocol toolboxes. WiFi uses WLAN
configuration/waveform functions; Bluetooth uses BLE helpers; Zigbee uses
`lrwpanOQPSKConfig`. `ver` and `which` establish what this host has installed.
The Python `(DNNs)` environment does not supply MATLAB toolbox dependencies.

From a Bash terminal on Lambda:

```bash
cd ~/adamArchives/Adam/varMax/PADataset
matlab -nodesktop -nosplash
```

Then run this **MATLAB** setup from the repository root, also on any separate TX
or RX host after entering its local checkout:

```matlab
repo_root = pwd;
assert(isfile(fullfile(repo_root, 'core', 'pa_root.m')));
addpath(fullfile(repo_root, 'core'));
addpath(fullfile(repo_root, 'tools'));
addpath(fullfile(repo_root, 'txrx'));
addpath(genpath(fullfile(repo_root, 'protocol')));
assert(strcmp(pa_root(), repo_root));
which gen_pilot_shards -all
which pa_gen_windows_pa2_stream -all
```

There are two `pa_setup_paths.m` files, and they embed a Lambda path. Explicit
setup above avoids depending on which copy MATLAB resolves. Do not recursively
add the whole repository: historical implementations can shadow current helpers.

## Generate a small WiFi Burst shard

This creates ten digital Burst windows, not an OTA recording. Choose a new ID
for each changed collection/configuration; the example deliberately refuses an
existing output directory.

```matlab
dataset_id = "wifi_burst_context01";
R = pa_protocol_roots("wifi");
pilot_root = fullfile(R.data_pilot_shards, dataset_id);
assert(~isfolder(pilot_root), 'Choose a new dataset_id; outputs already exist.');
plan = pa_make_dataset_plan("wifi", "high", dataset_id, ...
    'pa_order', "PA2", 'n_per_pa', 10, 'n_shards', 1, ...
    'windows_per_segment', 10, 'seed_session_id', 1, 'seed_tape_id', 1);
gen_pilot_shards("wifi", plan, 'shards', 1, 'overwrite', false);
pilot_file = fullfile(pilot_root, 'shard_001', 'pilot_S01_PA2.mat');
S = load(pilot_file, 'Xsig_all', 'meta');
assert(size(S.Xsig_all, 2) == 10 && numel(S.meta) == 10);
assert(size(S.Xsig_all, 1) == 400000, 'Check waveform length before building TX tape.');
assert(numel(unique([S.meta.window_id])) == 10);
disp(size(S.Xsig_all));
```

Expected files are `dataset_plan.mat` and `shard_001/pilot_S01_PA2.mat` beneath
`data/wifi/digital/pilot_shards/wifi_burst_context01/`. The pilot contains complex
`Xsig_all` with windows in columns, `meta`, and optional `sched`. Metadata includes
PA/protocol, dataset ID, canonical window ID, seed IDs and transport shard ID.
Ten 400,000-sample complex-single windows occupy about 32 MB before metadata;
larger shard plans require substantially more RAM and disk.

## Scale, select shards, or add a behavior

- For all five behaviors, set `'pa_order', ["PA1","PA2","PA3","PA4","PA8"]`
  on a new plan. For another protocol, change both the planner protocol and the
  generator protocol, and use a protocol-prefixed dataset ID.
- `n_per_pa` must be divisible by `n_shards`; their quotient must be divisible
  by `windows_per_segment`. Use positive integers even where the parser accepts
  a wider numeric range. Production defaults are 10,000 windows/PA, ten shards,
  and ten windows/segment; start with a small shard to validate the environment.
- To generate another shard of an existing unchanged plan, load its
  `dataset_plan.mat` and call `gen_pilot_shards("wifi", S.plan, 'shards', 2)`.
  This requires that shard 2 actually exists in the plan. Existing pilot files
  are skipped by default. The generator still writes `dataset_plan.mat` before
  checking pilot files, so never use a modified plan as a casual resume command.
- Both generation and tape building accept `'stage_root', path` for alternate
  storage. Pass the same staging root to both. Capture/planning helpers do not
  automatically inherit it; inspect their resolved paths before proceeding.
- Adding a new PA requires implementing the protocol generator and extending
  dispatch in `gen_pilot_shards.m`, then checking transport PA-ID encoding and
  downstream label mapping. Merely adding a name to `pa_order` is insufficient.

## Scientific and implementation invariants

Keep the same configuration, PA order, seeds and canonical IDs when comparing
sharding strategies. Sharding is transport partitioning; the plan constructs
window/segment identity independently of shard count. Changing PA order or
collection size can change canonical IDs. A new dataset ID names outputs but is
not by itself a new random seed.

`snr_regime` is carried in plan/metadata. This orchestration call does not set
radio gain or guarantee a measured SNR. Record physical acquisition conditions
in the capture workflow.

The default configuration describes 20 MS/s and 20 ms windows, corresponding to
400,000 raw samples. TX transport fixes its window size at 400,000 and currently
plays at 12.5 MS/s: physical playback is therefore 32 ms. Do not confuse raw
waveform size, playback duration, or downstream pooled feature length. Inspect
actual output dimensions before tape building. `starter_ota12.json` is not the
generator's default and the inspected version fails JSON parsing; do not simply
substitute it as a working configuration. Protocol-specific constructors may
also reject incompatible configured rates.

## Validation and recovery

The example checks count, window dimensions and unique IDs. Also check that
metadata PA/protocol match the plan and that waveforms are finite and nonzero.
Use `which ... -all` for shadowed helpers, and inspect the protocol constructor
and `starter.json` for toolbox/rate errors. Preserve the failed inputs and use a
new dataset ID after changing settings; do not overwrite a collection whose
captures or results already depend on it.

The commands were checked against source at `077c8d9466e1a4e70bb8163560e4b52e108cef92`
and matching Lambda source. They were not executed in MATLAB during documentation
authoring. Runtime/toolbox and waveform checks above are part of first use.

MAT payloads, generated plans, capture files and later caches are artifacts.
They may exist on Lambda or external storage while being ignored by Git. Their
absence from GitHub does not imply a missing implementation. Preserve source
configuration, seeds and collection identity alongside those artifacts.
