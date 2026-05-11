function build_tx_tape_shards(protocol, dataset_id, varargin)
%BUILD_TX_TAPE_SHARDS Build transport-sized tx_tape shard files from pilot shards.
%
% Streamed version:
%   - does NOT keep the whole tx_tape in RAM
%   - writes tx_tape directly into a v7.3 MAT-file
%   - writes matching tx_spec_shard_###.mat
%
% Usage:
%   build_tx_tape_shards("wifi", "wifi_high_run01")
%   build_tx_tape_shards("wifi", "wifi_high_run01", 'shards', 1:2)
%   build_tx_tape_shards("wifi", "wifi_high_run01", 'stage_root', "D:\PADataset_stage")
%
% Notes:
%   - If you change shard count or dataset plan, use a new dataset_id or delete old outputs.

    ip = inputParser();
    ip.addParameter('shards', [], @(x) isnumeric(x) || isempty(x));
    ip.addParameter('stage_root', "", @(x) isstring(x) || ischar(x));
    ip.parse(varargin{:});

    protocol = string(protocol);
    stage_root = string(ip.Results.stage_root);

    R = pa_protocol_roots(protocol);

    if strlength(stage_root) == 0
        base_root = fullfile(R.data_pilot_shards, char(dataset_id));
        out_root  = fullfile(R.txrx_tapes_digital, char(dataset_id));
    else
        base_root = fullfile(char(stage_root), 'data', char(protocol), 'digital', 'pilot_shards', char(dataset_id));
        out_root  = fullfile(char(stage_root), 'txrx', 'tapes', 'digital', char(protocol), char(dataset_id));
    end

    if ~exist(out_root, 'dir')
        mkdir(out_root);
    end

    Splan = load(fullfile(base_root, 'dataset_plan.mat'), 'plan');
    plan = Splan.plan;

    if isempty(ip.Results.shards)
        shard_ids = 1:numel(plan.shards);
    else
        shard_ids = unique(double(ip.Results.shards(:))).';
    end

    addpath(fullfile(pa_root(), 'txrx'));

    tx_params = struct();
    tx_params.protocol       = char(protocol);
    tx_params.dataset_id     = char(dataset_id);
    tx_params.session_id     = plan.seed_session_id;
    tx_params.seed_tape_id   = plan.seed_tape_id;
    tx_params.frameLen       = 100000;
    tx_params.W              = 400000;
    tx_params.guardFrames    = 2;
    tx_params.guardN         = tx_params.guardFrames * tx_params.frameLen;
    tx_params.N_start_frames = 20;
    tx_params.N_stop_frames  = 50;
    tx_params.Lpre           = 20000;
    tx_params.spsHdr         = 10;
    tx_params.NhdrBits       = 64;
    tx_params.NhdrSyms       = 1 + tx_params.NhdrBits;
    tx_params.Lhdr           = tx_params.NhdrSyms * tx_params.spsHdr;
    tx_params.beaconAmp      = 0.20;
    tx_params.startAmp       = 0.35;
    tx_params.preAmp         = 0.35;
    tx_params.hdrAmp         = 0.25;
    tx_params.tx_scale       = 0.35;
    tx_params.PAs            = string(plan.pa_order);

    sync = pa_make_preambles_v03(tx_params.Lpre, tx_params.startAmp, tx_params.beaconAmp, tx_params.preAmp);

    % Constant record length in samples
    rec_len = int64(tx_params.frameLen + tx_params.W + tx_params.guardN);

    for s = shard_ids
        shard_root = fullfile(base_root, sprintf('shard_%03d', s));

        % ------------------------------------------------------------
        % PASS 1: count records only
        % ------------------------------------------------------------
        total_records = 0;
        for pa = tx_params.PAs
            f = fullfile(shard_root, sprintf('pilot_S%02d_%s.mat', tx_params.session_id, pa));
            Smeta = load(f, 'meta');
            total_records = total_records + numel(Smeta.meta);
        end

        total_len = int64(tx_params.N_start_frames) * int64(tx_params.frameLen) + ...
                    int64(total_records) * rec_len + ...
                    int64(tx_params.N_stop_frames) * int64(tx_params.frameLen);

        % ------------------------------------------------------------
        % Create output MAT-file and preallocate tx_tape on disk
        % ------------------------------------------------------------
        out_file = fullfile(out_root, sprintf('tx_tape_shard_%03d.mat', s));
        if isfile(out_file)
            delete(out_file);
        end

        save(out_file, 'tx_params', 'sync', '-v7.3');
        Mout = matfile(out_file, 'Writable', true);

        % Allocate the tx_tape variable on disk
        Mout.tx_tape(total_len, 1) = complex(single(0), single(0));

        idx_rows = cell(total_records, 11);
        rec = 0;
        write_cursor = int64(1);

        % ------------------------------------------------------------
        % Write start frames
        % ------------------------------------------------------------
        startFrame = complex(zeros(tx_params.frameLen,1,'single'), zeros(tx_params.frameLen,1,'single'));
        startFrame(1:tx_params.Lpre) = sync.start_preamble;

        for k = 1:tx_params.N_start_frames
            span = double(write_cursor : write_cursor + int64(tx_params.frameLen) - 1);
            Mout.tx_tape(span, 1) = startFrame;
            write_cursor = write_cursor + int64(tx_params.frameLen);
        end

        % ------------------------------------------------------------
        % PASS 2: stream records to disk, one record at a time
        % ------------------------------------------------------------
        for pa = tx_params.PAs
            f = fullfile(shard_root, sprintf('pilot_S%02d_%s.mat', tx_params.session_id, pa));
            S = load(f, 'Xsig_all', 'meta');
            X = S.Xsig_all;
            meta = S.meta;

            ids = arrayfun(@(m) double(m.window_id), meta);
            [~, ord] = sort(ids, 'ascend');
            X = X(:, ord);
            meta = meta(ord);

            mx_pa = max(abs(X(:)));
            if mx_pa < 1e-12
                mx_pa = 1;
            end
            pa_gain = single(tx_params.tx_scale / double(mx_pa));
            pa_id = pa_to_id(pa);
            N = size(X,2);

            for i = 1:N
                rec = rec + 1;
                wid = uint16(meta(i).window_id);
                seq = uint16(rec);

                ph = complex(zeros(tx_params.frameLen,1,'single'), zeros(tx_params.frameLen,1,'single'));
                ph(1:tx_params.Lpre) = sync.win_preamble;
                hdr = pa_dbpsk_header_encode_v03(pa_id, wid, seq, tx_params.spsHdr, tx_params.hdrAmp);
                ph(tx_params.Lpre + (1:numel(hdr))) = hdr;

                payload = pa_gain * X(:,i);
                guard = complex(zeros(tx_params.guardN,1,'single'), zeros(tx_params.guardN,1,'single'));

                rec_block = [ph; payload; guard];

                k_ph      = write_cursor;
                k_payload = write_cursor + int64(tx_params.frameLen);
                k_end     = k_payload + int64(tx_params.W) - 1;

                span = double(write_cursor : write_cursor + int64(numel(rec_block)) - 1);
                Mout.tx_tape(span, 1) = rec_block;

                idx_rows(rec,:) = { ...
                    rec, char(protocol), char(dataset_id), s, char(pa), uint16(pa_id), uint16(wid), uint16(seq), ...
                    k_ph, k_payload, k_end};

                write_cursor = write_cursor + int64(numel(rec_block));
            end

            clear S X meta
        end

        % ------------------------------------------------------------
        % Write stop frames
        % ------------------------------------------------------------
        stopFrame = complex(zeros(tx_params.frameLen,1,'single'), zeros(tx_params.frameLen,1,'single'));
        stopFrame(1:tx_params.Lpre) = sync.win_preamble;
        stop_hdr = pa_dbpsk_header_encode_v03(uint8(15), uint16(65535), uint16(65535), tx_params.spsHdr, tx_params.hdrAmp);
        stopFrame(tx_params.Lpre + (1:numel(stop_hdr))) = stop_hdr;

        for k = 1:tx_params.N_stop_frames
            span = double(write_cursor : write_cursor + int64(tx_params.frameLen) - 1);
            Mout.tx_tape(span, 1) = stopFrame;
            write_cursor = write_cursor + int64(tx_params.frameLen);
        end

        if write_cursor - 1 ~= total_len
            error('Internal length mismatch for shard %03d | wrote=%d expected=%d', s, write_cursor - 1, total_len);
        end

        tx_index = cell2table(idx_rows, 'VariableNames', ...
            ["rec","protocol","dataset_id","shard_id","pa","pa_id","window_id","seq","k_ph","k_payload","k_payload_end"]);

        save(out_file, 'tx_index', '-append');

        fprintf('Built tx_tape shard: %s | samples=%d | %.3f GB\n', out_file, total_len, double(total_len)*8/1e9);

        tx_spec = struct();
        tx_spec.protocol   = char(protocol);
        tx_spec.dataset_id = char(dataset_id);
        tx_spec.shard_id   = s;
        tx_spec.tx_params  = tx_params;
        tx_spec.sync       = sync;
        tx_spec.tx_index   = tx_index;

        spec_file = fullfile(out_root, sprintf('tx_spec_shard_%03d.mat', s));
        if isfile(spec_file)
            delete(spec_file);
        end
        save(spec_file, 'tx_spec', '-v7');
        fprintf('Built tx_spec shard: %s\n', spec_file);

        clear Mout idx_rows tx_index
    end
end

function pa_id = pa_to_id(pa)
    switch string(pa)
        case "PA1", pa_id = uint16(1);
        case "PA2", pa_id = uint16(2);
        case "PA3", pa_id = uint16(3);
        case "PA4", pa_id = uint16(4);
        case "PA5", pa_id = uint16(5);
        case "PA6", pa_id = uint16(6);
        case "PA7", pa_id = uint16(7);
        case "PA8", pa_id = uint16(8);
        otherwise
            error("Unknown PA %s", pa);
    end
end