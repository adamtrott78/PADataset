function [x, prep] = pa_preprocess_ota_basic(x)
% DC remove + RMS normalize (store scale)
    x = x(:);
    mu = mean(x);
    x = x - mu;
    r = pa_rms(x);
    if ~isfinite(r), r = 0; end
    sc = 1 / (double(r) + 1e-12);
    x = x * single(sc);
    prep = struct("dc_mean",mu,"rms",r,"scale",sc);
end