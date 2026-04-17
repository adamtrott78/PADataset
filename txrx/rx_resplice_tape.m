function rx_resplice_tape(protocol, dataset_id_or_ota_file, shard_id_or_tx_spec_file, make_png)
%RX_RESPLICE_TAPE Header-first OTA resplice for one recorded shard.
%
% Usage:
%   rx_resplice_tape
%   rx_resplice_tape("wifi")
%   rx_resplice_tape("wifi", "high_run01", 1)
%   rx_resplice_tape("bluetooth", "high_run01", 2)
%   rx_resplice_tape("zigbee", "high_run01", 1)
%
% New direct shard usage:
%   rx_resplice_tape(protocol, dataset_id, shard_id)
% where dataset_id may be either:
%   "high_run01"           -> expands to "<protocol>_high_run01"
%   "wifi_high_run01"      -> used as-is
%
% Backward-compatible override usage:
%   rx_resplice_tape(protocol, ota_file_override, tx_spec_file_override)
%
% Optional:
%   rx_resplice_tape(..., make_png)
%   make_png defaults to false

    if nargin < 1 || isempty(protocol)
        protocol = "wifi";
    end
    protocol = string(protocol);
    assert(any(protocol == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    if nargin < 2
        dataset_id_or_ota_file = [];
    end
    if nargin < 3
        shard_id_or_tx_spec_file = [];
    end
    if nargin < 4 || isempty(make_png)
        make_png = false;
    end

    R = pa_protocol_roots(protocol);
    addpath(R.txrx);

    [ota_file, spec_file, dataset_full, shard_num, out_data, out_res] = ...
        resolve_resplice_files(protocol, dataset_id_or_ota_file, shard_id_or_tx_spec_file);

    png_root = fullfile(out_res, "png");

    if ~exist(out_data, "dir"), mkdir(out_data); end
    if ~exist(out_res, "dir"), mkdir(out_res); end
    if make_png && ~exist(png_root, "dir"), mkdir(png_root); end

    T = load(ota_file, "x_tape", "rx_cfg");
    x_tape = T.x_tape(:);
    rx_cfg = T.rx_cfg;

    S = load(spec_file, "tx_spec");
    tx_spec = S.tx_spec;
    p = tx_spec.tx_params;
    sync = tx_spec.sync;
    tx_index = tx_spec.tx_index;

    seq_max = height(tx_index);
    wid_max = max(double(tx_index.window_id));

    if strlength(dataset_full) > 0
        fprintf("RESPLICE | protocol=%s | dataset=%s | shard=%03d\n", ...
            protocol, dataset_full, shard_num);
    end
    fprintf("RESPLICE | ota=%s\n", ota_file);
    fprintf("RESPLICE | spec=%s\n", spec_file);
    fprintf("RESPLICE | tape=%d | Fs=%.6f MS/s | frameLen=%d | W=%d | guardN=%d | overruns=%d\n", ...
        numel(x_tape), rx_cfg.Fs/1e6, p.frameLen, p.W, p.guardN, rx_cfg.overruns);

    pilot_root = pilot_root_from_protocol(protocol);
    
    PAs = ["PA2","PA3","PA4","PA8"];
    X = struct(); M = struct(); counts = struct();
    
    pa_col = string(tx_index.pa);
    
    for pa = PAs
        n_alloc = sum(pa_col == pa);
        X.(char(pa)) = complex(zeros(p.W, n_alloc, "single"), zeros(p.W, n_alloc, "single"));
        M.(char(pa)) = repmat(empty_meta(), 1, n_alloc);
        counts.(char(pa)) = 0;
    end
    
    need_gap = p.frameLen + p.W;
    
    [h_seed, ok0] = find_seed_header_direct(x_tape, p, sync, seq_max, wid_max, 20);
    if ~ok0
        error("Seed lock failed: no trustworthy data header found.");
    end
    
    fprintf("Seed hdr | protocol=%s | k=%d | seq=%d | pa=%s | wid=%d | r=%.2f\n", ...
        protocol, h_seed.k, h_seed.seq, h_seed.pa, h_seed.wid, h_seed.r);
    
    [H, nH, stop_seen] = bootstrap_header_chain(x_tape, h_seed, p, seq_max, wid_max);
    
    t0 = tic;
    tPrint = tic;
    nExact = 0;
    nBroad = 0;
    nFail = 0;
    
    while ~stop_seen
        cur = H(nH);
        [nxt, ok, mode] = find_next_valid_header_slipfirst(x_tape, cur, p, seq_max, wid_max);
        if ~ok
            nFail = nFail + 1;
            fprintf("NEXT hdr not found | protocol=%s | after seq=%d | pa=%s | wid=%d | k=%d\n", ...
                protocol, cur.seq, cur.pa, cur.wid, cur.k);
            break;
        end

        if nH == numel(H)
            H = [H repmat(empty_hdr(), 1, 512)];
        end
        nH = nH + 1;
        H(nH) = nxt;
        stop_seen = nxt.is_stop; 

        if nxt.is_stop
            fprintf("HDR FOUND | protocol=%s | STOP | k=%d\n", protocol, nxt.k);
        else
            fprintf("HDR FOUND | protocol=%s | seq=%d | pa=%s | wid=%d | k=%d | mode=%s\n", ...
                protocol, nxt.seq, nxt.pa, nxt.wid, nxt.k, mode);
        end

        if startsWith(mode, "fast")
            nExact = nExact + 1;
        else
            nBroad = nBroad + 1;
        end

        if toc(tPrint) > 1.0
            fprintf("HDR prog | protocol=%s | found=%d | last_seq=%d | last_pa=%s | k=%d | exact=%d | broad=%d | elapsed=%.1fs\n", ...
                protocol, nH, H(nH).seq, H(nH).pa, H(nH).k, nExact, nBroad, toc(t0));
            tPrint = tic;
        end
    end

    H = H(1:nH);
    fprintf("HDR done | protocol=%s | found=%d | stop_seen=%d | exact=%d | broad=%d | fail=%d | first_seq=%d | last_seq=%d\n", ...
        protocol, nH, stop_seen, nExact, nBroad, nFail, H(1).seq, H(end).seq);

    drop_log = repmat(empty_drop(), 1, max(1, nH));
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
            fprintf("DROP | protocol=%s | seq=%d | pa=%s | wid=%d | k=%d | next_k=%d | gap=%d\n", ...
                protocol, cur.seq, pa, cur.wid, cur.k, nxt.k, gap);
            continue;
        end

        c = counts.(char(pa)) + 1;
        counts.(char(pa)) = c;
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
            fprintf("DROP | protocol=%s | seq=%d | pa=%s | wid=%d | k=%d | reason=unpaired_tail\n", ...
                protocol, tail.seq, tail.pa, tail.wid, tail.k);
        end
    end

    drop_log = drop_log(1:nDrop);

    for pa = PAs
        c = counts.(char(pa));
        Xrx_all = X.(char(pa))(:,1:c);
        meta_rx = M.(char(pa))(1:c);
        out = fullfile(out_data, sprintf("ota_rx_%s.mat", pa));
        save(out, "Xrx_all", "meta_rx", "rx_cfg", "-v7.3");
        fprintf("Saved %s | %d windows\n", out, c);
    end

    summary = struct();
    summary.protocol = char(protocol);
    summary.stop_seen = logical(stop_seen);
    summary.headers_found = H;
    summary.n_headers = int32(nH);
    summary.n_keep = int32(nKeep);
    summary.n_drop = int32(nDrop);
    summary.counts = counts;
    summary.rx_cfg = rx_cfg;
    summary.need_gap = int32(need_gap);

    save(fullfile(out_res, "resplice_summary.mat"), "summary", "drop_log", "-v7.3");

    if make_png
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
    else
        fprintf("RESPLICE DONE | protocol=%s | kept=%d | dropped=%d | stop_seen=%d | PNGs=disabled\n", ...
            protocol, nKeep, nDrop, stop_seen);
    end
end

function [h_seed, ok] = find_seed_header_direct(x_tape, p, sync, seq_max, wid_max, n_seed)
    h_seed = empty_hdr();
    ok = false;

    if nargin < 6 || isempty(n_seed)
        n_seed = 20;
    end

    Lrec = double(p.frameLen) + double(p.W) + double(p.guardN);
    k_expected_first = double(p.N_start_frames) * double(p.frameLen) + 1;
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;

    searchR = 12000;
    best_key = [inf, -inf];  % [seq, r]
    t_all = tic;

    fprintf('SEED SEEK | n_seed=%d | k_expected_first=%d | Lrec=%d\n', ...
        n_seed, k_expected_first, Lrec);

    for j = 0:(n_seed-1)
        kc = k_expected_first + j * Lrec;
        lo = max(1, kc - searchR);
        hi = min(kmax, kc + searchR);

        fprintf('  seed=%d/%d | expected_k=%d | search=[%d,%d]\n', ...
            j+1, n_seed, kc, lo, hi);

        for k = lo:hi
            [hdr, okh] = raw_decode_crc_plausible_header_at_k( ...
                x_tape, k, p, uint16(0), uint16(seq_max), uint16(wid_max));

            if ~okh || hdr.is_stop
                continue;
            end

            rr = preamble_score_at_k(x_tape, k, p, sync);
            key = [double(hdr.seq), -rr];

            fprintf('    seed cand | k=%d | seq=%d | pa=%s | wid=%d | r=%.2f\n', ...
                k, hdr.seq, hdr.pa, hdr.wid, rr);

            if ~ok || lexicographically_better(key, best_key)
                hdr.r = rr;
                h_seed = hdr;
                best_key = key;
                ok = true;
            end
        end
    end

    if ok
        fprintf('SEED SEEK SUCCESS | seq=%d | k=%d | r=%.2f | elapsed=%.1fs\n', ...
            h_seed.seq, h_seed.k, h_seed.r, toc(t_all));
    else
        fprintf('SEED SEEK FAILED | elapsed=%.1fs\n', toc(t_all));
    end
end

function [H, nH, stop_seen] = bootstrap_header_chain(x_tape, h_seed, p, seq_max, wid_max)
    Hf = repmat(empty_hdr(), 1, seq_max + 64);
    nf = 1;
    Hf(1) = h_seed;
    stop_seen = h_seed.is_stop;

    % ---------- forward ----------
    cur = h_seed;
    while ~stop_seen
        [nxt, ok, mode] = find_next_valid_header_slipfirst(x_tape, cur, p, seq_max, wid_max);
        if ~ok
            fprintf('FWD BREAK | after seq=%d | k=%d\n', cur.seq, cur.k);
            break;
        end

        nf = nf + 1;
        Hf(nf) = nxt;
        cur = nxt;
        stop_seen = nxt.is_stop;

        if nxt.is_stop
            fprintf('FWD HDR | STOP | k=%d | mode=%s\n', nxt.k, mode);
        else
            fprintf('FWD HDR | seq=%d | pa=%s | wid=%d | k=%d | mode=%s\n', ...
                nxt.seq, nxt.pa, nxt.wid, nxt.k, mode);
        end
    end

    % ---------- backward ----------
    Hb = repmat(empty_hdr(), 1, max(1, double(h_seed.seq)));
    nb = 0;
    cur = h_seed;

    while double(cur.seq) > 1
        [prv, ok, mode] = find_prev_valid_header_slipfirst(x_tape, cur, p, seq_max, wid_max);
        if ~ok
            fprintf('BWD BREAK | before seq=%d | k=%d\n', cur.seq, cur.k);
            break;
        end

        nb = nb + 1;
        Hb(nb) = prv;
        cur = prv;

        fprintf('BWD HDR | seq=%d | pa=%s | wid=%d | k=%d | mode=%s\n', ...
            prv.seq, prv.pa, prv.wid, prv.k, mode);
    end

    H = [fliplr(Hb(1:nb)) Hf(1:nf)];
    nH = numel(H);
end

function [prv, ok, mode] = find_prev_valid_header_slipfirst(x_tape, cur, p, seq_max, wid_max)
    prv = empty_hdr();
    ok = false;
    mode = "";

    Lrec = double(p.frameLen) + double(p.W) + double(p.guardN);
    seq_target = uint16(double(cur.seq) - 1);

    if double(seq_target) < 1
        return;
    end

    k_nom = double(cur.k) - Lrec;

    % 1) exact nominal
    [cand, okc] = search_exact_range_for_seq( ...
        x_tape, round(k_nom-2), round(k_nom+2), p, seq_target, seq_max, wid_max);
    if okc
        prv = cand;
        ok = true;
        mode = "fast_nominal_back";
        return;
    end

    % 2) positive frame-slip hypotheses when walking backward
    slipFrames = 1:12;
    localR = 1800;

    for sf = slipFrames
        center = k_nom + double(sf) * double(p.frameLen);

        [cand, okc] = search_exact_range_for_seq( ...
            x_tape, round(center-localR), round(center+localR), p, seq_target, seq_max, wid_max);
        if okc
            prv = cand;
            ok = true;
            mode = sprintf("back_slip_%d", sf);
            return;
        end
    end

    % 3) limited local scan only
    scan_lo = max(1, round(k_nom - 2 * double(p.frameLen)));
    scan_hi = min(double(cur.k)-1, round(k_nom + 12 * double(p.frameLen)));

    fprintf('BWD SCAN | before seq=%d | scan=[%d,%d]\n', cur.seq, scan_lo, scan_hi);

    for k = scan_lo:scan_hi
        [hdr, okh] = raw_decode_crc_plausible_header_at_k( ...
            x_tape, k, p, uint16(double(seq_target)-1), uint16(seq_max), uint16(wid_max));

        if ~okh || hdr.is_stop
            continue;
        end

        if double(hdr.seq) ~= double(seq_target)
            continue;
        end

        prv = hdr;
        ok = true;
        mode = "scan_back";
        return;
    end
