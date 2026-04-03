function sync = pa_make_preambles_v03(Lpre, startAmp, beaconAmp, winAmp)
% 3 distinct 7-bit LFSR m-seqs -> BPSK -> repeated to Lpre samples.

    chips_beacon = mseq127([7 3]); % poly x^7 + x^3 + 1
    chips_start  = mseq127([7 1]); % poly x^7 + x^1 + 1
    chips_win    = mseq127([7 4]); % poly x^7 + x^4 + 1 (another tap)

    sync.beacon_preamble = beaconAmp * bpsk_repeat(chips_beacon, Lpre);
    sync.start_preamble  = startAmp  * bpsk_repeat(chips_start,  Lpre);
    sync.win_preamble    = winAmp    * bpsk_repeat(chips_win,    Lpre);
end

function v = bpsk_repeat(chips, N)
    bpsk = single(2*chips - 1);
    rep = ceil(N/numel(bpsk));
    v = repmat(bpsk, rep, 1);
    v = v(1:N);
    v = complex(v, zeros(N,1,"single"));
end

function chips = mseq127(taps)
% taps = [7 k] means feedback = xor(state(7), state(k))
    state = true(7,1);
    chips = false(127,1);
    k = taps(2);
    for i=1:127
        chips(i) = state(end);
        newb = xor(state(end), state(k));
        state = [newb; state(1:end-1)];
    end
    chips = single(chips);
end