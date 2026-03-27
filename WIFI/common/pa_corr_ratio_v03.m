function ratio = pa_corr_ratio_v03(x, pre)
% correlation peak / median ratio (magnitude), fast enough for monitor mode.

    x = double(x(:));
    pre = double(pre(:));

    nfft = 2^nextpow2(numel(x)+numel(pre)-1);
    c = abs(ifft(fft(x,nfft) .* fft(conj(flipud(pre)),nfft)));
    c = c(numel(pre):numel(pre)+numel(x)-1);

    pk = max(c);
    med = median(c) + 1e-12;
    ratio = pk/med;
end