end

function [k_last, n_found, ok] = find_last_start_frame_anchor(x_tape, p, sync)
    k_last = int64(0);
    n_found = 0;
    ok = false;

    kmax = numel(x_tape) - numel(sync.start_preamble) + 1;
    seed_hi = min(kmax, 2 * double(p.frameLen));

    fprintf('START SEEK BEGIN | seed_search=[1,%d] | frameLen=%d\n', ...
        seed_hi, p.frameLen);

    [seed_k, seed_r] = collect_start_seed_candidates( ...
        x_tape, 1, seed_hi, sync.start_preamble, 12);

    if isempty(seed_k)
        fprintf('START SEEK FAILED | no plausible start seeds found\n');
        return;
    end

    best_len = -inf;
    best_score = -inf;
    best_last = 0;
    best_first = 0;

    for i = 1:numel(seed_k)
        fprintf('START SEED TEST | %d/%d | seed_k=%d | seed_r=%.2f\n', ...
            i, numel(seed_k), seed_k(i), seed_r(i));

        [last_k_i, len_i, score_i] = grow_start_chain( ...
            x_tape, seed_k(i), p, sync.start_preamble, 12);

        fprintf('START SEED RESULT | seed_k=%d | chain_len=%d | last_k=%d | score=%.2f\n', ...
            seed_k(i), len_i, last_k_i, score_i);

        if len_i > best_len || (len_i == best_len && score_i > best_score)
            best_len = len_i;
            best_score = score_i;
            best_last = last_k_i;
            best_first = seed_k(i);
        end
    end

    if best_len < 2
        fprintf('START ANCHOR FAILED | best chain too short | len=%d\n', best_len);
        return;
    end

    k_last = int64(best_last);
    n_found = best_len;
    ok = true;

    fprintf('START ANCHOR CHOSEN | first_k=%d | last_k=%d | n_found=%d | score=%.2f\n', ...
        best_first, best_last, n_found, best_score);
