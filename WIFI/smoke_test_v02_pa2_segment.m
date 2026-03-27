function smoke_test_v02_pa2_segment()
    cfg = pa_load_cfg("starter.json");
    pa_validate_cfg(cfg);
    wlanCfg = pa_make_wlan_cfg(cfg);

    session_id = 1; tape_id = 1; segment_id = 1;
    windows_needed_for_segment = 16;   % keep small for smoke test

    plan = pa_plan_segment_windows(cfg, session_id, tape_id, segment_id, windows_needed_for_segment);
    fprintf("Plan: seg_len=%.3fs, L=%d, W=%d, J=%d, S=%d, N_base=%d\n", ...
        plan.segment_len_s, plan.L, plan.W, plan.J, plan.S, plan.N_base);

    [x_seg1, seginfo1] = pa_gen_segment_pa2(cfg, wlanCfg, session_id, tape_id, segment_id, plan.L);
    [x_seg2, ~]        = pa_gen_segment_pa2(cfg, wlanCfg, session_id, tape_id, segment_id, plan.L);

    st = plan.starts(1);
    xw1 = x_seg1(double(st):double(st+plan.W-1));
    xw2 = x_seg2(double(st):double(st+plan.W-1));

    fprintf("Extracted window len: %d (expected %d)\n", numel(xw1), plan.W);
    fprintf("Deterministic segment (bitwise) on extracted window: %d\n", isequal(xw1, xw2));
    fprintf("Window RMS (signal-only, before noise): %.6f\n", sqrt(mean(abs(double(xw1)).^2)));

    fprintf("Segment bursts: %d\n", numel(seginfo1.burst_starts_samp));
end