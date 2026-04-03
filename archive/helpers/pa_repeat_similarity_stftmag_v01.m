function sim = pa_repeat_similarity_stftmag_v01(x, Fs, intervals, nfft, hop, maxlag_frames)
% Phase-robust similarity using STFT magnitude correlation over intervals.
% (Use if IQ xcorr becomes too sensitive to OTA phase/CFO effects.)

    x = x(:);
    if nargin < 4, nfft = 1024; end
    if nargin < 5, hop = 256; end
    if nargin < 6, maxlag_frames = 3; end

    if isempty(intervals) || size(intervals,1) < 2
        sim = struct("score",0,"used",size(intervals,1));
        return;
    end

    win = hann(nfft,"periodic");
    [S,~,~] = spectrogram(x, win, nfft-hop, nfft, Fs, "centered");
    M = abs(S);  % magnitude spectrogram [freq x time]

    % Convert sample intervals -> STFT frame intervals
    frame_of = @(k) max(1, floor((k-1)/hop) + 1);
    ivf = [frame_of(intervals(:,1)) frame_of(intervals(:,2))];

    % Take a fixed-length slice from each interval and correlate vs first
    L = min(ivf(:,2)-ivf(:,1)+1);
    L = max(8, min(L, 40));  % keep compute bounded

    ref = M(:, ivf(1,1):ivf(1,1)+L-1);
    ref = ref - mean(ref(:));
    ref = ref / (norm(ref(:)) + 1e-12);

    scores = zeros(size(ivf,1)-1,1);
    for i = 2:size(ivf,1)
        A = M(:, ivf(i,1):ivf(i,1)+L-1);
        A = A - mean(A(:));
        A = A / (norm(A(:)) + 1e-12);
        % simple dot similarity (you can add lag search later)
        scores(i-1) = max(-1,min(1, sum(ref(:).*A(:))));
    end

    sim = struct("score", mean(scores), "used", size(ivf,1), "pairwise", scores);
end