end

function [seed_k, seed_r] = collect_start_seed_candidates(x_tape, lo, hi, pre, r_thr)
    seed_k = [];
    seed_r = [];

    pre = double(pre(:));
    N = numel(pre);
    kmax = numel(x_tape) - N + 1;

    lo = max(1, round(lo));
    hi = min(kmax, round(hi));
    if hi < lo
        return;
    end

    coarse_step = 250;
    ks = lo:coarse_step:hi;
    if ks(end) ~= hi
        ks(end+1) = hi;
    end

    r = -inf(size(ks));
    for i = 1:numel(ks)
        k = ks(i);
        r(i) = pa_corr_ratio_v03(x_tape(k:k+N-1), pre);
    end

    pick = find(r >= r_thr);
    if isempty(pick)
        [~, ord] = sort(r, 'descend');
        pick = ord(1:min(12, numel(ord)));
    else
        [~, ord] = sort(r(pick), 'descend');
        pick = pick(ord(1:min(12, numel(ord))));
    end

    cand_k = zeros(numel(pick), 1);
    cand_r = zeros(numel(pick), 1);
    n = 0;

    for ii = 1:numel(pick)
        center = ks(pick(ii));
        [k_ref, ok_ref, r_ref] = search_preamble_near(x_tape, center, 1200, pre, r_thr);
        if ~ok_ref
            continue;
        end
        n = n + 1;
        cand_k(n) = double(k_ref);
        cand_r(n) = r_ref;
    end

    cand_k = cand_k(1:n);
    cand_r = cand_r(1:n);

    if isempty(cand_k)
        return;
    end

    % dedupe nearby candidates; keep the strongest one in each cluster
    [cand_k, ord] = sort(cand_k);
    cand_r = cand_r(ord);

    keep_k = [];
    keep_r = [];

    cluster_k = cand_k(1);
    cluster_r = cand_r(1);

    for i = 2:numel(cand_k)
        if abs(cand_k(i) - cluster_k(end)) <= 1500
            if cand_r(i) > cluster_r
                cluster_k = cand_k(i);
                cluster_r = cand_r(i);
            end
        else
            keep_k(end+1,1) = cluster_k; %#ok<AGROW>
            keep_r(end+1,1) = cluster_r; %#ok<AGROW>
            cluster_k = cand_k(i);
            cluster_r = cand_r(i);
        end
    end

    keep_k(end+1,1) = cluster_k;
    keep_r(end+1,1) = cluster_r;

    seed_k = keep_k;
    seed_r = keep_r;

    fprintf('START SEEDS |');
    for i = 1:numel(seed_k)
        fprintf(' (%d, %.2f)', seed_k(i), seed_r(i));
    end
    fprintf('\n');
