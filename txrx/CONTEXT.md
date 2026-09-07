# OTA transport, capture and resplicing

Read this to build TX tapes, plan a recording session, coordinate transmitter
and receiver, or recover PA windows from an OTA tape. First follow
[PA generation](../protocol/CONTEXT.md) for MATLAB path setup and digital pilots.
The [root README](../README.md) defines the broader research pipeline.

## Model and source ownership

Digital PA windows are packed into a transport tape containing synchronization,
headers and guard intervals. RX records the tape, then resplicing identifies
headers and recovers windows plus their PA/window IDs. Bank building and feature
caching happen afterward; a successful capture is not yet a training dataset.

| Source | Inputs and outputs |
|---|---|
| [build_tx_tape_shards.m](build_tx_tape_shards.m) | Pilot plan/shards → paired TX tape and TX spec |
| [make_recording_session_plan_v01.m](make_recording_session_plan_v01.m) | Dataset IDs/shard count → ordered steps and resolved file paths |
| [tx_stream_tape_batch_v01.m](tx_stream_tape_batch_v01.m) | Plan + TX settings → operator-paced playback/logs |
| [rx_capture_tape_batch_v01.m](rx_capture_tape_batch_v01.m) | Same plan + RX settings → raw OTA tape/logs |
| [tx_stream_tape.m](tx_stream_tape.m), [rx_capture_tape.m](rx_capture_tape.m) | SDR implementation and actual sample-rate settings |
| [rx_resplice_tape_simple.m](rx_resplice_tape_simple.m) | OTA tape + matching spec → recovered PA windows and drop diagnostics |
| [rx_resplice_tape_batch_v01.m](rx_resplice_tape_batch_v01.m) | Separate v05 resplicing workflow; different output subtree |

## Build the Burst example's transport tape

Continue in MATLAB after generating `wifi_burst_context01` in the parent
workflow. Use a fresh output directory because the builder deletes/replaces an
existing tape file; there is no `overwrite=false` option here.

```matlab
dataset_id = "wifi_burst_context01";
R = pa_protocol_roots("wifi");
digital_root = fullfile(R.txrx_tapes_digital, dataset_id);
assert(~isfolder(digital_root), 'Choose a new collection ID or inspect existing tapes first.');
build_tx_tape_shards("wifi", dataset_id, 'shards', 1);
tape_file = fullfile(digital_root, 'tx_tape_shard_001.mat');
spec_file = fullfile(digital_root, 'tx_spec_shard_001.mat');
assert(isfile(tape_file) && isfile(spec_file));
whos('-file', char(tape_file))
whos('-file', char(spec_file))
```

Default outputs are beneath `txrx/tapes/digital/wifi/wifi_burst_context01/`.
Keep each tape paired with the spec created by the same build. The builder writes
the tape incrementally to a v7.3 MAT file, but playback loads the whole tape into
RAM; streamed construction does not imply constant-memory playback. Its payload
window is 400,000 samples, frame size 100,000, and guard length 200,000 samples.

## Create and inspect a one-step recording plan

```matlab
session_tag = "wifi_burst_context01_capture01";
session_root = fullfile(pa_root(), 'results', 'recording_sessions', session_tag);
assert(~isfolder(session_root), 'Use a new session tag.');
dataset_ids = struct('wifi', "wifi_burst_context01");
capture_plan = make_recording_session_plan_v01("high", dataset_ids, 1, ...
    'protocol_order', "wifi", 'session_tag', session_tag);
plan_file = fullfile(session_root, 'recording_session_plan.mat');
disp(struct2table(capture_plan.steps));
assert(all([capture_plan.steps.tx_exists]) && all([capture_plan.steps.tx_spec_exists]));
assert(~isfile(capture_plan.steps(1).rx_file), 'Existing capture: do not overwrite it.');
```

This writes the plan and a readable summary beneath
`results/recording_sessions/<session_tag>/`. It does not operate either radio.
For multiple protocols, provide `wifi`, `bluetooth`, `zigbee` fields in
`dataset_ids` and list them in `protocol_order`. Canary steps require both
`canary_protocol` and `canary_dataset_id`; they are disabled by default.

The plan stores resolved paths. Both hosts need a valid plan for their filesystem
layout, matching step identities and identical TX specs; do not assume absolute
paths from one computer resolve on another. TX needs its tape, RX needs its spec.
Recorded `tx_exists` fields are a planning-time snapshot; recheck the files before
capture. A different session tag does **not** change the dataset/shard OTA filename.

## Run a physical capture

The implementation uses `comm.SDRuTransmitter`/`comm.SDRuReceiver` with platform
`N200/N210/USRP2`, a 100 MHz master clock and interpolation/decimation 8, giving
**12.5 MS/s**. Use the existing MATLAB USRP support and the actual connected
hardware's IP address, antenna port, center frequency and gain. These values
depend on the lab setup and are deliberately not guessed.

