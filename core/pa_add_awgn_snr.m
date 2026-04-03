function y = pa_add_awgn_snr(x, snr_db, rs)
    sigma = 10^(-double(snr_db)/20);
    w = (sigma/sqrt(2)) * (randn(rs, size(x), "single") + 1j*randn(rs, size(x), "single"));
    y = x + w;
end