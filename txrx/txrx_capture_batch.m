function txrx_capture_batch(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id, shard_list)
%TXRX_CAPTURE_BATCH Run txrx_capture over many shards back-to-back with retry.
%
% Behavior:
%   - Calls txrx_capture for each shard
%   - Loads saved txrx_cfg from the output MAT-file
%   - Retries the shard if capture_overruns exceeds a threshold
%   - Deletes bad output before retrying
%
% Example:
%   txrx_capture_batch("wifi", "192.168.10.2", "192.168.10.3", ...
%       2.437e9, 30, 10, "TX/RX", "wifi_high_run01", 1:20)

    if nargin < 9
        error("Usage: txrx_capture_batch(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id, shard_list)");
    end

    shard_list = double(shard_list(:)).';

    % ---------------- USER KNOBS ----------------
    max_retries = 4;                 % total attempts per shard = 1 + max_retries
    max_capture_overruns = 10;       % retry if capture_overruns > this
    max_total_overruns = inf;        % optional secondary gate; leave inf to ignore
    pause_between_attempts_s = 5.0;  % wait a bit before retry
    pause_between_shards_s = 2.0;    % wait between successful shards
    delete_failed_output = true;     % delete shard file before retry
    % -------------------------------------------

    protocol_s = string(protocol);
    dataset_id_s = string(dataset_id);

    if exist('pa_root', 'file') == 2
        root = pa_root();
    else
        this_file = mfilename('fullpath');
        this_dir = fileparts(this_file);
        if strcmp(string(fileparts(this_dir)), "txrx")
            root = fileparts(this_dir);
        else
            root = this_dir;
        end
    end

    addpath(fullfile(root, 'core'));
    addpath(fullfile(root, 'txrx'));
    addpath(fullfile(root, 'tools'));
    if isfolder(fullfile(root, 'protocol'))
        addpath(genpath(fullfile(root, 'protocol')));
    end

    R = pa_protocol_roots(protocol_s);
    dataset_full = normalize_dataset_id_local(protocol_s, dataset_id_s);

    fprintf("TXRX BATCH | protocol=%s | dataset=%s | shards=%s\n", ...
        protocol_s, dataset_full, mat2str(shard_list));
    fprintf("TXRX BATCH | retry policy: max_retries=%d | max_capture_overruns=%g | max_total_overruns=%g\n", ...
        max_retries, max_capture_overruns, max_total_overruns);

    batch_t0 = tic;
    results = struct( ...
        'shard', {}, ...
        'ok', {}, ...
        'attempts', {}, ...
        'capture_overruns', {}, ...
        'total_overruns', {}, ...
        'message', {}, ...
        'elapsed_s', {});

    for i = 1:numel(shard_list)
        shard_id = shard_list(i);

        out_file = fullfile( ...
            R.txrx_tapes_ota, ...
            char(dataset_full), ...
            sprintf("ota_tape_shard_%03d.mat", shard_id));

        fprintf("\n============================================================\n");
        fprintf("TXRX BATCH | starting shard %03d (%d/%d)\n", shard_id, i, numel(shard_list));
        fprintf("============================================================\n");

        shard_ok = false;
        shard_msg = "";
        shard_capture_overruns = NaN;
        shard_total_overruns = NaN;
        shard_attempts = 0;
        shard_t0 = tic;

        for attempt = 1:(1 + max_retries)
            shard_attempts = attempt;

            fprintf("TXRX BATCH | shard %03d | attempt %d/%d\n", ...
                shard_id, attempt, 1 + max_retries);

            try
                txrx_capture(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id, shard_id);

                if ~isfile(out_file)
                    error("Expected output file not found after capture: %s", out_file);
                end

                S = load(out_file, 'txrx_cfg');
                if ~isfield(S, 'txrx_cfg')
                    error("Output file missing txrx_cfg: %s", out_file);
                end

                txrx_cfg = S.txrx_cfg;

                if isfield(txrx_cfg, 'capture_overruns')
                    shard_capture_overruns = double(txrx_cfg.capture_overruns);
                else
                    shard_capture_overruns = NaN;
                end

                if isfield(txrx_cfg, 'overruns')
                    shard_total_overruns = double(txrx_cfg.overruns);
                else
                    shard_total_overruns = NaN;
                end

                fprintf("TXRX BATCH | shard %03d | attempt %d result: capture_overruns=%g | total_overruns=%g\n", ...
                    shard_id, attempt, shard_capture_overruns, shard_total_overruns);

                bad_capture = isfinite(max_capture_overruns) && isfinite(shard_capture_overruns) && ...
                              (shard_capture_overruns > max_capture_overruns);

                bad_total = isfinite(max_total_overruns) && isfinite(shard_total_overruns) && ...
                            (shard_total_overruns > max_total_overruns);

                if bad_capture || bad_total
                    reasons = strings(0,1);
                    if bad_capture
                        reasons(end+1) = "capture_overruns=" + string(shard_capture_overruns) + ...
                                         " > " + string(max_capture_overruns); %#ok<AGROW>
                    end
                    if bad_total
                        reasons(end+1) = "total_overruns=" + string(shard_total_overruns) + ...
                                         " > " + string(max_total_overruns); %#ok<AGROW>
                    end
                    shard_msg = "Retrying because " + strjoin(reasons, ", ");

                    fprintf("TXRX BATCH | shard %03d | %s\n", shard_id, shard_msg);

                    if delete_failed_output && isfile(out_file)
                        delete(out_file);
                        fprintf("TXRX BATCH | shard %03d | deleted failed output before retry\n", shard_id);
                    end

                    if attempt < (1 + max_retries)
                        pause(pause_between_attempts_s);
                        continue;
                    else
                        shard_ok = false;
                        break;
                    end
                end

                shard_ok = true;
                shard_msg = "OK";
                break

            catch ME
                shard_msg = string(ME.message);

                fprintf("TXRX BATCH | shard %03d | attempt %d FAILED\n", shard_id, attempt);
                fprintf("TXRX BATCH | error: %s\n", ME.message);

                if delete_failed_output && isfile(out_file)
                    delete(out_file);
                    fprintf("TXRX BATCH | shard %03d | deleted partial/failed output\n", shard_id);
                end

                if attempt < (1 + max_retries)
                    pause(pause_between_attempts_s);
                end
            end
        end

        elapsed_s = toc(shard_t0);

        results(end+1).shard = shard_id; %#ok<AGROW>
        results(end).ok = shard_ok;
        results(end).attempts = shard_attempts;
        results(end).capture_overruns = shard_capture_overruns;
        results(end).total_overruns = shard_total_overruns;
        results(end).message = shard_msg;
        results(end).elapsed_s = elapsed_s;

        if shard_ok
            fprintf("TXRX BATCH | shard %03d completed successfully in %.1f s after %d attempt(s)\n", ...
                shard_id, elapsed_s, shard_attempts);
            pause(pause_between_shards_s);
        else
            fprintf("TXRX BATCH | shard %03d FAILED after %.1f s and %d attempt(s)\n", ...
                shard_id, elapsed_s, shard_attempts);
        end
    end

    fprintf("\n============================================================\n");
    fprintf("TXRX BATCH DONE | total elapsed = %.1f s\n", toc(batch_t0));
    fprintf("============================================================\n");

    for i = 1:numel(results)
        if results(i).ok
            fprintf("  shard %03d : OK     | attempts=%d | capture_overruns=%g | total_overruns=%g | %.1f s\n", ...
                results(i).shard, ...
                results(i).attempts, ...
                results(i).capture_overruns, ...
                results(i).total_overruns, ...
                results(i).elapsed_s);
        else
            fprintf("  shard %03d : FAIL   | attempts=%d | capture_overruns=%g | total_overruns=%g | %.1f s | %s\n", ...
                results(i).shard, ...
                results(i).attempts, ...
                results(i).capture_overruns, ...
                results(i).total_overruns, ...
                results(i).elapsed_s, ...
                results(i).message);
        end
    end
end


function dataset_full = normalize_dataset_id_local(protocol_s, dataset_id)
    dataset_id = string(dataset_id);
    prefix = protocol_s + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
    else
        dataset_full = prefix + dataset_id;
    end
end