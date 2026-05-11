function resplice_bank_worker(protocol, dataset_id, shard_id, varargin)
%RESPLICE_BANK_WORKER One-shard worker: resplice -> verify -> bank -> verify -> prune
%
% Default policy (matches your preference):
%   - KEEP OTA tapes
%   - DELETE spliced shard dir after bank succeeds
%   - DELETE tx_tape shard after bank succeeds
%
% Usage (from repo root):
%   matlab -batch "resplice_bank_worker('wifi','wifi_high_run01',7)"
%
% Optional name/value:
%   'seed_k'                   (default 100000)
%   'seed_radius'              (default 50000)
%   'search_radius'            (default 500)
%   'slip_frames'              (default -3:3)
%   'auto_skip_records'        (default 20)
%   'auto_skip_search_radius'  (default 500)
%   'resplice_min_keep_frac'   (default 0.98)
%   'hard_scan_enable'         (default true)   % only used if resplicer supports it
%   'hard_scan_span'           (default 700000) % only used if resplicer supports it
%   'delete_spliced_after_bank'(default true)
%   'delete_tx_tape_after_bank'(default true)
%   'delete_ota_after_bank'    (default false)

    % ---------- parse args ----------
    ip = inputParser;
    addParameter(ip, 'seed_k', 100000, @(x) isnumeric(x) && isscalar(x));
    addParameter(ip, 'seed_radius', 50000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'search_radius', 500, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'slip_frames', -3:3, @(x) isnumeric(x) && isvector(x));
    addParameter(ip, 'auto_skip_records', 20, @(x) isnumeric(x) && isscalar(x) && x >= 0);
    addParameter(ip, 'auto_skip_search_radius', 500, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'resplice_min_keep_frac', 0.98, @(x) isnumeric(x) && isscalar(x) && x > 0 && x <= 1);
    addParameter(ip, 'hard_scan_enable', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'hard_scan_span', 700000, @(x) isnumeric(x) && isscalar(x) && x > 0);

    addParameter(ip, 'delete_spliced_after_bank', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'delete_tx_tape_after_bank', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'delete_ota_after_bank', false, @(x) islogical(x) || isnumeric(x));

    parse(ip, varargin{:});

    protocol   = string(protocol);
    dataset_id = string(dataset_id);
    shard_id   = round(double(shard_id));

    seed_k                  = round(double(ip.Results.seed_k));
    seed_radius             = round(double(ip.Results.seed_radius));
    search_radius           = round(double(ip.Results.search_radius));
    slip_frames             = round(double(ip.Results.slip_frames(:).'));
    auto_skip_records       = round(double(ip.Results.auto_skip_records));
    auto_skip_search_radius = round(double(ip.Results.auto_skip_search_radius));
    resplice_min_keep_frac  = double(ip.Results.resplice_min_keep_frac);
    hard_scan_enable        = logical(ip.Results.hard_scan_enable);
    hard_scan_span          = round(double(ip.Results.hard_scan_span));

    del_spliced = logical(ip.Results.delete_spliced_after_bank);
    del_tx      = logical(ip.Results.delete_tx_tape_after_bank);
    del_ota     = logical(ip.Results.delete_ota_after_bank);

    % ---------- paths ----------
    root = "";
    if exist('pa_root','file') == 2
        root = string(pa_root());
    else
        root = string(fileparts(mfilename('fullpath')));
    end
    addpath(fullfile(root,'core'));
    addpath(fullfile(root,'txrx'));
    addpath(fullfile(root,'tools'));
    if isfolder(fullfile(root,'protocol'))
        addpath(genpath(fullfile(root,'protocol')));
    end

    fprintf("\n=== WORKER | %s | %s | shard %03d ===\n", protocol, dataset_id, shard_id);

    % normalize dataset_full like your other scripts
    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
    else
        dataset_full = prefix + dataset_id;
    end

    R = pa_protocol_roots(protocol);

    ota_file = fullfile(R.txrx_tapes_ota, char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_id));
    spec_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_spec_shard_%03d.mat", shard_id));

    if ~isfile(ota_file),  error("OTA tape missing: %s", ota_file); end
    if ~isfile(spec_file), error("TX spec missing: %s", spec_file); end

    % ---------- 1) RESPLICE ----------
    fprintf("RESPLICE...\n");
    % Only pass hard_scan args if the resplicer supports them (avoids 'unrecognized parameter')
    args = { ...
        'seed_k', seed_k, ...
        'seed_radius', seed_radius, ...
        'search_radius', search_radius, ...
        'slip_frames', slip_frames, ...
        'auto_skip_records', auto_skip_records, ...
        'auto_skip_search_radius', auto_skip_search_radius, ...
        'make_png', false, ...
        'delete_ota_after_load', false ...
    };

    try
        rx_resplice_tape_simple(protocol, dataset_id, shard_id, args{:}, ...
            'hard_scan_enable', hard_scan_enable, ...
            'hard_scan_span', hard_scan_span);
    catch ME
        % If resplicer doesn't accept hard_scan args, retry without them.
        if contains(string(ME.message), "not a recognized") || contains(string(ME.message), "Unrecognized parameter")
            rx_resplice_tape_simple(protocol, dataset_id, shard_id, args{:});
        else
            rethrow(ME);
        end
    end

    % ---------- 2) RESPLICE QUALITY ----------
    [resp_ok, resp_msg, keep_frac] = check_resplice_quality_local(protocol, dataset_full, shard_id, resplice_min_keep_frac);
    if ~resp_ok
        error("RESPLICE_QUALITY_FAIL | %s", resp_msg);
    end
    fprintf("RESPLICE OK | keep_frac=%.4f\n", keep_frac);

    % ---------- 3) BANK ----------
    [bank_name, run_suffix, pas, expected_total] = bank_policy_from_dataset(protocol, dataset_id);

    fprintf("BANK... | bank_name=%s | run_suffix=%s\n", bank_name, run_suffix);

    if protocol == "wifi"
        build_ota_bank(bank_name, shard_id, ...
            'run_suffix', run_suffix, ...
            'protocols', "wifi", ...
            'pas', pas, ...
            'mode', "all", ...
            'chunk_n', 8, ...
            'delete_spliced_after_write', false, ...
            'verbose', true);
    elseif protocol == "bluetooth"
        build_ota_bank(bank_name, [], ...
            'run_suffix', run_suffix, ...
            'protocols', "bluetooth", ...
            'bt_shards', shard_id, ...
            'pas', pas, ...
            'mode', "all", ...
            'chunk_n', 8, ...
            'delete_spliced_after_write', false, ...
            'verbose', true);
    elseif protocol == "zigbee"
        build_ota_bank(bank_name, [], ...
            'run_suffix', run_suffix, ...
            'protocols', "zigbee", ...
            'zb_shards', shard_id, ...
            'pas', pas, ...
            'mode', "all", ...
            'chunk_n', 8, ...
            'delete_spliced_after_write', false, ...
            'verbose', true);
    else
        error("Unsupported protocol %s", protocol);
    end

    % ---------- 4) BANK QUALITY (missing <= 20) ----------
    [bank_ok, bank_msg] = check_bank_quality_local(root, protocol, bank_name, shard_id, pas, expected_total, 20);
    if ~bank_ok
        error("BANK_QUALITY_FAIL | %s", bank_msg);
    end
    fprintf("BANK OK | %s\n", bank_msg);

    % ---------- 5) PRUNE (on success only) ----------
    if del_spliced
        try_delete_spliced_shard_local(root, protocol, dataset_full, shard_id);
    end
    if del_tx
        try_delete_tx_tape_local(protocol, dataset_full, shard_id);
    end
    if del_ota
        try_delete_ota_tape_local(protocol, dataset_full, shard_id);
    end

    fprintf("=== WORKER DONE | %s | %s | shard %03d ===\n", protocol, dataset_id, shard_id);
