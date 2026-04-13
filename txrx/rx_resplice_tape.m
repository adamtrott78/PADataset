function rx_resplice_tape(protocol)
%RX_RESPLICE_TAPE Header-first OTA resplice using ONLY the new tx_spec.mat format.
%
% Strategy:
%   1) Load captured OTA tape from txrx/tapes/ota/<protocol>/ota_tape_S01.mat
%   2) Load TX metadata from txrx/tapes/digital/<protocol>/tx_spec.mat
%   3) Recover a monotone chain of CRC-valid headers
%   4) Keep payload i only if header(i+1) starts after payload(i) fully ends
%   5) Split recovered windows back out by PA and save them
%
% Usage:
%   rx_resplice_tape
%   rx_resplice_tape("wifi")
%   rx_resplice_tape("bluetooth")
%   rx_resplice_tape("zigbee")

    if nargin < 1 || isempty(protocol)
        protocol = "wifi";
    end

    protocol = string(protocol);
    assert(any(protocol == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    P = pa_paths();
    addpath(P.txrx);

    ota_file   = fullfile(P.txrx_tapes_ota,     char(protocol), "ota_tape_S01.mat");
    spec_file  = fullfile(P.txrx_tapes_digital, char(protocol), "tx_spec.mat");
    pilot_root = pilot_root_from_protocol(protocol);
    out_data   = spliced_root_from_protocol(protocol);
    out_res    = results_root_from_protocol(protocol);
    png_root   = fullfile(out_res, "png");

    if ~exist(out_data,"dir"), mkdir(out_data); end
    if ~exist(out_res,"dir"),  mkdir(out_res);  end

    fprintf("RX RESPLICE | protocol=%s\n", protocol);
    fprintf("OTA FILE    | %s\n", ota_file);
    fprintf("SPEC FILE   | %s\n", spec_file);

    assert(isfile(ota_file),  "Missing OTA tape file: %s", ota_file);
    assert(isfile(spec_file), "Missing tx_spec file: %s", spec_file);

    T = load(ota_file, "x_tape", "rx_cfg");
    assert(isfield(T,"x_tape"), "OTA file missing x_tape: %s", ota_file);
    assert(isfield(T,"rx_cfg"),  "OTA file missing rx_cfg: %s", ota_file);
    x_tape = T.x_tape(:);
    rx_cfg = T.rx_cfg;

    S = load(spec_file, "tx_spec");
    assert(isfield(S,"tx_spec"), "Spec file missing tx_spec struct: %s", spec_file);

    tx_spec = S.tx_spec;
    must_have = ["tx_params","sync","tx_index"];
    for k = 1:numel(must_have)
        assert(isfield(tx_spec, must_have(k)), ...
            "Spec file missing tx_spec.%s: %s", must_have(k), spec_file);
    end

    p = tx_spec.tx_params;
    sync = tx_spec.sync;
    tx_index = tx_spec.tx_index;
    tx_lut = make_tx_lut(tx_index);

    fprintf("SPEC OK     | records=%d | frameLen=%d | W=%d | guardN=%d\n", ...
        height(tx_index), p.frameLen, p.W, p.guardN);

    fprintf("OTA INFO    | protocol=%s | samples=%d | Fs=%.6f MS/s | overruns=%d\n", ...
        protocol, numel(x_tape), rx_cfg.Fs/1e6, rx_cfg.overruns);

    PAs = ["PA2","PA3","PA4","PA8"];

    % Preallocate per-PA storage from tx_index counts
    tx_pa = normalize_pa_column(tx_index.pa);
    X = struct();
    M = struct();
    counts = struct();

    for pa = PAs
        npa = sum(tx_pa == pa);
        if npa < 1, npa = 1; end
        X.(char(pa)) = complex(zeros(p.W, npa, "single"), zeros(p.W, npa, "single"));
        M.(char(pa)) = repmat(empty_meta(), 1, npa);
        counts.(char(pa)) = 0;
    end

    need_gap = p.frameLen + p.W;

    [k0, ok0, r0] = find_first_record(x_tape, p, sync, tx_lut, 8);
    if ~ok0
        error("Start lock failed: no valid first data header found.");
    end

    [h0, okh0] = raw_decode_valid_header_at_k(x_tape, k0, p, tx_lut, uint16(0));
    if ~okh0
        error("Internal error: first record decode failed at k0.");
    end
    h0.r = r0;

    fprintf("First hdr   | k=%d | seq=%d | pa=%s | wid=%d | r=%.2f\n", ...
        h0.k, h0.seq, h0.pa, h0.wid, h0.r);

    H = repmat(empty_hdr(), 1, tx_lut.N + 64);
    nH = 1;
    H(1) = h0;

    t0 = tic;
    tPrint = tic;
    nExact = 0;
    nBroad = 0;
    nFail = 0;
    stop_seen = h0.is_stop;

    while ~stop_seen
        cur = H(nH);
        [nxt, ok, mode] = find_next_valid_header(x_tape, cur, p, sync, tx_lut);
        if ~ok
            nFail = nFail + 1;
            fprintf("NEXT hdr not found | after seq=%d | pa=%s | wid=%d | k=%d\n", ...
                cur.seq, cur.pa, cur.wid, cur.k);
            break;
        end

        if nH == numel(H)
            H = [H repmat(empty_hdr(), 1, 512)]; %#ok<AGROW>
        end
        nH = nH + 1;
        H(nH) = nxt;
        stop_seen = nxt.is_stop;

        if mode == "exact"
            nExact = nExact + 1;
        else
            nBroad = nBroad + 1;
        end

        if toc(tPrint) > 1.0
            fprintf("HDR prog    | found=%d | last_seq=%d | last_pa=%s | k=%d | exact=%d | broad=%d | elapsed=%.1fs\n", ...
                nH, H(nH).seq, H(nH).pa, H(nH).k, nExact, nBroad, toc(t0));
            tPrint = tic;
        end
    end

    H = H(1:nH);
    fprintf("HDR done    | found=%d | stop_seen=%d | exact=%d | broad=%d | fail=%d | first_seq=%d | last_seq=%d\n", ...
        nH, stop_seen, nExact, nBroad, nFail, H(1).seq, H(end).seq);

    drop_log = repmat(empty_drop(), 1, max(1, nH));
    nDrop = 0;
    nKeep = 0;

    for i = 1:max(0, nH-1)
        cur = H(i);
        nxt = H(i+1);

        if cur.is_stop, break; end
        pa = cur.pa;
        if pa == "", continue; end

        pay0 = double(cur.k) + p.frameLen;
        pay1 = pay0 + p.W - 1;
        gap = double(nxt.k - cur.k);

        if pay1 > numel(x_tape) || gap < need_gap
            nDrop = nDrop + 1;
            drop_log(nDrop) = struct( ...
                "seq", uint16(cur.seq), ...
                "pa_type", char(pa), ...
                "window_id", uint16(cur.wid), ...
                "k_hdr", int64(cur.k), ...
                "k_next", int64(nxt.k), ...
                "gap", int64(gap), ...
                "reason", "truncated_or_unproven");
            fprintf("DROP        | seq=%d | pa=%s | wid=%d | k=%d | next_k=%d | gap=%d\n", ...
                cur.seq, pa, cur.wid, cur.k, nxt.k, gap);
            continue;
        end

        c = counts.(char(pa)) + 1;
        counts.(char(pa)) = c;

        % grow storage if needed
        if c > size(X.(char(pa)), 2)
            X.(char(pa))(:, end+256) = complex(single(0), single(0)); %#ok<AGROW>
            M.(char(pa))(end+256) = empty_meta(); %#ok<AGROW>
        end

        X.(char(pa))(:,c) = x_tape(pay0:pay1);

        M.(char(pa))(c) = struct( ...
            "schema_version", "ota_resplice", ...
            "protocol", char(protocol), ...
            "session_id", 1, ...
            "tape_id", 1, ...
            "segment_id", 0, ...
            "window_id", uint16(cur.wid), ...
            "pa_type", char(pa), ...
            "fs_hz", double(rx_cfg.Fs), ...
            "window_length_s", double(p.W)/double(rx_cfg.Fs), ...
            "seq", uint16(cur.seq), ...
            "k_ph", int64(cur.k), ...
            "k_next", int64(nxt.k), ...
            "gap_to_next", int64(gap), ...
            "header_r", double(cur.r));

        nKeep = nKeep + 1;
    end

    % Conservative tail handling: last non-stop header is not kept without a follower.
    if ~H(end).is_stop
        tail = H(end);
        if tail.pa ~= ""
            nDrop = nDrop + 1;
            drop_log(nDrop) = struct( ...
                "seq", uint16(tail.seq), ...
                "pa_type", char(tail.pa), ...
                "window_id", uint16(tail.wid), ...
                "k_hdr", int64(tail.k), ...
                "k_next", int64(-1), ...
                "gap", int64(-1), ...
                "reason", "unpaired_tail");
            fprintf("DROP        | seq=%d | pa=%s | wid=%d | k=%d | reason=unpaired_tail\n", ...
                tail.seq, tail.pa, tail.wid, tail.k);
        end
    end

    drop_log = drop_log(1:nDrop);

    for pa = PAs
        c = counts.(char(pa));
        Xrx_all = X.(char(pa))(:,1:c);
        meta_rx = M.(char(pa))(1:c);
        out = fullfile(out_data, sprintf("ota_rx_S01_%s.mat", pa));
        save(out, "Xrx_all", "meta_rx", "rx_cfg", "-v7.3");
        fprintf("Saved       | %s | %d windows\n", out, c);
    end

    summary = struct();
    summary.protocol = char(protocol);
    summary.spec_file = spec_file;
    summary.ota_file = ota_file;
    summary.stop_seen = logical(stop_seen);
    summary.headers_found = H;
    summary.n_headers = int32(nH);
    summary.n_keep = int32(nKeep);
    summary.n_drop = int32(nDrop);
    summary.counts = counts;
    summary.rx_cfg = rx_cfg;
    summary.need_gap = int32(need_gap);

    save(fullfile(out_res, "resplice_summary.mat"), "summary", "drop_log", "-v7.3");

    if exist(png_root,"dir"), rmdir(png_root,"s"); end
    mkdir(png_root);

    for pa = PAs
        c = counts.(char(pa));
        K = min(10, c);
        for i = 1:K
            wid = double(M.(char(pa))(i).window_id);
            x_o = X.(char(pa))(:,i);
            [x_d, Fs_d, ok] = load_digital_by_window_id(pilot_root, pa, wid);
            if ~ok, continue; end
            outpng = fullfile(png_root, sprintf("DIG_vs_OTA_%s_%s_w%04d.png", protocol, pa, wid));
            plot_pair_dig_vs_ota(pa, x_d, Fs_d, x_o, rx_cfg.Fs, outpng);
        end
    end

    fprintf("RESPLICE DONE | protocol=%s | kept=%d | dropped=%d | stop_seen=%d | PNGs=%s\n", ...
        protocol, nKeep, nDrop, stop_seen, png_root);
end


function [k0, ok, best_r] = find_first_record(x_tape, p, sync, tx_lut, r_thr)
    ok = false; k0 = 1; best_r = 0;
    offs = unique([1, 1+round(p.frameLen/4), 1+round(p.frameLen/2), 1+round(3*p.frameLen/4)]);
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;

    for o = offs
        for k = o:p.frameLen:kmax
            r = preamble_score_at_k(x_tape, k, p, sync);
            if r < r_thr, continue; end
            [hdr, okh] = raw_decode_valid_header_at_k(x_tape, k, p, tx_lut, uint16(0));
            if ~okh || hdr.is_stop, continue; end
            hdr.r = r; %#ok<NASGU>
            k0 = k;
            best_r = r;
            ok = true;
            return;
        end
    end
end


function [nxt, ok, mode] = find_next_valid_header(x_tape, cur, p, sync, tx_lut)
    Lrec = p.frameLen + p.W + p.guardN;
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    k_exp = double(cur.k) + Lrec;

    nxt = empty_hdr(); ok = false; mode = "";

    % Fast exact/local path around expected position
    smallR = 2048;
    [cand, ok1] = search_exact_range(x_tape, max(double(cur.k)+1, k_exp-smallR), min(kmax, k_exp+smallR), cur, p, tx_lut, k_exp);
    if ok1
        cand.r = preamble_score_at_k(x_tape, cand.k, p, sync);
        nxt = cand; ok = true; mode = "exact"; return;
    end

    % Broad relock path for dropped-sample recovery
    leftR = max(400000, 4*p.frameLen);
    rightR = max(4*Lrec, 2800000);
    a = max(double(cur.k)+1, k_exp-leftR);
    b = min(kmax, k_exp+rightR);
    if b < a, return; end

    stride = 5000;
    ks = a:stride:b;
    r = zeros(size(ks));
    for i = 1:numel(ks), r(i) = preamble_score_at_k(x_tape, ks(i), p, sync); end

    r_thr = 6;
    pick = find(r >= r_thr);
    if isempty(pick)
        [~,ord] = sort(r, "descend");
        pick = ord(1:min(24, numel(ord)));
    else
        [~,ord] = sort(r(pick), "descend");
        pick = pick(ord(1:min(24, numel(ord))));
    end

    coarse = ks(pick);
    [~,ord2] = sort(abs(coarse - k_exp), "ascend");
    coarse = coarse(ord2);

    refineR = 3500;
    ranges = [max(double(cur.k)+1, coarse(:)-refineR), min(kmax, coarse(:)+refineR)];
    ranges = merge_ranges(ranges);

    best = empty_hdr(); okBest = false;
    for i = 1:size(ranges,1)
        [cand, okc] = search_exact_range(x_tape, ranges(i,1), ranges(i,2), cur, p, tx_lut, k_exp);
        if okc && (~okBest || cand_better(cand, best, cur, k_exp))
            best = cand;
            okBest = true;
        end
    end

    if okBest
        best.r = preamble_score_at_k(x_tape, best.k, p, sync);
        nxt = best;
        ok = true;
        mode = "broad";
    end
end


function [best, ok] = search_exact_range(x_tape, lo, hi, cur, p, tx_lut, k_exp)
    best = empty_hdr(); ok = false;
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    lo = max(lo, double(cur.k)+1);
    hi = min(hi, kmax);
    if hi < lo, return; end

    for k = lo:hi
        [cand, okc] = raw_decode_valid_header_at_k(x_tape, k, p, tx_lut, uint16(cur.seq));
        if ~okc, continue; end
        if ~ok || cand_better(cand, best, cur, k_exp)
            best = cand;
            ok = true;
        end
    end
end


function [hdr, ok] = raw_decode_valid_header_at_k(x_tape, k, p, tx_lut, seq_floor)
    hdr = empty_hdr(); ok = false;
    k = round(double(k));
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    if k < 1 || k > kmax, return; end

    hdr_samp = x_tape(k + p.Lpre + (1:p.Lhdr));
    [pa_id, wid, seq, crc_ok] = pa_dbpsk_header_decode_v03(hdr_samp, p.spsHdr);
    if ~crc_ok, return; end

    pa_id = uint16(pa_id);
    wid = uint16(wid);
    seq = uint16(seq);

    is_stop = (double(pa_id) == 15) && (double(wid) == 65535) && (double(seq) == 65535);
    if is_stop
        hdr = struct("k", int64(k), "pa_id", pa_id, "pa", "", "wid", wid, "seq", seq, "is_stop", true, "r", NaN);
        ok = true;
        return;
    end

    pa = id_to_pa(pa_id);
    if pa == "", return; end
    if seq <= seq_floor, return; end

    s = double(seq);
    if s < 1 || s > tx_lut.N, return; end
    if tx_lut.pa_id(s) ~= pa_id || tx_lut.wid(s) ~= wid, return; end

    hdr = struct("k", int64(k), "pa_id", pa_id, "pa", pa, "wid", wid, "seq", seq, "is_stop", false, "r", NaN);
    ok = true;
end


function tf = cand_better(a, b, cur, k_exp)
    ka = cand_key(a, cur, k_exp);
    kb = cand_key(b, cur, k_exp);
    tf = false;
    for i = 1:numel(ka)
        if ka(i) < kb(i), tf = true; return; end
        if ka(i) > kb(i), return; end
    end
end


function key = cand_key(cand, cur, k_exp)
    seq_target = double(cur.seq) + 1;
    if cand.is_stop
        grp = 2; seqk = 0;
    elseif double(cand.seq) == seq_target
        grp = 1; seqk = 0;
    else
        grp = 3; seqk = double(cand.seq);
    end
    dist = abs(double(cand.k) - double(k_exp));
    key = [grp, seqk, dist];
end


function r = preamble_score_at_k(x_tape, k, p, sync)
    k = round(double(k));
    if k < 1 || (k + p.Lpre - 1) > numel(x_tape), r = 0; return; end
    r = pa_corr_ratio_v03(x_tape(k:k+p.Lpre-1), sync.win_preamble);
end


function ranges = merge_ranges(ranges)
    if isempty(ranges), ranges = zeros(0,2); return; end
    ranges = sortrows(ranges, 1);
    out = ranges(1,:);
    for i = 2:size(ranges,1)
        if ranges(i,1) <= out(end,2) + 1
            out(end,2) = max(out(end,2), ranges(i,2));
        else
            out = [out; ranges(i,:)]; %#ok<AGROW>
        end
    end
    ranges = out;
end


function lut = make_tx_lut(tx_index)
    lut = struct();
    lut.N = height(tx_index);
    lut.pa_id = uint16(tx_index.pa_id(:));
    lut.wid = uint16(tx_index.window_id(:));
end


function pa = id_to_pa(pa_id)
    switch double(pa_id)
        case 2, pa = "PA2";
        case 3, pa = "PA3";
        case 4, pa = "PA4";
        case 8, pa = "PA8";
        otherwise, pa = "";
    end
end


function [x_d, Fs_d, ok] = load_digital_by_window_id(data_root, pa, wid)
    f = fullfile(data_root, sprintf("pilot_S01_%s.mat", pa));
    if ~isfile(f), x_d=[]; Fs_d=[]; ok=false; return; end
    S = load(f, "Xsig_all", "meta");
    ids = arrayfun(@(m) double(m.window_id), S.meta);
    j = find(ids == wid, 1, "first");
    if isempty(j), x_d=[]; Fs_d=[]; ok=false; return; end
    x_d = S.Xsig_all(:,j);
    Fs_d = double(S.meta(j).fs_hz);
    ok = true;
end


function plot_pair_dig_vs_ota(pa, x_d, Fs_d, x_o, Fs_o, out_png)
    nfft = 1024; hop = 256; win = hann(nfft,"periodic");
    td = (0:numel(x_d)-1)/Fs_d*1e3;
    to = (0:numel(x_o)-1)/Fs_o*1e3;

    f = figure("Visible","off","Color","w","Position",[100 100 1700 950]);
    tiledlayout(2,2,"Padding","compact","TileSpacing","compact");

    nexttile;
    [Sd,Fd,Td2] = spectrogram(x_d, win, nfft-hop, nfft, Fs_d, "centered");
    imagesc(Td2*1e3, Fd/1e6, 10*log10(abs(Sd).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)"); title(string(pa)+" (DIG)"); colorbar;

    nexttile;
    [So,Fo,To2] = spectrogram(x_o, win, nfft-hop, nfft, Fs_o, "centered");
    imagesc(To2*1e3, Fo/1e6, 10*log10(abs(So).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)"); title(string(pa)+" (OTA)"); colorbar;

    nexttile;
    plot(td, real(x_d)); hold on; plot(td, imag(x_d), "--");
    grid on; xlabel("Time (ms)"); ylabel("I / Q"); title("Waveform (DIG)");
    legend("I","Q","Location","northeast");

    nexttile;
    plot(to, real(x_o)); hold on; plot(to, imag(x_o), "--");
    grid on; xlabel("Time (ms)"); ylabel("I / Q"); title("Waveform (OTA)");
    legend("I","Q","Location","northeast");

    exportgraphics(f, out_png);
    close(f);
end


function m = empty_meta()
    m = struct( ...
        "schema_version", "", ...
        "protocol", "", ...
        "session_id", 0, ...
        "tape_id", 0, ...
        "segment_id", 0, ...
        "window_id", uint16(0), ...
        "pa_type", "", ...
        "fs_hz", 0, ...
        "window_length_s", 0, ...
        "seq", uint16(0), ...
        "k_ph", int64(0), ...
        "k_next", int64(0), ...
        "gap_to_next", int64(0), ...
        "header_r", NaN );
end


function h = empty_hdr()
    h = struct("k", int64(0), "pa_id", uint16(0), "pa", "", "wid", uint16(0), "seq", uint16(0), "is_stop", false, "r", NaN);
end


function d = empty_drop()
    d = struct( ...
        "seq", uint16(0), ...
        "pa_type", "", ...
        "window_id", uint16(0), ...
        "k_hdr", int64(0), ...
        "k_next", int64(0), ...
        "gap", int64(0), ...
        "reason", "" );
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


function out_root = spliced_root_from_protocol(protocol)
    root = pa_root();
    switch string(protocol)
        case "wifi"
            out_root = fullfile(root, "data", "wifi", "ota", "spliced", "v05");
        case "bluetooth"
            out_root = fullfile(root, "data", "bluetooth", "ota", "spliced", "v05");
        case "zigbee"
            out_root = fullfile(root, "data", "zigbee", "ota", "spliced", "v05");
        otherwise
            error("Unknown protocol %s", protocol);
    end
end


function out_root = results_root_from_protocol(protocol)
    root = pa_root();
    switch string(protocol)
        case "wifi"
            out_root = fullfile(root, "results", "wifi", "ota", "rx_resplice_tape");
        case "bluetooth"
            out_root = fullfile(root, "results", "bluetooth", "ota", "rx_resplice_tape");
        case "zigbee"
            out_root = fullfile(root, "results", "zigbee", "ota", "rx_resplice_tape");
        otherwise
            error("Unknown protocol %s", protocol);
    end
end


function pa_s = normalize_pa_column(pa_col)
    pa_s = string(pa_col);
end