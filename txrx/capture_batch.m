function capture_batch(jobs, varargin)
%CAPTURE_BATCH Capture-only batch runner with strict retry gate.
% For each shard:
%   - if tx_tape missing => skip (expected if you deleted after banking)
%   - else attempt capture up to max_capture_attempts
%   - txrx_capture is called with quality_enable=true so failures do NOT save
%
% Writes:
%   results/buh_logs/capture_<timestamp>.log
%   results/buh_logs/capture_<timestamp>.csv
%   results/buh_logs/capture_<timestamp>.mat

    if nargin < 1 || isempty(jobs)
        error("capture_batch requires an explicit jobs array.");
    end

    ip = inputParser;
    addParameter(ip, 'tx_ip', "192.168.10.2", @(x) isstring(x) || ischar(x));
    addParameter(ip, 'rx_ip', "192.168.10.3", @(x) isstring(x) || ischar(x));
    addParameter(ip, 'ant',   "TX/RX",        @(x) isstring(x) || ischar(x));
    addParameter(ip, 'fc_hz', 2.437e9,        @(x) isnumeric(x) && isscalar(x));
    addParameter(ip, 'tx_gain_db', 30,        @(x) isnumeric(x) && isscalar(x));
    addParameter(ip, 'rx_gain_db', 10,        @(x) isnumeric(x) && isscalar(x));

    addParameter(ip, 'max_capture_attempts', 20, @(x) isnumeric(x) && isscalar(x) && x>=1);
    addParameter(ip, 'max_capture_events',   4,  @(x) isnumeric(x) && isscalar(x) && x>=0);
    addParameter(ip, 'min_fill_frac',        0.999, @(x) isnumeric(x) && isscalar(x) && x>0 && x<=1);
    addParameter(ip, 'pause_between_attempts_s', 5.0, @(x) isnumeric(x) && isscalar(x) && x>=0);

    addParameter(ip, 'skip_if_ota_ok', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'overwrite', false, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'skip_if_bank_ok', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'skip_if_spliced_ok', true, @(x) islogical(x) || isnumeric(x));

    parse(ip, varargin{:});

    tx_ip = string(ip.Results.tx_ip);
    rx_ip = string(ip.Results.rx_ip);
    ant   = string(ip.Results.ant);

    fc_hz = double(ip.Results.fc_hz);
    tx_gain_db = double(ip.Results.tx_gain_db);
    rx_gain_db = double(ip.Results.rx_gain_db);

    max_capture_attempts = round(double(ip.Results.max_capture_attempts));
    max_capture_events   = round(double(ip.Results.max_capture_events));
    min_fill_frac        = double(ip.Results.min_fill_frac);
    pause_s              = double(ip.Results.pause_between_attempts_s);

    skip_if_ota_ok = logical(ip.Results.skip_if_ota_ok);
    overwrite      = logical(ip.Results.overwrite);
    skip_if_bank_ok   = logical(ip.Results.skip_if_bank_ok);
    skip_if_spliced_ok = logical(ip.Results.skip_if_spliced_ok);

    % ---------------- LOGGING ----------------
    log_root = fullfile(pa_root(), "results", "buh_logs");
    if ~exist(log_root, "dir"), mkdir(log_root); end

    run_tag = char(datetime("now","Format","yyyyMMdd_HHmmss"));
    log_file = fullfile(log_root, "capture_" + string(run_tag) + ".log");
    csv_file = fullfile(log_root, "capture_" + string(run_tag) + ".csv");
    mat_file = fullfile(log_root, "capture_" + string(run_tag) + ".mat");

    diary off; diary(log_file); diary on;
    fprintf("=== CAPTURE RUN %s ===\n", run_tag);
    fprintf("Log: %s\n", log_file);
    fprintf("Gate: attempts=%d | max_events=%d | min_fill_frac=%.4f\n", ...
        max_capture_attempts, max_capture_events, min_fill_frac);
    fprintf("Policy: skip_if_ota_ok=%d | overwrite=%d\n", skip_if_ota_ok, overwrite);
    % -----------------------------------------

    rows = struct( ...
        'timestamp', {}, 'protocol', {}, 'dataset_id', {}, 'shard_id', {}, ...
        'status', {}, 'attempts_used', {}, 'events', {}, 'fill_frac', {}, ...
        'out_file', {}, 'seconds', {}, 'message', {} );
    row_idx = 0;

    for j = 1:numel(jobs)
        protocol   = string(jobs(j).protocol);
        dataset_id = string(jobs(j).dataset_id);
        shards     = double(jobs(j).shards(:)).';

        fprintf("\n============================================================\n");
        fprintf("JOB %d/%d | CAPTURE ONLY | %s | %s | shards=%s\n", ...
            j, numel(jobs), protocol, dataset_id, mat2str(shards));
        fprintf("============================================================\n");

        for shard_id = shards
            row_idx = row_idx + 1;
            t0 = datetime("now");
            status = "ok";
            msg = "";
            attempts_used = 0;
            events = NaN;
            fill_frac = NaN;

            fprintf("\n--- CAPTURE | %s | %s | shard %03d ---\n", protocol, dataset_id, shard_id);
    
            % ---- 0) BANK precedence skip ----
            if skip_if_bank_ok && bank_complete(protocol, dataset_id, shard_id)
                status = "skipped_bank_ok";
                msg = "bank complete; capture skipped";
                fprintf("SKIP | %s\n", msg);
                dt_s = seconds(datetime("now") - t0);
                rows(row_idx) = make_row(t0, protocol, dataset_id, shard_id, status, attempts_used, events, fill_frac, "", dt_s, msg); %#ok<AGROW>
                continue;
            end
            
            % ---- 0b) SPLICE precedence skip ----
            if skip_if_spliced_ok && splices_complete(protocol, dataset_id, shard_id)
                status = "skipped_spliced_ok";
                msg = "splices complete; capture skipped";
                fprintf("SKIP | %s\n", msg);
                dt_s = seconds(datetime("now") - t0);
                rows(row_idx) = make_row(t0, protocol, dataset_id, shard_id, status, attempts_used, events, fill_frac, "", dt_s, msg);
                continue;
            end
        
            [tape_ok, tape_file, out_file] = resolve_files(protocol, dataset_id, shard_id);

            fprintf("\n--- CAPTURE | %s | %s | shard %03d ---\n", protocol, dataset_id, shard_id);

            % If tx_tape missing, we cannot capture. This is expected for shards you already banked.
            if ~tape_ok
                status = "skipped_no_tx";
                msg = "TX tape missing (likely deleted after banking).";
                fprintf("SKIP | %s\n", msg);
                dt_s = seconds(datetime("now") - t0);
                rows(row_idx) = make_row(t0, protocol, dataset_id, shard_id, status, attempts_used, events, fill_frac, out_file, dt_s, msg);
                continue;
            end
            
            % if a previous run died mid-save, kill the stranded tmp so we can recapture cleanly
            tmp = out_file + ".tmp";
            if isfile(tmp)
                delete(tmp);
                fprintf("CLEAN | deleted stranded tmp: %s\n", tmp);
            end
            
            % Skip if OTA already good
            if skip_if_ota_ok && isfile(out_file)
                [ok_old, e_old, f_old] = ota_meets_gate(out_file, max_capture_events, min_fill_frac);
                if ok_old
                    status = "skipped_ota_ok";
                    events = e_old;
                    fill_frac = f_old;
                    msg = "Existing OTA meets gate.";
                    fprintf("SKIP | %s | events=%d fill=%.6f\n", msg, events, fill_frac);
                    dt_s = seconds(datetime("now") - t0);
                    rows(row_idx) = make_row(t0, protocol, dataset_id, shard_id, status, attempts_used, events, fill_frac, out_file, dt_s, msg); %#ok<AGROW>
                    continue;
                else
                    if overwrite
                        fprintf("EXISTING BAD | overwrite=1 | deleting: %s\n", out_file);
                        delete(out_file);
                    else
                        fprintf("EXISTING BAD | overwrite=0 | will recapture, but keeping old file until a good one is produced.\n");
                        % We'll only delete it once we have a new good one.
                    end
                end
            end

            % Attempt loop
            ok = false;
            last_err = "";
            last_events = NaN;
            last_fill = NaN;

            for attempt = 1:max_capture_attempts
                attempts_used = attempt;
                fprintf("CAPTURE attempt %d/%d | %s | shard %03d\n", attempt, max_capture_attempts, dataset_id, shard_id);

                % If overwrite=1, ensure out_file cleared before attempt.
                % If overwrite=0, only delete out_file if it was created by a prior failed attempt (rare).
                if overwrite && isfile(out_file)
                    delete(out_file);
                end

                try
                    % Strict gate INSIDE txrx_capture: it will throw TXRX_GATED_FAIL and NOT save
                    txrx_capture(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id, shard_id, ...
                        'quality_enable', true, ...
                        'quality_max_events', max_capture_events, ...
                        'quality_min_fill_frac', min_fill_frac);

                    % If we got here, it passed gate AND should have saved.
                    if ~isfile(out_file) && ~isfile(out_file+".tmp")
                        error("Capture passed gate but out_file not found: %s", out_file);
                    end

                    [ok_now, e_now, f_now] = ota_meets_gate(out_file, max_capture_events, min_fill_frac);
                    last_events = e_now;
                    last_fill   = f_now;

                    if ok_now
                        ok = true;
                        fprintf("CAPTURE PASS | events=%d fill=%.6f\n", e_now, f_now);

                        % If overwrite=0 and we had a previous bad file, replace it now
                        % (we do nothing special here; txrx_capture wrote to the canonical path).
                        break;
                    else
                        last_err = sprintf("Post-check failed gate: events=%d fill=%.6f", e_now, f_now);
                        fprintf("CAPTURE FAIL (post-check) | %s\n", last_err);
                    end

                catch ME
                    last_err = string(ME.message);
                    fprintf("CAPTURE FAIL | %s\n", last_err);

                    % Ensure we do not keep a partial output when gate fails
                    if isfile(out_file) && overwrite
                        delete(out_file);
                    end
                end

                if attempt < max_capture_attempts
                    pause(pause_s);
                end
            end

            if ok
                status = "ok";
                events = last_events;
                fill_frac = last_fill;
                msg = "captured_ok";
            else
                status = "fail_quality";
                msg = "No attempt met gate. Last error: " + last_err;
            end

            dt_s = seconds(datetime("now") - t0);
            fprintf("DONE | %s | %s | shard %03d | status=%s | attempts=%d | events=%s | fill=%s | %.1fs\n", ...
                protocol, dataset_id, shard_id, status, attempts_used, num2str(events), num2str(fill_frac), dt_s);

            rows(row_idx) = make_row(t0, protocol, dataset_id, shard_id, status, attempts_used, events, fill_frac, out_file, dt_s, msg); %#ok<AGROW>
        end
    end

    % Write CSV + MAT
    T = struct2table(rows);
    writetable(T, csv_file);
    save(mat_file, "rows", "T", "jobs");

    fprintf("\nSaved CSV: %s\n", csv_file);
    fprintf("Saved MAT: %s\n", mat_file);

    diary off;