end

% ---------------- helpers ----------------

function [ok, msg, keep_frac] = check_resplice_quality_local(protocol, dataset_full, shard_id, min_keep_frac)
    ok = false; msg = ""; keep_frac = NaN;

    out_res = fullfile(pa_root(), 'results', char(protocol), 'ota', 'rx_resplice_simple', ...
        char(dataset_full), sprintf('shard_%03d', shard_id));
    fsum = fullfile(out_res, "resplice_summary_simple.mat");
    if ~isfile(fsum)
        msg = "missing resplice_summary_simple.mat";
        return;
    end
    S = load(fsum, "summary");
    summary = S.summary;

    if ~isfield(summary,'stop_seen') || summary.stop_seen ~= 1
        msg = "stop_seen=0 (chain did not terminate cleanly)";
        return;
    end

    n_keep = double(summary.n_keep);
    n_hdr  = double(summary.n_headers);
    keep_frac = n_keep / max(1, n_hdr);

    if keep_frac < min_keep_frac
        msg = sprintf("keep_frac=%.4f < %.4f (keep=%d hdr=%d)", keep_frac, min_keep_frac, n_keep, n_hdr);
        return;
    end

    ok = true;
    msg = "ok";
end

function [bank_name, run_suffix, pas, expected_total] = bank_policy_from_dataset(protocol, dataset_id)
    % dataset_id may be "wifi_high_run01" or "high_run01"
    % We key off suffix tokens.
    did = string(dataset_id);
    did = erase(did, protocol + "_"); % remove protocol prefix if present

    if contains(did, "high_run01")
        bank_name = "ota_core_high_run01";
        run_suffix = "high_run01";
        pas = ["PA2","PA3","PA4","PA8"];
        expected_total = 4 * 500;
        return;
    end
    if contains(did, "pa1_run01")
        bank_name = "ota_pa1_run01";
        run_suffix = "pa1_run01";
        pas = ["PA1"];
        expected_total = 1 * 2000; % your PA1 shards are 2000 windows per shard (5 shards over 10k)
        % If you want a different expected count, change here.
        return;
    end

    error("Unknown dataset_id suffix mapping for banking: %s", dataset_id);
