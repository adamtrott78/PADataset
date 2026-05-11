function capture_resplice_batch(jobs, varargin)
%CAPTURE_RESPLICE_BATCH
% Per shard: CAPTURE (retry-gated) -> RESPLICE -> BANK -> (optional) DELETE OTA/TX/spliced.
%
% Key feature: capture retries until (capture_overruns + capture_underruns) <= max_capture_events
% and capture_len_raw >= expected_Ncap * min_fill_frac.

    if nargin < 1 || isempty(jobs)
        jobs = capture_jobs_v01();
    end

    % ---------------- OPTIONS ----------------
    ip = inputParser;

    % pruning (default: ON for real runs; set all false for smoke)
    addParameter(ip, 'prune_ota_after_bank', true,  @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'prune_tx_tape_after_success', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'prune_spliced_after_bank', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'skip_if_bank_exists', false, @(x) islogical(x) || isnumeric(x));

    % resplice knobs
    addParameter(ip, 'seed_k', 0, @(x) isnumeric(x) && isscalar(x));
    addParameter(ip, 'seed_radius', 25000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'search_radius', 1000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'slip_frames', -2:2, @(x) isnumeric(x) && isvector(x));
    addParameter(ip, 'auto_skip_records', 20, @(x) isnumeric(x) && isscalar(x) && x >= 0);
    addParameter(ip, 'auto_skip_search_radius', 500, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'resplice_min_keep_frac', 0.98, @(x) isnumeric(x) && isscalar(x) && x > 0 && x <= 1);

    % capture retry gate
    addParameter(ip, 'max_capture_attempts', 5, @(x) isnumeric(x) && isscalar(x) && x >= 1);
    addParameter(ip, 'max_capture_events', 10, @(x) isnumeric(x) && isscalar(x) && x >= 0); % overruns+underruns
    addParameter(ip, 'min_fill_frac', 0.999, @(x) isnumeric(x) && isscalar(x) && x > 0 && x <= 1);
    addParameter(ip, 'pause_between_capture_attempts_s', 5.0, @(x) isnumeric(x) && isscalar(x) && x >= 0);

    parse(ip, varargin{:});

    prune_ota_after_bank = logical(ip.Results.prune_ota_after_bank);
    prune_tx_tape_after_success = logical(ip.Results.prune_tx_tape_after_success);
    prune_spliced_after_bank = logical(ip.Results.prune_spliced_after_bank);
    skip_if_bank_exists = logical(ip.Results.skip_if_bank_exists);

    seed_k = round(double(ip.Results.seed_k));
    seed_radius = round(double(ip.Results.seed_radius));
    search_radius = round(double(ip.Results.search_radius));
    slip_frames = round(double(ip.Results.slip_frames(:).'));
    auto_skip_records = round(double(ip.Results.auto_skip_records));
    auto_skip_search_radius = round(double(ip.Results.auto_skip_search_radius));
    resplice_min_keep_frac = double(ip.Results.resplice_min_keep_frac);

    max_capture_attempts = round(double(ip.Results.max_capture_attempts));
    max_capture_events = round(double(ip.Results.max_capture_events));
    min_fill_frac = double(ip.Results.min_fill_frac);
    pause_between_capture_attempts_s = double(ip.Results.pause_between_capture_attempts_s);
    % -----------------------------------------

    % ---------------- USER SETTINGS ----------------
    tx_ip = "192.168.10.2";
    rx_ip = "192.168.10.3";
    ant   = "TX/RX";

    fc_hz = 2.437e9;
    tx_gain_db = 30;
    rx_gain_db = 10;
    % ------------------------------------------------

    % ---------------- LOGGING SETUP ----------------
    log_root = fullfile(pa_root(), "results", "ota_batch_logs");
    if ~exist(log_root, "dir"), mkdir(log_root); end

    run_tag = char(datetime("now","Format","yyyyMMdd_HHmmss"));
    log_file = fullfile(log_root, "capture_resplice_" + string(run_tag) + ".log");
    csv_file = fullfile(log_root, "capture_resplice_" + string(run_tag) + ".csv");
    mat_file = fullfile(log_root, "capture_resplice_" + string(run_tag) + ".mat");

    diary off; diary(log_file); diary on;
    fprintf("=== RUN %s ===\n", run_tag);
    fprintf("Log: %s\n", log_file);
    fprintf("Capture gate: attempts=%d | max_events=%d | min_fill_frac=%.4f\n", ...
        max_capture_attempts, max_capture_events, min_fill_frac);
    fprintf("Prune: ota=%d tx=%d spliced=%d\n", ...
        prune_ota_after_bank, prune_tx_tape_after_success, prune_spliced_after_bank);
    % ------------------------------------------------

    rows = [];
    row_idx = 0;

    for j = 1:numel(jobs)
        protocol   = string(jobs(j).protocol);
        dataset_id = string(jobs(j).dataset_id);
        shards     = double(jobs(j).shards(:)).';
        do_cap     = logical(jobs(j).do_capture);
        do_rsp     = logical(jobs(j).do_resplice);

        fprintf("\n============================================================\n");
        fprintf("JOB %d/%d | %s | %s | shards=%s | capture=%d resplice=%d\n", ...
            j, numel(jobs), protocol, dataset_id, mat2str(shards), do_cap, do_rsp);
        fprintf("============================================================\n");

        for shard_id = shards
            row_idx = row_idx + 1;
            t0 = datetime("now");
            status = "ok";
            where = "none";
            msg = "";
            bank_ok = false;

            cap_ok = ~do_cap;         % if not capturing, treat as "ok" (or set false if you want)
            cap_events = NaN;
            resp_ok = ~do_rsp;        % if not resplicing, treat as "ok"
            resp_keep_frac = NaN;

            fprintf("\n--- %s | %s | shard %03d ---\n", protocol, dataset_id, shard_id);

            try
                suf = run_suffix_from_dataset(protocol, dataset_id);
                bank_name = bank_name_from_suffix(suf);
                pas = pas_for_dataset_suffix(suf);

                if skip_if_bank_exists && bank_exists(protocol, bank_name, shard_id)
                    fprintf("Skip: bank exists for %s shard %03d\n", bank_name, shard_id);
                    status = "skipped_bank_exists";
                else
                    % ---- 1) CAPTURE (retry-gated) ----
                    if do_cap
                        where = "capture";
                        [cap_ok, cap_events, kept_bad] = txrx_capture_retry_gate( ...
                            protocol, dataset_id, shard_id, ...
                            tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, ...
                            max_capture_attempts, max_capture_events, min_fill_frac, pause_between_capture_attempts_s);
                        
                        if ~cap_ok
                            error("CAPTURE_QUALITY_FAIL | events=%d > %d | kept_bad=%d | stopping shard (OTA retained).", ...
                                cap_events, max_capture_events, kept_bad);
                        end
                    end

                    % ---- 2) RESPLICE (never delete OTA inside resplicer) ----
                    if do_rsp
                        where = "resplice";
                        rx_resplice_tape_simple(protocol, dataset_id, shard_id, ...
                            'seed_k', seed_k, ...
                            'seed_radius', seed_radius, ...
                            'search_radius', search_radius, ...
                            'slip_frames', slip_frames, ...
                            'auto_skip_records', auto_skip_records, ...
                            'auto_skip_search_radius', auto_skip_search_radius, ...
                            'make_png', false, ...
                            'delete_ota_after_load', false);
                            
                        [resp_ok, resp_msg, resp_keep_frac] = check_resplice_quality(protocol, dataset_id, shard_id, resplice_min_keep_frac);
                        if ~resp_ok
                            error("RESPLICE_QUALITY_FAIL | %s (keeping OTA + keeping splices).", resp_msg);
                        end
                    end

                    % ---- 3) BANK ----
                    where = "bank";
                    
                    % IMPORTANT POLICY:
                    %   Never delete spliced inputs inside build_ota_bank.
                    %   We only delete spliced shard folder AFTER bank succeeds.
                    del_spliced_inside_bank = false;
                    
                    if protocol == "wifi"
                        build_ota_bank(bank_name, shard_id, ...
                            'run_suffix', suf, ...
                            'protocols', "wifi", ...
                            'pas', pas, ...
                            'mode', "all", ...
                            'chunk_n', 8, ...
                            'delete_spliced_after_write', del_spliced_inside_bank, ...
                            'verbose', true);
                    
                    elseif protocol == "bluetooth"
                        build_ota_bank(bank_name, [], ...
                            'run_suffix', suf, ...
                            'protocols', "bluetooth", ...
                            'bt_shards', shard_id, ...
                            'pas', pas, ...
                            'mode', "all", ...
                            'chunk_n', 8, ...
                            'delete_spliced_after_write', del_spliced_inside_bank, ...
                            'verbose', true);
                    
                    elseif protocol == "zigbee"
                        build_ota_bank(bank_name, [], ...
                            'run_suffix', suf, ...
                            'protocols', "zigbee", ...
                            'zb_shards', shard_id, ...
                            'pas', pas, ...
                            'mode', "all", ...
                            'chunk_n', 8, ...
                            'delete_spliced_after_write', del_spliced_inside_bank, ...
                            'verbose', true);
                    else
                        error("Unsupported protocol %s", protocol);
                    end
                    
                    bank_ok = true;  % only reaches here if bank succeeded
                    
                    % ---- 3b) DELETE SPLICED (atomic per-shard) ----
                    if prune_spliced_after_bank && bank_ok
                        where = "delete_spliced";
                        try_delete_spliced_shard(protocol, dataset_id, shard_id);
                    end
                    
                    % ---- 4) DELETE OTA ONLY AFTER bank_ok ----
                    if prune_ota_after_bank && bank_ok
                        where = "delete_ota";
                        try_delete_ota_tape(protocol, dataset_id, shard_id);
                    end
                    
                    % ---- 5) DELETE TX tape (optional) ----
                    if prune_tx_tape_after_success && bank_ok && cap_ok && resp_ok && (cap_events <= max_capture_events) && (resp_keep_frac >= resplice_min_keep_frac)
                        where = "delete_tx_tape";
                        try_delete_tx_tape(protocol, dataset_id, shard_id);
                    else
                        if prune_tx_tape_after_success
                            fprintf("KEEP TX_TAPE | bank_ok=%d cap_ok=%d resp_ok=%d cap_events=%g keep_frac=%g\n", ...
                                bank_ok, cap_ok, resp_ok, cap_events, resp_keep_frac);
                        end
                    end
                end

            catch ME
                status = "fail";
                msg = string(ME.message);
                fprintf("!!! ERROR in %s: %s\n", where, msg);
                fprintf("%s\n", getReport(ME, "extended", "hyperlinks", "off"));
            end

            t1 = datetime("now");
            dt_s = seconds(t1 - t0);

            rows(row_idx).timestamp  = char(t0); %#ok<AGROW>
            rows(row_idx).protocol   = char(protocol);
            rows(row_idx).dataset_id = char(dataset_id);
            rows(row_idx).shard_id   = shard_id;
            rows(row_idx).capture    = do_cap;
            rows(row_idx).resplice   = do_rsp;
            rows(row_idx).status     = char(status);
            rows(row_idx).where      = char(where);
            rows(row_idx).seconds    = dt_s;
            rows(row_idx).message    = char(msg);

            fprintf("DONE shard %03d | status=%s | where=%s | %.1fs\n", shard_id, status, where, dt_s);
        end
    end

    T = struct2table(rows);
    writetable(T, csv_file);
    save(mat_file, "T", "jobs");

    fprintf("\n=== COMPLETE ===\n");
    fprintf("CSV: %s\n", csv_file);
    fprintf("MAT: %s\n", mat_file);

    diary off;
    disp(groupcounts(T, "status"));
