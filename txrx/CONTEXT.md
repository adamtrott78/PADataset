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
| [txrx_capture.m](txrx_capture.m) | Mature same-host one-shard TX/RX capture, RAM preallocation, quality gate and OTA save |
| [capture_batch.m](capture_batch.m) | Explicit protocol/dataset/shard jobs → gated retries, capture logs and OTA artifacts |
| [rx_resplice_tape_simple.m](rx_resplice_tape_simple.m) | OTA tape + exact matching TX spec → recovered PA windows and drop diagnostics |
| [resplice_worker.m](resplice_worker.m) | One-shard non-destructive resplice worker used by later parallel orchestration |
| [make_recording_session_plan_v01.m](make_recording_session_plan_v01.m) | Historical cross-protocol recording schedule and resolved paths |
| [tx_stream_tape_batch_v01.m](tx_stream_tape_batch_v01.m), [rx_capture_tape_batch_v01.m](rx_capture_tape_batch_v01.m) | Historical separate-process plan-driven TX/RX workflow |
| [tx_stream_tape.m](tx_stream_tape.m), [rx_capture_tape.m](rx_capture_tape.m) | Historical separate-process SDR implementation |
| [rx_resplice_tape_batch_v01.m](rx_resplice_tape_batch_v01.m) | Separate v05 resplicing workflow; different output subtree |



## Acquisition architectures: historical and current

Three different planning/control concepts exist in this subsystem and must
not be conflated.

**Dataset-generation plan.** `pa_make_dataset_plan.m` defines canonical
generated sample/segment identities and transport-shard tasks. It is the
upstream scientific/data contract described in `protocol/CONTEXT.md`.

**Historical recording-session plan.**
`make_recording_session_plan_v01.m` created an ordered cross-protocol
schedule with record/canary steps and resolved TX/spec/RX/log paths. It was
designed for a separate TX/RX operator workflow. It remains useful
provenance, but surviving evidence does not establish it as the driver of
the mature production campaign.

**Mature same-host capture runtime.** The later successful path uses
`txrx_capture.m`, normally through `capture_batch.m`, with both N210s
controlled from one MATLAB process on the same host. This avoids the
fragile coordination of independent TX and RX MATLAB processes. It is
host-coordinated capture, not proof of PPS, shared 10-MHz, MIMO-cable, or
timed-radio synchronization.

For a future collection, preserve the deterministic generation plan and
tape/spec contracts, but build any new multi-shard operator manifest around
the same-host capture worker rather than automatically reviving the
historical two-process recording-session plan.

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

## Historical recording-session plan


This section preserves the earlier plan-driven architecture because its
files may still appear in the repository or old run evidence. It is **not**
the recommended physical-capture interface for a new campaign.


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


### Historical plan caveats

A custom `session_tag` controls where the plan MAT/text summary is saved,
but the current `make_step` implementation constructs each `log_file` under
`<snr_regime>_session/logs/...`. Therefore `plan.session_tag` does not
necessarily identify the actual per-step log path. Inspect
`capture_plan.steps(i).log_file` instead of reconstructing that path from
the session tag.

The old separate-process TX path also should not be described as waiting
indefinitely for operator SPACE input. The inspected
`tx_stream_tape.m` contains a ten-second automatic transition. Preserve
that behavior as historical implementation detail rather than as the
recommended capture synchronization mechanism.


## Recommended physical capture: same-host coordinated path

The mature production implementation controls both radios from one MATLAB
process through `txrx_capture.m`. `capture_batch.m` adds shard iteration,
retries, downstream-artifact skips, quality logging, and post-save
verification.

`txrx_capture.m` uses a 100-MHz master clock and integer
interpolation/decimation factor 8, yielding an actual sample rate of
**12.5 MS/s**. That actual rate, not an old nominal 12-MHz comment, controls
OTA timing. A 400,000-sample payload therefore spans 32 ms over this
transport.

The current batch source contains historical Lambda lab defaults for the
radio IPs, center frequency, gains, antenna, retry count, and quality gate.
Those are evidence of the executed campaign, not universal settings. For a
new collection, pass the actual current hardware/RF values explicitly and
record them with the acquisition provenance.

For a deliberately selected one-shard pilot, use a template that refuses
to operate until the hardware values have been filled in:

