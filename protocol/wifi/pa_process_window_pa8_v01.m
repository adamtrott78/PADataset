function [x, vr] = pa_process_window_pa8_v01(cfg, x_sig, session_id, tape_id, segment_id, window_id)
%PA_PROCESS_WINDOW_PA8_V01 Strict v0.1 PA8 pipeline (NO schedule).
% Detect repeats from signal-only via occupancy components + STFT-based similarity.

    Fs = round(double(pa_get_nested(cfg,"rates.fs_hz")));
    schema = pa_get_nested(cfg,"schema_version");
    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");

    % --- CFO on signal-only ---
    [~, seed_cfo] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "cfo");
    rs_cfo = RandStream("mt19937ar","Seed",double(seed_cfo));
    cfo_rng = double(pa_get_nested(cfg,"signal_pipeline.impairments.cfo_hz.range_hz"));
    f_cfo = cfo_rng(1) + (cfo_rng(2)-cfo_rng(1)) * rand(rs_cfo);
    x1 = pa_apply_cfo(x_sig, Fs, f_cfo);

    % --- normalize signal RMS to 1 ---
    r = pa_rms(x1);
    if r == 0 || ~isfinite(r), error("Signal RMS invalid"); end
    x1 = x1 / single(r);

    % --- padding types ---
    types = pa_get_nested(cfg,"windowing.padding_policy.types");
    q_snr = []; bg_snr = [];
    for i = 1:numel(types)
        nm = string(types(i).name);
        if nm == "quiet", q_snr = double(types(i).snr_db);
        elseif nm == "benign_background", bg_snr = double(types(i).snr_db);
        end
    end
    if isempty(q_snr) || isempty(bg_snr), error("padding_policy.types missing quiet/benign_background"); end

    % --- quiet noise across full window ---
    [~, seed_q] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "snr_quiet");
    rs_q = RandStream("mt19937ar","Seed",double(seed_q));
    snr_quiet = q_snr(1) + (q_snr(2)-q_snr(1)) * rand(rs_q);

    [~, seed_qn] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "noise_quiet");
    rs_qn = RandStream("mt19937ar","Seed",double(seed_qn));
    x2 = pa_add_awgn_snr(x1, snr_quiet, rs_qn);

    % --- occupancy->components (shared detector); evidence span = TRAIN SPAN ---
    bp = pa_get_nested(cfg,"validation.detectors.burst.params");
    smooth_s = double(bp.power_smoothing_s);
    close_s  = double(pa_get_nested(cfg,"validation.detectors.burst.mask_close_s"));
    occ_k    = double(pa_get_nested(cfg,"validation.detectors.burst.params.thresholds.occ_sigma_k"));
    
    occ = pa_detect_occupancy_from_quiet(x2, Fs, snr_quiet, smooth_s, occ_k, close_s, 2e-4);
    
    starts = occ.starts;
    ends   = occ.ends;
    repeat_count = numel(starts);
    
    emask     = occ.train_mask;
    span_frac = occ.train_frac;

    % --- benign background only on non-evidence ---
    [~, seed_bg] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "snr_bg");
    rs_bg = RandStream("mt19937ar","Seed",double(seed_bg));
    snr_bg = bg_snr(1) + (bg_snr(2)-bg_snr(1)) * rand(rs_bg);

    [~, seed_bgn] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "noise_bg");
    rs_bgn = RandStream("mt19937ar","Seed",double(seed_bgn));

    x3 = x2;
    idx = ~emask;
    if any(idx)
        sigma = 10^(-double(snr_bg)/20);
        w = (sigma/sqrt(2)) * (randn(rs_bgn, sum(idx), 1, "single") + 1j*randn(rs_bgn, sum(idx), 1, "single"));
        x3(idx) = x3(idx) + w;
    end

    % --- repeat similarity (shared detector) ---
    intervals = [starts(:) ends(:)];
    sim = pa_detect_repeat_similarity_iqxcorr(x3, Fs, intervals, 4, 2e-4, 8e-3);
    
    used_repeats = sim.used_repeats;
    sim_score    = sim.score;

    % --- QC ---
    window_peak = max(abs(x3));
    window_rms  = single(pa_rms(x3));
    window_papr = single(20*log10(double(window_peak) / max(1e-12, double(window_rms))));
    rdiff = abs(diff(x3)) / max(1e-12, window_rms);
    rth = double(pa_get_nested(cfg,"validation.drop_reject.discontinuity_rule.r_threshold"));
    disc = any(~isfinite(x3)) || any(rdiff > rth);

    x = x3;

    vr = struct();
    vr.valid = true;
    vr.reject_reason = "none";

    vr.proc = struct("f_cfo_hz", f_cfo, "snr_quiet_db", snr_quiet, "snr_bg_db", snr_bg);
    vr.qc   = struct("window_rms", window_rms, "window_peak", single(window_peak), "window_papr", window_papr, "discontinuity", disc);

    vr.det = struct();
    vr.det.repeat = struct();
    vr.det.repeat.span = struct("frac", span_frac);
    vr.det.repeat.count = struct("detected", repeat_count, "used", used_repeats);
    vr.det.repeat.intervals = [starts(:) ends(:)]; % detected from signal
    vr.det.repeat.similarity = struct("score", sim.score, "pairwise", sim.pairwise, "Lc_used", sim.Lc_used, "maxlag_used", sim.maxlag_used);

    % --- PA8 accept rules (from pas.PA8.accept) ---
    if disc
        vr.valid = false; vr.reject_reason = "discontinuity_detected"; return;
    end
    
    span_min = double(pa_get_nested(cfg,"pas.PA8.accept.evidence_span_frac_min"));
    if span_frac < span_min
        vr.valid = false; vr.reject_reason = "evidence_span_fail"; return;
    end
    
    rep_min  = double(pa_get_nested(cfg,"pas.PA8.accept.repeat_min"));
    rej_miss = logical(pa_get_nested(cfg,"pas.PA8.accept.reject_if_repeat_missing"));
    if rej_miss && used_repeats < rep_min
        vr.valid = false; vr.reject_reason = "repeat_missing"; return;
    end
    
    sim_min = double(pa_get_nested(cfg,"pas.PA8.accept.repeat_similarity_min"));
    if used_repeats >= rep_min && sim_score < sim_min
        vr.valid = false; vr.reject_reason = "repeat_similarity_fail"; return;
    end
    
    if window_peak > double(pa_get_nested(cfg,"signal_pipeline.peak_reject.peak_threshold"))
        vr.valid = false; vr.reject_reason = "peak_exceeded"; return;
    end
end