end

% ---------------- capture retry gate ----------------
function [ok, events, kept_bad] = txrx_capture_retry_gate(protocol, dataset_id, shard_id, ...
    tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, ...
    max_attempts, max_events, min_fill_frac, pause_s)

    ok = false;
    kept_bad = false;
    events = inf;

    protocol = string(protocol);
    dataset_id = string(dataset_id);

    prefix = protocol + "_";
    if startsWith(dataset_id, prefix), dataset_full = dataset_id; else, dataset_full = prefix + dataset_id; end
    R = pa_protocol_roots(protocol);

    out_file = fullfile(R.txrx_tapes_ota, char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_id));

    % TX cache build-once (your cached version; keep as you already implemented)
    tape_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_tape_shard_%03d.mat", shard_id));
    spec_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_spec_shard_%03d.mat", shard_id));
    if ~isfile(tape_file), error("Missing tx_tape: %s", tape_file); end
    if ~isfile(spec_file), error("Missing tx_spec: %s", spec_file); end

    St = load(tape_file, "tx_tape", "tx_params", "sync");
    Ss = load(spec_file, "tx_spec");
    tx_tape = St.tx_tape(:);
    tx_tape = complex(single(real(tx_tape)), single(imag(tx_tape)));
    p = St.tx_params; sync = St.sync; tx_spec = Ss.tx_spec;
    frameLen = double(p.frameLen);
    assert(mod(numel(tx_tape), frameLen) == 0, "tx_tape must be multiple of frameLen");
    tx_frames = reshape(tx_tape, frameLen, []);
    clear tx_tape

    tx_cache = struct("tx_frames",tx_frames,"tx_params",p,"sync",sync,"tx_spec",tx_spec);

    for attempt = 1:max_attempts
        fprintf("CAPTURE RETRY | %s | %s | shard %03d | attempt %d/%d\n", protocol, dataset_full, shard_id, attempt, max_attempts);

        if isfile(out_file), delete(out_file); end
        pretouch = (attempt == 1);

        try
            if attempt < max_attempts
                % strict attempts: do NOT write tape unless quality passes
                txrx_capture(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id, shard_id, ...
                    'tx_cache', tx_cache, ...
                    'pretouch_enable', pretouch, ...
                    'quality_enable', true, ...
                    'quality_max_events', max_events, ...
                    'quality_min_fill_frac', min_fill_frac);
                % if we get here => saved file exists
                ok = true;
            else
                % last attempt: try strict first; if it fails, keep a saved tape for debugging
                try
                    txrx_capture(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id, shard_id, ...
                        'tx_cache', tx_cache, ...
                        'pretouch_enable', pretouch, ...
                        'quality_enable', true, ...
                        'quality_max_events', max_events, ...
                        'quality_min_fill_frac', min_fill_frac);
                    ok = true;
                catch
                    % “keep last bad capture” policy
                    txrx_capture(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id, shard_id, ...
                        'tx_cache', tx_cache, ...
                        'pretouch_enable', pretouch, ...
                        'quality_enable', false);
                    ok = false;
                    kept_bad = true;
                end
            end

            if ~isfile(out_file)
                error("Expected OTA output not found: %s", out_file);
            end

            S = load(out_file, "txrx_cfg");
            co = double(S.txrx_cfg.capture_overruns);
            cu = double(S.txrx_cfg.capture_underruns);
            events = co + cu;

            fprintf("CAPTURE RETRY | DONE | ok=%d kept_bad=%d events=%d (max=%d)\n", ok, kept_bad, events, max_events);
            return;

        catch ME
            fprintf("CAPTURE RETRY | FAIL attempt %d/%d | %s\n", attempt, max_attempts, ME.message);
            if isfile(out_file), delete(out_file); end
            if attempt < max_attempts
                pause(pause_s);
            end
        end
    end