end

% ---------------- helpers ----------------

function row = make_row(t0, protocol, dataset_id, shard_id, status, attempts_used, events, fill_frac, out_file, dt_s, msg)
    row = struct();
    row.timestamp = char(t0);
    row.protocol  = char(protocol);
    row.dataset_id = char(dataset_id);
    row.shard_id  = shard_id;
    row.status    = char(status);
    row.attempts_used = attempts_used;
    row.events    = events;
    row.fill_frac = fill_frac;
    row.out_file  = char(out_file);
    row.seconds   = double(dt_s);
    row.message   = char(msg);
end

function [tape_ok, tape_file, out_file] = resolve_files(protocol, dataset_id, shard_id)
    protocol = string(protocol);
    dataset_id = string(dataset_id);

    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
    else
        dataset_full = prefix + dataset_id;
    end

    R = pa_protocol_roots(protocol);

    tape_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_tape_shard_%03d.mat", shard_id));
    out_file  = fullfile(R.txrx_tapes_ota,     char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_id));

    tape_ok = isfile(tape_file);
end

function [ok, events, fill_frac] = ota_meets_gate(out_file, max_events, min_fill_frac)
    ok = false; events = NaN; fill_frac = NaN;

    try
        S = load(out_file, "txrx_cfg");
        if ~isfield(S, "txrx_cfg")
            return;
        end
        cfg = S.txrx_cfg;

        co = double(cfg.capture_overruns);
        cu = double(cfg.capture_underruns);
        events = co + cu;

        % compute expected Ncap from cfg fields (no guessing)
        expected_Ncap = double(cfg.frameLen) * double(cfg.n_guard_pre_frames + cfg.n_main_frames + cfg.n_guard_post_frames);
        filled = double(cfg.capture_len_raw);
        fill_frac = filled / max(1, expected_Ncap);

        ok = (events <= max_events) && (fill_frac >= min_fill_frac);
    catch
        ok = false;
    end
