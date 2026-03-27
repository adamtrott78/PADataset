function rx_pilot_all_pas_usrp_v02_sync(ip, fc_hz, rx_gain_db, rx_ant)
%RX_PILOT_ALL_PAS_USRP_V02_SYNC Sync-per-window RX capture.
% Usage:
%   rx_pilot_all_pas_usrp_v02_sync("192.168.10.2", 2.437e9, 10, "TX/RX");

Fs = 12e6;
W  = 400000;
session_id = 1;
tape_id = 1;

mcr = 100e6;
decim = round(mcr/Fs);

frameLen = 100000;
assert(mod(W,frameLen)==0, "W must be divisible by frameLen.");

syncLen = 20000;
syncAmp = 0.35;
sync = make_sync_bpsk(syncLen, syncAmp);

guardFrames = 2;
guardN = guardFrames * frameLen;

data_root = fullfile("pilot_out_v01","data");
PAs = ["PA8","PA2","PA3","PA4"];

out_root = fullfile("ota_rx_out_v02");
out_data = fullfile(out_root,"data");
if ~exist(out_data,"dir"), mkdir(out_data); end

% Load TX meta only for window_id ordering/counts
txN = struct(); txIDs = struct();
for pa = PAs
    f = fullfile(data_root, sprintf("pilot_S%02d_%s.mat", session_id, pa));
    S = load(f,"meta","Xsig_all");
    N = size(S.Xsig_all,2);
    ids = arrayfun(@(m)m.window_id, S.meta);
    ids = sort(ids,"ascend");
    txN.(char(pa)) = N;
    txIDs.(char(pa)) = ids;
end

fprintf("RX plan: PA2=%d, PA3=%d, PA4=%d, PA8=%d windows\n", ...
    txN.PA2, txN.PA3, txN.PA4, txN.PA8);

rx = comm.SDRuReceiver( ...
    "Platform","N200/N210/USRP2", ...
    "IPAddress", ip, ...
    "CenterFrequency", fc_hz, ...
    "Gain", rx_gain_db, ...
    "MasterClockRate", mcr, ...
    "DecimationFactor", decim, ...
    "SamplesPerFrame", frameLen, ...
    "OutputDataType","single", ...
    "ChannelMapping", 1);

if nargin >= 4 && ~isempty(rx_ant) && isprop(rx,"Antenna")
    rx.Antenna = rx_ant;
end

fprintf("RX PILOT v02 | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | Fs=%.3f MS/s | frameLen=%d | ant=%s\n", ...
    ip, fc_hz/1e9, rx_gain_db, Fs/1e6, frameLen, string(rx_ant));

stash = complex(zeros(0,1,"single"), zeros(0,1,"single"));
overruns = 0;
g_samp = int64(0);

    function pull_frame()
        [y,len,ov] = rx(); %#ok<ASGLU>
        if ov, overruns = overruns + 1; end
        if len>0
            y = y(1:len);
            stash = [stash; y]; %#ok<AGROW>
            g_samp = g_samp + int64(len);
        end
    end

    function xN = readN(N)
        while numel(stash) < N
            pull_frame();
        end
        xN = stash(1:N);
        stash = stash(N+1:end);
    end

% ---------- ALIGN: find sync start in a buffer ----------
fprintf("ALIGN: buffering...\n");
while numel(stash) < 10*frameLen
    pull_frame();
end
buf = stash(1:10*frameLen);   % 50 ms buffer

[k0, peak, ratio] = find_sync(buf, sync, Fs);
if isempty(k0)
    release(rx);
    error("ALIGN failed: sync not found. (peak too low)");
end

% Drop everything before sync start so we're frame-aligned to TX's sync frame
stash = buf(k0:end);
fprintf("ALIGN OK: k0=%d | peak=%.3f | ratio=%.3f | overruns=%d\n", k0, peak, ratio, overruns);

% ---------- CAPTURE ----------
for pa = PAs
    N = txN.(char(pa));
    Xrx_all = complex(zeros(W, N, "single"), zeros(W, N, "single"));
    meta_rx = repmat(struct(), 1, N);

    fprintf("CAPTURE %s (%d windows)\n", pa, N);

    for i = 1:N
        tx_win_id = txIDs.(char(pa))(i);

        % 1) read sync frame
        xs = readN(frameLen);
        [~, pk, rr] = find_sync(xs, sync, Fs);
        pwr = mean(abs(double(xs)).^2);

        % 2) read payload window
        xw = readN(W);
        Xrx_all(:,i) = xw;

        % 3) discard guard
        readN(guardN);

        meta_rx(i).schema_version = pa_get_nested(pa_load_cfg("starter.json"),"schema_version");
        meta_rx(i).session_id = session_id;
        meta_rx(i).tape_id = tape_id;
        meta_rx(i).segment_id = 0;
        meta_rx(i).window_id = tx_win_id;
        meta_rx(i).pa_type = char(pa);
        meta_rx(i).fs_hz = Fs;
        meta_rx(i).window_length_s = W/Fs;
        meta_rx(i).rx_overrun_count_total = int64(overruns);
        meta_rx(i).sync_peak = pk;
        meta_rx(i).sync_ratio = rr;
        meta_rx(i).sync_frame_meanP = pwr;

        if mod(i,25)==0 || i==N
            fprintf("  %s %d/%d | sync_peak=%.3f ratio=%.3f | syncP=%.3e | overruns=%d\n", ...
                pa, i, N, pk, rr, pwr, overruns);
        end

        % If overruns happen, you should stop and re-run — your sample stream is no longer reliable
        if overruns > 0
            warning("RX overrun occurred; stream integrity compromised. Consider re-running with lower Fs or larger frameLen.");
        end
    end

    out_file = fullfile(out_data, sprintf("ota_rx_S%02d_%s.mat", session_id, pa));
    save(out_file, "Xrx_all", "meta_rx", "-v7");
    fprintf("Saved %s\n", out_file);
end

release(rx);
fprintf("RX DONE | total_overruns=%d\n", overruns);

end

function [k0, peak, ratio] = find_sync(x, sync, Fs)
% Find sync start via decimated FFT correlation for speed.
% Returns k0 (1-based index into x), peak corr value, and peak/median ratio.
ds = 10;                        % coarse detect
xd = double(x(1:ds:end));
sd = double(sync(1:ds:end));

Lx = numel(xd); Ls = numel(sd);
nfft = 2^nextpow2(Lx + Ls - 1);

X = fft(xd, nfft);
S = fft(conj(flipud(sd)), nfft);
c = abs(ifft(X .* S));          % correlation magnitude

% valid region where full overlap exists
c = c(Ls:(Ls+Lx-1));

[peak, idx] = max(c);
med = median(c) + 1e-12;
ratio = peak / med;

% threshold: tune if needed
if ratio < 25
    k0 = [];
    return;
end

k0d = idx;                      % in decimated samples
k0 = 1 + (k0d-1)*ds;            % back to full-rate approx
end

function sync = make_sync_bpsk(N, amp)
chips = lfsr_mseq_127();
bpsk = single(2*chips - 1);
rep = ceil(N/numel(bpsk));
v = repmat(bpsk, rep, 1);
v = v(1:N);
sync = amp * complex(v, zeros(N,1,"single"));
end

function bits = lfsr_mseq_127()
state = ones(7,1,'logical');
bits = false(127,1);
for k=1:127
    bits(k) = state(end);
    newb = xor(state(end), state(3));
    state = [newb; state(1:end-1)];
end
bits = single(bits);
end