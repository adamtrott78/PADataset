function [x, vr] = pa_process_window_pa3_v01(cfg, x_sig, session_id, tape_id, segment_id, window_id)
%PA_PROCESS_WINDOW_PA3_V01 Strict v0.1 PA3 pipeline + semantic detector outputs (no E# aliases).

    Fs = round(double(pa_get_nested(cfg,"rates.fs_hz")));
    schema = pa_get_nested(cfg,"schema_version");
    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");

    % ---------- impairments: CFO on signal-only ----------
    [~, seed_cfo] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "cfo");
    rs_cfo = RandStream("mt19937ar","Seed",double(seed_cfo));
    cfo_rng = double(pa_get_nested(cfg,"signal_pipeline.impairments.cfo_hz.range_hz"));
    f_cfo = cfo_rng(1) + (cfo_rng(2)-cfo_rng(1)) * rand(rs_cfo);
    x1 = pa_apply_cfo(x_sig, Fs, f_cfo);

    % ---------- normalize signal RMS to 1 ----------
    r = pa_rms(x1);
    if r == 0 || ~isfinite(r), error("Signal RMS invalid"); end
    x1 = x1 / single(r);

    % ---------- read padding types ----------
    types = pa_get_nested(cfg,"windowing.padding_policy.types");
    if ~isstruct(types), error("windowing.padding_policy.types must be struct array"); end
    q_snr = []; bg_snr = [];
    for i = 1:numel(types)
        nm = string(types(i).name);
        if nm == "quiet", q_snr = double(types(i).snr_db);
        elseif nm == "benign_background", bg_snr = double(types(i).snr_db);
        end
    end
    if isempty(q_snr),  error("quiet snr_db not found"); end
    if isempty(bg_snr), error("benign_background snr_db not found"); end

    % ---------- quiet noise across entire window ----------
    [~, seed_q] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "snr_quiet");
    rs_q = RandStream("mt19937ar","Seed",double(seed_q));
    snr_quiet = q_snr(1) + (q_snr(2)-q_snr(1)) * rand(rs_q);

    [~, seed_qn] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "noise_quiet");
    rs_qn = RandStream("mt19937ar","Seed",double(seed_qn));
    x2 = pa_add_awgn_snr(x1, snr_quiet, rs_qn);

    % ---------- burst edges detector ----------
    bp = pa_get_nested(cfg,"validation.detectors.burst.params");
    smooth_s = double(bp.power_smoothing_s);
    refr_s   = double(bp.refractory_s);
    k_hi     = double(bp.thresholds.hi_mad_k);
    k_lo     = double(bp.thresholds.lo_mad_k);

    e23 = pa_detect_E2E3(x2, Fs, smooth_s, refr_s, k_hi, k_lo);

   % --- PA3 occupancy mask (noise-referenced, shared detector) ---
    close_s = double(pa_get_nested(cfg,"validation.detectors.burst.mask_close_s"));
    occ_k   = double(pa_get_nested(cfg,"validation.detectors.burst.params.thresholds.occ_sigma_k"));

    occ = pa_detect_occupancy_from_quiet(x2, Fs, snr_quiet, smooth_s, occ_k, close_s, 0);

    onmask    = occ.mask;
    span_frac = occ.duty_frac;

    % ---------- benign background only on non-evidence ----------
    [~, seed_bg] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "snr_bg");
    rs_bg = RandStream("mt19937ar","Seed",double(seed_bg));
    snr_bg = bg_snr(1) + (bg_snr(2)-bg_snr(1)) * rand(rs_bg);

    [~, seed_bgn] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "noise_bg");
    rs_bgn = RandStream("mt19937ar","Seed",double(seed_bgn));

    x3 = x2;
    idx = ~onmask;
    if any(idx)
        sigma = 10^(-double(snr_bg)/20);
        w = (sigma/sqrt(2)) * (randn(rs_bgn, sum(idx), 1, "single") + 1j*randn(rs_bgn, sum(idx), 1, "single"));
        x3(idx) = x3(idx) + w;
    end

    % ---------- STFT bins (shared) ----------
    sp = pa_get_nested(cfg,"validation.detectors.stationarity.params");
    nfft = double(sp.nfft); hop = double(sp.hop); nb = double(sp.nbins);

    B = pa_stft_bins32(x3, nfft, hop, nb);   % [nb x T] linear power
    epsv = 1e-12;

    % stationarity.shape
    N = sqrt(sum(B.^2, 1)) + epsv;
    Bh = B ./ N;
    c = sum(Bh(:,1:end-1) .* Bh(:,2:end), 1);
    st_shape = mean(c);

    % stationarity.energy + CV
    E = sum(B, 1) + epsv;
    energy_cv = std(E) / (mean(E) + epsv);
    st_energy = 1 / (1 + energy_cv);

    pframes = double(pa_get_nested(cfg,"validation.detectors.freq.params.persistence_frames"));
    sframes = double(pa_get_nested(cfg,"validation.detectors.freq.params.smooth_frames"));
    dbins   = double(pa_get_nested(cfg,"validation.detectors.freq.params.min_delta_bins"));
    fj = pa_detect_freq_jump(B, pframes, sframes, dbins);

    % ---------- QC metrics ----------
    window_peak = max(abs(x3));
    window_rms  = single(pa_rms(x3));
    window_papr = single(20*log10(double(window_peak) / max(1e-12, double(window_rms))));

    rdiff = abs(diff(x3)) / max(1e-12, window_rms);
    rth = double(pa_get_nested(cfg,"validation.drop_reject.discontinuity_rule.r_threshold"));
    disc = any(~isfinite(x3)) || any(rdiff > rth);

    % ---------- outputs ----------
    x = x3;

    vr = struct();
    vr.valid = true;
    vr.reject_reason = "none";

    vr.proc = struct("f_cfo_hz", f_cfo, "snr_quiet_db", snr_quiet, "snr_bg_db", snr_bg);

    vr.qc = struct();
    vr.qc.window_rms  = window_rms;
    vr.qc.window_peak = single(window_peak);
    vr.qc.window_papr = window_papr;
    vr.qc.discontinuity = disc;

    vr.det = struct();

    vr.det.burst = struct();
    vr.det.burst.edges = struct();
    vr.det.burst.edges.start = struct("count", e23.E2_count, "idx", e23.rise_idx);
    vr.det.burst.edges.end   = struct("count", e23.E3_count, "idx", e23.fall_idx);
    vr.det.burst.span = struct("frac", span_frac);

    vr.det.stationarity = struct("shape", st_shape, "energy", st_energy, "energy_cv", energy_cv);

    vr.det.freq = struct();
    vr.det.freq.jump = struct("count", fj.count, "bin_trace", fj.bin_trace, "raw_trace", fj.raw_trace, "change_idx", fj.change_idx, "centroid", fj.centroid);

    % ---------- PA3 accept rules ----------
    if disc
        vr.valid = false; vr.reject_reason = "discontinuity_detected"; return;
    end

    if span_frac < double(pa_get_nested(cfg,"pas.PA3.accept.evidence_span_frac_min"))
        vr.valid = false; vr.reject_reason = "evidence_span_fail"; return;
    end

    edge_max = double(pa_get_nested(cfg,"pas.PA3.accept.edge_max"));
    if e23.E2_count > edge_max || e23.E3_count > edge_max
        vr.valid = false; vr.reject_reason = "edge_density_fail"; return;
    end

    % Stationarity must be high in BOTH senses
    st_min = double(pa_get_nested(cfg,"pas.PA3.accept.stationarity_min"));
    shape_hi = double(pa_get_nested(cfg,"validation.thresholds.stationarity.shape_high"));
    energy_hi = double(pa_get_nested(cfg,"validation.thresholds.stationarity.energy_high"));
    if st_shape < max(st_min, shape_hi) || st_energy < max(st_min, energy_hi)
        vr.valid = false; vr.reject_reason = "stationarity_fail"; return;
    end

    % Reject any frequency jumps for PA3
    if fj.count > 0
        vr.valid = false; vr.reject_reason = "freq_jump_detected"; return;
    end

    if window_peak > double(pa_get_nested(cfg,"signal_pipeline.peak_reject.peak_threshold"))
        vr.valid = false; vr.reject_reason = "peak_exceeded"; return;
    end
end