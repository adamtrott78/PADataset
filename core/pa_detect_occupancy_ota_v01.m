function occ = pa_detect_occupancy_ota_v01(x, Fs, smooth_s, close_s, q_floor, k_mad, min_comp_s)
% Per-window noise-floor occupancy on smoothed power:
% thr = noise_med + k_mad * noise_mad   (power domain)
% Fix: avoid filter warm-up poisoning (use movmean + stats on steady region).

    x = x(:);
    W = numel(x);

    M = max(1, round(double(smooth_s) * double(Fs)));

    % --- smoothed power (NO filter warm-up ramp) ---
    ps = movmean(abs(x).^2, M, "Endpoints","shrink");   % single
    p  = double(ps);

    % --- estimate "noise-like" region from the lower tail, BUT from steady region ---
    i0 = min(W, max(1, M));            % ignore the first ~M samples for stats
    p_stats = p(i0:end);
    if isempty(p_stats), p_stats = p; end

    qv  = quantile(p_stats, double(q_floor));
    low = p_stats(p_stats <= qv);
    if isempty(low), low = p_stats; end

    med0 = median(low);
    mad0 = median(abs(low - med0)) + 1e-12;

    thr_pow = med0 + double(k_mad) * mad0;

    mask0 = p > thr_pow;

    % close (optional)
    if close_s > 0
        kclose = max(1, round(double(close_s) * double(Fs)));
        mask = pa_mask_close(mask0, kclose);
    else
        mask = mask0;
    end
    mask = logical(mask(:));

    % components
    d = diff([false; mask; false]);
    starts = find(d==1);
    ends   = find(d==-1)-1;

    if min_comp_s > 0 && ~isempty(starts)
        min_len = max(1, round(double(min_comp_s) * double(Fs)));
        keep = (ends - starts + 1) >= min_len;
        starts = starts(keep);
        ends   = ends(keep);
    end

    % train-span mask
    train_mask = false(W,1);
    if ~isempty(starts)
        train_mask(starts(1):ends(end)) = true;
    end

    occ = struct();
    occ.mask = mask;
    occ.duty_frac = mean(mask);
    occ.starts = starts(:);
    occ.ends = ends(:);
    occ.train_mask = train_mask;
    occ.train_frac = mean(train_mask);
    occ.thr_pow = thr_pow;
    occ.med0 = med0;
    occ.mad0 = mad0;
end