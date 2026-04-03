function build_tx_tape_v03()
    P = pa_paths();
%BUILD_TX_TAPE_V03 Build a single continuous tx_tape with start-sync + per-window headers.
% Output:
%   WIFI/pilot_out_v01/tx_tape_v03/tx_tape_v03.mat  (tx_tape, tx_index, tx_params, sync)
%
% Requires:
%   WIFI/pilot_out_v01/data/pilot_S01_PA2.mat ... etc (Xsig_all, meta)

    addpath(P.txrx);

    % ---------- fixed framing ----------
    tx_params = struct();
    tx_params.session_id   = 1;
    tx_params.frameLen     = 100000;
    tx_params.W            = 400000;
    tx_params.guardFrames  = 2;
    tx_params.guardN       = tx_params.guardFrames * tx_params.frameLen;

    % ---------- start sync ----------
    tx_params.N_start_frames = 20;     % repeated START_SYNC frames at beginning of tx_tape
    tx_params.N_stop_frames  = 50;     % repeated STOP frames at end of tx_tape

    % ---------- per-window PH frame layout ----------
    tx_params.Lpre   = 20000;          % preamble samples inside PH frame
    tx_params.spsHdr = 10;             % DBPSK header samples/symbol
    tx_params.NhdrBits = 64;           % (fields+crc)
    tx_params.NhdrSyms = 1 + tx_params.NhdrBits;                 % +1 reference symbol
    tx_params.Lhdr  = tx_params.NhdrSyms * tx_params.spsHdr;     % samples

    assert(tx_params.Lpre + tx_params.Lhdr <= tx_params.frameLen, "PH frame overflow");

    % ---------- amplitudes ----------
    tx_params.beaconAmp   = 0.20;      % beacon (pre-tape) amplitude
    tx_params.startAmp    = 0.35;      % start-sync amplitude in tx_tape
    tx_params.preAmp      = 0.35;      % per-window preamble amplitude
    tx_params.hdrAmp      = 0.25;      % header amplitude
    tx_params.tx_scale    = 0.35;      % payload scaling (per-PA global)

    % ---------- PA order (your current order) ----------
    PAs = ["PA2","PA3","PA4","PA8"];
    tx_params.PAs = PAs;

    data_root = P.data_wifi_pilot;
    out_root  = P.txrx_tapes_digital;
    if ~exist(out_root,"dir"), mkdir(out_root); end

    % ---------- preambles ----------
    sync = pa_make_preambles_v03(tx_params.Lpre, tx_params.startAmp, tx_params.beaconAmp, tx_params.preAmp);

    % ---------- load pilot + build payload blocks ----------
    blocks = {};  % each entry is a vector appended to tx_tape
    idx_rows = []; % will become table at end

    % start-sync frames (at head of tx_tape)
    startFrame = complex(zeros(tx_params.frameLen,1,"single"), zeros(tx_params.frameLen,1,"single"));
    startFrame(1:tx_params.Lpre) = sync.start_preamble;
    for k = 1:tx_params.N_start_frames
        blocks{end+1} = startFrame; %#ok<AGROW>
    end

    % build per-window records
    rec = 0;
    samp_cursor = int64(tx_params.N_start_frames * tx_params.frameLen) + 1;

    for pa = PAs
        f = fullfile(data_root, sprintf("pilot_S%02d_%s.mat", tx_params.session_id, pa));
        S = load(f, "Xsig_all", "meta");
        X = S.Xsig_all; meta = S.meta;

        ids = arrayfun(@(m) double(m.window_id), meta);
        [~,ord] = sort(ids,"ascend");
        X = X(:,ord); meta = meta(ord);

        mx_pa = max(abs(X(:))); if mx_pa < 1e-12, mx_pa = 1; end
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

            % payload (scaled)
            payload = pa_gain * X(:,i);

            % guard zeros
            guard = complex(zeros(tx_params.guardN,1,"single"), zeros(tx_params.guardN,1,"single"));

            % append record
            blocks{end+1} = ph; %#ok<AGROW>
            blocks{end+1} = payload; %#ok<AGROW>
            blocks{end+1} = guard; %#ok<AGROW>

            % index row (sample positions in tx_tape)
            k_ph = samp_cursor;
            k_payload = samp_cursor + int64(tx_params.frameLen);
            k_end = k_payload + int64(tx_params.W) - 1;

            idx_rows = [idx_rows; {rec, char(pa), uint16(pa_id), uint16(wid), uint16(seq), k_ph, k_payload, k_end}]; %#ok<AGROW>

            samp_cursor = k_end + int64(tx_params.guardN) + 1;
        end
    end

    % stop frames (at tail of tx_tape)
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
        ["rec","pa","pa_id","window_id","seq","k_ph","k_payload","k_payload_end"]);

    save(fullfile(out_root,"tx_tape_v03.mat"), "tx_tape", "tx_index", "tx_params", "sync", "-v7.3");
    fprintf("Built tx_tape_v03: %s\n", fullfile(out_root,"tx_tape_v03.mat"));
    fprintf("tx_tape samples: %d (%.3f GB as complex single)\n", numel(tx_tape), numel(tx_tape)*8/1e9);

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