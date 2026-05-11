function [best_ratio, best_k] = preamble_best_ratio_in_frame(x, pre)
    x = double(x(:));
    pre = double(pre(:));

    N = numel(pre);
    M = numel(x);
    L = M - N + 1;

    if L < 1
        best_ratio = 0;
        best_k = [];
        return;
    end

    nfft = 2^nextpow2(M + N - 1);
    C = ifft(fft(x, nfft) .* fft(conj(flipud(pre)), nfft));

    % valid start positions only
    c = abs(C(N : N + M - 1));
    c = c(1:L);

    [pk, best_k] = max(c);
    med = median(c) + 1e-12;
    best_ratio = pk / med;
end