end

function [last_k, len, score] = grow_start_chain(x_tape, seed_k, p, pre, r_thr)
    cur_k = double(seed_k);
    last_k = cur_k;
    len = 1;
    score = 0;

    localR = 2500;
    max_gap_frames = 4;
    max_chain = double(p.N_start_frames) + 8;

    while len < max_chain
        found = false;
        best_k = 0;
        best_r = -inf;
        best_gap = inf;
        best_err = inf;

        for gap = 1:max_gap_frames
            kc = cur_k + gap * double(p.frameLen);
            [k_next, ok_next, r_next] = search_preamble_near(x_tape, kc, localR, pre, r_thr);
            if ~ok_next
                continue;
            end

            err = abs(double(k_next) - kc);

            if ~found || gap < best_gap || ...
               (gap == best_gap && r_next > best_r) || ...
               (gap == best_gap && abs(r_next - best_r) < 1e-9 && err < best_err)
                found = true;
                best_k = double(k_next);
                best_r = r_next;
                best_gap = gap;
                best_err = err;
            end
        end

        if ~found
            break;
        end

        fprintf('START CHAIN | n=%d -> %d | k=%d | gap_frames=%d | r=%.2f\n', ...
            len, len+1, best_k, best_gap, best_r);

        cur_k = best_k;
        last_k = cur_k;
        len = len + 1;

        % prefer longer chains, penalize skipped missing frames a bit
        score = score + best_r - 200 * (best_gap - 1);
    end
