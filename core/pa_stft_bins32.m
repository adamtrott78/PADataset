function B = pa_stft_bins32(x, nfft, hop, nbins)
    win = hann(nfft, "periodic");
    nover = nfft - hop;
    [S,~] = spectrogram(x, win, nover, nfft, 1, "centered"); % Fs cancels for bins
    P = abs(S).^2;                                          % [nfft x T]
    nper = nfft / nbins;
    if mod(nfft, nbins) ~= 0, error("nfft must be divisible by nbins"); end
    T = size(P,2);
    B = zeros(nbins, T);
    for b = 1:nbins
        r0 = (b-1)*nper + 1;
        r1 = b*nper;
        B(b,:) = sum(P(r0:r1,:), 1);
    end
end