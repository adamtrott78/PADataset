function [x_seg, seginfo] = pa_gen_segment_pa2(cfg, wlanCfg, session_id, tape_id, segment_id, L)
%PA_GEN_SEGMENT_PA2 Generate signal-only PA2 segment of length L samples.
% Deterministic burst schedule driven by PA2 param ranges.
% Bursts are energy-on segments implemented by concatenated packets truncated to burst_on_s.

    Fs = round(double(pa_get_nested(cfg,"rates.fs_hz")));
    assert(Fs > 0);
    L = int64(L);

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % PA2 parameter ranges
    bc_rng   = double(pa_get_nested(cfg,"pas.PA2.params.burst_count"));      % [4,8] per 20ms (used as density reference)
    on_rng   = double(pa_get_nested(cfg,"pas.PA2.params.burst_on_s"));       % [0.5,1.8] ms
    ibi_rng  = double(pa_get_nested(cfg,"pas.PA2.params.ibi_mean_s"));       % [2.0,4.5] ms
    jit_rng  = double(pa_get_nested(cfg,"pas.PA2.params.ibi_jitter_frac")); % [0.10,0.25]

    % Segment-level RNG for schedule
    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA2_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    % Prealloc segment (signal-only gaps are zeros; noise is added later per-window)
    x_seg = complex(zeros(double(L),1,'single'), zeros(double(L),1,'single'));

    burst_starts = [];
    burst_lens   = [];
    ibi_samps_v  = [];
    pkt_idx_v    = [];

    t = int64(1);         % burst onset
    pkt_idx = int64(1);   % global packet counter within this segment (for deterministic per-packet seeds)

    % Heuristic density: choose schedule so typical 20ms contains ~4-8 bursts
    % Implemented by drawing IBI ~[2,4.5]ms and burst_on ~[0.5,1.8]ms repeatedly.

    min_gap_samps = int64(round(0.0002 * Fs)); % 0.2ms guard to avoid overlaps (deterministic clamp)

    while t <= L
        % draw burst_on duration
        burst_on_s = on_rng(1) + (on_rng(2)-on_rng(1)) * rand(rs);
        burst_on = int64(max(1, round(burst_on_s * Fs)));

        % generate enough packets to cover burst_on
        % get one packet length (deterministic) by generating first packet once (cached per function call)
        % but for strictness, just generate packets as needed
        x_burst = complex(zeros(0,1,'single'), zeros(0,1,'single'));
        while int64(numel(x_burst)) < burst_on
            % per-packet payload seed and scrambler seed (deterministic from ids + pkt_idx)
            [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "payload");
            [~, seed_scr]     = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "scrambler");
            rs_scr = RandStream("mt19937ar","Seed",double(seed_scr));
            scr = randi(rs_scr, [1 127], 1, 1);

            x_pkt = pa_gen_packet(uint32(seed_payload), scr, wlanCfg);
            x_burst = [x_burst; x_pkt]; %#ok<AGROW>
            pkt_idx_v(end+1,1) = double(pkt_idx); %#ok<AGROW>
            pkt_idx = pkt_idx + 1;
        end

        % truncate burst to exact length
        x_burst = x_burst(1:double(burst_on));

        % place burst if it fits
        if t + burst_on - 1 > L
            break;
        end
        x_seg(double(t):double(t+burst_on-1)) = x_burst;

        burst_starts(end+1,1) = double(t); %#ok<AGROW>
        burst_lens(end+1,1)   = double(burst_on); %#ok<AGROW>

        % draw IBI (gap between burst onsets)
        ibi_mean_s = ibi_rng(1) + (ibi_rng(2)-ibi_rng(1)) * rand(rs);
        jit_frac   = jit_rng(1) + (jit_rng(2)-jit_rng(1)) * rand(rs);
        ibi_s      = ibi_mean_s + (2*rand(rs)-1) * (jit_frac * ibi_mean_s);
        ibi = int64(max(1, round(ibi_s * Fs)));

        % enforce no overlap: next onset >= t + burst_on + min_gap
        if ibi < burst_on + min_gap_samps
            ibi = burst_on + min_gap_samps;
        end
        ibi_samps_v(end+1,1) = double(ibi); %#ok<AGROW>

        t = t + ibi;
    end

    seginfo = struct();
    seginfo.segment_id = segment_id;
    seginfo.session_id = session_id;
    seginfo.tape_id    = tape_id;
    seginfo.L          = double(L);
    seginfo.Fs         = Fs;
    seginfo.burst_starts_samp = burst_starts;
    seginfo.burst_len_samp    = burst_lens;
    seginfo.ibi_samp          = ibi_samps_v;
    seginfo.packet_indices_used = pkt_idx_v;
end