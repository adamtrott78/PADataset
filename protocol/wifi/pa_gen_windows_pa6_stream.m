function [Xsig, sched] = pa_gen_windows_pa6_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan)
%PA_GEN_WINDOWS_PA6_STREAM Signal-only PA6 windows (burst timing + intra-burst drift).
% - Burst schedule like PA2
% - Inside each burst: apply CFO ramp (linear freq drift => quadratic phase)
% - Per-burst ramp parameters are deterministic and differ across bursts (not repeat-similar)

    Fs = int64(plan.Fs); W = int64(plan.W); L = int64(plan.L);
    starts = int64(plan.starts(:)); M = int64(numel(starts));
    ends   = starts + W - 1;

    % Sort windows by start for efficient overlap checks, return in plan order
    [startsS, ord] = sort(starts);
    endsS = ends(ord);
    invord = zeros(size(ord)); invord(ord) = 1:numel(ord);

    XsigS = complex(zeros(double(W), double(M), "single"), zeros(double(W), double(M), "single"));

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % PA6 burst timing params (PA2-like)
    on_rng  = double(pa_get_nested(cfg,"pas.PA6.params.burst_on_s"));
    ibi_rng = double(pa_get_nested(cfg,"pas.PA6.params.ibi_mean_s"));
    jit_rng = double(pa_get_nested(cfg,"pas.PA6.params.ibi_jitter_frac"));

    % PA6 drift params
    drift_rng = double(pa_get_nested(cfg,"pas.PA6.params.drift_total_hz")); % total drift over burst (Hz)
    f0_rng    = double(pa_get_nested(cfg,"pas.PA6.params.f0_hz"));         % baseline within-burst offset (Hz)
    aj_rng    = double(pa_get_nested(cfg,"pas.PA6.params.amp_jitter_db")); % per-burst gain jitter (dB)

    % Segment-level RNG drives everything deterministically
    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA6_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    min_gap_samps = int64(round(0.0002 * double(Fs))); % 0.2ms guard
    L_need = min(L, max(endsS));

    t = int64(1);
    pkt_idx = int64(1);
    wi = 1;

    % sched logs
    burst_starts = zeros(0,1);
    burst_lens   = zeros(0,1);
    ibi_samps_v  = zeros(0,1);
    f0_hz_v      = zeros(0,1);
    drift_hz_v   = zeros(0,1);
    slope_hzs_v  = zeros(0,1);
    gain_db_v    = zeros(0,1);

    while t <= L_need && wi <= M
        % burst length
        burst_on_s = on_rng(1) + (on_rng(2)-on_rng(1)) * rand(rs);
        burst_on   = int64(max(1, round(burst_on_s * double(Fs))));
        burst_end  = t + burst_on - 1;
        if burst_end > L_need, break; end

        % --- generate enough Wi-Fi samples to fill burst ---
        xb = complex(zeros(0,1,"single"), zeros(0,1,"single"));
        while int64(numel(xb)) < burst_on
            [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "payload");
            [~, seed_scr]     = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "scrambler");
            rs_scr = RandStream("mt19937ar","Seed",double(seed_scr));
            scr = randi(rs_scr, [1 127], 1, 1);

            x_pkt = pa_gen_packet(uint32(seed_payload), scr, wlanCfg);
            xb = [xb; x_pkt]; %#ok<AGROW>
            pkt_idx = pkt_idx + 1;
        end
        xb = xb(1:double(burst_on));

        % --- sample per-burst drift parameters (deterministic) ---
        f0 = f0_rng(1) + (f0_rng(2)-f0_rng(1)) * rand(rs);

        drift_total = drift_rng(1) + (drift_rng(2)-drift_rng(1)) * rand(rs);
        if rand(rs) < 0.5, drift_total = -drift_total; end

        Tburst = double(burst_on) / double(Fs);               % seconds
        k_hzs  = drift_total / max(1e-9, Tburst);             % Hz/s slope so total drift ~ drift_total

        g_db = aj_rng(1) + (aj_rng(2)-aj_rng(1)) * rand(rs);
        gain = 10^(g_db/20);

        % --- apply gain jitter ---
        xb = xb * single(gain);

        % --- apply CFO ramp: x[n] * exp(j*2pi*(f0*t + 0.5*k*t^2)) ---
        n = single(0:double(burst_on)-1).';
        tt = n / single(double(Fs));
        phi = single(2*pi) * ( single(f0)*tt + single(0.5)*single(k_hzs)*(tt.^2) );
        xb = xb .* complex(cos(phi), sin(phi));

        % advance pointer past windows ending before burst
        while wi <= M && endsS(wi) < t
            wi = wi + 1;
        end

        % copy overlaps into windows
        wj = wi;
        while wj <= M && startsS(wj) <= burst_end
            ovL = max(t, startsS(wj));
            ovR = min(burst_end, endsS(wj));
            if ovL <= ovR
                b0 = ovL - t + 1;
                b1 = ovR - t + 1;
                w0 = ovL - startsS(wj) + 1;
                w1 = ovR - startsS(wj) + 1;
                XsigS(double(w0):double(w1), double(wj)) = XsigS(double(w0):double(w1), double(wj)) + xb(double(b0):double(b1));
            end
            wj = wj + 1;
        end

        % log
        burst_starts(end+1,1) = double(t); %#ok<AGROW>
        burst_lens(end+1,1)   = double(burst_on); %#ok<AGROW>
        f0_hz_v(end+1,1)      = f0; %#ok<AGROW>
        drift_hz_v(end+1,1)   = drift_total; %#ok<AGROW>
        slope_hzs_v(end+1,1)  = k_hzs; %#ok<AGROW>
        gain_db_v(end+1,1)    = g_db; %#ok<AGROW>

        % IBI
        ibi_mean_s = ibi_rng(1) + (ibi_rng(2)-ibi_rng(1)) * rand(rs);
        jit_frac   = jit_rng(1) + (jit_rng(2)-jit_rng(1)) * rand(rs);
        ibi_s      = ibi_mean_s + (2*rand(rs)-1) * (jit_frac * ibi_mean_s);
        ibi        = int64(max(1, round(ibi_s * double(Fs))));
        if ibi < burst_on + min_gap_samps
            ibi = burst_on + min_gap_samps;
        end
        ibi_samps_v(end+1,1) = double(ibi); %#ok<AGROW>

        t = t + ibi;
    end

    Xsig = XsigS(:, invord);

    sched = struct();
    sched.L_need = double(L_need);
    sched.burst_starts_samp = burst_starts;
    sched.burst_len_samp    = burst_lens;
    sched.ibi_samp          = ibi_samps_v;
    sched.f0_hz             = f0_hz_v;
    sched.drift_total_hz    = drift_hz_v;
    sched.drift_slope_hzs   = slope_hzs_v;
    sched.gain_db           = gain_db_v;
end