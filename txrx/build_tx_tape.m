function build_tx_tape(protocol)
%BUILD_TX_TAPE Build a single continuous tx_tape with start-sync + per-window headers.
%
% Usage:
%   build_tx_tape
%   build_tx_tape("wifi")
%   build_tx_tape("bluetooth")
%   build_tx_tape("zigbee")
%
% Output:
%   PADataset/txrx/tapes/digital/<protocol>/tx_tape.mat
%
% Requires:
%   PADataset/data/<protocol>/digital/pilot/pilot_S01_PA2.mat ... etc (Xsig_all, meta)

    if nargin < 1 || isempty(protocol)
        protocol = "wifi";
    end
    protocol = string(protocol);
    assert(any(protocol == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    P = pa_paths();
    addpath(P.txrx);

    % ---------- fixed framing ----------
    tx_params = struct();
    tx_params.protocol     = char(protocol);
    tx_params.session_id   = 1;
    tx_params.frameLen     = 100000;
    tx_params.W            = 400000;
    tx_params.guardFrames  = 2;
    tx_params.guardN       = tx_params.guardFrames * tx_params.frameLen;

    % ---------- start/stop sync ----------
    tx_params.N_start_frames = 20;
    tx_params.N_stop_frames  = 50;

    % ---------- per-window PH frame layout ----------
    tx_params.Lpre     = 20000;
    tx_params.spsHdr   = 10;
    tx_params.NhdrBits = 64;
    tx_params.NhdrSyms = 1 + tx_params.NhdrBits;
    tx_params.Lhdr     = tx_params.NhdrSyms * tx_params.spsHdr;

    assert(tx_params.Lpre + tx_params.Lhdr <= tx_params.frameLen, "PH frame overflow");

    % ---------- amplitudes ----------
    tx_params.beaconAmp = 0.20;
    tx_params.startAmp  = 0.35;
    tx_params.preAmp    = 0.35;
    tx_params.hdrAmp    = 0.25;
    tx_params.tx_scale  = 0.35;

    % ---------- PA order ----------
    PAs = ["PA2","PA3","PA4","PA8"];
    tx_params.PAs = PAs;

    data_root = pilot_root_from_protocol(protocol);
    out_root  = fullfile(P.txrx_tapes_digital, char(protocol));
    if ~exist(out_root, "dir"), mkdir(out_root); end

    % ---------- preambles ----------
    sync = pa_make_preambles_v03(tx_params.Lpre, tx_params.startAmp, tx_params.beaconAmp, tx_params.preAmp);

    % ---------- build tape blocks ----------
    blocks = {};
    idx_rows = {};

    % start-sync frames
    startFrame = complex(zeros(tx_params.frameLen,1,"single"), zeros(tx_params.frameLen,1,"single"));
    startFrame(1:tx_params.Lpre) = sync.start_preamble;
    for k = 1:tx_params.N_start_frames
        blocks{end+1} = startFrame; %#ok<AGROW>
    end

    rec = 0;
    samp_cursor = int64(tx_params.N_start_frames * tx_params.frameLen) + 1;

    for pa = PAs
        f = fullfile(data_root, sprintf("pilot_S%02d_%s.mat", tx_params.session_id, pa));
        S = load(f, "Xsig_all", "meta");
        X = S.Xsig_all;
        meta = S.meta;

        ids = arrayfun(@(m) double(m.window_id), meta);
        [~, ord] = sort(ids, "ascend");
        X = X(:,ord);
        meta = meta(ord);

        mx_pa = max(abs(X(:)));
        if mx_pa < 1e-12, mx_pa = 1; end
        pa_gain = single(tx_params.tx_scale / double(mx_pa));

        pa_id = pa_to_id(pa);
        N = size(X,2);

        for i = 1:N
            rec = rec + 1;
            wid = uint16(meta(i).window_id);
            seq = uint16(rec);

            % PH frame: preamble + header + zeros
            ph = complex(zeros(tx_params.frameLen,1,"single"), zeros(tx_params.frameLen,1,"single"));
            ph(1:tx_params.Lpre) = sync.win_preamble;

            hdr = pa_dbpsk_header_encode_v03(pa_id, wid, seq, tx_params.spsHdr, tx_params.hdrAmp);
            ph(tx_params.Lpre + (1:numel(hdr))) = hdr;

            % payload
            payload = pa_gain * X(:,i);

            % guard zeros
            guard = complex(zeros(tx_params.guardN,1,"single"), zeros(tx_params.guardN,1,"single"));

            % append record
            blocks{end+1} = ph; %#ok<AGROW>
            blocks{end+1} = payload; %#ok<AGROW>
            blocks{end+1} = guard; %#ok<AGROW>

            % sample positions in tx_tape
            k_ph      = samp_cursor;
            k_payload = samp_cursor + int64(tx_params.frameLen);
            k_end     = k_payload + int64(tx_params.W) - 1;

            idx_rows(end+1,:) = { ... %#ok<AGROW>
                rec, char(protocol), char(pa), uint16(pa_id), uint16(wid), uint16(seq), ...
                k_ph, k_payload, k_end};

            samp_cursor = k_end + int64(tx_params.guardN) + 1;
        end
    end

    % stop frames
    stopFrame = complex(zeros(tx_params.frameLen,1,"single"), zeros(tx_params.frameLen,1,"single"));
    stopFrame(1:tx_params.Lpre) = sync.win_preamble;

    stop_hdr = pa_dbpsk_header_encode_v03(uint8(15), uint16(65535), uint16(65535), tx_params.spsHdr, tx_params.hdrAmp);
    stopFrame(tx_params.Lpre + (1:numel(stop_hdr))) = stop_hdr;

    for k = 1:tx_params.N_stop_frames
        blocks{end+1} = stopFrame; %#ok<AGROW>
    end

    % concatenate
    tx_tape = vertcat(blocks{:});
    tx_index = cell2table(idx_rows, "VariableNames", ...
        ["rec","protocol","pa","pa_id","window_id","seq","k_ph","k_payload","k_payload_end"]);

    out_file = fullfile(out_root, "tx_tape.mat");
    save(out_file, "tx_tape", "tx_index", "tx_params", "sync", "-v7.3");

    fprintf("Built tx_tape: %s\n", out_file);
    fprintf("protocol=%s | tx_tape samples=%d (%.3f GB as complex single)\n", ...
        protocol, numel(tx_tape), numel(tx_tape)*8/1e9);
end


function data_root = pilot_root_from_protocol(protocol)
    root = pa_root();

    switch string(protocol)
        case "wifi"
            data_root = fullfile(root, "data", "wifi", "digital", "pilot");
        case "bluetooth"
            data_root = fullfile(root, "data", "bluetooth", "digital", "pilot");
        case "zigbee"
            data_root = fullfile(root, "data", "zigbee", "digital", "pilot");
        otherwise
            error("Unknown protocol %s", protocol);
    end
end


function pa_id = pa_to_id(pa)
    switch string(pa)
        case "PA2", pa_id = uint8(2);
        case "PA3", pa_id = uint8(3);
        case "PA4", pa_id = uint8(4);
        case "PA8", pa_id = uint8(8);
        otherwise,  error("Unknown PA %s", pa);
    end
end