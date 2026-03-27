function gen_pilot_v01()
%GEN_PILOT_V01 Generate and save signal-only pilot windows for PA2/PA3/PA4/PA8.

    cfg = pa_load_cfg("starter.json");
    pa_validate_cfg(cfg);
    wlanCfg = pa_make_wlan_cfg(cfg);

    out_root  = fullfile("pilot_out_v01");
    data_root = fullfile(out_root, "data");
    if ~exist(data_root,"dir"), mkdir(data_root); end

    N_per_pa   = 200;
    batch      = 16;
    session_id = 1;
    tape_id    = 1;

    Fs = round(double(pa_get_nested(cfg,"rates.fs_hz")));
    W  = round(double(pa_get_nested(cfg,"windowing.window_length_s")) * Fs);

    PAs = ["PA2","PA3","PA4","PA8"]; % ["PA4"];

    for pa = PAs
        fprintf("\n=== GEN %s | target %d windows ===\n", pa, N_per_pa);

        Xsig_all = complex(zeros(W, N_per_pa, "single"), zeros(W, N_per_pa, "single"));
        meta = repmat(struct(), 1, N_per_pa);

        % PA8 schedule (only used for PA8)
        sch = [];  % allocated on first PA8 batch using sch_batch(1) template

        n_done = 0;
        seg_id = 0;

        while n_done < N_per_pa
            n_batch = min(batch, N_per_pa - n_done);

            if pa == "PA8"
                % PA8 is window-intrinsic; no segment planning needed.
                plan = make_dummy_plan(Fs, W, n_batch);
                window_ids = (n_done + (1:n_batch)).';  % global pilot window IDs
                [Xsig, sch_batch] = pa_gen_windows_pa8_stream(cfg, wlanCfg, session_id, tape_id, plan, window_ids);

                if isempty(sch)
                    sch = repmat(sch_batch(1), 1, N_per_pa); % correct field template
                end

                for i = 1:n_batch
                    idx = n_done + i;
                    Xsig_all(:,idx) = Xsig(:,i);
                    sch(idx) = sch_batch(i);

                    meta(idx).schema_version     = pa_get_nested(cfg,"schema_version");
                    meta(idx).session_id         = session_id;
                    meta(idx).tape_id            = tape_id;
                    meta(idx).segment_id         = 0;     % PA8 window-intrinsic
                    meta(idx).window_id          = idx;
                    meta(idx).pa_type            = char(pa);
                    meta(idx).fs_hz              = Fs;
                    meta(idx).window_length_s    = double(pa_get_nested(cfg,"windowing.window_length_s"));
                    meta(idx).window_start_sample = NaN;  % not meaningful for intrinsic PA8
                end

            else
                % Segment-based PAs
                seg_id = seg_id + 1;
                plan = pa_plan_segment_windows(cfg, session_id, tape_id, seg_id, n_batch);

                switch pa
                    case "PA2"
                        [Xsig, ~] = pa_gen_windows_pa2_stream(cfg, wlanCfg, session_id, tape_id, seg_id, plan);
                    case "PA3"
                        [Xsig, ~] = pa_gen_windows_pa3_stream(cfg, wlanCfg, session_id, tape_id, seg_id, plan);
                    case "PA4"
                        [Xsig, ~] = pa_gen_windows_pa4_stream(cfg, wlanCfg, session_id, tape_id, seg_id, plan);
                end

                for i = 1:n_batch
                    idx = n_done + i;
                    Xsig_all(:,idx) = Xsig(:,i);

                    meta(idx).schema_version     = pa_get_nested(cfg,"schema_version");
                    meta(idx).session_id         = session_id;
                    meta(idx).tape_id            = tape_id;
                    meta(idx).segment_id         = seg_id;
                    meta(idx).window_id          = idx;
                    meta(idx).pa_type            = char(pa);
                    meta(idx).fs_hz              = Fs;
                    meta(idx).window_length_s    = double(pa_get_nested(cfg,"windowing.window_length_s"));
                    meta(idx).window_start_sample = double(plan.starts(i));
                end
            end

            n_done = n_done + n_batch;
            fprintf("  %s: %d/%d\r", pa, n_done, N_per_pa);
        end
        fprintf("\n");

        outfile = fullfile(data_root, sprintf("pilot_S%02d_%s.mat", session_id, pa));
        if pa == "PA8"
            save(outfile, "Xsig_all", "meta", "sch", "-v7");
        else
            save(outfile, "Xsig_all", "meta", "-v7");
        end
        fprintf("Saved: %s\n", outfile);
    end
end

function plan = make_dummy_plan(Fs, W, M)
    plan = struct();
    plan.Fs = Fs;
    plan.W  = W;
    plan.L  = W;
    plan.J  = 0;
    plan.S  = W;
    plan.starts = int64(ones(M,1));
end