end

function [h_best, ok] = find_first_data_header_from_anchor(x_tape, k_start_last, p, sync, seq_max, wid_max, max_seq_probe)
    h_best = empty_hdr();
    ok = false;

    Lrec = double(p.frameLen) + double(p.W) + double(p.guardN);

    % After the last start frame, the first PH frame begins one frame later.
    k_base = double(k_start_last) + double(p.frameLen);

    % Early tape may already be compressed by dropped 100k chunks.
    % Search seq 1..max_seq_probe with discrete negative frame-slip hypotheses.
    slipFrames = 0:-1:-40;
    localR = 1800;

    fprintf('FIRST DATA SEEK | base_k=%d | seq_probe=1:%d\n', k_base, max_seq_probe);

    for seqj = 1:max_seq_probe
        k_nom = k_base + (seqj - 1) * Lrec;

        found_any = false;
        best_key = [inf, inf];
        best_hdr = empty_hdr();

        fprintf('  seq=%d | nominal_k=%d\n', seqj, k_nom);

        for sf = slipFrames
            center = k_nom + double(sf) * double(p.frameLen);
            lo = round(center - localR);
            hi = round(center + localR);

            [cand, okc] = search_exact_range_for_seq(x_tape, lo, hi, p, uint16(seqj), seq_max, wid_max);
            if ~okc
                continue;
            end

            cand.r = preamble_score_at_k(x_tape, cand.k, p, sync);
            key = [abs(sf), abs(double(cand.k) - center)];

            fprintf('    FIRST DATA CAND | seq=%d | k=%d | slip=%d | r=%.2f\n', ...
                cand.seq, cand.k, sf, cand.r);

            if ~found_any || lexicographically_better(key, best_key)
                best_hdr = cand;
                best_key = key;
                found_any = true;
            end
        end

        if found_any
            h_best = best_hdr;
            ok = true;
            fprintf('FIRST DATA SUCCESS | seq=%d | k=%d | r=%.2f\n', ...
                h_best.seq, h_best.k, h_best.r);
            return;
        end
    end
end