end

% ---------------- helper functions ----------------
function [ok, msg, keep_frac] = check_resplice_quality(protocol, dataset_id, shard_id, min_keep_frac)
    protocol = string(protocol);
    dataset_id = string(dataset_id);

    prefix = protocol + "_";
    if startsWith(dataset_id, prefix), dataset_full = dataset_id; else, dataset_full = prefix + dataset_id; end

    out_res = fullfile(pa_root(), 'results', char(protocol), 'ota', 'rx_resplice_simple', ...
        char(dataset_full), sprintf('shard_%03d', shard_id));

    fsum = fullfile(out_res, "resplice_summary_simple.mat");
    if ~isfile(fsum)
        ok = false; msg = "missing resplice_summary_simple.mat"; keep_frac = NaN; return;
    end

    S = load(fsum, "summary");
    summary = S.summary;

    if ~summary.stop_seen
        ok = false; msg = "stop_seen=0 (chain did not terminate cleanly)"; keep_frac = NaN; return;
    end

    n_keep = double(summary.n_keep);
    n_hdr  = double(summary.n_headers);
    keep_frac = n_keep / max(1, n_hdr);

    if keep_frac < min_keep_frac
        ok = false; msg = sprintf("keep_frac=%.3f < %.3f (keep=%d hdr=%d)", keep_frac, min_keep_frac, n_keep, n_hdr);
        return;
    end

    ok = true; msg = "ok";
