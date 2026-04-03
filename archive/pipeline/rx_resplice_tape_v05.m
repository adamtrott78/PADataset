function rx_resplice_tape_v05()
    P = pa_paths();
%RX_RESPLICE_TAPE_V05 Header-first OTA resplice that tolerates dropped samples.
% Strategy:
%   1) Recover a monotone chain of CRC-valid headers.
%   2) Keep payload i only if header(i+1) starts after payload(i) fully ends.
%   3) If the next valid header starts too early, payload(i) was truncated -> drop it.
%
% Requires:
%   pilot_out_v01/ota_rx_tape_v03/ota_tape_S01_v03.mat
%   pilot_out_v01/tx_tape_v03/tx_tape_v03.mat   (must contain tx_index)
%   pilot_out_v01/data/pilot_S01_PA*.mat        (for optional PNG pairing)

    addpath(P.txrx);

    T = load(fullfile(P.txrx_tapes_ota,"ota_tape_S01_v03.mat"), "x_tape", "rx_cfg");
    x_tape = T.x_tape(:);
    rx_cfg = T.rx_cfg;

    S = load(fullfile(P.txrx_tapes_digital,"tx_tape_v03.mat"), "tx_params", "sync", "tx_index");
    p = S.tx_params;
    sync = S.sync;
    tx_index = S.tx_index;
    tx_lut = make_tx_lut_v05(tx_index);

    out_data = P.data_wifi_spliced_v05;
    if ~exist(out_data,"dir"), mkdir(out_data); end
    if ~exist(P.results_rx_resplice_v05,"dir"), mkdir(P.results_rx_resplice_v05); end

    fprintf("RESPLICE v05 | tape=%d | Fs=%.6f MS/s | frameLen=%d | W=%d | guardN=%d | overruns=%d\n", ...
        numel(x_tape), rx_cfg.Fs/1e6, p.frameLen, p.W, p.guardN, rx_cfg.overruns);

    PAs = ["PA2","PA3","PA4","PA8"];
    X = struct(); M = struct(); counts = struct();
    for pa = PAs
        X.(char(pa)) = complex(zeros(p.W, 400, "single"), zeros(p.W, 400, "single"));
        M.(char(pa)) = repmat(empty_meta_v05(), 1, 400);
        counts.(char(pa)) = 0;
    end

    Lrec = p.frameLen + p.W + p.guardN;
    need_gap = p.frameLen + p.W;

    [k0, ok0, r0] = find_first_record_v05(x_tape, p, sync, tx_lut, 8);
    if ~ok0, error("Start lock failed: no valid first data header found."); end

    [h0, okh0] = raw_decode_valid_header_at_k_v05(x_tape, k0, p, tx_lut, uint16(0));
    if ~okh0, error("Internal error: first record decode failed at k0."); end
    h0.r = r0;

    fprintf("First hdr | k=%d | seq=%d | pa=%s | wid=%d | r=%.2f\n", ...
        h0.k, h0.seq, h0.pa, h0.wid, h0.r);

    H = repmat(empty_hdr_v05(), 1, tx_lut.N + 64);
    nH = 1;
    H(1) = h0;

    t0 = tic; tPrint = tic;
    nExact = 0; nBroad = 0; nFail = 0;
    stop_seen = h0.is_stop;

    while ~stop_seen
        cur = H(nH);
        [nxt, ok, mode] = find_next_valid_header_v05(x_tape, cur, p, sync, tx_lut);
        if ~ok
            nFail = nFail + 1;
            fprintf("NEXT hdr not found after seq=%d | pa=%s | wid=%d | k=%d\n", ...
                cur.seq, cur.pa, cur.wid, cur.k);
            break;
        end

        if nH == numel(H), H = [H repmat(empty_hdr_v05(), 1, 512)]; end %#ok<AGROW>
        nH = nH + 1;
        H(nH) = nxt;
        stop_seen = nxt.is_stop;

        if mode == "exact", nExact = nExact + 1; else, nBroad = nBroad + 1; end

        if toc(tPrint) > 1.0
            fprintf("HDR prog | found=%d | last_seq=%d | last_pa=%s | k=%d | exact=%d | broad=%d | elapsed=%.1fs\n", ...
                nH, H(nH).seq, H(nH).pa, H(nH).k, nExact, nBroad, toc(t0));
            tPrint = tic;
        end
    end

    H = H(1:nH);
    fprintf("HDR done | found=%d | stop_seen=%d | exact=%d | broad=%d | fail=%d | first_seq=%d | last_seq=%d\n", ...
        nH, stop_seen, nExact, nBroad, nFail, H(1).seq, H(end).seq);

    drop_log = repmat(empty_drop_v05(), 1, max(1, nH));
    nDrop = 0; nKeep = 0;

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
            fprintf("DROP | seq=%d | pa=%s | wid=%d | k=%d | next_k=%d | gap=%d\n", ...
                cur.seq, pa, cur.wid, cur.k, nxt.k, gap);
            continue;
        end

        c = counts.(char(pa)) + 1;
        counts.(char(pa)) = c;
        X.(char(pa))(:,c) = x_tape(pay0:pay1);

        M.(char(pa))(c) = struct( ...
            "schema_version", "ota_v05", ...
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
            "header_r", double(cur.r) );

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
            fprintf("DROP | seq=%d | pa=%s | wid=%d | k=%d | reason=unpaired_tail\n", ...
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
        fprintf("Saved %s | %d windows\n", out, c);
    end

    summary = struct();
    summary.version = "v05";
    summary.stop_seen = logical(stop_seen);
    summary.headers_found = H;
    summary.n_headers = int32(nH);
    summary.n_keep = int32(nKeep);
    summary.n_drop = int32(nDrop);
    summary.counts = counts;
    summary.rx_cfg = rx_cfg;
    summary.need_gap = int32(need_gap);
    save(fullfile(P.results_rx_resplice_v05, "resplice_summary_v05.mat"), "summary", "drop_log", "-v7.3");

    png_root = P.results_rx_resplice_v05_png;
    if exist(png_root,"dir"), rmdir(png_root,"s"); end
    mkdir(png_root);

    for pa = PAs
        c = counts.(char(pa));
        K = min(10, c);
        for i = 1:K
            wid = double(M.(char(pa))(i).window_id);
            x_o = X.(char(pa))(:,i);
            [x_d, Fs_d, ok] = load_digital_by_window_id_v05(P.data_wifi_pilot, pa, wid);
            if ~ok, continue; end
            outpng = fullfile(png_root, sprintf("DIG_vs_OTA_%s_w%04d.png", pa, wid));
            plot_pair_dig_vs_ota_v05(pa, x_d, Fs_d, x_o, rx_cfg.Fs, outpng);
        end
    end

    fprintf("RESPLICE DONE | kept=%d | dropped=%d | stop_seen=%d | PNGs=%s\n", ...
        nKeep, nDrop, stop_seen, png_root);
end

function [k0, ok, best_r] = find_first_record_v05(x_tape, p, sync, tx_lut, r_thr)
    ok = false; k0 = 1; best_r = 0;
    offs = unique([1, 1+round(p.frameLen/4), 1+round(p.frameLen/2), 1+round(3*p.frameLen/4)]);
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;

    for o = offs
        for k = o:p.frameLen:kmax
            r = preamble_score_at_k_v05(x_tape, k, p, sync);
            if r < r_thr, continue; end
            [hdr, okh] = raw_decode_valid_header_at_k_v05(x_tape, k, p, tx_lut, uint16(0));
            if ~okh || hdr.is_stop, continue; end
            hdr.r = r; %#ok<NASGU>
            k0 = k;
            best_r = r;
            ok = true;
            return;
        end
    end
end

function [nxt, ok, mode] = find_next_valid_header_v05(x_tape, cur, p, sync, tx_lut)
    Lrec = p.frameLen + p.W + p.guardN;
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    k_exp = double(cur.k) + Lrec;

    nxt = empty_hdr_v05(); ok = false; mode = "";

    % Fast exact/local path around expected position; allow left and right drift.
    smallR = 2048;
    [cand, ok1] = search_exact_range_v05(x_tape, max(double(cur.k)+1, k_exp-smallR), min(kmax, k_exp+smallR), cur, p, tx_lut, k_exp);
    if ok1
        cand.r = preamble_score_at_k_v05(x_tape, cand.k, p, sync);
        nxt = cand; ok = true; mode = "exact"; return;
    end

    % Broad relock path for dropped-sample recovery.
    leftR = max(400000, 4*p.frameLen);
    rightR = max(4*Lrec, 2800000);
    a = max(double(cur.k)+1, k_exp-leftR);
    b = min(kmax, k_exp+rightR);
    if b < a, return; end

    stride = 5000;
    ks = a:stride:b;
    r = zeros(size(ks));
    for i = 1:numel(ks), r(i) = preamble_score_at_k_v05(x_tape, ks(i), p, sync); end

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
    ranges = merge_ranges_v05(ranges);

    best = empty_hdr_v05(); okBest = false;
    for i = 1:size(ranges,1)
        [cand, okc] = search_exact_range_v05(x_tape, ranges(i,1), ranges(i,2), cur, p, tx_lut, k_exp);
        if okc && (~okBest || cand_better_v05(cand, best, cur, k_exp))
            best = cand;
            okBest = true;
        end
    end

    if okBest
        best.r = preamble_score_at_k_v05(x_tape, best.k, p, sync);
        nxt = best;
        ok = true;
        mode = "broad";
    end
end

function [best, ok] = search_exact_range_v05(x_tape, lo, hi, cur, p, tx_lut, k_exp)
    best = empty_hdr_v05(); ok = false;
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    lo = max(lo, double(cur.k)+1);
    hi = min(hi, kmax);
    if hi < lo, return; end

    for k = lo:hi
        [cand, okc] = raw_decode_valid_header_at_k_v05(x_tape, k, p, tx_lut, uint16(cur.seq));
        if ~okc, continue; end
        if ~ok || cand_better_v05(cand, best, cur, k_exp)
            best = cand;
            ok = true;
        end
    end
end

function [hdr, ok] = raw_decode_valid_header_at_k_v05(x_tape, k, p, tx_lut, seq_floor)
    hdr = empty_hdr_v05(); ok = false;
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

    pa = id_to_pa_v05(pa_id);
    if pa == "", return; end
    if seq <= seq_floor, return; end

    s = double(seq);
    if s < 1 || s > tx_lut.N, return; end
    if tx_lut.pa_id(s) ~= pa_id || tx_lut.wid(s) ~= wid, return; end

    hdr = struct("k", int64(k), "pa_id", pa_id, "pa", pa, "wid", wid, "seq", seq, "is_stop", false, "r", NaN);
    ok = true;
end

function tf = cand_better_v05(a, b, cur, k_exp)
    ka = cand_key_v05(a, cur, k_exp);
    kb = cand_key_v05(b, cur, k_exp);
    tf = false;
    for i = 1:numel(ka)
        if ka(i) < kb(i), tf = true; return; end
        if ka(i) > kb(i), return; end
    end
end

function key = cand_key_v05(cand, cur, k_exp)
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

function r = preamble_score_at_k_v05(x_tape, k, p, sync)
    k = round(double(k));
    if k < 1 || (k + p.Lpre - 1) > numel(x_tape), r = 0; return; end
    r = pa_corr_ratio_v03(x_tape(k:k+p.Lpre-1), sync.win_preamble);
end

function ranges = merge_ranges_v05(ranges)
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

function lut = make_tx_lut_v05(tx_index)
    lut = struct();
    lut.N = height(tx_index);
    lut.pa_id = uint16(tx_index.pa_id(:));
    lut.wid = uint16(tx_index.window_id(:));
end

function pa = id_to_pa_v05(pa_id)
    switch double(pa_id)
        case 2, pa = "PA2";
        case 3, pa = "PA3";
        case 4, pa = "PA4";
        case 8, pa = "PA8";
        otherwise, pa = "";
    end
end

function [x_d, Fs_d, ok] = load_digital_by_window_id_v05(data_root, pa, wid)
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

function plot_pair_dig_vs_ota_v05(pa, x_d, Fs_d, x_o, Fs_o, out_png)
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

function h = empty_hdr_v05()
    h = struct("k", int64(0), "pa_id", uint16(0), "pa", "", "wid", uint16(0), "seq", uint16(0), "is_stop", false, "r", NaN);
end

function m = empty_meta_v05()
    m = struct( ...
        "schema_version", "", ...
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

function d = empty_drop_v05()
    d = struct("seq", uint16(0), "pa_type", "", "window_id", uint16(0), "k_hdr", int64(0), "k_next", int64(0), "gap", int64(0), "reason", "");
end