function [nxt, ok, mode] = find_next_valid_header_slipfirst(x_tape, cur, p, seq_max, wid_max)
    nxt = empty_hdr();
    ok = false;
    mode = "";

    Lrec = double(p.frameLen) + double(p.W) + double(p.guardN);
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;

    seq_target = uint16(double(cur.seq) + 1);
    k_nom = double(cur.k) + Lrec;

    % 1) exact nominal
    [cand, okc] = search_exact_range_for_seq(x_tape, round(k_nom-2), round(k_nom+2), p, seq_target, seq_max, wid_max);
    if okc
        nxt = cand;
        ok = true;
        mode = "fast_nominal";
        return;
    end

    % 2) exact nominal stop
    [stop_hdr, ok_stop] = search_stop_range(x_tape, round(k_nom-32), round(k_nom+32), p, cur.seq, seq_max, wid_max);
    if ok_stop
        nxt = stop_hdr;
        ok = true;
        mode = "fast_stop";
        fprintf('STOP FOUND | after seq=%d | stop_k=%d\n', cur.seq, nxt.k);
        return;
    end

    % 3) discrete negative frame-slip hypotheses
    slipFrames = -1:-1:-12;
    localR = 1800;

    for sf = slipFrames
        center = k_nom + double(sf) * double(p.frameLen);

        [cand, okc] = search_exact_range_for_seq( ...
            x_tape, round(center-localR), round(center+localR), p, seq_target, seq_max, wid_max);
        if okc
            nxt = cand;
            ok = true;
            mode = sprintf("slip_%d", sf);
            return;
        end

        [stop_hdr, ok_stop] = search_stop_range( ...
            x_tape, round(center-localR), round(center+localR), p, cur.seq, seq_max, wid_max);
        if ok_stop
            nxt = stop_hdr;
            ok = true;
            mode = sprintf("stop_slip_%d", sf);
            fprintf('STOP FOUND | after seq=%d | stop_k=%d\n', cur.seq, nxt.k);
            return;
        end
    end

    % 4) last resort: limited brute-force scan, not whole remaining tape
    scan_lo = max(double(cur.k)+1, double(cur.k) + double(p.frameLen));
    scan_hi = min(kmax, round(k_nom + 2 * double(p.frameLen)));

    fprintf('SCAN | after seq=%d | scan=[%d,%d]\n', cur.seq, scan_lo, scan_hi);

    for k = scan_lo:scan_hi
        if mod(k - scan_lo, 100000) == 0
            fprintf('SCAN PROG | after seq=%d | checked up to k=%d\n', cur.seq, k);
        end

        [hdr, okh] = raw_decode_crc_plausible_header_at_k(x_tape, k, p, cur.seq, uint16(seq_max), uint16(wid_max));
        if ~okh
            continue;
        end

        nxt = hdr;
        ok = true;

        if hdr.is_stop
            mode = "stop_recover";
            fprintf('STOP FOUND | after seq=%d | stop_k=%d\n', cur.seq, hdr.k);
            return;
        end

        mode = "scan_recover";
        return;
    end
end

function [k_best, ok, best_r] = search_preamble_near(x_tape, kc, radius, pre, r_thr)
    k_best = int64(0);
    ok = false;
    best_r = -inf;

    pre = double(pre(:));
    N = numel(pre);
    kmax = numel(x_tape) - N + 1;

    lo = max(1, round(double(kc) - double(radius)));
    hi = min(kmax, round(double(kc) + double(radius)));
    if hi < lo
        fprintf('PREAMBLE SEEK INVALID | kc=%d | radius=%d | search=[%d,%d]\n', ...
            round(double(kc)), round(double(radius)), lo, hi);
        return;
    end

    % ---------- tuning knobs ----------
    coarse_step   = 50;     % coarse grid spacing
    refine_radius = 250;    % +/- refine around top coarse peaks
    topN          = 6;      % refine the top-N coarse candidates
    plateau_frac  = 0.985;  % choose earliest k in the near-peak plateau
    % ----------------------------------

    fprintf('PREAMBLE SEEK | kc=%d | radius=%d | search=[%d,%d] | N=%d | thr=%.2f\n', ...
        round(double(kc)), round(double(radius)), lo, hi, N, r_thr);

    % ---------- coarse pass ----------
    ks = lo:coarse_step:hi;
    if ks(end) ~= hi
        ks(end+1) = hi;
    end

    r_coarse = -inf(size(ks));
    t0 = tic;
    tPrint = tic;

    for i = 1:numel(ks)
        k = ks(i);
        r_coarse(i) = pa_corr_ratio_v03(x_tape(k:k+N-1), pre);

        if toc(tPrint) > 1.0 || i == numel(ks)
            [pk, ipk] = max(r_coarse(1:i));
            fprintf('  COARSE PROG | checked=%d/%d | k=%d | best_r=%.2f @ %d | elapsed=%.1fs\n', ...
                i, numel(ks), k, pk, ks(ipk), toc(t0));
            tPrint = tic;
        end
    end

    [~, ord] = sort(r_coarse, 'descend');
    ord = ord(1:min(topN, numel(ord)));
    centers = ks(ord);

    fprintf('  COARSE DONE | best coarse centers =');
    fprintf(' %d', centers);
    fprintf('\n');

    % ---------- build merged refine ranges ----------
    ranges = zeros(numel(centers), 2);
    for i = 1:numel(centers)
        ranges(i,1) = max(lo, centers(i) - refine_radius);
        ranges(i,2) = min(hi, centers(i) + refine_radius);
    end

    ranges = sortrows(ranges, 1);
    merged = ranges(1,:);
    for i = 2:size(ranges,1)
        if ranges(i,1) <= merged(end,2) + 1
            merged(end,2) = max(merged(end,2), ranges(i,2));
        else
            merged = [merged; ranges(i,:)]; %#ok<AGROW>
        end
    end

    fprintf('  REFINE RANGES:\n');
    for i = 1:size(merged,1)
        fprintf('    range %d/%d = [%d,%d]\n', i, size(merged,1), merged(i,1), merged(i,2));
    end

    % ---------- refine pass ----------
    t_ref = tic;
    tPrint = tic;
    n_total = sum(merged(:,2) - merged(:,1) + 1);
    n_done = 0;

    K_ref = zeros(n_total,1);
    R_ref = -inf(n_total,1);
    ptr = 0;

    for i = 1:size(merged,1)
        rlo = merged(i,1);
        rhi = merged(i,2);

        for k = rlo:rhi
            r = pa_corr_ratio_v03(x_tape(k:k+N-1), pre);

            ptr = ptr + 1;
            K_ref(ptr) = k;
            R_ref(ptr) = r;

            if r > best_r
                best_r = r;
            end

            n_done = n_done + 1;
            if toc(tPrint) > 1.0 || n_done == n_total
                [pk, ipk] = max(R_ref(1:ptr));
                fprintf('  REFINE PROG | checked=%d/%d | k=%d | best_r=%.2f @ %d | elapsed=%.1fs\n', ...
                    n_done, n_total, k, pk, K_ref(ipk), toc(t_ref));
                tPrint = tic;
            end
        end
    end

    K_ref = K_ref(1:ptr);
    R_ref = R_ref(1:ptr);

    [peak_r, ipeak] = max(R_ref);
    k_peak = K_ref(ipeak);

    ok = peak_r >= r_thr;
    if ~ok
        best_r = peak_r;
        k_best = int64(k_peak);
        fprintf('PREAMBLE DONE | ok=0 | peak_r=%.2f | k_peak=%d | thr=%.2f | total_elapsed=%.1fs\n', ...
            peak_r, k_peak, r_thr, toc(t0));
        return;
    end

    % ---------- boundary selection ----------
    % Choose the earliest sample in the contiguous near-peak plateau
    % containing the peak. This is much closer to the actual frame start
    % than the raw argmax.
    plateau_thr = max(r_thr, plateau_frac * peak_r);
    mask = (R_ref >= plateau_thr);

    left = ipeak;
    while left > 1 && mask(left-1) && (K_ref(left) - K_ref(left-1) == 1)
        left = left - 1;
    end

    right = ipeak;
    while right < numel(K_ref) && mask(right+1) && (K_ref(right+1) - K_ref(right) == 1)
        right = right + 1;
    end

    k_boundary = K_ref(left);

    k_best = int64(k_boundary);
    best_r = peak_r;

    fprintf('PREAMBLE DONE | ok=1 | peak_r=%.2f | k_peak=%d | plateau_thr=%.2f | boundary_k=%d | run=[%d,%d] | total_elapsed=%.1fs\n', ...
        peak_r, k_peak, plateau_thr, k_boundary, K_ref(left), K_ref(right), toc(t0));