end

function [ok, msg] = check_bank_quality_local(root, protocol, bank_name, shard_id, pas, expected_total, max_missing)
    ok = false; msg = "";

    out_dir = fullfile(root, "data", char(protocol), "ota", char(bank_name));
    if ~isfolder(out_dir)
        msg = sprintf("missing bank dir: %s", out_dir);
        return;
    end

    actual_total = 0;
    missing_files = strings(0,1);

    for pa = pas
        f = fullfile(out_dir, sprintf("%s__shard_%03d__%s.mat", char(bank_name), shard_id, char(pa)));
        if ~isfile(f)
            missing_files(end+1,1) = string(f); %#ok<AGROW>
            continue;
        end
        W = whos('-file', f, 'X');
        if isempty(W)
            missing_files(end+1,1) = string(f) + " (no X)"; %#ok<AGROW>
            continue;
        end
        actual_total = actual_total + double(W.size(1));
    end

    missing = expected_total - actual_total;
    if missing <= max_missing && isempty(missing_files)
        ok = true;
        msg = sprintf("expected=%d actual=%d missing=%d (<=%d)", expected_total, actual_total, missing, max_missing);
    else
        msg = sprintf("expected=%d actual=%d missing=%d | missing_files=%d", expected_total, actual_total, missing, numel(missing_files));
    end
end

function try_delete_spliced_shard_local(root, protocol, dataset_full, shard_id)
    spliced_dir = fullfile(root, "data", char(protocol), "ota", "spliced", "simple", ...
        char(dataset_full), sprintf("shard_%03d", shard_id));
    if isfolder(spliced_dir)
        try
            rmdir(spliced_dir, 's');
            fprintf("Deleted spliced shard dir: %s\n", spliced_dir);
        catch ME
            warning("Failed deleting spliced shard dir: %s | %s", spliced_dir, ME.message);
        end
    end
end

function try_delete_tx_tape_local(protocol, dataset_full, shard_id)
    R = pa_protocol_roots(protocol);
    tx_tape_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_tape_shard_%03d.mat", shard_id));
    if isfile(tx_tape_file)
        try
            delete(tx_tape_file);
            fprintf("Deleted TX tape shard: %s\n", tx_tape_file);
        catch ME
            warning("Failed deleting TX tape shard: %s | %s", tx_tape_file, ME.message);
        end
    end
end

function try_delete_ota_tape_local(protocol, dataset_full, shard_id)
    R = pa_protocol_roots(protocol);
    ota_file = fullfile(R.txrx_tapes_ota, char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_id));
    if isfile(ota_file)
        try
            delete(ota_file);
            fprintf("Deleted OTA tape shard: %s\n", ota_file);
        catch ME
            warning("Failed deleting OTA tape shard: %s | %s", ota_file, ME.message);
        end
    end
end
