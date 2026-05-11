function bank_missing_shards(protocol, dataset_id, shards)
%BANK_MISSING_SHARDS Rebuild only missing/corrupt bank files for given shards.
% Assumes spliced inputs exist:
%   data/<protocol>/ota/spliced/simple/<dataset_full>/shard_###/ota_rx_<PA>.mat
%
% Does NOT delete splices, does NOT delete OTA tapes.

    protocol = string(protocol);
    dataset_id = string(dataset_id);
    shards = double(shards(:)).';

    assert(any(protocol == ["wifi","bluetooth","zigbee"]), "bad protocol");

    addpath(fullfile(pa_root(),'core'));
    addpath(fullfile(pa_root(),'txrx'));

    % normalize dataset_full
    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
        suffix = erase(dataset_id, prefix);
    else
        dataset_full = prefix + dataset_id;
        suffix = dataset_id;
    end

    % map dataset suffix -> bank config
    if suffix == "high_run01"
        bank_name = "ota_core_high_run01";
        run_suffix = "high_run01";
        pas = ["PA2","PA3","PA4","PA8"];
        expected_rows = 500;
    elseif suffix == "pa1_run01"
        bank_name = "ota_pa1_run01";
        run_suffix = "pa1_run01";
        pas = ["PA1"];
        expected_rows = 2000;
    else
        error("Unknown dataset suffix mapping: %s", suffix);
    end

    bank_dir = fullfile(pa_root(),"data",char(protocol),"ota",char(bank_name));
    if ~exist(bank_dir,'dir'), mkdir(bank_dir); end

    for shard_id = shards
        fprintf("\n=== BANK MISSING | %s | %s | shard %03d ===\n", protocol, dataset_full, shard_id);

        % require spliced inputs exist for all PAs
        sp_dir = fullfile(pa_root(),"data",char(protocol),"ota","spliced","simple",char(dataset_full),sprintf("shard_%03d",shard_id));
        for pa = pas
            fsp = fullfile(sp_dir, sprintf("ota_rx_%s.mat", pa));
            if ~isfile(fsp)
                fprintf("SKIP | missing spliced input: %s\n", fsp);
                goto_next_shard();
                continue;
            end
        end

        % determine whether bank is needed (missing or wrong-size X)
        needs = false;
        for pa = pas
            fb = fullfile(bank_dir, sprintf("%s__shard_%03d__%s.mat", bank_name, shard_id, pa));
            if ~isfile(fb)
                fprintf("NEED | missing bank: %s\n", fb);
                needs = true;
                continue;
            end
            try
                W = whos('-file', fb, 'X');
                if isempty(W) || W.size(1) ~= expected_rows
                    fprintf("NEED | corrupt/partial bank: %s (rows=%s)\n", fb, mat2str(W.size));
                    needs = true;
                end
            catch
                fprintf("NEED | unreadable bank (whos failed): %s\n", fb);
                needs = true;
            end
        end

        if ~needs
            fprintf("OK | all bank files present with expected rows=%d\n", expected_rows);
            goto_next_shard();
            continue;
        end

        % rebuild bank for this shard (no deletion of splices inside bank)
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
        else % zigbee
            build_ota_bank(bank_name, [], ...
                'run_suffix', run_suffix, ...
                'protocols', "zigbee", ...
                'zb_shards', shard_id, ...
                'pas', pas, ...
                'mode', "all", ...
                'chunk_n', 8, ...
                'delete_spliced_after_write', false, ...
                'verbose', true);
        end

        fprintf("DONE | banked shard %03d\n", shard_id);

        goto_next_shard();
    end

    function goto_next_shard()
        % local no-op label
    end
end