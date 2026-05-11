function zb_gen_pilot(n_per_pa)
%ZB_GEN_PILOT Generate and save Zigbee pilot windows for PA2/PA3/PA4/PA8.

    if nargin < 1 || isempty(n_per_pa)
        n_per_pa = 200;
    end

    P = pa_paths();
    cfg = pa_load_cfg(fullfile(P.config, "starter.json"));

    % strict cfg validation
    zbCfg = zb_make_zigbee_cfg(cfg); %#ok<NASGU>

    Fs = round(double(pa_get_nested(cfg, "rates.fs_hz")));
    W  = round(double(pa_get_nested(cfg, "windowing.window_length_s")) * Fs);

    session_id = 1;
    tape_id    = 1;
    segment_id = 1;

    out_root = fullfile(pa_root(), "data", "zigbee", "digital", "pilot");
    if ~exist(out_root, "dir"), mkdir(out_root); end

    PAs = ["PA2","PA3","PA4","PA8"];

    for pa = PAs
        fprintf("\n=== GEN %s | target %d windows ===\n", pa, n_per_pa);

        starts = int64(1 + (0:n_per_pa-1)*W).';
        plan = struct();
        plan.Fs = Fs;
        plan.W = W;
        plan.starts = starts;

        switch pa
            case "PA2"
                [Xsig_all, meta, sched] = zb_gen_windows_pa2_stream(cfg, session_id, tape_id, segment_id, plan);

            case "PA3"
                [Xsig_all, meta] = zb_gen_windows_pa3_stream(cfg, session_id, tape_id, segment_id, plan);
                sched = [];

            case "PA4"
                [Xsig_all, meta, sched] = zb_gen_windows_pa4_stream(cfg, session_id, tape_id, segment_id, plan);

            case "PA8"
                window_ids = int64((1:n_per_pa).');
                [Xsig_all, sched] = zb_gen_windows_pa8_stream(cfg, session_id, tape_id, plan, window_ids);
                meta = make_pa8_meta(cfg, session_id, tape_id, plan, window_ids, sched);

            otherwise
                error("Unsupported PA: %s", pa);
        end

        outfile = fullfile(out_root, sprintf("pilot_S%02d_%s.mat", session_id, pa));

        if isempty(sched)
            save(outfile, "Xsig_all", "meta", "-v7");
        else
            save(outfile, "Xsig_all", "meta", "sched", "-v7");
        end

        fprintf("Saved: %s\n", outfile);
    end
end


function meta = make_pa8_meta(cfg, session_id, tape_id, plan, window_ids, sched)
    M = numel(window_ids);
    meta = repmat(struct(), 1, M);

    for i = 1:M
        meta(i).schema_version      = pa_get_nested(cfg, "schema_version");
        meta(i).session_id          = session_id;
        meta(i).tape_id             = tape_id;
        meta(i).segment_id          = 0;
        meta(i).window_id           = double(window_ids(i));
        meta(i).pa_type             = "PA8";
        meta(i).protocol            = "zigbee";
        meta(i).fs_hz               = double(plan.Fs);
        meta(i).window_length_s     = double(pa_get_nested(cfg, "windowing.window_length_s"));
        meta(i).window_start_sample = double(plan.starts(i));

        meta(i).repeat_mode         = sched(i).mode;
        meta(i).repeat_count        = sched(i).repeat_count;
        meta(i).template_len_samp   = sched(i).template_len_samp;
        meta(i).repeat_spacing_samp = sched(i).repeat_spacing_samp;
        meta(i).t0_samp             = sched(i).t0_samp;
        meta(i).intervals           = sched(i).intervals;
        meta(i).train_span_samp     = sched(i).train_span_samp;
        meta(i).train_span_frac     = sched(i).train_span_frac;
        meta(i).duty_frac           = sched(i).duty_frac;
        meta(i).near_exact_params   = sched(i).near_exact_params;
    end
end