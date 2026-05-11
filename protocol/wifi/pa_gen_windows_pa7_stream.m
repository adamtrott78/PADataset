function [Xsig, sched] = pa_gen_windows_pa7_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan)
%PA_GEN_WINDOWS_PA7_STREAM Signal-only PA7 windows (fingerprint acquisition / transient elicitation).
% Pattern: repeated short probe bursts with deterministic transient shaping.
% Key properties:
%  - many transients per 20ms window (probe train)
%  - probe content + transient parameters vary per probe => not repeat-similar

    Fs = int64(plan.Fs); W = int64(plan.W); L = int64(plan.L);
    starts = int64(plan.starts(:)); M = int64(numel(starts));
    ends   = starts + W - 1;

    % sort windows for overlap copy, return in plan order
    [startsS, ord] = sort(starts);
    endsS = ends(ord);
    invord = zeros(size(ord)); invord(ord) = 1:numel(ord);

    XsigS = complex(zeros(double(W), double(M), "single"), zeros(double(W), double(M), "single"));

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % --- PA7 params ---
    len_rng = double(pa_get_nested(cfg,"pas.PA7.params.probe_len_s"));
    gap_rng = double(pa_get_nested(cfg,"pas.PA7.params.gap_s"));
    aj_rng  = double(pa_get_nested(cfg,"pas.PA7.params.amp_jitter_db"));

    tr = pa_get_nested(cfg,"pas.PA7.params.transient");
    rise_rng = double(tr.rise_s);
    fall_rng = double(tr.fall_s);
    ov_rng   = double(tr.overshoot_db);
    ra_rng   = double(tr.ring_amp);
    rf_rng   = double(tr.ring_freq_hz);
    rt_rng   = double(tr.ring_tau_s);

    % schedule RNG
    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA7_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    min_gap_samps = int64(round(0.0002 * double(Fs))); % guard
    L_need = min(L, max(endsS));

    t = int64(1);
    pkt_idx = int64(1);
    wi = 1;

    % logs
    probe_starts = zeros(0,1);
    probe_lens   = zeros(0,1);
    gap_samps_v  = zeros(0,1);
    rise_samp_v  = zeros(0,1);
    fall_samp_v  = zeros(0,1);
    ov_db_v      = zeros(0,1);
    ring_amp_v   = zeros(0,1);
    ring_f_v     = zeros(0,1);
    ring_tau_v   = zeros(0,1);
    gain_db_v    = zeros(0,1);

    while t <= L_need && wi <= M
        % --- choose probe length ---
        probe_len_s = len_rng(1) + (len_rng(2)-len_rng(1)) * rand(rs);
        Lp = int64(max(1, round(probe_len_s * double(Fs))));
        probe_end = t + Lp - 1;
        if probe_end > L_need, break; end

        % --- generate probe waveform from Wi-Fi packets (truncate) ---
        xp = complex(zeros(0,1,"single"), zeros(0,1,"single"));
        while int64(numel(xp)) < Lp
            [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "payload");
            [~, seed_scr]     = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "scrambler");
            rs_scr = RandStream("mt19937ar","Seed",double(seed_scr));
            scr = randi(rs_scr, [1 127], 1, 1);

            x_pkt = pa_gen_packet(uint32(seed_payload), scr, wlanCfg);
            xp = [xp; x_pkt]; %#ok<AGROW>
            pkt_idx = pkt_idx + 1;
        end
        xp = xp(1:double(Lp));

        % --- transient shaping parameters (vary per probe; never identical) ---
        rise_s = rise_rng(1) + (rise_rng(2)-rise_rng(1)) * rand(rs);
        fall_s = fall_rng(1) + (fall_rng(2)-fall_rng(1)) * rand(rs);
        Lr = int64(max(1, round(rise_s * double(Fs))));
        Lf = int64(max(1, round(fall_s * double(Fs))));
        if Lr + Lf > Lp
            % deterministic clamp (no resampling): scale down to fit
            scale = double(Lp) / double(Lr + Lf);
            Lr = int64(max(1, floor(double(Lr)*scale)));
            Lf = int64(max(1, floor(double(Lf)*scale)));
        end

        ov_db = ov_rng(1) + (ov_rng(2)-ov_rng(1)) * rand(rs);
        ov_gain = 10^(ov_db/20);

        ring_amp = ra_rng(1) + (ra_rng(2)-ra_rng(1)) * rand(rs);
        ring_f   = rf_rng(1) + (rf_rng(2)-rf_rng(1)) * rand(rs);
        ring_tau = rt_rng(1) + (rt_rng(2)-rt_rng(1)) * rand(rs);

        g_db = aj_rng(1) + (aj_rng(2)-aj_rng(1)) * rand(rs);
        g_lin = 10^(g_db/20);

        % --- build envelope: rise -> steady -> fall with overshoot + optional ringing ---
        env = ones(double(Lp),1,'single');

        % rise ramp
        if Lr > 1
            env(1:double(Lr)) = single(linspace(0, 1, double(Lr))).';
        else
            env(1) = 1;
        end

        % fall ramp
        if Lf > 1
            a0 = double(Lp - Lf + 1);
            env(a0:double(Lp)) = single(linspace(1, 0, double(Lf))).';
        else
            env(end) = 0;
        end

        % overshoot: apply to first ~10% of rise region (or at least 32 samples)
        osh = min(double(Lp), max(32, floor(0.10*double(Lp))));
        env(1:osh) = min(single(ov_gain), single(1.0) + single(ov_gain-1.0)) .* env(1:osh);

        % ringing: (1 + a*exp(-t/tau)*cos(2pi f t))
        if ring_amp > 0
            n = (0:double(Lp)-1).';
            tt = single(n / double(Fs));
            ring = 1 + single(ring_amp) * exp(-tt/single(ring_tau)) .* cos(single(2*pi*ring_f)*tt);
            env = env .* ring;
        end

        % apply gain + envelope
        xp = xp * single(g_lin);
        xp = xp .* env;

        % advance past windows that end before this probe
        while wi <= M && endsS(wi) < t
            wi = wi + 1;
        end

        % copy overlap into windows
        wj = wi;
        while wj <= M && startsS(wj) <= probe_end
            ovL = max(t, startsS(wj));
            ovR = min(probe_end, endsS(wj));
            if ovL <= ovR
                b0 = ovL - t + 1;
                b1 = ovR - t + 1;
                w0 = ovL - startsS(wj) + 1;
                w1 = ovR - startsS(wj) + 1;
                XsigS(double(w0):double(w1), double(wj)) = XsigS(double(w0):double(w1), double(wj)) + xp(double(b0):double(b1));
            end
            wj = wj + 1;
        end

        % log
        probe_starts(end+1,1) = double(t); %#ok<AGROW>
        probe_lens(end+1,1)   = double(Lp); %#ok<AGROW>
        rise_samp_v(end+1,1)  = double(Lr); %#ok<AGROW>
        fall_samp_v(end+1,1)  = double(Lf); %#ok<AGROW>
        ov_db_v(end+1,1)      = double(ov_db); %#ok<AGROW>
        ring_amp_v(end+1,1)   = double(ring_amp); %#ok<AGROW>
        ring_f_v(end+1,1)     = double(ring_f); %#ok<AGROW>
        ring_tau_v(end+1,1)   = double(ring_tau); %#ok<AGROW>
        gain_db_v(end+1,1)    = double(g_db); %#ok<AGROW>

        % gap to next probe
        gap_s = gap_rng(1) + (gap_rng(2)-gap_rng(1)) * rand(rs);
        gap = int64(max(1, round(gap_s * double(Fs))));
        if gap < min_gap_samps, gap = min_gap_samps; end
        gap_samps_v(end+1,1) = double(gap); %#ok<AGROW>

        t = probe_end + gap;
    end

    Xsig = XsigS(:, invord);

    sched = struct();
    sched.L_need = double(L_need);
    sched.probe_starts_samp = probe_starts(:);
    sched.probe_len_samp    = probe_lens(:);
    sched.gap_samp          = gap_samps_v(:);
    sched.rise_samp         = rise_samp_v(:);
    sched.fall_samp         = fall_samp_v(:);
    sched.overshoot_db      = ov_db_v(:);
    sched.ring_amp          = ring_amp_v(:);
    sched.ring_freq_hz      = ring_f_v(:);
    sched.ring_tau_s        = ring_tau_v(:);
    sched.gain_db           = gain_db_v(:);
end