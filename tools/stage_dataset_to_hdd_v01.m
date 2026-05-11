function plan = stage_dataset_to_hdd_v01(protocol, snr_regime, dataset_id, varargin)
%STAGE_DATASET_TO_HDD_V01 Build a dataset plan, pilot shards, and TX shards on an HDD.
%
% This is for pre-experiment staging only.
% It does NOT build a recording session plan.
%
% Usage:
%   plan = stage_dataset_to_hdd_v01("wifi", "high", "wifi_high_run01", ...
%       'stage_root', "D:\PADataset_stage", ...
%       'n_per_pa', 10000, ...
%       'n_shards', 10, ...
%       'windows_per_segment', 100, ...
%       'seed_session_id', 1, ...
%       'seed_tape_id', 1);
%
% Optional name/value:
%   'stage_root'           : required for HDD staging
%   'n_per_pa'             : default 10000
%   'n_shards'             : default 10
%   'windows_per_segment'  : default 100
%   'seed_session_id'      : default 1
%   'seed_tape_id'         : default 1
%   'pilot_shards'         : subset of shard ids for gen_pilot_shards, default []
%   'tape_shards'          : subset of shard ids for build_tx_tape_shards, default []
%   'overwrite'            : default false
%   'verify'               : default true
%
% What it does:
%   1) creates dataset plan
%   2) writes pilot shards to <stage_root>/data/<protocol>/digital/pilot_shards/<dataset_id>/
%   3) optionally verifies shard IDs
%   4) writes TX tape + TX spec shards to <stage_root>/txrx/tapes/digital/<protocol>/<dataset_id>/
%   5) saves a small manifest under <stage_root>/manifests/<protocol>/<dataset_id>/
%
% Notes:
%   - This is for large artifact generation only.
%   - Build the recording session plan later, on the actual TX/RX machines.

    if nargin < 3
        error('Usage: stage_dataset_to_hdd_v01(protocol, snr_regime, dataset_id, ...)');
    end

    protocol = string(protocol);
    snr_regime = string(snr_regime);
    dataset_id = string(dataset_id);

    ip = inputParser();
    ip.addParameter('stage_root', "", @(x) isstring(x) || ischar(x));
    ip.addParameter('n_per_pa', 10000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    ip.addParameter('n_shards', 10, @(x) isnumeric(x) && isscalar(x) && x > 0);
    ip.addParameter('windows_per_segment', 100, @(x) isnumeric(x) && isscalar(x) && x > 0);
    ip.addParameter('pa_order', [], @(x) isempty(x) || isstring(x) || ischar(x) || iscellstr(x));
    ip.addParameter('seed_session_id', 1, @(x) isnumeric(x) && isscalar(x));
    ip.addParameter('seed_tape_id', 1, @(x) isnumeric(x) && isscalar(x));
    ip.addParameter('pilot_shards', [], @(x) isnumeric(x) || isempty(x));
    ip.addParameter('tape_shards', [], @(x) isnumeric(x) || isempty(x));
    ip.addParameter('overwrite', false, @(x) islogical(x) && isscalar(x));
    ip.addParameter('verify', true, @(x) islogical(x) && isscalar(x));
    ip.parse(varargin{:});

    stage_root = string(ip.Results.stage_root);
    n_per_pa = double(ip.Results.n_per_pa);
    n_shards = double(ip.Results.n_shards);
    windows_per_segment = double(ip.Results.windows_per_segment);
    pa_order = string(ip.Results.pa_order);
    seed_session_id = double(ip.Results.seed_session_id);
    seed_tape_id = double(ip.Results.seed_tape_id);
    pilot_shards = ip.Results.pilot_shards;
    tape_shards = ip.Results.tape_shards;
    overwrite = ip.Results.overwrite;
    do_verify = ip.Results.verify;

    if strlength(stage_root) == 0
        error('stage_root is required, e.g. "D:\PADataset_stage"');
    end
    if ~isfolder(stage_root)
        mkdir(stage_root);
    end

    % Make sure repo helpers are available
    root = pa_root();
    addpath(fullfile(root, 'core'));
    addpath(fullfile(root, 'tools'));
    addpath(fullfile(root, 'txrx'));
    if isfolder(fullfile(root, 'protocol', 'wifi'))
        addpath(fullfile(root, 'protocol', 'wifi'));
    end
    if isfolder(fullfile(root, 'protocol', 'bluetooth'))
        addpath(fullfile(root, 'protocol', 'bluetooth'));
    end
    if isfolder(fullfile(root, 'protocol', 'zigbee'))
        addpath(fullfile(root, 'protocol', 'zigbee'));
    end

    fprintf('STAGE DATASET TO HDD\n');
    fprintf('  protocol            : %s\n', protocol);
    fprintf('  snr_regime          : %s\n', snr_regime);
    fprintf('  dataset_id          : %s\n', dataset_id);
    fprintf('  stage_root          : %s\n', stage_root);
    fprintf('  n_per_pa            : %d\n', n_per_pa);
    fprintf('  n_shards            : %d\n', n_shards);
    fprintf('  windows_per_segment : %d\n', windows_per_segment);
    fprintf('  seed_session_id     : %d\n', seed_session_id);
    fprintf('  seed_tape_id        : %d\n', seed_tape_id);
    fprintf('\n');

    % 1) Build canonical dataset plan
    plan_args = { ...
        'n_per_pa', n_per_pa, ...
        'n_shards', n_shards, ...
        'windows_per_segment', windows_per_segment, ...
        'seed_session_id', seed_session_id, ...
        'seed_tape_id', seed_tape_id };
    
    if exist("pa_order","var") && ~isempty(pa_order) && strlength(pa_order(1)) > 0
        plan_args = [plan_args, {'pa_order', pa_order}];
    end
    
    plan = pa_make_dataset_plan(protocol, snr_regime, dataset_id, plan_args{:});

    fprintf('Plan built:\n');
    fprintf('  total_windows         : %d\n', numel(plan.pa_order) * plan.n_per_pa);
    fprintf('  windows_per_shard_pa  : %d\n', plan.windows_per_shard_per_pa);
    fprintf('  windows_per_shard     : %d\n', numel(plan.pa_order) * plan.windows_per_shard_per_pa);
    fprintf('\n');

    % 2) Generate pilot shards directly to HDD
    fprintf('=== GENERATE PILOT SHARDS TO HDD ===\n');
    gen_pilot_args = {'stage_root', stage_root, 'overwrite', overwrite};
    if ~isempty(pilot_shards)
        gen_pilot_args = [gen_pilot_args, {'shards', pilot_shards}]; %#ok<AGROW>
    end
    gen_pilot_shards(protocol, plan, gen_pilot_args{:});

    % 3) Verify shard integrity
    if do_verify
        fprintf('\n=== VERIFY SHARD DATASET ===\n');
        R = verify_shard_dataset_v01_stage(protocol, dataset_id, stage_root);
        if R.has_global_duplicates || ~isempty(R.global_missing_ids) || ~isempty(R.problems)
            error('Shard verification failed for %s / %s. Inspect verify report before continuing.', protocol, dataset_id);
        end
    end

    % 4) Build TX tape/spec shards directly to HDD
    fprintf('\n=== BUILD TX TAPE SHARDS TO HDD ===\n');
    build_tape_args = {'stage_root', stage_root};
    if ~isempty(tape_shards)
        build_tape_args = [build_tape_args, {'shards', tape_shards}]; %#ok<AGROW>
    end
    build_tx_tape_shards(protocol, dataset_id, build_tape_args{:});

    % 5) Write a small manifest
    manifest_root = fullfile(char(stage_root), 'manifests', char(protocol), char(dataset_id));
    if ~exist(manifest_root, 'dir')
        mkdir(manifest_root);
    end

    manifest = struct();
    manifest.protocol = protocol;
    manifest.snr_regime = snr_regime;
    manifest.dataset_id = dataset_id;
    manifest.stage_root = stage_root;
    manifest.repo_root = string(root);
    manifest.n_per_pa = n_per_pa;
    manifest.n_shards = n_shards;
    manifest.windows_per_segment = windows_per_segment;
    manifest.seed_session_id = seed_session_id;
    manifest.seed_tape_id = seed_tape_id;
    manifest.generated_at = datetime("now");
    manifest.plan = plan;

    save(fullfile(manifest_root, 'stage_manifest.mat'), 'manifest', '-v7');

    txt_file = fullfile(manifest_root, 'stage_manifest.txt');
    fid = fopen(txt_file, 'w');
    fprintf(fid, 'STAGE DATASET MANIFEST\n');
    fprintf(fid, 'protocol            : %s\n', protocol);
    fprintf(fid, 'snr_regime          : %s\n', snr_regime);
    fprintf(fid, 'dataset_id          : %s\n', dataset_id);
    fprintf(fid, 'stage_root          : %s\n', stage_root);
    fprintf(fid, 'n_per_pa            : %d\n', n_per_pa);
    fprintf(fid, 'n_shards            : %d\n', n_shards);
    fprintf(fid, 'windows_per_segment : %d\n', windows_per_segment);
    fprintf(fid, 'seed_session_id     : %d\n', seed_session_id);
    fprintf(fid, 'seed_tape_id        : %d\n', seed_tape_id);
    fprintf(fid, 'generated_at        : %s\n', string(manifest.generated_at));
    fclose(fid);

    fprintf('\n=== STAGING COMPLETE ===\n');
    fprintf('Pilot shards root:\n  %s\n', fullfile(char(stage_root), 'data', char(protocol), 'digital', 'pilot_shards', char(dataset_id)));
    fprintf('TX tape/spec root:\n  %s\n', fullfile(char(stage_root), 'txrx', 'tapes', 'digital', char(protocol), char(dataset_id)));
    fprintf('Manifest:\n  %s\n', txt_file);
