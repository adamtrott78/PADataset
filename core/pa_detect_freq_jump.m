function out = pa_detect_freq_jump(B, persistence_frames, smooth_frames, min_delta_bins)
%PA_DETECT_FREQ_JUMP Persistent frequency changes using CENTROID-STATE.
% B: [nbins x T] linear power bins from pa_stft_bins32 (nbins=32)
%
% Model:
%  - Wi-Fi NonHT is wideband; translations shift the centroid even if no bin is dominant.
%  - Compute spectral centroid per frame, quantize to nearest bin -> raw_state.
%  - Count a "jump" when state changes by >= min_delta_bins and persists.

    if nargin < 2 || isempty(persistence_frames), persistence_frames = 2; end
    if nargin < 3 || isempty(smooth_frames), smooth_frames = 3; end
    if nargin < 4 || isempty(min_delta_bins), min_delta_bins = 2; end

    [nbins, T] = size(B);
    if T == 0
        out = struct("count",0,"bin_trace",zeros(0,1),"raw_trace",zeros(0,1), ...
                     "change_idx",zeros(0,1),"centroid",zeros(0,1));
        return;
    end
    if T == 1
        out = struct("count",0,"bin_trace",ones(1,1),"raw_trace",ones(1,1), ...
                     "change_idx",zeros(0,1),"centroid",ones(1,1));
        return;
    end

    % time smoothing
    if smooth_frames > 1
        Bsm = movmean(B, smooth_frames, 2);
    else
        Bsm = B;
    end

    epsv = 1e-12;
    k = (1:nbins).';

    % centroid in bin units (continuous)
    denom = sum(Bsm, 1) + epsv;
    mu = (k.' * Bsm) ./ denom;        % 1 x T
    mu = mu(:);                       % T x 1

    % quantize to integer bin state
    raw = round(mu);
    raw = max(1, min(nbins, raw));

    % count persistent changes
    state = zeros(T,1);
    state(1) = raw(1);
    cur = raw(1);
    cnt = 0;

    chg = zeros(T,1); nchg = 0;

    t = 2;
    while t <= T
        if raw(t) == cur
            state(t) = cur;
            t = t + 1;
            continue;
        end

        if abs(double(raw(t)) - double(cur)) < double(min_delta_bins)
            state(t) = cur;
            t = t + 1;
            continue;
        end

        cand = raw(t);
        p = persistence_frames;

        if t + p - 1 <= T && all(raw(t:t+p-1) == cand)
            cnt = cnt + 1;
            cur = cand;
            nchg = nchg + 1;
            chg(nchg) = t;
            state(t:t+p-1) = cur;
            t = t + p;
        else
            state(t) = cur;
            t = t + 1;
        end
    end

    % fill any remaining zeros
    for t = 2:T
        if state(t) == 0, state(t) = state(t-1); end
    end

    out = struct();
    out.count = cnt;
    out.bin_trace = state(:);    % persistent centroid-state
    out.raw_trace = raw(:);      % raw quantized centroid
    out.change_idx = chg(1:nchg);
    out.centroid = mu(:);        % continuous centroid (bin units)
end