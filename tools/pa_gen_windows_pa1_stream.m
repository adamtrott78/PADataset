function [Xsig, sched] = pa_gen_windows_pa1_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan)
%PA_GEN_WINDOWS_PA1_STREAM Signal-only PA1 windows (survey/probing scan).
% Pattern: monotonic scan through a unique offset list (no revisits within a scan),
% then start a new scan list when exhausted.
%
% Reuses PA4 streaming architecture:
%   base packet stream at Fs -> (optional) oversample -> mix -> LPF -> decimate

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

    % ---- PA1 scan params ----
    dwell_rng = double(pa_get_nested(cfg,"pas.PA1.params.dwell_s"));           % [min,max] seconds
    scan_rng  = double(pa_get_nested(cfg,"pas.PA1.params.scan_set_size"));     % [min,max] unique offsets per scan

    max_abs_df = double(pa_get_nested(cfg,"operators.freq_translation.max_abs_offset_hz"));
    assert(max_abs_df > 0);

    % ---- reuse PA4 oversample/decimate parameters ----
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

        if mod(nt, os) ~= 0, nt = nt + (os - mod(nt, os)); end

        h = fir1(nt-1, fc/(Fs_os/2), kaiser(nt, beta));
        h = double(h(:)).';

        interp = dsp.FIRInterpolator(os, h);
        decim  = dsp.FIRDecimator(os, h);

        phi_os = 0;
    else
        interp = []; decim = [];
        phi_os = 0;
        os = 1;
        Fs_os = double(Fs);
        fc = NaN; nt = NaN; beta = NaN;
    end

    % ---- segment-level RNG for PA1 schedule ----
    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA1_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    % ---- offset grid (reuse PA4 grid config) ----
    hp = pa_get_nested(cfg,"operators.hop_step_schedule");
    og = pa_get_nested(cfg,"pas.PA1.params.offset_grid_hz");
    gmin = double(og.min_hz); gmax = double(og.max_hz); gstep = double(og.step_hz);
    assert(gstep > 0 && gmax >= gmin);

    grid = (ceil(gmin/gstep):floor(gmax/gstep)) * gstep;
    grid = grid(:);

    % Apply wrap/alias safety like PA4
    if rc_enable
        df_lim = (Fs_os/2) - fc;
        grid = grid(abs(grid) <= min(max_abs_df, df_lim));
    else
        df_lim = (double(Fs)/2) - (double(Fs)/2)*0.95;
        grid = grid(abs(grid) <= min(max_abs_df, df_lim));
    end
    assert(~isempty(grid), "Offset grid is empty after limits; adjust config.");

    % ---- build scan blocks until covering L_need ----
    dwell_samp = zeros(0,1);
    offsets_hz = zeros(0,1);
    scan_id    = zeros(0,1);   % scan segment id per block (for debugging)

    total = int64(0);
    sid = 0;

    while total < L_need
        sid = sid + 1;

        Kscan = randi(rs, [round(scan_rng(1)), round(scan_rng(2))], 1, 1);
        assert(numel(grid) >= Kscan, "Offset grid too small for scan_set_size=%d", Kscan);

        dir = 1;
        if rand(rs) < 0.5, dir = -1; end

        % choose start index so we can take Kscan unique steps without wrap
        if dir == 1
            i0 = randi(rs, [1, numel(grid) - Kscan + 1], 1, 1);
            idxs = i0:(i0+Kscan-1);
        else
            i0 = randi(rs, [Kscan, numel(grid)], 1, 1);
            idxs = i0:-1:(i0-Kscan+1);
        end

        scan_offsets = grid(idxs);

        % walk through scan_offsets once; then we’ll create a new scan list
        for k = 1:numel(scan_offsets)
            if total >= L_need, break; end

            dwell_s = dwell_rng(1) + (dwell_rng(2)-dwell_rng(1)) * rand(rs);
            ds = int64(max(1, round(dwell_s * double(Fs))));

            dwell_samp(end+1,1) = double(ds); %#ok<AGROW>
            offsets_hz(end+1,1) = double(scan_offsets(k)); %#ok<AGROW>
            scan_id(end+1,1)    = double(sid); %#ok<AGROW>

            total = total + ds;
        end
    end

    % ---- base packet stream state ----
    pkt_idx = int64(1);
    pkt_buf = complex(zeros(0,1,"single"), zeros(0,1,"single"));
    pkt_ptr = int64(1);

    % ---- walk blocks and write overlaps ----
    t = int64(1);
    wi = 1;
    pkt_count = 0;

    for bi = 1:numel(dwell_samp)
        if t > L_need || wi > M, break; end

        ds = int64(dwell_samp(bi));
        df = double(offsets_hz(bi));

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

        if pkt_ptr > 50000
            pkt_buf = pkt_buf(double(pkt_ptr):end);
            pkt_ptr = int64(1);
        end

        % oversample -> mix -> LPF -> decimate
        if rc_enable
            seg_os = step(interp, seg);
            [seg_os_mixed, phi_os] = mix_block(seg_os, Fs_os, df, phi_os);
            seg_mixed = step(decim, seg_os_mixed);
        else
            phi = phi_os;
            [seg_mixed, phi] = pa_mix_freq_offset_block(seg, double(Fs), df, phi);
            phi_os = phi;
        end

        block_end = t + ds - 1;

        while wi <= M && endsS(wi) < t
            wi = wi + 1;
        end

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
    sched.dwell_samp = dwell_samp(:);
    sched.offsets_hz = offsets_hz(:);
    sched.scan_id = scan_id(:);
    sched.offset_grid_hz = grid(:);

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
    n = double(0:numel(x)-1).';
    dphi = 2*pi*df/Fs;
    ang = phi_in + dphi*n;
    y = x .* complex(single(cos(ang)), single(sin(ang)));
    phi_out = phi_in + dphi*double(numel(x));
    phi_out = mod(phi_out, 2*pi);
end