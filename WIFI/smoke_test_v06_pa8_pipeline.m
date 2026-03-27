function smoke_test_v06_pa8_pipeline()
    cfg = pa_load_cfg("starter.json");
    pa_validate_cfg(cfg);
    wlanCfg = pa_make_wlan_cfg(cfg);

    session_id=1; tape_id=1; segment_id=1;
    M = 16;

    plan = pa_plan_segment_windows(cfg, session_id, tape_id, segment_id, M);
    window_ids = (1:M).';
    [Xsig, sch] = pa_gen_windows_pa8_stream(cfg, wlanCfg, session_id, tape_id, plan, window_ids);

    fprintf("Built %d signal-only windows (PA8).\n", M);

    n_valid = 0;
    for i = 1:M
        window_id = i;
        [~, vr] = pa_process_window_pa8_v01(cfg, Xsig(:,i), sch(i), session_id, tape_id, segment_id, window_id);
        n_valid = n_valid + vr.valid;

        span = vr.det.repeat.span.frac;
        sim  = vr.det.repeat.similarity.score;
        mode = string(vr.det.repeat.schedule.mode);
        rc   = vr.det.repeat.schedule.repeat_count;
        pk   = vr.qc.window_peak;

        fprintf("win %02d: valid=%d reason=%s span=%.3f sim=%.3f mode=%s repeats=%d peak=%.3f\n", ...
            i, vr.valid, vr.reject_reason, span, sim, mode, rc, pk);
    end
    fprintf("Valid: %d/%d\n", n_valid, M);
end