function tx_pilot_all_pas_usrp_v02_sync(ip, fc_hz, gain_db, tx_ant)
%TX_PILOT_ALL_PAS_USRP_V02_SYNC Sync-per-window TX, frame-aligned.
% Usage:
%   tx_pilot_all_pas_usrp_v02_sync("192.168.10.2", 2.437e9, 20, "TX/RX");

Fs = 12e6;
W  = 400000;
session_id = 1;

mcr = 100e6;
interp = round(mcr/Fs);

frameLen = 100000;
assert(mod(W,frameLen)==0, "W must be divisible by frameLen.");

syncLen = 20000;                      % 1 ms inside first frame
syncAmp = 0.35;                       % headroom
sync = make_sync_bpsk(syncLen, syncAmp);

syncFrame = complex(zeros(frameLen,1,"single"), zeros(frameLen,1,"single"));
syncFrame(1:syncLen) = sync;

guardFrames = 2;                      % 10 ms guard (2*5ms)
zframe = complex(zeros(frameLen,1,"single"), zeros(frameLen,1,"single"));

tx_scale = 0.35;                      % global-ish scale per PA (not per window)
data_root = fullfile("pilot_out_v01","data");
PAs = ["PA8","PA2","PA3","PA4"];

tx = comm.SDRuTransmitter( ...
    "Platform","N200/N210/USRP2", ...
    "IPAddress", ip, ...
    "CenterFrequency", fc_hz, ...
    "Gain", gain_db, ...
    "MasterClockRate", mcr, ...
    "InterpolationFactor", interp, ...
    "ChannelMapping", 1);

if nargin >= 4 && ~isempty(tx_ant) && isprop(tx,"Antenna")
    tx.Antenna = tx_ant;
end

fprintf("TX PILOT v02 | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | Fs=%.3f MS/s | frameLen=%d\n", ...
    ip, fc_hz/1e9, gain_db, Fs/1e6, frameLen);

underruns = 0;
win_total = 0;

try
    % preroll
    for k=1:10, underruns = underruns + double(tx(zframe)); end

    for pa = PAs
        pa_file = fullfile(data_root, sprintf("pilot_S%02d_%s.mat", session_id, pa));
        S = load(pa_file,"Xsig_all","meta");
        X = S.Xsig_all;
        meta = S.meta;

        % sort by window_id
        ids = arrayfun(@(m)m.window_id, meta);
        [~,ord] = sort(ids,"ascend");
        X = X(:,ord);
        meta = meta(ord);

        % per-PA max for consistent scaling (not per-window)
        mx_pa = max(abs(X(:)));
        if mx_pa < 1e-12, mx_pa = 1; end
        pa_gain = tx_scale / mx_pa;

        N = size(X,2);
        fprintf("PA=%s | windows=%d | pa_gain=%.3g | file=%s\n", pa, N, pa_gain, pa_file);

        for i = 1:N
            win_total = win_total + 1;

            underruns = underruns + double(tx(syncFrame));

            xw = pa_gain * X(:,i);

            for k = 1:(W/frameLen)
                a = (k-1)*frameLen + 1;
                b = a + frameLen - 1;
                underruns = underruns + double(tx(xw(a:b)));
            end

            for g = 1:guardFrames
                underruns = underruns + double(tx(zframe));
            end

            if mod(i,25)==0 || i==N
                fprintf("  %s %d/%d | total_win=%d | underruns=%d\n", pa, i, N, win_total, underruns);
            end
        end
    end

    for k=1:10, underruns = underruns + double(tx(zframe)); end
    release(tx);
    fprintf("TX DONE | total_windows=%d | underruns=%d\n", win_total, underruns);

catch ME
    release(tx);
    rethrow(ME);
end

end

function sync = make_sync_bpsk(N, amp)
% Simple 7-bit LFSR m-seq mapped to BPSK, repeated to length N.
chips = lfsr_mseq_127();                % length 127, bits in {0,1}
bpsk = single(2*chips - 1);             % -> {-1,+1}
rep = ceil(N/numel(bpsk));
v = repmat(bpsk, rep, 1);
v = v(1:N);
sync = amp * complex(v, zeros(N,1,"single"));
end

function bits = lfsr_mseq_127()
% 7-bit LFSR, primitive poly example: x^7 + x^3 + 1 (taps 7 and 3)
state = ones(7,1,'logical');            % nonzero seed
bits = false(127,1);
for k=1:127
    bits(k) = state(end);
    newb = xor(state(end), state(3));   % taps
    state = [newb; state(1:end-1)];
end
bits = single(bits);
end