function [Xsig, sched] = bt_gen_windows_pa8_stream(cfg, session_id, tape_id, plan, window_ids)
%BT_GEN_WINDOWS_PA8_STREAM Signal-only PA8 windows for Bluetooth.

    Fs = round(double(pa_get_nested(cfg,"rates.fs_hz")));
    W  = round(double(pa_get_nested(cfg,"windowing.window_length_s")) * Fs);
    M  = numel(plan.starts);

    if nargin < 5
        error("bt_gen_windows_pa8_stream requires window_ids (length M).");
    end
    window_ids = int64(window_ids(:));
    if numel(window_ids) ~= M
        error("window_ids length (%d) must equal numel(plan.starts) (%d).", numel(window_ids), M);
    end

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % PA8 is window-intrinsic; mirror Wi-Fi behavior
    segment_id_seed = 0;

    span_min    = double(pa_get_nested(cfg,"pas.PA8.accept.evidence_span_frac_min"));
    span_target = ceil(span_min * W);

    peak_thr = double(pa_get_nested(cfg,"signal_pipeline.peak_reject.peak_threshold"));

    % PA8 params
    rc_rng   = double(pa_get_nested(cfg,"pas.PA8.params.repeat_count"));
    sp_rng_s = double(pa_get_nested(cfg,"pas.PA8.params.repeat_spacing_s"));   % START-TO-START spacing
    tl_rng_s = double(pa_get_nested(cfg,"pas.PA8.params.template_len_s"));
    modes    = string(pa_get_nested(cfg,"pas.PA8.params.repeat_mode"));
    near     = pa_get_nested(cfg,"pas.PA8.params.near_exact");

    spacing_min = max(1, round(sp_rng_s(1) * Fs));
    spacing_max = max(1, round(sp_rng_s(2) * Fs));
    tlen_min    = max(1, round(tl_rng_s(1) * Fs));
    tlen_max    = max(1, round(tl_rng_s(2) * Fs));

    Xsig  = complex(zeros(W, M, "single"), zeros(W, M, "single"));
    sched = repmat(struct(), 1, M);

    btCfg = bt_make_ble_cfg(cfg);

    for i = 1:M
        window_id = double(window_ids(i));

        [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id_seed, window_id, "PA8_window_ops");
        rs = RandStream("mt19937ar","Seed",double(seed_op));

        % choose mode
        mode = modes(randi(rs, [1 numel(modes)], 1, 1));

        % choose repeat_count, but enforce >=3
        repeat_count = randi(rs, [round(rc_rng(1)) round(rc_rng(2))], 1, 1);
        if repeat_count < 3, repeat_count = 3; end

        % choose template length
        tlen = randi(rs, [tlen_min tlen_max], 1, 1);

        % --- feasibility enforcement for span_target under spacing bounds ---
        tlen_req = span_target - (repeat_count-1)*spacing_max;
        if tlen_req > tlen_max
            repeat_count = 4;
            tlen_req = span_target - (repeat_count-1)*spacing_max;
        end
        tlen = max(tlen, max(tlen_min, tlen_req));

        % choose spacing to satisfy train-span target + enforce non-overlap
        gap_min = max(1, round(0.0002 * Fs));   % 0.2 ms guard
        spacing_req = ceil((span_target - tlen) / max(1, repeat_count-1));
        spacing_req = max(spacing_req, tlen + gap_min);
        spacing = min(max(spacing_req, spacing_min), spacing_max);

        train_len = (repeat_count-1)*spacing + tlen;
        if train_len < span_target
            repeat_count = 4;
            tlen_req = span_target - (repeat_count-1)*spacing_max;
            tlen = max(tlen, max(tlen_min, tlen_req));
            spacing_req = ceil((span_target - tlen) / max(1, repeat_count-1));
            spacing_req = max(spacing_req, tlen + gap_min);
            spacing = min(max(spacing_req, spacing_min), spacing_max);
            train_len = (repeat_count-1)*spacing + tlen;
        end

        % choose start so the last repeat fits
        t0_max = W - train_len + 1;
        start_min = round(0.001 * Fs);
        start_max = round(0.003 * Fs);
        lo = max(1, min(start_min, t0_max));
        hi = max(lo, min(start_max, t0_max));
        t0 = randi(rs, [lo hi], 1, 1);

        intervals = zeros(repeat_count, 2);
        for r = 1:repeat_count
            a = t0 + (r-1)*spacing;
            b = a + tlen - 1;
            intervals(r,:) = [a b];
        end

        % build template snippet
        tpl = make_template(cfg, btCfg, master_seed, schema, session_id, tape_id, ...
                            segment_id_seed, window_id, tlen, rs);

        % place repeats into W-length window
        [xw, near_params] = place_repeats(W, tpl, mode, near, master_seed, schema, ...
                                          session_id, tape_id, segment_id_seed, ...
                                          window_id, Fs, intervals);

        % peak-after-normalization safety fallback
        rms0 = pa_rms(xw);
        pk0  = max(abs(xw));
        if rms0 > 0 && (double(pk0) / double(rms0)) > peak_thr
            repeat_count2 = 4;
            tlen2 = tlen_max;

            spacing_req2 = ceil((span_target - tlen2) / max(1, repeat_count2-1));
            spacing_req2 = max(spacing_req2, tlen2 + gap_min);
            spacing2 = min(max(spacing_req2, spacing_min), spacing_max);

            train_len2 = (repeat_count2-1)*spacing2 + tlen2;
            t0_max2 = W - train_len2 + 1;

            lo2 = max(1, min(start_min, t0_max2));
            hi2 = max(lo2, min(start_max, t0_max2));
            t02 = randi(rs, [lo2 hi2], 1, 1);

            intervals2 = zeros(repeat_count2,2);
            for r = 1:repeat_count2
                a = t02 + (r-1)*spacing2;
                b = a + tlen2 - 1;
                intervals2(r,:) = [a b];
            end

            tpl2 = make_template(cfg, btCfg, master_seed, schema, session_id, tape_id, ...
                                 segment_id_seed, window_id+7777, tlen2, rs);
            [xw, near_params] = place_repeats(W, tpl2, mode, near, master_seed, schema, ...
                                              session_id, tape_id, segment_id_seed, ...
                                              window_id, Fs, intervals2);

            repeat_count = repeat_count2;
            tlen = tlen2;
            spacing = spacing2;
            t0 = t02;
            intervals = intervals2;
        end

        Xsig(:,i) = xw;

        sched(i).mode = char(mode);
        sched(i).repeat_count = repeat_count;
        sched(i).template_len_samp = tlen;
        sched(i).repeat_spacing_samp = spacing;   % START-TO-START
        sched(i).t0_samp = t0;
        sched(i).intervals = intervals;
        sched(i).train_span_samp = intervals(end,2) - intervals(1,1) + 1;
        sched(i).train_span_frac = sched(i).train_span_samp / W;
        sched(i).duty_frac = (repeat_count * tlen) / W;
        sched(i).near_exact_params = near_params;
        sched(i).window_id = window_id;
    end