end

function tf = lexicographically_better(a, b)
    tf = false;
    for i = 1:numel(a)
        if a(i) < b(i)
            tf = true;
            return;
        end
        if a(i) > b(i)
            return;
        end
    end
end

function [best, ok] = search_exact_range_for_seq(x_tape, lo, hi, p, seq_target, seq_max, wid_max)
    best = empty_hdr();
    ok = false;

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    lo = max(1, lo);
    hi = min(hi, kmax);
    if hi < lo
        return;
    end

    kc = round((lo + hi) / 2);
    best_dist = inf;

    for k = lo:hi
        [hdr, okh] = raw_decode_crc_plausible_header_at_k( ...
            x_tape, k, p, uint16(seq_target - 1), uint16(seq_max), uint16(wid_max));

        if ~okh
            continue;
        end

        if hdr.is_stop
            continue;
        end

        if double(hdr.seq) ~= double(seq_target)
            continue;
        end

        dist = abs(double(k) - kc);
        if ~ok || dist < best_dist
            best = hdr;
            ok = true;
            best_dist = dist;
        end
    end
end

function [best, ok] = search_stop_range(x_tape, lo, hi, p, seq_floor, seq_max, wid_max)
    best = empty_hdr();
    ok = false;

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    lo = max(1, lo);
    hi = min(hi, kmax);
    if hi < lo
        return;
    end

    for k = lo:hi
        [hdr, okh] = raw_decode_crc_plausible_header_at_k( ...
            x_tape, k, p, uint16(seq_floor), uint16(seq_max), uint16(wid_max));

        if ~okh
            continue;
        end

        if hdr.is_stop
            best = hdr;
            ok = true;
            return;
        end
    end
end

