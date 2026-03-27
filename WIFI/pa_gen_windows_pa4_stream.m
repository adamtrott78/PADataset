function [Xsig, sched] = pa_gen_windows_pa4_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan)
%PA_GEN_WINDOWS_PA4_STREAM Signal-only PA4 windows (streaming), with
% oversample -> mix -> LPF -> decimate inside the generator (deterministic).
%
% Key property (v0.1): each dwell block produces EXACTLY ds output samples.

    Fs = int64(plan.Fs); W = int64(plan.W); L = int64(plan.L);
    starts = int64(plan.starts(:)); M = int64(numel(starts));
    ends   = starts + W - 1;

    [startsS, ord] = sort(starts);
    endsS = ends(ord);
    invord = zeros(size(ord)); invord(ord) = 1:numel(ord);

    XsigS = complex(zeros(double(W), double(M), "single"), zeros(double(W), double(M), "single"));

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % Only simulate until last needed window end
    L_need = min(L, max(endsS));

    % ---- hop schedule parameters ----
    hp = pa_get_nested(cfg,"operators.hop_step_schedule");
    dwell_rng      = double(hp.dwell_s);          % [min,max] seconds
    set_rng        = double(hp.hop_set_size);     % [min,max]
    require_revisit = logical(hp.require_revisit);

    max_abs_df = double(pa_get_nested(cfg,"operators.freq_translation.max_abs_offset_hz"));
    assert(max_abs_df > 0);

    % ---- PA4 oversample/decimate parameters ----
    rc = pa_get_nested(cfg,"operators.hop_step_schedule.rate_conversion");
    rc_enable = logical(rc.enable);

    if rc_enable
        os = double(rc.os_factor);
        assert(os == round(os) && os >= 2, "rate_conversion.os_factor must be integer >=2");

        Fs0 = double(Fs);
        Fs_os = Fs0 * os;

        fc = double(rc.lpf_cutoff_hz);
        assert(fc > 0 && fc < (Fs0/2), "rate_conversion.lpf_cutoff_hz must be in (0, Fs/2)");

        nt = double(rc.fir_numtaps);
        assert(nt == round(nt) && nt >= 16, "rate_conversion.fir_numtaps must be integer >=16");
        beta = double(rc.kaiser_beta);

        % Make taps multiple of os for clean polyphase
        if mod(nt, os) ~= 0, nt = nt + (os - mod(nt, os)); end

        h = fir1(nt-1, fc/(Fs_os/2), kaiser(nt, beta));   % deterministic
        h = double(h(:)).';                               % row

        interp = dsp.FIRInterpolator(os, h);
        decim  = dsp.FIRDecimator(os, h);

        % Phase accumulator is tracked at Fs_os for the mixer
        phi_os = 0;
    else
        interp = []; decim = [];
        phi_os = 0;
        os = 1;
        Fs_os = double(Fs);
        fc = NaN; nt = NaN; beta = NaN;
    end

    % ---- Segment-level RNG for hop schedule (deterministic) ----
    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA4_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    % Offset grid from config (deterministic)
    og = hp.offset_grid_hz;
    gmin = double(og.min_hz); gmax = double(og.max_hz); gstep = double(og.step_hz);
    assert(gstep > 0 && gmax >= gmin);

    grid = (ceil(gmin/gstep):floor(gmax/gstep)) * gstep;
    grid = grid(:);

    % Do NOT allow offsets that would wrap at the oversampled rate:
    % require |df| + fc < Fs_os/2  (fc is our protected band-edge)
    if rc_enable
        df_lim = (Fs_os/2) - fc;
        grid = grid(abs(grid) <= min(max_abs_df, df_lim));
    else
        % If not oversampling, MUST avoid wrap at Fs directly: |df| + fc < Fs/2
        df_lim = (double(Fs)/2) - (double(Fs)/2)*0.95; % fallback small; you should keep rc_enable=true
        grid = grid(abs(grid) <= min(max_abs_df, df_lim));
    end

    assert(~isempty(grid), "Offset grid is empty after limits; adjust config.");

    % Choose hop set size K
    K = randi(rs, [round(set_rng(1)), round(set_rng(2))], 1, 1);
    assert(numel(grid) >= K, "Offset grid too small for K=%d", K);

    perm = randperm(rs, numel(grid), K);
    offset_set = grid(perm);

    % Build a repeating cycle (guarantees revisits)
    cycle = offset_set(randperm(rs, K));
    if require_revisit
        % revisit guaranteed by repeating cycle
    end

    % Build dwell blocks until covering L_need
    dwell_samp = zeros(0,1);
    offsets_hz = zeros(0,1);
    total = int64(0);
    ci = 1;
    while total < L_need
        dwell_s = dwell_rng(1) + (dwell_rng(2)-dwell_rng(1)) * rand(rs);
        ds = int64(max(1, round(dwell_s * double(Fs))));
        dwell_samp(end+1,1) = double(ds); %#ok<AGROW>
        offsets_hz(end+1,1) = double(cycle(ci)); %#ok<AGROW>
        total = total + ds;
        ci = ci + 1;
        if ci > numel(cycle), ci = 1; end
    end

    % ---- base packet stream state ----
    pkt_idx = int64(1);
    pkt_buf = complex(zeros(0,1,"single"), zeros(0,1,"single"));
    pkt_ptr = int64(1);

    % ---- walk dwell blocks and write overlaps ----
    t = int64(1);      % current segment sample index (1-based at Fs)
    wi = 1;            % window pointer in sorted order
    pkt_count = 0;

    for bi = 1:numel(dwell_samp)
        if t > L_need || wi > M, break; end

        ds = int64(dwell_samp(bi));
        df = double(offsets_hz(bi));

        % Trim last block if it overshoots L_need
        if t + ds - 1 > L_need
            ds = L_need - t + 1;
            if ds <= 0, break; end
        end

        % Produce ds baseband samples from packet stream (Fs)
        need = ds;
        while int64(numel(pkt_buf)) - pkt_ptr + 1 < need
            [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "payload");
            [~, seed_scr]     = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "scrambler");
            rs_scr = RandStream("mt19937ar","Seed",double(seed_scr));
            scr = randi(rs_scr, [1 127], 1, 1);
            x_pkt = pa_gen_packet(uint32(seed_payload), scr, wlanCfg);

            pkt_buf = [pkt_buf; x_pkt]; %#ok<AGROW>
            pkt_idx = pkt_idx + 1;
            pkt_count = pkt_count + 1;
        end

        seg = pkt_buf(double(pkt_ptr):double(pkt_ptr+need-1));
        pkt_ptr = pkt_ptr + need;

        % Compact buffer occasionally (deterministic)
        if pkt_ptr > 50000
            pkt_buf = pkt_buf(double(pkt_ptr):end);
            pkt_ptr = int64(1);
        end

        % ---- oversample -> mix -> LPF -> decimate (or direct mix) ----
        if rc_enable
            % interp: ds -> os*ds
            seg_os = step(interp, seg);                         % length os*ds

            % mix at Fs_os with phase continuity
            [seg_os_mixed, phi_os] = mix_block(seg_os, Fs_os, df, phi_os);

            % decim: os*ds -> ds
            seg_mixed = step(decim, seg_os_mixed);              % length ds (exact)
        else
            % legacy (will wrap if df too big — keep rc_enable true)
            phi = phi_os;
            [seg_mixed, phi] = pa_mix_freq_offset_block(seg, double(Fs), df, phi);
            phi_os = phi;
        end

        block_end = t + ds - 1;

        % Advance past windows that end before this block starts
        while wi <= M && endsS(wi) < t
            wi = wi + 1;
        end

        % Copy overlaps into windows overlapping this block
        wj = wi;
        while wj <= M && startsS(wj) <= block_end
            ovL = max(t, startsS(wj));
            ovR = min(block_end, endsS(wj));
            if ovL <= ovR
                b0 = ovL - t + 1;
                b1 = ovR - t + 1;
                w0 = ovL - startsS(wj) + 1;
                w1 = ovR - startsS(wj) + 1;

                XsigS(double(w0):double(w1), double(wj)) = ...
                    XsigS(double(w0):double(w1), double(wj)) + seg_mixed(double(b0):double(b1));
            end
            wj = wj + 1;
        end

        t = block_end + 1;
    end

    Xsig = XsigS(:, invord);

    sched = struct();
    sched.L_need = double(L_need);
    sched.packet_count = pkt_count;
    sched.offset_set_hz = offset_set(:);
    sched.cycle_hz = cycle(:);
    sched.dwell_samp = dwell_samp(:);
    sched.offsets_hz = offsets_hz(:);

    sched.rate_conversion = struct( ...
        "enable", rc_enable, ...
        "os_factor", double(os), ...
        "fs_hz", double(Fs), ...
        "fs_os_hz", double(Fs_os), ...
        "lpf_cutoff_hz", double(fc), ...
        "fir_numtaps", double(nt), ...
        "kaiser_beta", double(beta) ...
    );
end

function [y, phi_out] = mix_block(x, Fs, df, phi_in)
% Deterministic complex mixing with phase continuity (scalar phi state).
    n = double(0:numel(x)-1).';
    dphi = 2*pi*df/Fs;
    ang = phi_in + dphi*n;
    y = x .* complex(single(cos(ang)), single(sin(ang)));
    phi_out = phi_in + dphi*double(numel(x));
    % keep phi bounded (deterministic)
    phi_out = mod(phi_out, 2*pi);
end
