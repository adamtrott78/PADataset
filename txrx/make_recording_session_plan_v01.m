function plan = make_recording_session_plan_v01(snr_regime, dataset_ids, n_shards, varargin)
%MAKE_RECORDING_SESSION_PLAN_V01 Build a deterministic shard recording plan.
%
% Usage:
%   dataset_ids = struct( ...
%       'wifi',      "wifi_high_run01", ...
%       'bluetooth', "bluetooth_high_run01", ...
%       'zigbee',    "zigbee_high_run01");
%
%   plan = make_recording_session_plan_v01("high", dataset_ids, 10);
%
% Optional name/value:
%   'protocol_order'     : string array, default ["wifi","bluetooth","zigbee"]
%   'canary_every'       : integer, default 3
%   'canary_protocol'    : string, default ""  (disabled if empty)
%   'canary_dataset_id'  : string, default ""  (disabled if empty)
%   'session_tag'        : string, default "<snr>_session"
%
% What it does:
%   - creates an ordered step list for one SNR regime
%   - inserts canary steps at:
%       * start of each protocol block
%       * every N shards within a protocol block
%       * end of each protocol block
%   - records expected TX and RX tape paths
%   - saves the plan under results/recording_sessions/<session_tag>/
%
% Notes:
%   - This does not stream or capture anything yet.
%   - It is the plan both TX and RX machines should share.

    if nargin < 1 || isempty(snr_regime)
        error('snr_regime is required, e.g. "high"');
    end
    if nargin < 2 || isempty(dataset_ids)
        error('dataset_ids struct is required');
    end
    if nargin < 3 || isempty(n_shards)
        error('n_shards is required');
    end

    snr_regime = string(snr_regime);

    p = inputParser;
    addParameter(p, 'protocol_order', ["wifi","bluetooth","zigbee"]);
    addParameter(p, 'canary_every', 3);
    addParameter(p, 'canary_protocol', "");
    addParameter(p, 'canary_dataset_id', "");
    addParameter(p, 'session_tag', snr_regime + "_session");
    parse(p, varargin{:});

    protocol_order    = string(p.Results.protocol_order);
    canary_every      = double(p.Results.canary_every);
    canary_protocol   = string(p.Results.canary_protocol);
    canary_dataset_id = string(p.Results.canary_dataset_id);
    session_tag       = string(p.Results.session_tag);

    P = pa_paths();

    results_root = fullfile(P.results, 'recording_sessions', char(session_tag));
    if ~exist(results_root, 'dir')
        mkdir(results_root);
    end

    % Build step list
    steps = struct( ...
        'step_id', {}, ...
        'block_id', {}, ...
        'step_type', {}, ...
        'protocol', {}, ...
        'dataset_id', {}, ...
        'snr_regime', {}, ...
        'shard_id', {}, ...
        'tx_file', {}, ...
        'tx_spec_file', {}, ...
        'tx_exists', {}, ...
        'tx_spec_exists', {}, ...
        'rx_file', {}, ...
        'log_file', {}, ...
        'note', {} );
        step_id = 0;
        block_id = 0;

    for pidx = 1:numel(protocol_order)
        protocol = protocol_order(pidx);

        if ~isfield(dataset_ids, char(protocol))
            error('dataset_ids is missing field "%s"', protocol);
        end
        dataset_id = string(dataset_ids.(char(protocol)));

        block_id = block_id + 1;

        % Canary at start of protocol block
        if strlength(canary_protocol) > 0 && strlength(canary_dataset_id) > 0
            step_id = step_id + 1;
            steps(end+1) = make_step(step_id, block_id, "canary", ...
                canary_protocol, canary_dataset_id, snr_regime, 1, P, ...
                "Protocol-block start canary"); %#ok<AGROW>
        end

        % Main shard loop
        for shard_id = 1:n_shards
            step_id = step_id + 1;
            steps(end+1) = make_step(step_id, block_id, "record", ...
                protocol, dataset_id, snr_regime, shard_id, P, ...
                "Main recording shard"); %#ok<AGROW>

            % Periodic canary within protocol block
            if strlength(canary_protocol) > 0 && strlength(canary_dataset_id) > 0
                if canary_every > 0 && mod(shard_id, canary_every) == 0 && shard_id < n_shards
                    step_id = step_id + 1;
                    steps(end+1) = make_step(step_id, block_id, "canary", ...
                        canary_protocol, canary_dataset_id, snr_regime, 1, P, ...
                        sprintf('Periodic canary after shard %03d', shard_id)); %#ok<AGROW>
                end
            end
        end

        % Canary at end of protocol block
        if strlength(canary_protocol) > 0 && strlength(canary_dataset_id) > 0
            step_id = step_id + 1;
            steps(end+1) = make_step(step_id, block_id, "canary", ...
                canary_protocol, canary_dataset_id, snr_regime, 1, P, ...
                "Protocol-block end canary"); %#ok<AGROW>
        end
    end

    % Save plan
    plan = struct();
    plan.session_tag       = session_tag;
    plan.snr_regime        = snr_regime;
    plan.protocol_order    = protocol_order;
    plan.dataset_ids       = dataset_ids;
    plan.n_shards          = n_shards;
    plan.canary_every      = canary_every;
    plan.canary_protocol   = canary_protocol;
    plan.canary_dataset_id = canary_dataset_id;
    plan.results_root      = string(results_root);
    plan.steps             = steps;

    save(fullfile(results_root, 'recording_session_plan.mat'), 'plan', '-v7');

    % Also write a readable text summary
    txt_file = fullfile(results_root, 'recording_session_plan.txt');
    fid = fopen(txt_file, 'w');
    fprintf(fid, 'RECORDING SESSION PLAN\n');
    fprintf(fid, 'session_tag      : %s\n', session_tag);
    fprintf(fid, 'snr_regime       : %s\n', snr_regime);
    fprintf(fid, 'n_shards         : %d\n', n_shards);
    fprintf(fid, 'canary_every     : %d\n', canary_every);
    fprintf(fid, 'canary_protocol  : %s\n', canary_protocol);
    fprintf(fid, 'canary_dataset_id: %s\n\n', canary_dataset_id);

    fprintf(fid, 'STEPS\n');
    for i = 1:numel(steps)
        s = steps(i);
        fprintf(fid, '%03d | %-6s | %-10s | %-20s | shard=%03d | %s\n', ...
            s.step_id, s.step_type, s.protocol, s.dataset_id, s.shard_id, s.note);
        fprintf(fid, '      TX: %s\n', s.tx_file);
        fprintf(fid, '      TXSPEC: %s\n', s.tx_spec_file);
        fprintf(fid, '      RX: %s\n', s.rx_file);
        fprintf(fid, '      LOG: %s\n', s.log_file);
    end
    fclose(fid);

    % Print concise summary
    n_record = sum(strcmp(string({steps.step_type}), "record"));
    n_canary = sum(strcmp(string({steps.step_type}), "canary"));

    fprintf('Saved session plan:\n');
    fprintf('  %s\n', fullfile(results_root, 'recording_session_plan.mat'));
    fprintf('  %s\n', txt_file);
    fprintf('\n');
    fprintf('Summary\n');
    fprintf('  total steps : %d\n', numel(steps));
    fprintf('  record steps: %d\n', n_record);
    fprintf('  canary steps: %d\n', n_canary);
