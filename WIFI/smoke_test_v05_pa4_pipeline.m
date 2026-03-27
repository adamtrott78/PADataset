function smoke_test_v05_pa4_pipeline()
    cfg = pa_load_cfg("starter.json");
    pa_validate_cfg(cfg);
    wlanCfg = pa_make_wlan_cfg(cfg);

    session_id=1; tape_id=1; segment_id=1;
    M = 16;

    plan = pa_plan_segment_windows(cfg, session_id, tape_id, segment_id, M);
    [Xsig, sched] = pa_gen_windows_pa4_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan);

    fprintf("Built %d signal-only windows. Packets used: %d\n", M, sched.packet_count);

    n_valid = 0;
    for i = 1:M
        window_id = i;
        [~, vr] = pa_process_window_pa4_v01(cfg, Xsig(:,i), session_id, tape_id, segment_id, window_id);
        n_valid = n_valid + vr.valid;

        fj = vr.det.freq.jump.count;
        rv = vr.det.freq.revisit.present;
        span = vr.det.burst.span.frac;
        sh = vr.det.stationarity.shape;
        en = vr.det.stationarity.energy;
        pk = vr.qc.window_peak;

        fprintf("win %02d: valid=%d reason=%s span=%.3f fj=%d revisit=%d stat(shape=%.3f energy=%.3f) peak=%.3f\n", ...
            i, vr.valid, vr.reject_reason, span, fj, rv, sh, en, pk);
    end
    fprintf("Valid: %d/%d\n", n_valid, M);
end