function [hdr, ok] = raw_decode_crc_plausible_header_at_k(x_tape, k, p, seq_floor, seq_max, wid_max)
    hdr = empty_hdr();
    ok = false;

    k = round(double(k));
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    if k < 1 || k > kmax
        return;
    end

    hdr_samp = x_tape(k + p.Lpre + (1:p.Lhdr));
    [pa_id, wid, seq, crc_ok] = pa_dbpsk_header_decode_v03(hdr_samp, p.spsHdr);
    if ~crc_ok
        return;
    end

    pa_id = uint16(pa_id);
    wid   = uint16(wid);
    seq   = uint16(seq);

    is_stop = (double(pa_id) == 15) && (double(wid) == 65535) && (double(seq) == 65535);
    if is_stop
        hdr = struct("k", int64(k), "pa_id", pa_id, "pa", "", "wid", wid, "seq", seq, "is_stop", true, "r", NaN);
        ok = true;
        return;
    end

    pa = id_to_pa(pa_id);
    if pa == ""
        return;
    end

    if seq <= seq_floor
        return;
    end

    if double(seq) > double(seq_max)
        return;
    end

    if double(wid) < 1 || double(wid) > double(wid_max)
        return;
    end

    hdr = struct("k", int64(k), "pa_id", pa_id, "pa", pa, "wid", wid, "seq", seq, "is_stop", false, "r", NaN);
    ok = true;
end

function r = preamble_score_at_k(x_tape, k, p, sync)
    k = round(double(k));
    if k < 1 || (k + p.Lpre - 1) > numel(x_tape), r = 0; return; end
    r = pa_corr_ratio_v03(x_tape(k:k+p.Lpre-1), sync.win_preamble);
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

function h = empty_hdr()
    h = struct("k", int64(0), "pa_id", uint16(0), "pa", "", "wid", uint16(0), "seq", uint16(0), "is_stop", false, "r", NaN);
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

function [ota_file, spec_file, dataset_full, shard_num, out_data, out_res] = ...
    resolve_resplice_files(protocol_s, dataset_id_or_ota_file, shard_id_or_tx_spec_file)

    dataset_full = "";
    shard_num = [];

    % old default protocol-only mode
    if isempty(dataset_id_or_ota_file)
        R = pa_protocol_roots(protocol_s);
        ota_file = fullfile(R.txrx_tapes_ota, "ota_tape_S01.mat");
        spec_file = fullfile(R.txrx_tapes_digital, "tx_spec.mat");
        out_data = spliced_root_from_protocol(protocol_s);
        out_res  = results_root_from_protocol(protocol_s);
        return;
    end

    arg2 = string(dataset_id_or_ota_file);

    if strlength(arg2) == 0
        R = pa_protocol_roots(protocol_s);
        ota_file = fullfile(R.txrx_tapes_ota, "ota_tape_S01.mat");
        spec_file = fullfile(R.txrx_tapes_digital, "tx_spec.mat");
        out_data = spliced_root_from_protocol(protocol_s);
        out_res  = results_root_from_protocol(protocol_s);
        return;
    end

    % override mode: rx_resplice_tape(protocol, ota_file_override, tx_spec_file_override)
    if endsWith(lower(arg2), ".mat")
        ota_file = char(arg2);

        if isempty(shard_id_or_tx_spec_file)
            error("Override usage requires tx_spec_file_override as the 3rd argument.");
        end

        spec_file = char(string(shard_id_or_tx_spec_file));

        if ~isfile(ota_file)
            error("OTA tape file not found: %s", ota_file);
        end
        if ~isfile(spec_file)
            error("TX spec file not found: %s", spec_file);
        end

        out_data = spliced_root_from_protocol(protocol_s);
        out_res  = results_root_from_protocol(protocol_s);
        return;
    end

    % direct shard mode
    if isempty(shard_id_or_tx_spec_file) || ~(isnumeric(shard_id_or_tx_spec_file) || islogical(shard_id_or_tx_spec_file))
        error([ ...
            "For direct shard usage, call rx_resplice_tape(protocol, dataset_id, shard_id). " ...
            "For override usage, call rx_resplice_tape(protocol, ota_file_override, tx_spec_file_override)."]);
    end

    shard_num = validate_shard_id(shard_id_or_tx_spec_file);
    dataset_full = normalize_dataset_id(protocol_s, arg2);

    R = pa_protocol_roots(protocol_s);
    ota_file = fullfile(R.txrx_tapes_ota, char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_num));
    spec_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_spec_shard_%03d.mat", shard_num));

    if ~isfile(ota_file)
        error("OTA tape file not found: %s", ota_file);
    end
    if ~isfile(spec_file)
        error("TX spec file not found: %s", spec_file);
    end

    out_data = fullfile(spliced_root_from_protocol(protocol_s), char(dataset_full), sprintf("shard_%03d", shard_num));
    out_res  = fullfile(results_root_from_protocol(protocol_s), char(dataset_full), sprintf("shard_%03d", shard_num));
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
            out_root = fullfile(root, "data", "wifi", "ota", "spliced", "v06");
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