end

function s = make_step(step_id, block_id, step_type, protocol, dataset_id, snr_regime, shard_id, P, note)
    protocol = string(protocol);
    dataset_id = string(dataset_id);

    if step_type == "canary"
        tx_name      = 'tx_tape_canary.mat';
        tx_spec_name = 'tx_spec_canary.mat';
        rx_name      = 'ota_tape_canary.mat';
    else
        tx_name      = sprintf('tx_tape_shard_%03d.mat', shard_id);
        tx_spec_name = sprintf('tx_spec_shard_%03d.mat', shard_id);
        rx_name      = sprintf('ota_tape_shard_%03d.mat', shard_id);
    end
    
    tx_file      = fullfile(P.txrx, 'tapes', 'digital', char(protocol), char(dataset_id), tx_name);
    tx_spec_file = fullfile(P.txrx, 'tapes', 'digital', char(protocol), char(dataset_id), tx_spec_name);
    rx_dir       = fullfile(P.txrx, 'tapes', 'ota', char(protocol), char(dataset_id));
    log_dir = fullfile(P.results, 'recording_sessions', char(snr_regime + "_session"), 'logs', char(protocol), char(dataset_id));

    if ~exist(rx_dir, 'dir')
        mkdir(rx_dir);
    end
    if ~exist(log_dir, 'dir')
        mkdir(log_dir);
    end

    s = struct();
    s.step_id = step_id;
    s.block_id = block_id;
    s.step_type = string(step_type);
    s.protocol = protocol;
    s.dataset_id = dataset_id;
    s.snr_regime = string(snr_regime);
    s.shard_id = double(shard_id);
    s.tx_file = string(tx_file);
    s.tx_spec_file = string(tx_spec_file);
    s.tx_exists = isfile(tx_file);
    s.tx_spec_exists = isfile(tx_spec_file);
    s.rx_file = string(fullfile(rx_dir, rx_name));
    s.log_file = string(fullfile(log_dir, sprintf('step_%03d_log.mat', step_id)));
    s.note = string(note);
end