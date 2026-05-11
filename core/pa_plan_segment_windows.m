function plan = pa_plan_segment_windows(cfg, session_id, tape_id, segment_id, windows_needed_for_segment)
%PA_PLAN_SEGMENT_WINDOWS Choose stride S∈{W,W/2}, choose/increase segment length, then compute
% base starts + jittered starts deterministically.
%
% Definitions:
%  Fs = cfg.rates.fs_hz
%  W  = round(Fs * window_length_s)
%  J  = round(Fs * max_jitter_s)
%  L  = segment samples
%  N_base = floor((L - 2J - W)/S) + 1

    Fs = round(double(pa_get_nested(cfg,"rates.fs_hz")));
    W  = round(double(pa_get_nested(cfg,"windowing.window_length_s")) * Fs);
    J  = round(double(pa_get_nested(cfg,"windowing.alignment_jitter_policy.max_jitter_s")) * Fs);

    smin = double(pa_get_nested(cfg,"generator.structure.segment_min_seconds"));
    smax = double(pa_get_nested(cfg,"generator.structure.segment_max_seconds"));

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % Deterministic segment-plan RNG (segment-level; use window_id=0)
    [~, seed_plan] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "segment_plan");
    rs_plan = RandStream("mt19937ar","Seed",double(seed_plan));

    % Draw initial segment length uniformly, then deterministically increase if needed
    seg_len_s0 = smin + (smax - smin) * rand(rs_plan);

    % Candidate strides in order: W then floor(W/2)
    S_cands = [W, floor(W/2)];

    chosen = false;
    for ci = 1:numel(S_cands)
        S = S_cands(ci);

        % Minimum L to ensure N_base >= windows_needed: L_min = 2J + W + (windows_needed-1)*S
        L_min = 2*J + W + max(0, windows_needed_for_segment-1) * S;
        seg_len_need_s = double(L_min) / double(Fs);

        seg_len_s = max(seg_len_s0, seg_len_need_s);
        if seg_len_s <= smax + 1e-12
            chosen = true;
            break;
        end
    end
    if ~chosen
        error("Cannot satisfy windows_needed_for_segment=%d within segment_max_seconds=%.3f (even with S=W/2). Reduce windows_needed or increase segment_max_seconds.", ...
              windows_needed_for_segment, smax);
    end

    % Finalize L (integer samples), enforce L >= L_min exactly
    L = round(seg_len_s * Fs);
    L_min = 2*J + W + max(0, windows_needed_for_segment-1) * S;
    if L < L_min, L = L_min; end
    seg_len_s = double(L)/double(Fs);

    % Deterministic "insufficient windows" fallback definition
    N_base = floor((double(L) - 2*double(J) - double(W)) / double(S)) + 1;

    if N_base < windows_needed_for_segment
        % Your rule: if insufficient at stride S, set S=W/2 and recompute; if still insufficient, increase seg length
        S = floor(W/2);
        N_base = floor((double(L) - 2*double(J) - double(W)) / double(S)) + 1;

        if N_base < windows_needed_for_segment
            % Increase segment length minimally until sufficient (only S=W/2 allowed now)
            L_need = 2*J + W + (windows_needed_for_segment-1)*S;
            if L_need > round(smax*Fs)
                error("Even after S=W/2, required segment length %.3fs exceeds segment_max_seconds %.3fs.", double(L_need)/Fs, smax);
            end
            L = L_need;
            seg_len_s = double(L)/double(Fs);
            N_base = floor((double(L) - 2*double(J) - double(W)) / double(S)) + 1;
        end
    end

    % Base starts with guard margin J from bounds: base_start ∈ [J, L-J-W]
    base_starts = int64(J) + int64(0:(windows_needed_for_segment-1)) * int64(S);

    % Jitter RNG (per-window, deterministic)
    [~, seed_jit] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "jitter_stream");
    rs_jit = RandStream("mt19937ar","Seed",double(seed_jit));

    starts = int64(zeros(windows_needed_for_segment,1));
    for i = 1:windows_needed_for_segment
        ok = false;
        while ~ok
            jit = int64(randi(rs_jit, 2*J+1) - (J+1));   % uniform in [-J, +J]
            st  = base_starts(i) + jit;
            % enforce bounds without clamping; redraw if OOB
            if st >= 1 && (st + W - 1) <= L
                ok = true;
                starts(i) = st;
            end
        end
    end

    % Pack plan
    plan = struct();
    plan.Fs = Fs; plan.W = W; plan.J = J; plan.S = S;
    plan.L = int64(L); plan.segment_len_s = seg_len_s;
    plan.windows_needed = windows_needed_for_segment;
    plan.N_base = N_base;
    plan.base_starts = base_starts(:);
    plan.starts = starts(:);
end