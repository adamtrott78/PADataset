function rx_capture_tape(protocol, ip, fc_hz, rx_gain_db, rx_ant)
%RX_CAPTURE_TAPE Monitor beacon -> detect START_SYNC -> record full tx_tape into RAM.
%
% Usage:
%   rx_capture_tape("wifi", "192.168.10.3", 2.437e9, 10, "TX/RX")
%   rx_capture_tape("bluetooth", "192.168.10.3", 2.437e9, 10, "TX/RX")
%   rx_capture_tape("zigbee", "192.168.10.3", 2.437e9, 10, "TX/RX")
%
% Backward-compatible old usage:
%   rx_capture_tape("192.168.10.3", 2.437e9, 10, "TX/RX")
% which defaults protocol="wifi".

    % --------- backward-compatible argument handling ---------
    if nargin >= 1 && ~isempty(protocol)
        protocol_s = string(protocol);
    else
        protocol_s = "wifi";
    end

    if nargin >= 1 && ~ismember(protocol_s, ["wifi","bluetooth","zigbee"])
        % old signature: rx_capture_tape(ip, fc_hz, rx_gain_db, rx_ant)
        rx_ant     = rx_gain_db;
        rx_gain_db = fc_hz;
        fc_hz      = ip;
        ip         = protocol;
        protocol_s = "wifi";
    end

    if nargin < 4
        error("Usage: rx_capture_tape(protocol, ip, fc_hz, rx_gain_db, rx_ant)");
    end
    if nargin < 5
        rx_ant = [];
    end

    protocol_s = string(protocol_s);
    assert(any(protocol_s == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    P = pa_paths();
    addpath(P.txrx);

    tape_file = fullfile(P.txrx_tapes_digital, char(protocol_s), "tx_tape.mat");
    S = load(tape_file, "tx_tape", "tx_params", "sync");
    tx_tape = S.tx_tape;
    p = S.tx_params;
    sync = S.sync;

    out_root = fullfile(P.txrx_tapes_ota, char(protocol_s));
    if ~exist(out_root,"dir"), mkdir(out_root); end

    mcr = 100e6;
    decim = round(mcr / 12e6); % user-friendly default, but print actual
    Fs = mcr / decim;

    fprintf("RX | protocol=%s | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | MCR=%.0f | decim=%d | Fs=%.6f MS/s\n", ...
        protocol_s, ip, fc_hz/1e9, rx_gain_db, mcr, decim, Fs/1e6);

    rx = comm.SDRuReceiver( ...
        "Platform","N200/N210/USRP2", ...
        "IPAddress", ip, ...
        "CenterFrequency", fc_hz, ...
        "Gain", rx_gain_db, ...
        "MasterClockRate", mcr, ...
        "DecimationFactor", decim, ...
        "SamplesPerFrame", p.frameLen, ...
        "OutputDataType","single", ...
        "ChannelMapping", 1);

    if ~isempty(rx_ant) && isprop(rx,"Antenna")
        rx.Antenna = rx_ant;
    end

    stash = complex(zeros(0,1,"single"), zeros(0,1,"single"));
    overruns = 0;

    function pull_frame()
        [y,len,ov] = rx(); %#ok<ASGLU>
        if ov, overruns = overruns + 1; end
        if len > 0
            y = y(1:len);
            stash = [stash; y]; %#ok<AGROW>
        end
    end

    function xN = readN(N)
        while numel(stash) < N
            pull_frame();
        end
        xN = stash(1:N);
        stash = stash(N+1:end);
    end

    % ---------- monitor mode ----------
    fprintf("RX MONITOR | protocol=%s | watching beacon/start. Move antennas. TX press SPACE when ready.\n", protocol_s);

    start_thr = 25;
    consec_need = 3;
    consec = 0;

    t0 = tic;
    while true
        x = readN(p.frameLen);
        pow = mean(abs(double(x)).^2);

        rb = pa_corr_ratio_v03(x(1:p.Lpre), sync.beacon_preamble);
        rs = pa_corr_ratio_v03(x(1:p.Lpre), sync.start_preamble);

        if rs > start_thr && rs > rb
            consec = consec + 1;
        else
            consec = 0;
        end

        if toc(t0) > 0.5
            fprintf("MON | protocol=%s | pow=%.3e | beacon=%.1f | start=%.1f | consec=%d/%d | overruns=%d\n", ...
                protocol_s, pow, rb, rs, consec, consec_need, overruns);
            t0 = tic;
        end

        if consec >= consec_need
            fprintf("START_SYNC detected. Fine-aligning...\n");
            break;
        end
    end

    % ---------- fine align within a small buffer ----------
    buf = [x; readN(2*p.frameLen)]; % 3 frames total including last x
    [k0, ratio] = find_preamble_in_buffer(buf, sync.start_preamble);
    if isempty(k0)
        release(rx);
        error("Fine align failed (no start preamble peak).");
    end
    stash = buf(k0:end); % align stash to start of tx_tape

    fprintf("ALIGN OK | protocol=%s | k0=%d | ratio=%.1f | now capturing %d samples into RAM...\n", ...
        protocol_s, k0, ratio, numel(tx_tape));

    % ---------- capture tape ----------
    Ncap = numel(tx_tape);
    x_tape = complex(zeros(Ncap,1,"single"), zeros(Ncap,1,"single"));

    filled = 0;
    t1 = tic;
    while filled < Ncap
        need = min(p.frameLen, Ncap-filled);
        xx = readN(need);
        x_tape(filled+(1:need)) = xx;
        filled = filled + need;

        if mod(filled, 50*p.frameLen) == 0 || filled == Ncap
            fprintf("CAPTURE | protocol=%s | %d/%d samples (%.1f%%) | overruns=%d | elapsed=%.1fs\n", ...
                protocol_s, filled, Ncap, 100*filled/Ncap, overruns, toc(t1));
        end
    end

    rx_cfg = struct();
    rx_cfg.protocol = char(protocol_s);
    rx_cfg.ip = ip;
    rx_cfg.fc_hz = fc_hz;
    rx_cfg.rx_gain_db = rx_gain_db;
    rx_cfg.mcr = mcr;
    rx_cfg.decim = decim;
    rx_cfg.Fs = Fs;
    rx_cfg.frameLen = p.frameLen;
    rx_cfg.capture_len = Ncap;
    rx_cfg.overruns = overruns;
    rx_cfg.capture_time = datetime("now");

    out_file = fullfile(out_root, "ota_tape_S01.mat");
    save(out_file, "x_tape", "rx_cfg", "-v7.3");
    release(rx);

    fprintf("RX DONE | protocol=%s | saved tape: %s\n", protocol_s, out_file);
end


function [k0, best_ratio] = find_preamble_in_buffer(buf, pre)
    buf = double(buf(:));
    pre = double(pre(:));

    nfft = 2^nextpow2(numel(buf)+numel(pre)-1);
    C = ifft(fft(buf,nfft) .* fft(conj(flipud(pre)),nfft));
    c = abs(C(numel(pre):numel(pre)+numel(buf)-1));

    [pk, idx] = max(c);
    med = median(c) + 1e-12;
    best_ratio = pk / med;

    if best_ratio < 20
        k0 = [];
    else
        k0 = idx;
    end
end