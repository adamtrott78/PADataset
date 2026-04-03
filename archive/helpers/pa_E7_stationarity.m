function E7 = pa_E7_stationarity(B)
%PA_E7_STATIONARITY Energy-aware stationarity score.
% B: [nbins x T] linear power bins from pa_stft_bins32
% Shape term: cosine similarity of L2-normalized bin vectors (as specified)
% Energy term: penalizes large total-energy changes between frames (burstiness)

    epsv = 1e-12;

    % Shape term (cosine of L2-normalized vectors)
    N = sqrt(sum(B.^2, 1)) + epsv;
    Bh = B ./ N;
    c_shape = sum(Bh(:,1:end-1) .* Bh(:,2:end), 1);

    % Energy term (scale-sensitive, parameter-free)
    E = sum(B, 1) + epsv;
    c_energy = 1 - abs(E(2:end) - E(1:end-1)) ./ (E(2:end) + E(1:end-1));

    % Combined stationarity
    E7 = mean(c_shape .* c_energy);
end