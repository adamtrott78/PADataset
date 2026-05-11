function build_high_snr_local_v01()
%BUILD_HIGH_SNR_LOCAL_V01 Build all high-SNR datasets locally in the repo.
%
% What it builds:
%   - wifi_high_run01
%   - bluetooth_high_run01
%   - zigbee_high_run01
%   - wifi_high_canary
%
% Output roots:
%   data/<protocol>/digital/pilot_shards/<dataset_id>/
%   txrx/tapes/digital/<protocol>/<dataset_id>/
%
% Usage:
%   build_high_snr_local_v01

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
    rehash

    fprintf('PADataset root: %s\n\n', root);

    % -----------------------------
    % main high-SNR runs
    % -----------------------------
    runs = { ...
        struct('protocol',"wifi",      'dataset_id',"wifi_high_run01",      'seed_session_id',1, 'seed_tape_id',1, 'n_per_pa',10000, 'n_shards',20, 'windows_per_segment',100), ...
        struct('protocol',"bluetooth", 'dataset_id',"bluetooth_high_run01", 'seed_session_id',2, 'seed_tape_id',1, 'n_per_pa',10000, 'n_shards',20, 'windows_per_segment',100), ...
        struct('protocol',"zigbee",    'dataset_id',"zigbee_high_run01",    'seed_session_id',3, 'seed_tape_id',1, 'n_per_pa',10000, 'n_shards',20, 'windows_per_segment',100) ...
    };

    for i = 1:numel(runs)
        R = runs{i};

        fprintf('==================================================\n');
        fprintf('BUILDING %s | %s\n', upper(char(R.protocol)), char(R.dataset_id));
        fprintf('==================================================\n');

        plan = pa_make_dataset_plan(R.protocol, "high", R.dataset_id, ...
            'n_per_pa', R.n_per_pa, ...
            'n_shards', R.n_shards, ...
            'windows_per_segment', R.windows_per_segment, ...
            'seed_session_id', R.seed_session_id, ...
            'seed_tape_id', R.seed_tape_id);

        fprintf('\n--- GENERATE PILOT SHARDS ---\n');
        gen_pilot_shards(R.protocol, plan);

        fprintf('\n--- VERIFY SHARD DATASET ---\n');
        verify_shard_dataset_v01(R.protocol, R.dataset_id);

        fprintf('\n--- BUILD TX TAPE SHARDS ---\n');
        build_tx_tape_shards(R.protocol, R.dataset_id);

        fprintf('\nDONE: %s\n\n', char(R.dataset_id));
    end

    % -----------------------------
    % wifi canary
    % -----------------------------
    fprintf('==================================================\n');
    fprintf('BUILDING WIFI HIGH CANARY\n');
    fprintf('==================================================\n');

    canary_id = "wifi_high_canary";

    plan_canary = pa_make_dataset_plan("wifi", "high", canary_id, ...
        'n_per_pa', 20, ...
        'n_shards', 1, ...
        'windows_per_segment', 10, ...
        'seed_session_id', 101, ...
        'seed_tape_id', 1);

    fprintf('\n--- GENERATE CANARY PILOT SHARDS ---\n');
    gen_pilot_shards("wifi", plan_canary);

    fprintf('\n--- VERIFY CANARY SHARD DATASET ---\n');
    verify_shard_dataset_v01("wifi", canary_id);

    fprintf('\n--- BUILD CANARY TX TAPE SHARDS ---\n');
    build_tx_tape_shards("wifi", canary_id);

    % Rename/copy shard_001 outputs into canary filenames expected by session plan
    P = pa_paths();
    canary_root = fullfile(P.txrx, 'tapes', 'digital', 'wifi', char(canary_id));

    src_tape = fullfile(canary_root, 'tx_tape_shard_001.mat');
    src_spec = fullfile(canary_root, 'tx_spec_shard_001.mat');
    dst_tape = fullfile(canary_root, 'tx_tape_canary.mat');
    dst_spec = fullfile(canary_root, 'tx_spec_canary.mat');

    if isfile(src_tape)
        copyfile(src_tape, dst_tape);
        fprintf('Copied canary tape: %s\n', dst_tape);
    else
        warning('Canary source tape missing: %s', src_tape);
    end

    if isfile(src_spec)
        copyfile(src_spec, dst_spec);
        fprintf('Copied canary spec: %s\n', dst_spec);
    else
        warning('Canary source spec missing: %s', src_spec);
    end

    fprintf('\nALL HIGH-SNR LOCAL BUILDS COMPLETE.\n');
end