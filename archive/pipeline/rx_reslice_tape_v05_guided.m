function rx_reslice_tape_v05_guided()
    P = pa_paths();
%RX_RESLICE_TAPE_V05_GUIDED Salvage reslice using tx_index (no header/CRC needed).
%
% Requires:
%   pilot_out_v01/ota_rx_tape_v03/ota_tape_S01_v03.mat   (x_tape, rx_cfg)
%   pilot_out_v01/tx_tape_v03/tx_tape_v03.mat            (tx_params, sync, tx_index)

    addpath(P.txrx);

    tape_file = fullfile(P.txrx_tapes_ota,"ota_tape_S01_v03.mat");
    T = load(tape_file, "x_tape", "rx_cfg");
    x_tape = T.x_tape(:);
    rx_cfg = T.rx_cfg;

    spec_file = fullfile(P.txrx_tapes_digital,"tx_tape_v03.mat");
    S = load(spec_file, "tx_params", "sync", "tx_index");
    p = S.tx_params;
    sync = S.sync;
    tx_index = S.tx_index;

    fprintf("GUIDED RESLICE | tape=%d | Fs=%.6f MS/s\n", numel(x_tape), rx_cfg.Fs/1e6);
    fprintf("Records in tx_index: %d\n", height(tx_index));

    % ---- estimate global offset using first PH preamble ----
    kph0 = double(tx_index.k_ph(1));          % expected PH start in TX tape
    search = 2 * p.frameLen;                  % +/- 2 frames search

    a = max(1, kph0 - search);
    b = min(numel(x_tape), kph0 + search + p.Lpre - 1);
    buf = x_tape(a:b);

    [krel, ratio] = find_preamble_in_buffer(buf, sync.win_preamble);
    if isempty(krel)
        error("Could not find win_preamble near first record. ratio=%.2f", ratio);
    end
    kph_rx0 = a + krel - 1;
    offset = kph_rx0 - kph0;

    fprintf("Offset estimate: %d samples (ratio=%.2f)\n", offset, ratio);

    % ---- storage (exact counts per PA from tx_index) ----
    PAs = ["PA2","PA3","PA4","PA8"];
    out_data = P.data_wifi_spliced_v03;
    if ~exist(out_data,"dir"), mkdir(out_data); end

    X = struct(); M = struct(); counts = struct();
    meta_template = struct( ...
        "schema_version", "ota_v03", ...
        "session_id", 1, ...
        "tape_id", 1, ...
        "segment_id", 0, ...
        "window_id", uint16(0), ...
        "pa_type", "", ...
        "fs_hz", double(rx_cfg.Fs), ...
        "window_length_s", double(p.W)/double(rx_cfg.Fs), ...
        "seq", uint16(0), ...
        "k_ph", int64(0), ...
        "k_payload", int64(0) );

    for pa = PAs
        mask = strcmp(string(tx_index.pa), pa);
        Npa = sum(mask);
        X.(char(pa)) = complex(zeros(p.W, Npa, "single"), zeros(p.W, Npa, "single"));
        M.(char(pa)) = repmat(meta_template, 1, Npa);
        counts.(char(pa)) = 0;
    end

    % ---- extract using tx_index ----
    bad = 0;

    for i = 1:height(tx_index)
        pa = string(tx_index.pa{i});
        if ~any(pa == PAs), continue; end

        kph = double(tx_index.k_ph(i)) + offset;
        kpl = double(tx_index.k_payload(i)) + offset;

        % bounds check
        if kpl < 1 || (kpl + p.W - 1) > numel(x_tape)
            bad = bad + 1;
            continue;
        end

        % optional sanity: preamble ratio at kph
        r = pa_corr_ratio_v03(x_tape(kph : kph+p.Lpre-1), sync.win_preamble);
        if r < 6
            % if this happens a lot, your offset is wrong or you need drift handling
            % (but try salvage first)
        end

        payload = x_tape(kpl : kpl+p.W-1);

        c = counts.(char(pa)) + 1;
        counts.(char(pa)) = c;
        X.(char(pa))(:,c) = payload;

        meta = meta_template;
        meta.window_id = uint16(tx_index.window_id(i));
        meta.pa_type   = char(pa);
        meta.seq       = uint16(tx_index.seq(i));
        meta.k_ph      = int64(kph);
        meta.k_payload = int64(kpl);

        M.(char(pa))(c) = meta;
    end

    fprintf("GUIDED RESLICE finished | bad=%d\n", bad);

    % ---- save per PA ----
    for pa = PAs
        c = counts.(char(pa));
        Xrx_all = X.(char(pa))(:,1:c);
        meta_rx = M.(char(pa))(1:c);
        out = fullfile(out_data, sprintf("ota_rx_S01_%s.mat", pa));
        save(out, "Xrx_all", "meta_rx", "rx_cfg", "-v7.3");
        fprintf("Saved %s | %d windows\n", out, c);
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
    best_ratio = pk/med;
    if best_ratio < 10
        k0 = [];
    else
        k0 = idx;
    end
end