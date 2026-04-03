function out = pa_detect_occupancy_from_quiet(x, Fs, snr_quiet_db, smooth_s, occ_sigma_k, close_s, min_comp_s)
%PA_DETECT_OCCUPANCY_FROM_QUIET Noise-referenced occupancy detector.
% - Computes smoothed power, thresholds relative to quiet-noise sigma, applies mask close.
% - Also returns connected components and a train-span mask (first start -> last end).
%
% Inputs:
%   x            [W x 1] complex
%   Fs           sample rate (Hz)
%   snr_quiet_db quiet SNR used when quiet noise was added (dB)
%   smooth_s     smoothing time for power (seconds)
%   occ_sigma_k  threshold multiplier in sigma units
%   close_s      binary mask closing (seconds)
%   min_comp_s   (optional) component length floor (seconds), e.g. 2e-4
%
% Output struct fields:
%   mask         closed occupancy mask (duty)
%   duty_frac    mean(mask)
%   starts/ends  component sample indices after filtering
%   train_mask   mask from starts(1):ends(end)
%   train_frac   mean(train_mask)
%   th_pow       power threshold used
%   ps           smoothed power (single)

    if nargin < 7 || isempty(min_comp_s), min_comp_s = 0; end

    x = x(:);
    W = numel(x);

    % threshold from quiet sigma
    sigma_q = 10^(-double(snr_quiet_db)/20);
    th_pow  = (double(occ_sigma_k) * sigma_q)^2;

    % smoothed power
    M = max(1, round(double(smooth_s) * double(Fs)));
    p = abs(x).^2;
    ps = filter(ones(M,1,"single")/single(M), 1, p);

    mask0 = double(ps) > th_pow;

    % close mask
    kclose = max(1, round(double(close_s) * double(Fs)));
    mask = pa_mask_close(mask0, kclose);
    mask = logical(mask(:));

    % connected components
    d = diff([false; mask; false]);
    starts = find(d == 1);
    ends   = find(d == -1) - 1;

    % length filter
    if min_comp_s > 0 && ~isempty(starts)
        min_len = max(1, round(double(min_comp_s) * double(Fs)));
        keep = (ends - starts + 1) >= min_len;
        starts = starts(keep);
        ends   = ends(keep);
    end

    % train-span mask
    train_mask = false(W,1);
    if ~isempty(starts)
        a = starts(1);
        b = ends(end);
        if b >= a
            train_mask(a:b) = true;
        end
    end

    out = struct();
    out.mask       = mask;
    out.duty_frac  = mean(mask);
    out.starts     = starts(:);
    out.ends       = ends(:);
    out.train_mask = train_mask;
    out.train_frac = mean(train_mask);
    out.th_pow     = th_pow;
    out.ps         = ps;
end