function sim = pa_detect_repeat_similarity_iqxcorr(x, Fs, intervals, ds, maxlag_s, cap_len_s)
%PA_DETECT_REPEAT_SIMILARITY_IQXCORR Replay-style similarity detector.
% Uses phase-invariant complex IQ correlation (max |xcorr| within lag window).
%
% Inputs:
%   x         [W x 1] complex
%   Fs        Hz
%   intervals [K x 2] sample indices (starts, ends) for detected repeats
%   ds        downsample factor (integer), e.g. 4
%   maxlag_s  lag tolerance in seconds, e.g. 2e-4
%   cap_len_s max segment length used (seconds), e.g. 8e-3
%
% Output struct:
%   used_repeats, score, pairwise, Lc_used, maxlag_used

    if nargin < 4 || isempty(ds), ds = 4; end
    if nargin < 5 || isempty(maxlag_s), maxlag_s = 2e-4; end
    if nargin < 6 || isempty(cap_len_s), cap_len_s = 8e-3; end

    x = x(:);
    intervals = double(intervals);
    if isempty(intervals) || size(intervals,2) ~= 2
        sim = struct("used_repeats",0,"score",0,"pairwise",zeros(0,1),"Lc_used",0,"maxlag_used",0);
        return;
    end

    xd = x(1:ds:end);
    Fsd = double(Fs)/double(ds);

    sd = floor((intervals(:,1)-1)/ds) + 1;
    ed = floor((intervals(:,2)-1)/ds) + 1;

    keep = (ed > sd);
    sd = sd(keep); ed = ed(keep);
    used = numel(sd);

    pairwise = zeros(max(0, used-1), 1);
    score = 0; Lc_used = 0;

    if used >= 2
        Lc = min(ed - sd + 1);
        Lc = min(Lc, round(cap_len_s * Fsd)); % cap length
        if Lc >= 64
            maxlag = max(1, round(maxlag_s * Fsd));
            Lc_used = Lc;

            r0 = xd(sd(1):sd(1)+Lc-1);
            r0 = r0 - mean(r0);
            r0 = double(r0) / (norm(double(r0)) + 1e-12);

            for k = 2:used
                rk = xd(sd(k):sd(k)+Lc-1);
                rk = rk - mean(rk);
                rk = double(rk) / (norm(double(rk)) + 1e-12);

                c = xcorr(r0, rk, maxlag, "coeff");
                pairwise(k-1) = max(abs(c));
            end

            score = mean(pairwise);
        end
    end

    sim = struct();
    sim.used_repeats = used;
    sim.score = score;
    sim.pairwise = pairwise;
    sim.Lc_used = Lc_used;
    sim.maxlag_used = max(0, round(maxlag_s * Fsd));
end