Use separate MATLAB sessions for RX and TX. TX opens a figure and uses SPACE to
start tape playback, so it needs a working graphical MATLAB display; a headless
`matlab -batch` call is not an equivalent capture command. For a host with a
working display, launch `matlab -desktop` and perform the linked path setup.

On each host, set `plan_file` to the local recording-plan MAT path. Set `fc_hz`
to the same center frequency in Hz on both hosts. Set `rx_ip`, `rx_gain_db`,
`rx_ant` on RX and `tx_ip`, `tx_gain_db`, `tx_ant` on TX from the actual setup.
Then these are the exact MATLAB calls:

```matlab
% RX host: start this first, then press ENTER at its arm prompt.
rx_capture_tape_batch_v01(plan_file, rx_ip, fc_hz, rx_gain_db, rx_ant, ...
    'step_ids', 1);
```

```matlab
% TX host: once RX is armed, select the same step and follow the TX figure prompt.
tx_stream_tape_batch_v01(plan_file, tx_ip, fc_hz, tx_gain_db, tx_ant, ...
    'step_ids', 1);
```

Both batch runners prompt before each step and offer skip/quit. `step_ids` selects
plan positions; it is not a PA identifier. TX prompts in the terminal and then
waits for SPACE in its figure. RX waits for start synchronization. The wrappers
do not automatically skip a previously successful capture.

The example's raw output is
`txrx/tapes/ota/wifi/wifi_burst_context01/ota_tape_shard_001.mat`, containing
`x_tape` and `rx_cfg`. Each step also writes TX/RX log MATs with `_tx`/`_rx`
suffixes at the plan's log location. Check `log.status`, `log.error_message`,
saved tape existence and `rx_cfg`; a log marked `ok` alone does not establish
that all intended PA windows survived transport.

## Recover windows with the simple resplicer

Keep the raw capture and its spec available at their canonical paths. The full
dataset ID below is explicit; the resplicer also accepts a suffix and prepends
`wifi_`, `bluetooth_` or `zigbee_` when absent.

```matlab
rx_resplice_tape_simple("wifi", "wifi_burst_context01", 1, ...
    'delete_ota_after_load', false, 'make_png', false);
summary_file = fullfile(pa_root(), 'results', 'wifi', 'ota', ...
    'rx_resplice_simple', 'wifi_burst_context01', 'shard_001', ...
    'resplice_summary_simple.mat');
D = load(summary_file, 'summary', 'drop_log');
disp(D.summary.counts);
disp(D.summary.n_keep);
disp(D.summary.n_drop);
disp(D.summary.stop_seen);
```

Recovered data lives at
`data/wifi/ota/spliced/simple/wifi_burst_context01/shard_001/ota_rx_PA2.mat`
with `Xrx_all`, `meta_rx` and `rx_cfg`. Other PAs have their own files when
present. Compare recovered counts and IDs with the digital plan; investigate
missing/duplicate IDs, drop reasons and missing stop synchronization before
banking. Do not assume nominal planned counts equal usable measured counts.

For a broken header chain, inspect the printed expected locations and diagnostics.
Rerun with `'seed_k', header_index` and, if needed,
`'fallback_k', [index1 index2]`, using measured approximate header locations in
**raw samples**. Default slip hypotheses are `-2:2` in 100,000-sample frame steps.
Seed/fallback anchors must come from this capture, not a different run's notes.
Resplice reruns replace their generated PA files and summary. The optional
`delete_ota_after_load=true` deletes the raw tape before recovery finishes; it is
not part of this workflow.

The session batch resplicer targets `spliced/v05`; it is not interchangeable with
`spliced/simple`. The current [bank builder](../build_ota_bank.m) is the next
source to inspect for consuming recovered windows. Confirm its expected input
layout and PA label order before using any preprocessing wrapper.

## Validation limits and artifact handling

Check paired tape/spec, plan paths, RX/TX step alignment, capture logs and recovered
counts in that order. Missing spec prevents correct capture sizing; failed start
sync calls for checking matching tapes, actual sample rates and radio settings.
Very large tapes can exhaust playback/RX memory even when construction succeeds.

Commands and output paths were checked against executable source at
`077c8d9466e1a4e70bb8163560e4b52e108cef92` and matching Lambda files. No SDR or MATLAB
runtime validation was performed during documentation authoring. The hardware
parameters above remain required operator inputs.

Tapes, specs, plans, logs, recovered windows and diagnostic images are generated
artifacts, frequently stored through ignored paths or symlinks. Preserve raw
capture/spec identity for recovery; GitHub is not a complete inventory of local
data. Authored MATLAB/configuration files define behavior. Generated summaries
describe individual captures and do not override these operating instructions.
