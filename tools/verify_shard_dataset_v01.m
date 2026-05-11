function report = verify_shard_dataset_v01(protocol, dataset_id)
%VERIFY_SHARD_DATASET_V01 Verify sharded pilot dataset integrity.
%
% Usage:
%   verify_shard_dataset_v01("wifi", "wifi_high_smoke")
%   R = verify_shard_dataset_v01("bluetooth", "bt_mid_run01")
%
% Checks:
%   - finds shard folders under data/<protocol>/digital/pilot_shards/<dataset_id>/
%   - reads pilot_S01_PA*.mat files
%   - verifies meta count matches waveform count
%   - verifies window_id uniqueness within each file
%   - verifies global window_id uniqueness across all files
%   - reports per-PA counts and shard coverage
%   - skips non-pilot .mat files, but reports them
%
% Output:
%   - prints a summary
%   - saves report mat file to:
%       results/<protocol>/digital/verify_shard_dataset_v01/<dataset_id>/verify_report.mat

    if nargin < 1 || isempty(protocol)
        protocol = "wifi";
    end
    if nargin < 2 || isempty(dataset_id)
        error('dataset_id is required, e.g. verify_shard_dataset_v01("wifi","wifi_high_smoke")');
    end

    protocol = string(protocol);
    dataset_id = string(dataset_id);

    P = pa_paths();

    data_root = fullfile(P.data_root, char(protocol), 'digital', 'pilot_shards', char(dataset_id));
    results_root = fullfile(P.results, char(protocol), 'digital', 'verify_shard_dataset_v01', char(dataset_id));
    if ~exist(results_root, 'dir')
        mkdir(results_root);
    end

    if ~isfolder(data_root)
        error('Pilot shard root not found: %s', data_root);
    end

    fprintf('VERIFY SHARD DATASET\n');
    fprintf('  protocol   : %s\n', protocol);
    fprintf('  dataset_id : %s\n', dataset_id);
    fprintf('  root       : %s\n\n', data_root);

    shard_dirs = dir(fullfile(data_root, 'shard_*'));
    shard_dirs = shard_dirs([shard_dirs.isdir]);

    if isempty(shard_dirs)
        error('No shard_* folders found under: %s', data_root);
    end

    % Aggregation
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
        shard_num = parse_shard_num(shard_name);

        mat_files = dir(fullfile(shard_dirs(s).folder, shard_dirs(s).name, '*.mat'));
        for f = 1:numel(mat_files)
            fp = fullfile(mat_files(f).folder, mat_files(f).name);
            fn = string(mat_files(f).name);

            % Only verify pilot shard files here
            tok = regexp(char(fn), '^pilot_S\d+_(PA\d+)\.mat$', 'tokens', 'once');
            if isempty(tok)
                skipped_files(end+1,1) = string(fp); %#ok<AGROW>
                continue;
            end
            pa = string(tok{1});
            pa_order_seen(end+1,1) = pa; %#ok<AGROW>

            S = load(fp);

            % Required fields
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

            % Pull window IDs
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
            row.id_min = safe_min(ids_valid);
            row.id_max = safe_max(ids_valid);
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
    if isempty(pa_list)
        error('No pilot_S##_PA*.mat files found under: %s', data_root);
    end

    % Global ID checks
    n_total = numel(all_ids);
    n_unique = numel(unique(all_ids));
    has_global_duplicates = n_total ~= n_unique;

    if has_global_duplicates
        problems(end+1,1) = sprintf("Global duplicate window_id values detected | total=%d unique=%d", n_total, n_unique); %#ok<AGROW>
    end

    global_min = safe_min(all_ids);
    global_max = safe_max(all_ids);

    missing_ids = [];
    if ~isempty(all_ids) && all(~isnan(all_ids))
        expected_ids = (global_min:global_max).';
        missing_ids = setdiff(expected_ids, unique(all_ids));
        if ~isempty(missing_ids)
            problems(end+1,1) = sprintf("Global window_id gaps detected | missing=%d", numel(missing_ids)); %#ok<AGROW>
        end
    end

    % Per-PA counts
    pa_counts = struct();
    for i = 1:numel(pa_list)
        pa = pa_list(i);
        mask = (all_pas == pa);
        ids_pa = all_ids(mask);
        shards_pa = unique(all_shards(mask));

        pa_counts.(char(pa)) = struct( ...
            'count', numel(ids_pa), ...
            'unique_count', numel(unique(ids_pa)), ...
            'id_min', safe_min(ids_pa), ...
            'id_max', safe_max(ids_pa), ...
            'n_shards_present', numel(shards_pa), ...
            'shards_present', shards_pa(:).' );
    end

    % Report struct
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

    % Save
    save(fullfile(results_root, 'verify_report.mat'), 'report', '-v7');

    fprintf('SUMMARY\n');
    fprintf('  shard folders found : %d\n', report.n_shards_found);
    fprintf('  pilot IDs total     : %d\n', report.n_total_ids);
    fprintf('  pilot IDs unique    : %d\n', report.n_unique_ids);
    fprintf('  global id min/max   : %d / %d\n', report.global_id_min, report.global_id_max);
    fprintf('  has duplicates      : %s\n', tf(report.has_global_duplicates));
    fprintf('  has gaps            : %s', tf(~isempty(report.global_missing_ids)));
    if ~isempty(report.global_missing_ids)
        fprintf('  (%d missing)', numel(report.global_missing_ids));
    end
    fprintf('\n');

    fprintf('\nPER-PA\n');
    for i = 1:numel(pa_list)
        pa = pa_list(i);
        C = report.per_pa.(char(pa));
        fprintf('  %-4s | count=%5d | unique=%5d | ids=[%d..%d] | shards=%d\n', ...
            pa, C.count, C.unique_count, C.id_min, C.id_max, C.n_shards_present);
    end

    if ~isempty(skipped_files)
        fprintf('\nSKIPPED NON-PILOT MAT FILES (%d)\n', numel(skipped_files));
        for i = 1:numel(skipped_files)
            fprintf('  %s\n', skipped_files(i));
        end
    end

    if isempty(problems)
        fprintf('\nNo problems detected.\n');
    else
        fprintf('\nPROBLEMS DETECTED (%d)\n', numel(problems));
        for i = 1:numel(problems)
            fprintf('  - %s\n', problems(i));
        end
    end

    fprintf('\nSaved report: %s\n', fullfile(results_root, 'verify_report.mat'));
end

function n = parse_shard_num(shard_name)
    tok = regexp(char(shard_name), '^shard_(\d+)$', 'tokens', 'once');
    if isempty(tok)
        n = NaN;
    else
        n = str2double(tok{1});
    end
end

function v = safe_min(x)
    if isempty(x)
        v = NaN;
    else
        v = min(x);
    end
end

function v = safe_max(x)
    if isempty(x)
        v = NaN;
    else
        v = max(x);
    end
end

function s = tf(ok)
    if ok
        s = 'YES';
    else
        s = 'NO';
    end
end