end

function ok = splices_complete(protocol, dataset_id, shard_id)
% Return true iff spliced outputs exist and have expected window counts.

    protocol = string(protocol);
    dataset_id = string(dataset_id);

    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
        suffix = extractAfter(dataset_id, strlength(prefix));
    else
        dataset_full = prefix + dataset_id;
        suffix = dataset_id;
    end

    if suffix == "high_run01"
        pas = ["PA2","PA3","PA4","PA8"];
        expectedN = 500;
    elseif suffix == "pa1_run01"
        pas = ["PA1"];
        expectedN = 2000;
    else
        ok = false;
        return;
    end

    sp_dir = fullfile(pa_root(), "data", char(protocol), "ota", "spliced", "simple", char(dataset_full), sprintf("shard_%03d", shard_id));
    if ~isfolder(sp_dir)
        ok = false;
        return;
    end

    for pa = pas
        f = fullfile(sp_dir, sprintf("ota_rx_%s.mat", pa));
        if ~isfile(f)
            ok = false;
            return;
        end
        S = load(f, "meta_rx");
        if ~isfield(S,"meta_rx") || numel(S.meta_rx) ~= expectedN
            ok = false;
            return;
        end
    end

    ok = true;
end

function tf = bank_complete(protocol, dataset_id, shard_id)
    protocol = string(protocol);
    dataset_id = string(dataset_id);

    % suffix extraction (expects dataset_id already includes protocol prefix)
    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        suf = extractAfter(dataset_id, strlength(prefix));
    else
        % deterministic: if naming scheme violated, treat as not complete
        tf = false; return;
    end

    switch suf
        case "high_run01"
            bank_name = "ota_core_high_run01";
            pas = ["PA2","PA3","PA4","PA8"];
        case "pa1_run01"
            bank_name = "ota_pa1_run01";
            pas = ["PA1"];
        otherwise
            tf = false; return;
    end

    out_dir = fullfile(pa_root(), "data", char(protocol), "ota", char(bank_name));
    tf = true;
    for i = 1:numel(pas)
        f = fullfile(out_dir, sprintf("%s__shard_%03d__%s.mat", bank_name, shard_id, char(pas(i))));
        if ~isfile(f)
            tf = false; return;
        end
    end
end