end

function try_delete_spliced_shard(protocol, dataset_id, shard_id)
    protocol = string(protocol);
    dataset_id = string(dataset_id);

    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
    else
        dataset_full = prefix + dataset_id;
    end

    spliced_dir = fullfile(pa_root(), 'data', char(protocol), 'ota', 'spliced', 'simple', ...
        char(dataset_full), sprintf('shard_%03d', shard_id));

    if exist(spliced_dir, 'dir')
        try
            rmdir(spliced_dir, 's');
            fprintf("Deleted spliced shard dir: %s\n", spliced_dir);
        catch ME
            warning("Failed deleting spliced shard dir: %s | %s", spliced_dir, ME.message);
        end
    end
end

function suf = run_suffix_from_dataset(protocol, dataset_id)
    protocol = string(protocol);
    dataset_id = string(dataset_id);
    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        suf = extractAfter(dataset_id, strlength(prefix));
    else
        suf = dataset_id;
    end
end

function bank = bank_name_from_suffix(suf)
    suf = string(suf);
    if contains(lower(suf), "pa1")
        bank = "ota_pa1_run01";
    else
        bank = "ota_core_" + suf;
    end
end

function pas = pas_for_dataset_suffix(suf)
    suf = string(suf);
    if contains(lower(suf), "pa1")
        pas = ["PA1"];
    else
        pas = ["PA2","PA3","PA4","PA8"];
    end
