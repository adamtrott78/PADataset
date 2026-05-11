function run_shard_smoke_test_v01()
%RUN_SHARD_SMOKE_TEST_V01 Small end-to-end smoke test for sharded generation.
% Creates a tiny WIFI dataset plan, generates pilot shards, then builds TX tape shards.
%
% Usage:
%   run_shard_smoke_test_v01

    % -----------------------------
    % locate repo + add key folders
    % -----------------------------
    this_file = mfilename('fullpath');
    tools_dir = fileparts(this_file);
    root = fileparts(tools_dir);

    addpath(fullfile(root, 'core'));
    addpath(fullfile(root, 'tools'));
    addpath(fullfile(root, 'txrx'));
    addpath(fullfile(root, 'protocol', 'wifi'));
    if isfolder(fullfile(root, 'protocol', 'bluetooth'))
        addpath(fullfile(root, 'protocol', 'bluetooth'));
    end
    if isfolder(fullfile(root, 'protocol', 'zigbee'))
        addpath(fullfile(root, 'protocol', 'zigbee'));
    end

    fprintf('PADataset root: %s\n', root);

    % -----------------------------
    % tiny smoke-test parameters
    % -----------------------------
    protocol   = "wifi";
    snr_regime = "high";
    dataset_id = "wifi_high_smoke";

    n_per_pa             = 100;  % tiny test only
    n_shards             = 5;    % 400 total windows / 5 = 80 per shard
    windows_per_segment  = 10;   % small segment chunks
    seed_session_id      = 1;
    seed_tape_id         = 1;

    fprintf('\n=== BUILD PLAN ===\n');
    plan = pa_make_dataset_plan(protocol, snr_regime, dataset_id, ...
        'n_per_pa', n_per_pa, ...
        'n_shards', n_shards, ...
        'windows_per_segment', windows_per_segment, ...
        'seed_session_id', seed_session_id, ...
        'seed_tape_id', seed_tape_id);

    fprintf('Plan created:\n');
    fprintf('  protocol           : %s\n', string(plan.protocol));
    fprintf('  snr_regime         : %s\n', string(plan.snr_regime));
    fprintf('  dataset_id         : %s\n', string(plan.dataset_id));
    fprintf('  n_per_pa              : %d\n', plan.n_per_pa);
    fprintf('  total_windows         : %d\n', numel(plan.pa_order) * plan.n_per_pa);
    fprintf('  n_shards              : %d\n', plan.n_shards);
    fprintf('  windows_per_shard_pa  : %d\n', plan.windows_per_shard_per_pa);
    fprintf('  windows_per_shard     : %d\n', numel(plan.pa_order) * plan.windows_per_shard_per_pa);
    fprintf('  windows_per_segment   : %d\n', plan.windows_per_segment);

    fprintf('\n=== GENERATE PILOT SHARDS ===\n');
    gen_pilot_shards(protocol, plan);

    fprintf('\n=== BUILD TX TAPE SHARDS ===\n');
    build_tx_tape_shards(protocol, dataset_id);

    % -----------------------------
    % expected output locations
    % -----------------------------
    P = pa_paths();

    pilot_shard_root = fullfile(P.data_root, char(protocol), 'digital', 'pilot_shards', char(dataset_id));
    tx_shard_root    = fullfile(P.txrx, 'tapes', 'digital', char(protocol), char(dataset_id));

    fprintf('\n=== EXPECTED OUTPUT ROOTS ===\n');
    fprintf('Pilot shards: %s\n', pilot_shard_root);
    fprintf('TX shards   : %s\n', tx_shard_root);

    if isfolder(pilot_shard_root)
        d1 = dir(fullfile(pilot_shard_root, '**', '*.mat'));
        fprintf('Pilot shard MAT files found: %d\n', numel(d1));
    else
        fprintf('Pilot shard root not found yet.\n');
    end

    if isfolder(tx_shard_root)
        d2 = dir(fullfile(tx_shard_root, '*.mat'));
        fprintf('TX shard MAT files found: %d\n', numel(d2));
    else
        fprintf('TX shard root not found yet.\n');
    end

    fprintf('\nSmoke test complete.\n');
end