end


function report = verify_shard_dataset_v01_stage(protocol, dataset_id, stage_root)
%VERIFY_SHARD_DATASET_V01_STAGE Same logic as verify_shard_dataset_v01, but pointed at stage_root.
% Minimal wrapper so staging can verify HDD-based shard trees without changing your normal repo results layout.

    protocol = string(protocol);
    dataset_id = string(dataset_id);
    stage_root = string(stage_root);

    data_root = fullfile(char(stage_root), 'data', char(protocol), 'digital', 'pilot_shards', char(dataset_id));
    results_root = fullfile(char(stage_root), 'manifests', char(protocol), char(dataset_id), 'verify');
    if ~exist(results_root, 'dir')
        mkdir(results_root);
    end

    shard_dirs = dir(fullfile(data_root, 'shard_*'));
    shard_dirs = shard_dirs([shard_dirs.isdir]);

    if isempty(shard_dirs)
        error('No shard_* folders found under: %s', data_root);
    end

    all_ids = [];
    all_pas = strings(0,1);
    all_files = strings(0,1);
    all_shards = zeros(0,1);

    file_rows = struct( ...
        'shard_name', {}, ...
        'shard_num', {}, ...
        'pa', {}, ...
        'filepath', {}, ...
        'n_meta', {}, ...
        'n_waveforms', {}, ...
        'id_min', {}, ...
        'id_max', {}, ...
        'has_sched', {}, ...
        'protocol_ok', {}, ...
        'dataset_ok', {}, ...
        'duplicate_ids_within_file', {} );

    skipped_files = strings(0,1);
    problems = strings(0,1);
    pa_order_seen = strings(0,1);

    for s = 1:numel(shard_dirs)
        shard_name = string(shard_dirs(s).name);
        shard_num = parse_shard_num_local(shard_name);

        mat_files = dir(fullfile(shard_dirs(s).folder, shard_dirs(s).name, '*.mat'));
        for f = 1:numel(mat_files)
            fp = fullfile(mat_files(f).folder, mat_files(f).name);
            fn = string(mat_files(f).name);

            tok = regexp(char(fn), '^pilot_S\d+_(PA\d+)\.mat$', 'tokens', 'once');
            if isempty(tok)
                skipped_files(end+1,1) = string(fp); %#ok<AGROW>
                continue;
            end
            pa = string(tok{1});
            pa_order_seen(end+1,1) = pa; %#ok<AGROW>

            S = load(fp);
            if ~isfield(S, 'meta')
                problems(end+1,1) = "Missing meta in " + string(fp); %#ok<AGROW>
                continue;
            end
            if ~isfield(S, 'Xsig_all')
                problems(end+1,1) = "Missing Xsig_all in " + string(fp); %#ok<AGROW>
                continue;
            end

            meta = S.meta;
            Xsig_all = S.Xsig_all;
            has_sched = isfield(S, 'sch') || isfield(S, 'sched');

            n_meta = numel(meta);
            n_waveforms = size(Xsig_all, 2);
            if n_meta ~= n_waveforms
                problems(end+1,1) = sprintf("Count mismatch in %s | meta=%d waveforms=%d", fp, n_meta, n_waveforms); %#ok<AGROW>
            end

            ids = nan(n_meta, 1);
            protocol_ok = true;
            dataset_ok = true;

            for k = 1:n_meta
                if ~isfield(meta(k), 'window_id')
                    problems(end+1,1) = sprintf("Missing window_id in %s", fp); %#ok<AGROW>
                    ids(k) = NaN;
                else
                    ids(k) = double(meta(k).window_id);
                end
                if isfield(meta(k), 'protocol')
                    protocol_ok = protocol_ok && strcmp(string(meta(k).protocol), protocol);
                end
                if isfield(meta(k), 'dataset_id')
                    dataset_ok = dataset_ok && strcmp(string(meta(k).dataset_id), dataset_id);
                end
            end

            ids_valid = ids(~isnan(ids));
            dup_within = numel(unique(ids_valid)) ~= numel(ids_valid);
            if dup_within
                problems(end+1,1) = sprintf("Duplicate window_id values within file: %s", fp); %#ok<AGROW>
            end
            if ~protocol_ok
                problems(end+1,1) = sprintf("Protocol metadata mismatch in %s", fp); %#ok<AGROW>
            end
            if ~dataset_ok
                problems(end+1,1) = sprintf("Dataset metadata mismatch in %s", fp); %#ok<AGROW>
            end

            row = struct();
            row.shard_name = shard_name;
            row.shard_num = shard_num;
            row.pa = pa;
            row.filepath = string(fp);
            row.n_meta = n_meta;
            row.n_waveforms = n_waveforms;
            row.id_min = safe_min_local(ids_valid);
            row.id_max = safe_max_local(ids_valid);
            row.has_sched = has_sched;
            row.protocol_ok = protocol_ok;
            row.dataset_ok = dataset_ok;
            row.duplicate_ids_within_file = dup_within;
            file_rows(end+1) = row; %#ok<AGROW>

            all_ids = [all_ids; ids_valid(:)]; %#ok<AGROW>
            all_pas = [all_pas; repmat(pa, numel(ids_valid), 1)]; %#ok<AGROW>
            all_files = [all_files; repmat(string(fp), numel(ids_valid), 1)]; %#ok<AGROW>
            all_shards = [all_shards; repmat(shard_num, numel(ids_valid), 1)]; %#ok<AGROW>
        end
    end

    pa_list = unique(pa_order_seen, 'stable');
    n_total = numel(all_ids);
    n_unique = numel(unique(all_ids));
    has_global_duplicates = n_total ~= n_unique;

    global_min = safe_min_local(all_ids);
    global_max = safe_max_local(all_ids);

    missing_ids = [];
    if ~isempty(all_ids) && all(~isnan(all_ids))
        expected_ids = (global_min:global_max).';
        missing_ids = setdiff(expected_ids, unique(all_ids));
        if ~isempty(missing_ids)
            problems(end+1,1) = sprintf("Global window_id gaps detected | missing=%d", numel(missing_ids)); %#ok<AGROW>
        end
    end

    pa_counts = struct();
    for i = 1:numel(pa_list)
        pa = pa_list(i);
        mask = (all_pas == pa);
        ids_pa = all_ids(mask);
        shards_pa = unique(all_shards(mask));
        pa_counts.(char(pa)) = struct( ...
            'count', numel(ids_pa), ...
            'unique_count', numel(unique(ids_pa)), ...
            'id_min', safe_min_local(ids_pa), ...
            'id_max', safe_max_local(ids_pa), ...
            'n_shards_present', numel(shards_pa), ...
            'shards_present', shards_pa(:).' );
    end

    report = struct();
    report.protocol = protocol;
    report.dataset_id = dataset_id;
    report.data_root = string(data_root);
    report.results_root = string(results_root);
    report.n_shards_found = numel(shard_dirs);
    report.pa_list = pa_list;
    report.n_total_ids = n_total;
    report.n_unique_ids = n_unique;
    report.global_id_min = global_min;
    report.global_id_max = global_max;
    report.global_missing_ids = missing_ids;
    report.has_global_duplicates = has_global_duplicates;
    report.per_file = file_rows;
    report.per_pa = pa_counts;
    report.skipped_mat_files = skipped_files;
    report.problems = problems;

    save(fullfile(results_root, 'verify_report.mat'), 'report', '-v7');
end


function n = parse_shard_num_local(shard_name)
    tok = regexp(char(shard_name), '^shard_(\d+)$', 'tokens', 'once');
    if isempty(tok), n = NaN; else, n = str2double(tok{1}); end
end

function v = safe_min_local(x)
    if isempty(x), v = NaN; else, v = min(x); end
end

function v = safe_max_local(x)
    if isempty(x), v = NaN; else, v = max(x); end
end