```matlab
protocol = "wifi";
dataset_id = "wifi_burst_context01";
shard_id = 1;

tx_ip = "REPLACE_TX_IP";
rx_ip = "REPLACE_RX_IP";
fc_hz = NaN;
tx_gain_db = NaN;
rx_gain_db = NaN;
ant = "TX/RX";

assert(~startsWith(tx_ip, "REPLACE") && ~startsWith(rx_ip, "REPLACE"), ...
    "Fill the current radio IPs before capture.");
assert(all(isfinite([fc_hz tx_gain_db rx_gain_db])), ...
    "Fill center frequency and gains before capture.");

txrx_capture(protocol, tx_ip, rx_ip, fc_hz, ...
    tx_gain_db, rx_gain_db, ant, dataset_id, shard_id, ...
    'quality_enable', true, ...
    'quality_max_events', 4, ...
    'quality_min_fill_frac', 0.999);
```


The `4`-event and `0.999` fill settings above match the later
`capture_batch.m` defaults; treat them as historical campaign-quality
settings rather than universal RF constants. For repeated shards, prefer
`capture_batch` so failed acquisitions can be retried and recorded
explicitly:

```matlab
jobs = struct( ...
    'protocol', protocol, ...
    'dataset_id', dataset_id, ...
    'shards', 1);

capture_batch(jobs, ...
    'tx_ip', tx_ip, ...
    'rx_ip', rx_ip, ...
    'ant', ant, ...
    'fc_hz', fc_hz, ...
    'tx_gain_db', tx_gain_db, ...
    'rx_gain_db', rx_gain_db, ...
    'max_capture_attempts', 20, ...
    'max_capture_events', 4, ...
    'min_fill_frac', 0.999, ...
    'overwrite', false);
```


The mature capture implementation is deliberately **RAM-first**. It loads
the TX artifacts before radio work, reshapes the tape into frames,
preallocates the full complex-single RX buffer, pre-touches TX/RX memory,
warms and flushes the receiver, streams the main tape with minimal work in
the RF hot loop, applies the capture-event/fill gate, and only then
persists an accepted OTA artifact.

During development, direct-to-disk MAT writes inside live RF acquisition
were tried and produced severe overrun/corruption problems. That approach
was abandoned in favor of keeping disk I/O outside the RF hot loop. Do not
reintroduce live storage writes simply to lower RAM use without a new
controlled capture-quality validation.

Exact warmup, guard, trimming, search, and quality constants changed during
development and some current source values remain campaign-specific.
Inspect `txrx_capture.m` and `capture_batch.m` before a new acquisition
instead of copying an old chat value.

A successful raw artifact is normally
`txrx/tapes/ota/<protocol>/<dataset_id>/ota_tape_shard_###.mat`. File
existence alone is not capture success. Check the requested tape/spec
identity, `txrx_cfg`, capture overrun/underrun count, fill fraction, and the
later resplice coverage.

For a future large journal collection, retain this same-host worker but put
the repeated shard schedule, START/DONE/ERROR logging, status dashboard,
retry policy, and resume logic into a reviewed tracked shell/manifest
control layer. Test that wrapper on a small pilot before full acquisition.

## Recover windows with the simple resplicer


The exact TX spec used for transmission is part of the recovery contract,
not optional side metadata. The current resplicer loads
`tx_spec.tx_params`, `tx_spec.sync`, and `tx_spec.tx_index`, derives the PA
universe dynamically from `tx_index`, and uses transport geometry plus
sequence chaining to recover payloads.

A major historical failure mode was accepting a CRC-valid header that was
globally plausible but semantically impossible for the expected record.
The current decoder therefore checks more than CRC: for an ordinary header,
its sequence must be in the TX-index range and the decoded PA/window ID must
match the corresponding authoritative TX-index row. This prevents many
false locks that simple global ID-range checks would accept.

Recovery proceeds from an initial header through expected record geometry,
local/slip searches, optional whole-record skip recovery, hard reacquisition,
and operator fallback anchors. Payload extraction is conservative: a window
is kept only when the next boundary proves sufficient separation; otherwise
it is recorded as dropped, for example `truncated_or_unproven` or an
`unpaired_tail`.

Do not hardcode the historical PA2/PA3/PA4/PA8 universe into new recovery
orchestration. The active resplicer enumerates PAs from the matching
`tx_index`, which is required for later-added PA1 and future extensions.


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
