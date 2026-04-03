function out = pa_repeat_similarity_from_schedule(x, Fs, B, nfft, hop, nbins, intervals, reduce_mode)
%PA_REPEAT_SIMILARITY_FROM_SCHEDULE
% x: final window IQ (after noise)
% B: [nbins x T] bins for whole window (linear power), computed once
% intervals: [R x 2] sample intervals for repeats (window coords)
% reduce_mode: "min_pairwise" or "mean_pairwise"

    if nargin < 8 || isempty(reduce_mode), reduce_mode = "min_pairwise"; end
    reduce_mode = string(reduce_mode);

    % map sample interval to STFT frame indices using frame center
    T = size(B,2);
    frame_center = ((0:T-1)*hop + nfft/2);  % in samples, 1-based approx below
    frame_center = frame_center + 1;

    R = size(intervals,1);
    emb = zeros(nbins, R);

    for i = 1:R
        a = intervals(i,1); b = intervals(i,2);
        if a == 0 || b == 0 || b < a
            emb(:,i) = NaN;
            continue;
        end
        idx = find(frame_center >= a & frame_center <= b);
        if isempty(idx)
            % fallback: nearest frame to interval center
            c = round((a+b)/2);
            [~,k] = min(abs(frame_center - c));
            idx = k;
        end
        v = mean(B(:,idx), 2);
        nv = norm(v) + 1e-12;
        emb(:,i) = v / nv;
    end

    good = all(isfinite(emb),1);
    emb = emb(:,good);
    Rg = size(emb,2);

    if Rg < 2
        out = struct("score", -Inf, "pairwise", [], "used_repeats", Rg);
        return;
    end

    % pairwise cosine similarities
    sims = [];
    for i = 1:Rg
        for j = i+1:Rg
            sims(end+1,1) = max(-1,min(1, sum(emb(:,i).*emb(:,j)))); %#ok<AGROW>
        end
    end

    if reduce_mode == "min_pairwise"
        score = min(sims);
    else
        score = mean(sims);
    end

    out = struct("score", score, "pairwise", sims, "used_repeats", Rg);
end