end

function tf = bank_exists(protocol, bank_name, shard_id)
    protocol = string(protocol);
    bank_name = string(bank_name);
    out_dir = fullfile(pa_root(), "data", char(protocol), "ota", char(bank_name));
    if ~exist(out_dir, "dir"), tf = false; return; end
    pat = sprintf("%s__shard_%03d__*.mat", char(bank_name), shard_id);
    tf = ~isempty(dir(fullfile(out_dir, pat)));
end

function try_delete_ota_tape(protocol, dataset_id, shard_id)
    protocol = string(protocol);
    dataset_id = string(dataset_id);
    prefix = protocol + "_";
    if startsWith(dataset_id, prefix), dataset_full = dataset_id; else, dataset_full = prefix + dataset_id; end
    R = pa_protocol_roots(protocol);
    ota_file = fullfile(R.txrx_tapes_ota, char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_id));
    if isfile(ota_file)
        delete(ota_file);
        fprintf("Deleted OTA tape shard: %s\n", ota_file);
    end
end

function try_delete_tx_tape(protocol, dataset_id, shard_id)
    protocol = string(protocol);
    dataset_id = string(dataset_id);
    prefix = protocol + "_";
    if startsWith(dataset_id, prefix), dataset_full = dataset_id; else, dataset_full = prefix + dataset_id; end
    R = pa_protocol_roots(protocol);
    tx_tape_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_tape_shard_%03d.mat", shard_id));
    if isfile(tx_tape_file)
        delete(tx_tape_file);
        fprintf("Deleted TX tape shard: %s\n", tx_tape_file);
    end
end