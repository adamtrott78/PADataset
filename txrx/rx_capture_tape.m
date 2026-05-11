function rx_capture_tape(protocol, ip, fc_hz, rx_gain_db, rx_ant, dataset_id_or_spec_file, shard_id_or_out_file)
%RX_CAPTURE_TAPE Monitor beacon -> detect START_SYNC -> record one shard into RAM.
%
% Usage:
%   rx_capture_tape("wifi", "192.168.10.3", 2.437e9, 10, "TX/RX")
%   rx_capture_tape("wifi", "192.168.10.3", 2.437e9, 10, "TX/RX", "high_run01", 1)
%   rx_capture_tape("bluetooth", "192.168.10.3", 2.437e9, 10, "TX/RX", "high_run01", 1)
%   rx_capture_tape("zigbee", "192.168.10.3", 2.437e9, 10, "TX/RX", "high_run01", 1)
%
% New direct shard usage:
%   rx_capture_tape(protocol, ip, fc_hz, rx_gain_db, rx_ant, dataset_id, shard_id)
% where dataset_id may be either:
%   "high_run01"          -> expands to "<protocol>_high_run01"
%   "wifi_high_run01"     -> used as-is
%
% Backward-compatible old usage:
%   rx_capture_tape("192.168.10.3", 2.437e9, 10, "TX/RX")
% which defaults protocol="wifi".
%
% Backward-compatible override usage:
%   rx_capture_tape(protocol, ip, fc_hz, rx_gain_db, rx_ant, tx_spec_file_override, out_file_override)

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
        dataset_id_or_spec_file = [];
        shard_id_or_out_file = [];
    end

    if nargin < 4
        error("Usage: rx_capture_tape(protocol, ip, fc_hz, rx_gain_db, rx_ant, dataset_id, shard_id)");
    end

    if nargin < 5
        rx_ant = [];
    end

    if nargin < 6
        dataset_id_or_spec_file = [];
    end

    if nargin < 7
        shard_id_or_out_file = [];
    end

    protocol_s = string(protocol_s);
    assert(any(protocol_s == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    R = pa_protocol_roots(protocol_s);
    addpath(R.txrx);

    [spec_file, out_file, dataset_full, shard_num] = resolve_rx_files(protocol_s, R, dataset_id_or_spec_file, shard_id_or_out_file);

    S = load(spec_file, "tx_spec");
    tx_spec = S.tx_spec;
    p = tx_spec.tx_params;
    sync = tx_spec.sync;

    out_dir = fileparts(out_file);
    if ~exist(out_dir, 'dir')
        mkdir(out_dir);
    end

    mcr = 100e6;
    decim = round(mcr / 12e6); % user-friendly default, but print actual
    Fs = mcr / decim;

    if ~isempty(dataset_full)
        fprintf("RX | protocol=%s | dataset=%s | shard=%03d | spec=%s\n", ...
            protocol_s, dataset_full, shard_num, spec_file);
        fprintf("RX | protocol=%s | dataset=%s | shard=%03d | out=%s\n", ...
            protocol_s, dataset_full, shard_num, out_file);
    else
        fprintf("RX | protocol=%s | spec=%s\n", protocol_s, spec_file);
        fprintf("RX | protocol=%s | out=%s\n", protocol_s, out_file);
    end
    fprintf("RX | protocol=%s | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | MCR=%.0f | decim=%d | Fs=%.6f MS/s\n", ...
        protocol_s, ip, fc_hz/1e9, rx_gain_db, mcr, decim, Fs/1e6);

    % ---------- precompute capture size and allocate capture RAM early ----------
    Ncap = double(p.N_start_frames)*double(p.frameLen) + ...
           double(height(tx_spec.tx_index))*(double(p.frameLen) + double(p.W) + double(p.guardN)) + ...
           double(p.N_stop_frames)*double(p.frameLen);

    bytes_per_complex_single = 8; % 2 x single = 8 bytes total
    cap_gib = (double(Ncap) * bytes_per_complex_single) / (1024^3);

    fprintf("RX PREALLOC | protocol=%s | Ncap=%d samples | est_mem=%.2f GiB\n", ...
        protocol_s, Ncap, cap_gib);

    x_tape = complex(zeros(Ncap,1,"single"), zeros(Ncap,1,"single"));

    fprintf("RX PREALLOC DONE | protocol=%s | capture buffer ready before monitor.\n", ...
        protocol_s);

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

    % ---------- stash buffer ----------
    stash_cap = 20 * p.frameLen;
    stash = complex(zeros(stash_cap,1,"single"), zeros(stash_cap,1,"single"));
    stash_len = 0;
    overruns = 0;

    function append_stash(y)
        L = numel(y);
        need = stash_len + L;
        if need > numel(stash)
            new_cap = max(2*numel(stash), need + 4*p.frameLen);
            tmp = complex(zeros(new_cap,1,"single"), zeros(new_cap,1,"single"));
            if stash_len > 0
                tmp(1:stash_len) = stash(1:stash_len);
            end
            stash = tmp;
        end
        stash(stash_len + (1:L)) = y;
        stash_len = stash_len + L;
    end

    function pull_frame()
        [y,len,ov] = rx();
        if ov
            overruns = overruns + 1;
        end
        if len > 0
            append_stash(y(1:len));
        end
    end

    function xN = readN(N)
        while stash_len < N
            pull_frame();
        end
        xN = stash(1:N);

        rem = stash_len - N;
        if rem > 0
            stash(1:rem) = stash(N+1:stash_len);
        end
        stash_len = rem;
    end

    % ---------- monitor mode ----------
    fprintf("RX MONITOR | protocol=%s | watching beacon/start. Move antennas. TX press SPACE when ready.\n", protocol_s);

    start_thr = 20;
    consec_need = 3;
    consec = 0;

    t0 = tic;
    while true
        x = readN(p.frameLen);

        rb = pa_corr_ratio_v03(x(1:p.Lpre), sync.beacon_preamble);
        rs = pa_corr_ratio_v03(x(1:p.Lpre), sync.start_preamble);

        if rs > start_thr && rs > rb
            consec = consec + 1;
        else
            consec = 0;
        end

        if toc(t0) > 5.0
            fprintf("MON | protocol=%s | beacon=%.1f | start=%.1f | consec=%d/%d | overruns=%d\n", ...
                protocol_s, rb, rs, consec, consec_need, overruns);
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

    % realign stash to start of tx_tape
    aligned = buf(k0:end);
    stash_len = numel(aligned);
    if stash_len > numel(stash)
        new_cap = max(2*numel(stash), stash_len + 4*p.frameLen);
        stash = complex(zeros(new_cap,1,"single"), zeros(new_cap,1,"single"));
    end
    stash(1:stash_len) = aligned;

    fprintf("ALIGN OK | protocol=%s | k0=%d | ratio=%.1f | capture buffer already allocated | Ncap=%d samples.\n", ...
        protocol_s, k0, ratio, Ncap);

    % ---------- capture tape ----------
    x_tape(:) = complex(single(0), single(0));
    filled = 0;
    t1 = tic;

    % consume aligned stash once
    if stash_len > 0
        take = min(stash_len, Ncap);
        x_tape(1:take) = stash(1:take);
        filled = take;

        rem = stash_len - take;
        if rem > 0
            stash(1:rem) = stash(take+1:stash_len);
        end
        stash_len = rem;
    end

    while filled < Ncap
        [y, len, ov] = rx();
        if ov
            overruns = overruns + 1;
        end
        if len <= 0
            continue;
        end

        take = min(len, Ncap - filled);
        x_tape(filled + (1:take)) = y(1:take);
        filled = filled + take;

        if mod(filled, 100000000) == 0 || filled == Ncap
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

    save(out_file, "x_tape", "rx_cfg", "-v7.3");
    release(rx);

    fprintf("RX DONE | protocol=%s | saved tape: %s\n", protocol_s, out_file);
end


function [spec_file, out_file, dataset_full, shard_num] = resolve_rx_files(protocol_s, R, dataset_id_or_spec_file, shard_id_or_out_file)
    dataset_full = "";
    shard_num = [];

    if isempty(dataset_id_or_spec_file)
        spec_file = fullfile(R.txrx_tapes_digital, "tx_spec.mat");
        out_file = fullfile(R.txrx_tapes_ota, "ota_tape_S01.mat");
        return;
    end

    arg6 = string(dataset_id_or_spec_file);
    if strlength(arg6) == 0
        spec_file = fullfile(R.txrx_tapes_digital, "tx_spec.mat");
        out_file = fullfile(R.txrx_tapes_ota, "ota_tape_S01.mat");
        return;
    end

    if endsWith(lower(arg6), ".mat")
        spec_file = char(arg6);
        if isempty(shard_id_or_out_file)
            out_file = fullfile(R.txrx_tapes_ota, "ota_tape_S01.mat");
        else
            out_file = char(string(shard_id_or_out_file));
        end
        if ~isfile(spec_file)
            error("TX spec file not found: %s", spec_file);
        end
        return;
    end

    if isempty(shard_id_or_out_file) || ~(isnumeric(shard_id_or_out_file) || islogical(shard_id_or_out_file))
        error([ ...
            "For direct shard usage, call rx_capture_tape(protocol, ip, fc_hz, rx_gain_db, rx_ant, dataset_id, shard_id). " ...
            "For override usage, pass tx_spec_file_override and out_file_override."]);
    end

    shard_num = validate_shard_id(shard_id_or_out_file);
    dataset_full = normalize_dataset_id(protocol_s, arg6);
    spec_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_spec_shard_%03d.mat", shard_num));
    out_file = fullfile(R.txrx_tapes_ota, char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_num));

    if ~isfile(spec_file)
        error("TX spec file not found: %s", spec_file);
    end
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


function [snr_db, sig_pow, noise_pow] = estimate_preamble_snr(x, pre)
    x = double(x(:));
    pre = double(pre(:));

    N = min(numel(x), numel(pre));
    x = x(1:N);
    pre = pre(1:N);

    % Least-squares complex gain fit: x ~= alpha * pre
    den = sum(abs(pre).^2) + eps;
    alpha = (pre' * x) / den;

    s_hat = alpha * pre;
    err = x - s_hat;

    sig_pow = mean(abs(s_hat).^2);
    noise_pow = mean(abs(err).^2) + eps;
    snr_db = 10 * log10(sig_pow / noise_pow);
end


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


function dataset_full = normalize_dataset_id(protocol_s, dataset_id)
    dataset_id = string(dataset_id);
    prefix = protocol_s + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
    else
        dataset_full = prefix + dataset_id;
    end
end


function shard_num = validate_shard_id(shard_id)
    if ~(isnumeric(shard_id) || islogical(shard_id)) || numel(shard_id) ~= 1 || ~isfinite(double(shard_id))
        error("shard_id must be a finite scalar integer.");
    end
    shard_num = double(shard_id);
    if abs(shard_num - round(shard_num)) > 0 || shard_num < 1
        error("shard_id must be a positive integer.");
    end
    shard_num = round(shard_num);
end