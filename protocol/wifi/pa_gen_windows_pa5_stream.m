function [Xsig, sched] = pa_gen_windows_pa5_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan)
%PA_GEN_WINDOWS_PA5_STREAM Signal-only PA5 windows (margin / quality regimes).
% Behavior: continuous packet stream, multiplied by piecewise-constant gains within the 20ms window.
% No frequency translation.

    Fs = int64(plan.Fs); W = int64(plan.W); L = int64(plan.L);
    starts = int64(plan.starts(:)); M = int64(numel(starts));
    ends   = starts + W - 1;

    [startsS, ord] = sort(starts);
    endsS = ends(ord);
    invord = zeros(size(ord)); invord(ord) = 1:numel(ord);

    XsigS = complex(zeros(double(W), double(M), "single"), zeros(double(W), double(M), "single"));

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % PA5 regime params
    rc_rng   = double(pa_get_nested(cfg,"pas.PA5.params.regime_count"));      % [2,4]
    dwell_rng_s = double(pa_get_nested(cfg,"pas.PA5.params.regime_dwell_s")); % [min,max] seconds per regime
    gains_db = pa_get_nested(cfg,"pas.PA5.params.regime_gains_db");           % vector of dB values

    gains_db = double(gains_db(:));
    assert(~isempty(gains_db), "pas.PA5.params.regime_gains_db must be non-empty vector");

    % Only simulate until last needed window end
    L_need = min(L, max(endsS));

    % Segment-level RNG for regime schedule
    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA5_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    % Base packet stream state
    pkt_idx = int64(1);
    pkt_buf = complex(zeros(0,1,"single"), zeros(0,1,"single"));
    pkt_ptr = int64(1);
    pkt_count = 0;

    % Helper: generate continuous baseband samples for a length n (Fs)
    function seg = next_samples(nneed)
        while int64(numel(pkt_buf)) - pkt_ptr + 1 < nneed
            [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "payload");
            [~, seed_scr]     = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "scrambler");
            rs_scr = RandStream("mt19937ar","Seed",double(seed_scr));
            scr = randi(rs_scr, [1 127], 1, 1);

            x_pkt = pa_gen_packet(uint32(seed_payload), scr, wlanCfg);
            pkt_buf = [pkt_buf; x_pkt]; %#ok<AGROW>
            pkt_idx = pkt_idx + 1;
            pkt_count = pkt_count + 1;
        end
        seg = pkt_buf(double(pkt_ptr):double(pkt_ptr+nneed-1));
        pkt_ptr = pkt_ptr + nneed;

        if pkt_ptr > 50000
            pkt_buf = pkt_buf(double(pkt_ptr):end);
            pkt_ptr = int64(1);
        end
    end

    % We build regime schedule per window (so each 20ms window is guaranteed to contain regimes)
    sched = repmat(struct(), 1, numel(starts));

    for w = 1:M
        % Use true window_id for deterministic per-window regimes (prevents repeats across batches)
        window_id = double(ord(w)); %#ok<NASGU>
    end

    % We still stream through segment time to respect plan starts, but regimes are per-window-local.
    % Walk windows in sorted order and materialize each window directly.
    for w = 1:M
        st = startsS(w);
        en = endsS(w);

        % Advance stream to st by consuming samples (virtual tape)
        % We do this by consuming (st - cur_t) samples. Track a "cursor" in segment time.
        % For simplicity: maintain a cursor in samples.
        if w == 1
            cur_t = int64(1);
        end
        if st > cur_t
            throwaway = next_samples(st - cur_t); %#ok<NASGU>
            cur_t = st;
        end

        % Now produce exactly W samples for this window
        xw = next_samples(W);
        cur_t = cur_t + W;

        % --- build deterministic regime schedule for this window ---
        [~, seed_win] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, double(w), "PA5_window_regimes");
        rsw = RandStream("mt19937ar","Seed",double(seed_win));

        R = randi(rsw, [round(rc_rng(1)) round(rc_rng(2))], 1, 1);

        % choose gains (with replacement; allows repeated regimes)
        gsel = gains_db(randi(rsw, [1 numel(gains_db)], R, 1));
        gains_lin = 10.^(gsel/20);

        % choose dwell lengths and normalize to sum W
        dw = zeros(R,1);
        for k = 1:R
            ds = dwell_rng_s(1) + (dwell_rng_s(2)-dwell_rng_s(1)) * rand(rsw);
            dw(k) = max(1, round(ds * double(Fs)));
        end
        % normalize to window length
        dw = max(1, floor(dw * (double(W) / sum(dw))));
        % fix rounding to exact W
        diffW = double(W) - sum(dw);
        dw(end) = dw(end) + diffW;
        assert(sum(dw) == double(W));

        % apply regimes
        idx0 = 1;
        intervals = zeros(R,2);
        for k = 1:R
            idx1 = idx0 + dw(k) - 1;
            xw(idx0:idx1) = xw(idx0:idx1) * single(gains_lin(k));
            intervals(k,:) = [idx0, idx1];
            idx0 = idx1 + 1;
        end

        XsigS(:,w) = xw;

        sched(w).regime_count = R;
        sched(w).gains_db = gsel(:);
        sched(w).intervals = intervals; % window-local [start,end] samples
    end

    Xsig = XsigS(:, invord);

    % reorder sched back to plan order
    sched = sched(invord);

    % add global info
    for i = 1:numel(sched)
        sched(i).packet_count_est = pkt_count;
    end
end