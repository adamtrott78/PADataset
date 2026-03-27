function out = pa_detect_E2E3(x, Fs, smooth_s, refractory_s, k_hi, k_lo)
    % power and smoothing
    p = abs(x).^2;
    M = max(1, round(smooth_s * Fs));
    ps = filter(ones(M,1,"single")/single(M), 1, p);

    med = median(double(ps));
    madv = median(abs(double(ps) - med));
    hi = med + k_hi*madv;
    lo = med + k_lo*madv;

    % hysteresis mask
    m = false(size(ps));
    on = false;
    for i = 1:numel(ps)
        if ~on
            if double(ps(i)) > hi, on = true; end
        else
            if double(ps(i)) < lo, on = false; end
        end
        m(i) = on;
    end

    % edges
    dm = diff([false; m; false]);
    rises = find(dm == 1);
    falls = find(dm == -1) - 1;

    % refractory
    R = max(1, round(refractory_s * Fs));
    rises = keep_refractory(rises, R);
    falls = keep_refractory(falls, R);

    out = struct();
    out.mask = m;
    out.E2_count = numel(rises);
    out.E3_count = numel(falls);
    out.rise_idx = rises;
    out.fall_idx = falls;
    out.th_hi = hi;
    out.th_lo = lo;
end

function idx2 = keep_refractory(idx, R)
    if isempty(idx), idx2 = idx; return; end
    idx2 = idx(1);
    last = idx(1);
    for k = 2:numel(idx)
        if idx(k) - last >= R
            idx2(end+1,1) = idx(k); %#ok<AGROW>
            last = idx(k);
        end
    end
end