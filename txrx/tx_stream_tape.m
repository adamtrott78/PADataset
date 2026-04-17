function tx_stream_tape(protocol, ip, fc_hz, gain_db, tx_ant, dataset_id_or_tape_file, shard_id)
%TX_STREAM_TAPE Beacon mode -> SPACE -> stream one protocol tx tape or shard.
%
% Usage:
%   tx_stream_tape("wifi", "192.168.10.2", 2.437e9, 20, "TX/RX")
%   tx_stream_tape("wifi", "192.168.10.2", 2.437e9, 20, "TX/RX", "high_run01", 1)
%   tx_stream_tape("bluetooth", "192.168.10.2", 2.437e9, 20, "TX/RX", "high_run01", 1)
%   tx_stream_tape("zigbee", "192.168.10.2", 2.437e9, 20, "TX/RX", "high_run01", 1)
%
% New direct shard usage:
%   tx_stream_tape(protocol, ip, fc_hz, gain_db, tx_ant, dataset_id, shard_id)
% where dataset_id may be either:
%   "high_run01"          -> expands to "<protocol>_high_run01"
%   "wifi_high_run01"     -> used as-is
%
% Backward-compatible old usage:
%   tx_stream_tape("192.168.10.2", 2.437e9, 20, "TX/RX")
% which defaults protocol="wifi".
%
% Backward-compatible override usage:
%   tx_stream_tape(protocol, ip, fc_hz, gain_db, tx_ant, tape_file_override)

    % --------- backward-compatible argument handling ---------
    if nargin >= 1 && ~isempty(protocol)
        protocol_s = string(protocol);
    else
        protocol_s = "wifi";
    end

    if nargin >= 1 && ~ismember(protocol_s, ["wifi","bluetooth","zigbee"])
        % old signature: tx_stream_tape(ip, fc_hz, gain_db, tx_ant)
        tx_ant  = gain_db;
        gain_db = fc_hz;
        fc_hz   = ip;
        ip      = protocol;
        protocol_s = "wifi";
        dataset_id_or_tape_file = [];
        shard_id = [];
    end

    if nargin < 4
        error("Usage: tx_stream_tape(protocol, ip, fc_hz, gain_db, tx_ant, dataset_id, shard_id)");
    end

    if nargin < 5
        tx_ant = [];
    end

    if nargin < 6
        dataset_id_or_tape_file = [];
    end

    if nargin < 7
        shard_id = [];
    end

    protocol_s = string(protocol_s);
    assert(any(protocol_s == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    R = pa_protocol_roots(protocol_s);
    addpath(R.txrx);

    [tape_file, dataset_full, shard_num] = resolve_tx_tape_file(protocol_s, R, dataset_id_or_tape_file, shard_id);

    S = load(tape_file, "tx_tape", "tx_params", "sync");

    tx_tape = S.tx_tape;
    tx_tape = tx_tape(:);
    tx_tape = complex(single(real(tx_tape)), single(imag(tx_tape))); % ensure complex single

    p = S.tx_params;
    sync = S.sync;

    mcr = 100e6;
    interp = round(mcr / 12e6); % user-friendly default, but print actual
    Fs = mcr / interp;

    if ~isempty(dataset_full)
        fprintf("TX | protocol=%s | dataset=%s | shard=%03d | file=%s\n", ...
            protocol_s, dataset_full, shard_num, tape_file);
    else
        fprintf("TX | protocol=%s | file=%s\n", protocol_s, tape_file);
    end
    fprintf("TX | protocol=%s | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | MCR=%.0f | interp=%d | Fs=%.6f MS/s\n", ...
        protocol_s, ip, fc_hz/1e9, gain_db, mcr, interp, Fs/1e6);

    tx = comm.SDRuTransmitter( ...
        "Platform","N200/N210/USRP2", ...
        "IPAddress", ip, ...
        "CenterFrequency", fc_hz, ...
        "Gain", gain_db, ...
        "MasterClockRate", mcr, ...
        "InterpolationFactor", interp, ...
        "ChannelMapping", 1);

    if ~isempty(tx_ant) && isprop(tx,"Antenna")
        tx.Antenna = tx_ant;
    end

    % --------- beacon frame ---------
    beacon = complex(zeros(p.frameLen,1,"single"), zeros(p.frameLen,1,"single"));

    bp = single(sync.beacon_preamble(:));
    bp = bp(1:p.Lpre);

    % force complex beacon so tx locks to complex on first call
    bp_c = bp .* complex(single(1/sqrt(2)), single(1/sqrt(2)));
    beacon(1:p.Lpre) = bp_c;

    assert(~isreal(beacon), "Beacon is still real to tx(); preamble needs nonzero Q.");

    % --------- UI ---------
    st = struct("go",false,"quit",false);
    fig = figure("Name","TX Tape","Color","w","KeyPressFcn",@onkey);
    uicontrol("Style","text", ...
        "String",sprintf("Protocol: %s | Beacon running. Press SPACE to start tape. Press Q to quit.", protocol_s), ...
        "Units","normalized","Position",[0.05 0.4 0.9 0.2], ...
        "FontSize",14,"BackgroundColor","w");

    underruns = 0;
    t0 = tic;
    n_beacon = 0;

    try
        % --------- BEACON MODE ---------
        while ~st.go && ~st.quit
            underruns = underruns + double(tx(beacon));
            n_beacon = n_beacon + 1;

            if toc(t0) > 1.0
                fprintf("BEACON | protocol=%s | frames=%d | underruns=%d\n", ...
                    protocol_s, n_beacon, underruns);
                t0 = tic;
            end
            drawnow limitrate;
        end

        if st.quit
            release(tx);
            close(fig);
            fprintf("TX quit.\n");
            return;
        end

        fprintf("TX: SPACE pressed -> streaming %s tx_tape (%d samples)\n", protocol_s, numel(tx_tape));

        % --------- STREAM TAPE ---------
        N = numel(tx_tape);
        frameLen = p.frameLen;
        assert(mod(N, frameLen) == 0, "tx_tape must be multiple of frameLen");

        nFrames = N / frameLen;
        t1 = tic;
        for k = 1:nFrames
            a = (k-1)*frameLen + 1;
            b = a + frameLen - 1;
            underruns = underruns + double(tx(tx_tape(a:b)));

            if mod(k,100) == 0 || k == nFrames
                fprintf("TX | protocol=%s | %d/%d frames | underruns=%d | elapsed=%.1fs\n", ...
                    protocol_s, k, nFrames, underruns, toc(t1));
            end
        end

        release(tx);
        close(fig);
        fprintf("TX DONE | protocol=%s | underruns=%d\n", protocol_s, underruns);

    catch ME
        try, release(tx); end
        try, close(fig); end
        rethrow(ME);
    end

    function onkey(~, ev)
        if strcmp(ev.Key,"space"), st.go = true; end
        if strcmp(ev.Key,"q"),     st.quit = true; end
    end
end


function [tape_file, dataset_full, shard_num] = resolve_tx_tape_file(protocol_s, R, dataset_id_or_tape_file, shard_id)
    dataset_full = "";
    shard_num = [];

    if isempty(dataset_id_or_tape_file)
        tape_file = fullfile(R.txrx_tapes_digital, "tx_tape.mat");
        return;
    end

    arg6 = string(dataset_id_or_tape_file);
    if strlength(arg6) == 0
        tape_file = fullfile(R.txrx_tapes_digital, "tx_tape.mat");
        return;
    end

    if endsWith(lower(arg6), ".mat")
        tape_file = char(arg6);
        return;
    end

    if isempty(shard_id)
        error("When dataset_id is provided, shard_id is also required.");
    end

    shard_num = validate_shard_id(shard_id);
    dataset_full = normalize_dataset_id(protocol_s, arg6);
    tape_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_tape_shard_%03d.mat", shard_num));

    if ~isfile(tape_file)
        error("TX tape file not found: %s", tape_file);
    end
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
