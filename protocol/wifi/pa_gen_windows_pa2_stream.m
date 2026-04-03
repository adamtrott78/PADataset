function [Xsig, sched] = pa_gen_windows_pa2_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan)
%PA_GEN_WINDOWS_PA2_STREAM Build signal-only PA2 windows without allocating the full segment.
% Outputs:
%   Xsig  [W x M] complex single (columns = windows in plan order)
%   sched struct with burst schedule diagnostics

    Fs = int64(plan.Fs); W = int64(plan.W); L = int64(plan.L);
    starts = int64(plan.starts(:)); M = int64(numel(starts));
    ends   = starts + W - 1;

    % Sort windows by start for efficient overlap checks, but return in plan order
    [startsS, ord] = sort(starts);
    endsS = ends(ord);
    invord = zeros(size(ord)); invord(ord) = 1:numel(ord);

    XsigS = complex(zeros(double(W), double(M), "single"), zeros(double(W), double(M), "single"));

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    bc_rng  = double(pa_get_nested(cfg,"pas.PA2.params.burst_count"));
    on_rng  = double(pa_get_nested(cfg,"pas.PA2.params.burst_on_s"));
    ibi_rng = double(pa_get_nested(cfg,"pas.PA2.params.ibi_mean_s"));
    jit_rng = double(pa_get_nested(cfg,"pas.PA2.params.ibi_jitter_frac"));

    % Segment-level RNG for schedule
    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA2_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    min_gap_samps = int64(round(0.0002 * double(Fs))); % 0.2ms

    % Only simulate until last needed window end (huge speed win vs full L)
    L_need = min(L, max(endsS));

    t = int64(1);
    pkt_idx = int64(1);

    burst_starts = zeros(0,1);
    burst_lens   = zeros(0,1);
    ibi_samps_v  = zeros(0,1);

    wi = 1; % pointer into sorted windows (advance when window ends before current burst start)

    while t <= L_need && wi <= M
        burst_on_s = on_rng(1) + (on_rng(2)-on_rng(1)) * rand(rs);
        burst_on   = int64(max(1, round(burst_on_s * double(Fs))));
        burst_end  = t + burst_on - 1;
        if burst_end > L_need, break; end

        % Generate enough packets to cover burst_on, then truncate
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

        % Advance pointer past windows that end before burst starts
        while wi <= M && endsS(wi) < t
            wi = wi + 1;
        end

        % Copy overlap into every window that overlaps this burst (usually 1, sometimes 2)
        wj = wi;
        while wj <= M && startsS(wj) <= burst_end
            ovL = max(t, startsS(wj));
            ovR = min(burst_end, endsS(wj));
            if ovL <= ovR
                % Segment indices within burst
                b0 = ovL - t + 1;
                b1 = ovR - t + 1;
                % Window indices
                w0 = ovL - startsS(wj) + 1;
                w1 = ovR - startsS(wj) + 1;
                XsigS(double(w0):double(w1), double(wj)) = XsigS(double(w0):double(w1), double(wj)) + xb(double(b0):double(b1));
            end
            wj = wj + 1;
        end

        burst_starts(end+1,1) = double(t); %#ok<AGROW>
        burst_lens(end+1,1)   = double(burst_on); %#ok<AGROW>

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

    % Unsort back to plan order
    Xsig = XsigS(:, invord);

    sched = struct();
    sched.L_need = double(L_need);
    sched.burst_starts_samp = burst_starts;
    sched.burst_len_samp    = burst_lens;
    sched.ibi_samp          = ibi_samps_v;
end