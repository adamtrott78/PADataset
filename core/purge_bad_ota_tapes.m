function purge_bad_ota_tapes(protocol, dataset_id, shards, max_events, min_fill_frac, dry_run)
%PURGE_BAD_OTA_TAPES Delete OTA tapes that fail the strict capture gate.

    protocol = string(protocol);
    dataset_id = string(dataset_id);
    shards = double(shards(:)).';

    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
    else
        dataset_full = prefix + dataset_id;
    end

    R = pa_protocol_roots(protocol);

    for shard_id = shards
        f = fullfile(R.txrx_tapes_ota, char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_id));
        if ~isfile(f)
            continue;
        end

        [ok, events, fill_frac] = ota_meets_gate_local(f, max_events, min_fill_frac);
        if ok
            fprintf("KEEP | shard %03d | events=%d fill=%.6f | %s\n", shard_id, events, fill_frac, f);
        else
            fprintf("PURGE | shard %03d | events=%s fill=%s | %s\n", ...
                shard_id, num2str(events), num2str(fill_frac), f);
            if ~dry_run
                delete(f);
            end
        end
    end
end

function [ok, events, fill_frac] = ota_meets_gate_local(out_file, max_events, min_fill_frac)
    ok = false; events = NaN; fill_frac = NaN;
    try
        S = load(out_file, "txrx_cfg");
        if ~isfield(S, "txrx_cfg"), return; end
        cfg = S.txrx_cfg;

        events = double(cfg.capture_overruns) + double(cfg.capture_underruns);
        expected_Ncap = double(cfg.frameLen) * double(cfg.n_guard_pre_frames + cfg.n_main_frames + cfg.n_guard_post_frames);
        filled = double(cfg.capture_len_raw);
        fill_frac = filled / max(1, expected_Ncap);

        ok = (events <= max_events) && (fill_frac >= min_fill_frac);
    catch
        ok = false;
    end
end