end

function tpl = make_template(cfg, btCfg, master_seed, schema, session_id, tape_id, segment_id, window_id, tlen, rs)
%MAKE_TEMPLATE Build a deterministic Bluetooth replay template snippet.

    margin = 2000;
    need = tlen + margin;

    buf = complex(zeros(0,1,"single"), zeros(0,1,"single"));
    pkt_idx = int64(1);

    while numel(buf) < need
        [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, ...
                                        segment_id, window_id*100000 + double(pkt_idx), "payload");
        [x_pkt, ~] = bt_gen_packet(uint32(seed_payload), btCfg);
        buf = [buf; x_pkt]; %#ok<AGROW>
        pkt_idx = pkt_idx + 1;
    end

    % deterministic crop start
    smax = numel(buf) - tlen + 1;
    s0 = randi(rs, [1 max(1,smax)], 1, 1);
    tpl = buf(s0:s0+tlen-1);

    % optional recorded noise baked into replay template
    rn = pa_get_nested(cfg,"pas.PA8.params.recorded_noise");
    if isstruct(rn) && isfield(rn,"enable") && logical(rn.enable)
        snr_rng = double(rn.snr_db);
        if numel(snr_rng) ~= 2
            error("pas.PA8.params.recorded_noise.snr_db must be [lo,hi]");
        end

        [~, seed_rn] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "PA8_recorded_noise");
        rs_rn = RandStream("mt19937ar","Seed",double(seed_rn));

        snr_db = snr_rng(1) + (snr_rng(2)-snr_rng(1)) * rand(rs_rn);

        rt = pa_rms(tpl);
        if rt > 0
            sigma = double(rt) * 10^(-snr_db/20);
            w = (sigma/sqrt(2)) * (randn(rs_rn, size(tpl), "single") + 1j*randn(rs_rn, size(tpl), "single"));
            tpl = tpl + w;
        end
    end

    % normalize template RMS to 1
    r = pa_rms(tpl);
    if r > 0, tpl = tpl / single(r); end
end

function [xw, sim_params] = place_repeats(W, tpl, mode, near, master_seed, schema, session_id, tape_id, segment_id, window_id, Fs, intervals)
    xw = complex(zeros(W,1,"single"), zeros(W,1,"single"));
    sim_params = struct([]);

    repeat_count = size(intervals,1);
    for r = 1:repeat_count
        a = intervals(r,1);
        b = intervals(r,2);
        if a < 1 || b > W || b < a
            continue;
        end

        seg = tpl;

        if string(mode) == "near_exact"
            [~, seed_near] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, window_id, "PA8_near_" + string(r));
            rsn = RandStream("mt19937ar","Seed",double(seed_near));

            snr_rng = double(near.awgn_snr_db);
            snr_db = snr_rng(1) + (snr_rng(2)-snr_rng(1)) * rand(rsn);

            g_rng = double(near.amp_scale_db);
            g_db = g_rng(1) + (g_rng(2)-g_rng(1)) * rand(rsn);
            gain = 10^(g_db/20);

            ph_rng = double(near.phase_rot_deg);
            ph_deg = ph_rng(1) + (ph_rng(2)-ph_rng(1)) * rand(rsn);
            ph = deg2rad(ph_deg);

            f_rng = double(near.cfo_hz);
            df = f_rng(1) + (f_rng(2)-f_rng(1)) * rand(rsn);

            seg = seg * single(gain);
            seg = seg .* complex(single(cos(ph)), single(sin(ph)));

            n = single(0:numel(seg)-1).';
            dphi = single(2*pi) * single(df) / single(Fs);
            seg = seg .* complex(cos(dphi*n), sin(dphi*n));

            rsnr = pa_rms(seg);
            sigma = rsnr * 10^(-snr_db/20);
            w = (sigma/sqrt(2)) * (randn(rsn, size(seg), "single") + 1j*randn(rsn, size(seg), "single"));
            seg = seg + w;

            sim_params(r).snr_db = snr_db; %#ok<AGROW>
            sim_params(r).gain_db = g_db;
            sim_params(r).phase_deg = ph_deg;
            sim_params(r).cfo_hz = df;
        end

        xw(a:b) = xw(a:b) + seg;
    end
end